import hashlib
import json
import re
import uuid
import secrets
from django.conf import settings
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from datetime import timedelta
from .catalog import catalogue
from .models import Order, OrderLine, OrderEvent, Review, ReviewEvent, Notification, RateLimit
from server.bank_transfer import BankTransferConfig, quote_items, validate_test_shipping, InvalidTransfer

class CheckoutClosed(ValidationError): pass

def session_hash(request):
    if not request.session.session_key: request.session.create()
    # La rotación de sesión al iniciar sesión conserva la idempotencia del mismo navegador.
    # Logout o cambio de usuario vacía la sesión; no se comparte identidad con otro comprador.
    if not request.session.get('_shop_client_id'):
        request.session['_shop_client_id'] = secrets.token_urlsafe(32)
    return hashlib.sha256(request.session['_shop_client_id'].encode()).hexdigest()

def limit(key, count, seconds):
    hashed = hashlib.sha256(key.encode()).hexdigest()
    now = timezone.now(); cutoff = now - timedelta(seconds=seconds)
    row, _ = RateLimit.objects.get_or_create(key=hashed)
    RateLimit.objects.filter(pk=row.pk, starts__lt=cutoff).update(starts=now, count=0)
    return bool(RateLimit.objects.filter(pk=row.pk,count__lt=count).update(count=F('count')+1))

