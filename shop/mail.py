"""Outbox persistente. Desactivado sin configuración explícita, sin credenciales en código."""
from datetime import timedelta
from email.message import EmailMessage
from email.utils import parseaddr
import json
import smtplib
import ssl
import urllib.request
from django.conf import settings
from django.db.models import F, Q
from django.utils import timezone
from .models import Notification


def configured():
    basic=settings.MAIL_ENABLED and settings.MAIL_FROM and settings.SELLER_EMAIL and settings.TEST_BUYER_EMAILS
    if settings.MAIL_PROVIDER=='resend': return bool(basic and settings.RESEND_API_KEY)
    if settings.MAIL_PROVIDER=='smtp': return bool(basic and settings.SMTP_USER and settings.SMTP_PASSWORD and settings.SMTP_HOST=='smtp.gmail.com' and settings.SMTP_PORT in (465,587) and parseaddr(settings.MAIL_FROM)[1].lower()==settings.SMTP_USER.lower())
    return False

def content(notification):
    p=notification.payload;paid=notification.event=='paid_buyer'
    text=f"AYLIN SHOP — PRUEBA SIN ENVIO DE PRODUCTOS\nPedido: {p['number']}\n"
    text+='\n'.join(f"- {i['name']} | Talla {i['size']} | Cantidad {i['quantity']} | Unidad {i['unitPriceMinor']/100:.2f} EUR" for i in p['items'])
    text+=f"\nTotal: {p['totalMinor']//100},{p['totalMinor']%100:02d} EUR\n"
    state={'pending_payment':'Pendiente de pago','paid':'Pago confirmado manualmente por administrador','demo_confirmed':'Demostración gratuita sin pago'}.get(p['status'],p['status'])
    text+='Estado: '+state+'\nNo se enviará ningún producto. Esta prueba no es una venta comercial.\n'
    if p['method']=='bank_transfer' and not paid:
        b=p['bank'];text+=f"Beneficiario: {b['beneficiary']}\nIBAN: {b['iban']}\nImporte: {p['totalMinor']//100},{p['totalMinor']%100:02d} EUR\nConcepto: {b['reference']}\nNo se considera pagado hasta su comprobación manual.\n"
    if notification.event=='order_seller':
        text+='Datos de envío de prueba:\n'+'\n'.join(str(v) for v in p['customer'].values())
    title=('PRUEBA · Pago confirmado ' if paid else 'PRUEBA · Pedido ')+p['number']
    recipient=settings.SELLER_EMAIL if notification.event=='order_seller' else p['customer']['email']
    return recipient,title,text

def deliver(notification):
    recipient,title,text=content(notification)
    key='aylin-'+str(notification.id)
    if settings.MAIL_PROVIDER=='resend':
        req=urllib.request.Request('https://api.resend.com/emails',data=json.dumps({'from':settings.MAIL_FROM,'to':[recipient],'subject':title,'text':text}).encode(),headers={'Authorization':'Bearer '+settings.RESEND_API_KEY,'Content-Type':'application/json','Idempotency-Key':key,'User-Agent':'AylinShopLocal/2'},method='POST')
        with urllib.request.urlopen(req,timeout=15) as response:
            data=json.loads(response.read(65536))
            if 200<=response.status<300 and isinstance(data.get('id'),str) and data['id']: return data['id']
        raise ValueError('Proveedor sin confirmación.')
    message=EmailMessage();message['From']=settings.MAIL_FROM;message['To']=recipient;message['Subject']=title
    message['Message-ID']='<'+key+'@aylin-shop.local>';message.set_content(text)
    context=ssl.create_default_context()
    if settings.SMTP_PORT==465:
        client=smtplib.SMTP_SSL(settings.SMTP_HOST,settings.SMTP_PORT,timeout=15,context=context)
    else:
        client=smtplib.SMTP(settings.SMTP_HOST,settings.SMTP_PORT,timeout=15);client.ehlo();client.starttls(context=context);client.ehlo()
    with client:
        client.login(settings.SMTP_USER,settings.SMTP_PASSWORD)
        if client.send_message(message): raise ValueError('Destinatario no aceptado.')
    return str(message['Message-ID'])

def process_one(notification_id):
    row=Notification.objects.get(pk=notification_id)
    if row.order.is_fixture:
        Notification.objects.filter(pk=row.pk).update(status='fixture_no_mail'); return 'fixture_no_mail'
    if row.status in ('accepted','needs_reconciliation','recipient_not_allowed'): return row.status
    if not configured():
        Notification.objects.filter(pk=row.pk).exclude(status='accepted').update(status='not_configured')
        return 'not_configured'
    if row.payload['customer']['email'].lower() not in settings.TEST_BUYER_EMAILS:
        Notification.objects.filter(pk=row.pk).update(status='recipient_not_allowed');return 'recipient_not_allowed'
    now=timezone.now()
    if row.first_attempt and (now-row.first_attempt>=timedelta(hours=23) or (settings.MAIL_PROVIDER=='smtp' and row.status in ('unconfirmed','sending'))):
        Notification.objects.filter(pk=row.pk).update(status='needs_reconciliation');return 'needs_reconciliation'
    eligible=Q(status__in=['queued','not_configured','unconfirmed'])|Q(status='sending',locked_until__lt=now)
    changed=Notification.objects.filter(pk=row.pk,next_attempt__lte=now).filter(eligible).update(status='sending',locked_until=now+timedelta(seconds=90),attempts=F('attempts')+1,first_attempt=row.first_attempt or now)
    if not changed: return row.status
    row.refresh_from_db()
    try:
        identifier=deliver(row)
        Notification.objects.filter(pk=row.pk,status='sending').update(status='accepted',provider_id=identifier,locked_until=None)
        return 'accepted'  # Aceptación SMTP/API, no prueba de entrega al buzón.
    except Exception:
        status='unconfirmed' if settings.MAIL_PROVIDER=='resend' else 'needs_reconciliation'
        Notification.objects.filter(pk=row.pk,status='sending').update(status=status,locked_until=None,next_attempt=now+timedelta(minutes=5))
        return status