def create_order(request, body):
    if not isinstance(body, dict) or set(body) - {'items','customer','demoConsent','requestKey','paymentMethod'} or not {'items','customer','demoConsent','requestKey'} <= set(body) or body['demoConsent'] is not True:
        raise ValidationError('Datos de pedido no válidos.')
    if settings.MODE == 'family' and not (settings.FAMILY_CHECKOUT_ENABLED and settings.FAMILY_MONEY_RELEASED):
        raise CheckoutClosed('La configuración familiar está preparada, pero el checkout monetario permanece bloqueado. No hagas transferencias.')
    if settings.MODE == 'family' and not request.user.is_authenticated: raise PermissionDenied
    request_key = body['requestKey']
    if not isinstance(request_key,str) or not re.fullmatch(r'[A-Za-z0-9-]{16,100}',request_key): raise ValidationError('Solicitud no válida.')
    products = {p['id']:p for p in catalogue()['products']}
    try:
        quote = quote_items(body['items'],products)
        customer = validate_test_shipping(body['customer'])
    except (InvalidTransfer, KeyError, TypeError) as e: raise ValidationError('Comprueba datos, tallas y cantidades.') from e
    method = 'free_demo' if quote['totalMinor'] == 0 else 'bank_transfer'
    requested = body.get('paymentMethod', 'free_demo')
    if requested != method or (settings.MODE == 'demo' and quote['totalMinor'] != 0): raise ValidationError('Método de pago no disponible.')
    sid = session_hash(request)
    fingerprint = hashlib.sha256(json.dumps({'items':sorted(body['items'],key=lambda i:(i['id'],i['size'])), 'customer':customer, 'method':method},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    with transaction.atomic():
        old = Order.objects.filter(session_hash=sid,request_key=request_key,environment=settings.MODE).first()
        if old:
            if old.fingerprint != fingerprint: raise ValidationError('La solicitud ya se utilizó con otros datos.')
            return old
        if not limit('order:'+sid,3,900): raise ValidationError('Límite de pedidos de prueba alcanzado.')
        bank = {}
        if method == 'bank_transfer':
            try: bank = BankTransferConfig(True,settings.BANK_BENEFICIARY,settings.BANK_IBAN).validated_details()
            except ValueError as e: raise ValidationError('Configuración bancaria no disponible.') from e
        number = ('FAMILY-' if settings.MODE == 'family' else 'DEMO-') + str(uuid.uuid4())
        status = Order.Status.PENDING if method == 'bank_transfer' else Order.Status.DEMO
        order, created = Order.objects.get_or_create(session_hash=sid,request_key=request_key,environment=settings.MODE,
            defaults={'number':number,'fingerprint':fingerprint,'owner':request.user if request.user.is_authenticated else None,
                      'method':method,'status':status,'customer':customer,'total_minor':quote['totalMinor'],
                      'bank_snapshot':dict(bank,reference=number,amountMinor=quote['totalMinor'],currency='EUR') if bank else {}})
        if not created:
            if order.fingerprint != fingerprint: raise ValidationError('Solicitud duplicada con datos diferentes.')
            return order
        OrderLine.objects.bulk_create([OrderLine(order=order,product_id=i['id'],name=i['name'],size=i['size'],quantity=i['quantity'],unit_price_minor=i['unitPriceMinor']) for i in quote['items']])
        OrderEvent.objects.create(order=order,actor=request.user if request.user.is_authenticated else None,new_status=status,reason='Registro de pedido de prueba sin entrega de productos.')
        enqueue(order,'order_buyer'); enqueue(order,'order_seller')
        return order

def enqueue(order,event):
    notification,_ = Notification.objects.get_or_create(order=order,event=event,defaults={'payload':{
        'number':order.number,'environment':order.environment,'status':order.status,'method':order.method,
        'totalMinor':order.total_minor,'customer':order.customer,'bank':order.bank_snapshot,
        'items':[{'name':i.name,'size':i.size,'quantity':i.quantity,'unitPriceMinor':i.unit_price_minor} for i in order.lines.all()]}})
    return notification

def public_receipt(order):
    states = {n.event:n.status for n in order.notifications.all()}
    data = {'id':order.number,'demo':True,'environment':order.environment,'totalMinor':order.total_minor,
            'paymentStatus':order.status,'items':[{'id':i.product_id,'size':i.size,'quantity':i.quantity} for i in order.lines.all()],
            'mail':{'buyer':{'status':states.get('order_buyer','not_configured')},'seller':{'status':states.get('order_seller','not_configured')}}}
    if order.method == 'bank_transfer' and order.status == Order.Status.PENDING: data['bankTransfer'] = order.bank_snapshot
    return data

@transaction.atomic
def transition_order(actor,order_id,target,reason):
    permission = 'shop.confirm_transfer' if target == Order.Status.PAID else 'shop.cancel_order'
    if not actor.is_active or not actor.is_staff or not actor.has_perm(permission): raise PermissionDenied
    if target not in (Order.Status.PAID,Order.Status.CANCELLED) or len(reason.strip())<5: raise ValidationError('Confirma el motivo de la operación.')
    order = Order.objects.get(pk=order_id)
    if order.environment != settings.MODE: raise PermissionDenied
    if target == Order.Status.PAID:
        if order.method != 'bank_transfer' or order.total_minor <= 0 or order.status not in (Order.Status.PENDING,Order.Status.PAID): raise ValidationError('Este pedido no admite confirmación de transferencia.')
        # Solo fixtures en pruebas automatizadas o una futura liberación expresamente revisada.
        if not settings.FAMILY_MONEY_RELEASED and not order.is_fixture: raise CheckoutClosed('Confirmación monetaria bloqueada en esta entrega local.')
    if order.status == target: return False
    allowed = [Order.Status.PENDING] if target == Order.Status.PAID else [Order.Status.PENDING,Order.Status.DEMO]
    if order.status not in allowed: raise ValidationError('Transición no permitida.')
    changed = Order.objects.filter(pk=order.pk,status=order.status).update(status=target)
    if not changed: return False
    OrderEvent.objects.create(order=order,actor=actor,old_status=order.status,new_status=target,reason=reason.strip())
    order.status = target
    if target == Order.Status.PAID: enqueue(order,'paid_buyer')
    return True

def submit_review(request,body):
    if not isinstance(body,dict) or set(body) != {'publicName','rating','comment'}: raise ValidationError('Solo se admite alias, valoración y comentario.')
    name,rating,comment = body['publicName'],body['rating'],body['comment']
    if not isinstance(name,str) or not re.fullmatch(r"[\w .'-]{2,60}",name.strip()) or re.search(r'\d{7,}',name): raise ValidationError('Utiliza un alias público sin datos de contacto.')
    if type(rating) is not int or rating not in range(1,6) or not isinstance(comment,str) or not 10<=len(comment.strip())<=2000 or any(ord(c)<32 and c not in '\n\t' for c in comment): raise ValidationError('Selecciona 1–5 estrellas y un comentario de 10–2000 caracteres.')
    sid = session_hash(request)
    if not limit('review:'+sid,5,86400): raise ValidationError('Límite de opiniones de prueba alcanzado.')
    purchases = Order.objects.filter(environment=settings.MODE,status__in=[Order.Status.DEMO,Order.Status.PAID])
    purchases = purchases.filter(owner=request.user) if request.user.is_authenticated else purchases.filter(session_hash=sid,owner__isnull=True)
    return Review.objects.create(public_name=name.strip(),rating=rating,comment=comment.strip(),session_hash=sid,
          owner=request.user if request.user.is_authenticated else None,verified_demo=purchases.exists())

@transaction.atomic
def moderate(actor,review_ids,decision,reason):
    if not actor.is_active or not actor.is_staff or not actor.has_perm('shop.moderate_review'): raise PermissionDenied
    if decision not in ('approved','rejected') or len(reason.strip())<5: raise ValidationError('Indica una decisión y motivo válidos.')
    for review in Review.objects.filter(pk__in=review_ids):
        previous = review.status
        review.status = decision; review.reason = reason.strip()
        if decision=='approved' and previous!='approved' and review.published_at is None: review.published_at=timezone.now()
        review.save(update_fields=['status','reason','published_at'])
        ReviewEvent.objects.create(review=review,actor=actor,decision=decision,reason=reason.strip())
