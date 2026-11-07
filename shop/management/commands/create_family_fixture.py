"""Ensayo opcional y explícito para practicar el panel, nunca una venta ni un correo real."""
import uuid
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from shop.catalog import catalogue
from shop.models import Order,OrderLine,OrderEvent
from shop.services import enqueue
class Command(BaseCommand):
    def add_arguments(self,p):p.add_argument('--username',required=True);p.add_argument('--confirm-fictional',action='store_true')
    @transaction.atomic
    def handle(self,*args,**o):
        if settings.MODE!='family' or not o['confirm_fictional']:raise CommandError('Solo perfil familiar y --confirm-fictional explícito.')
        user=get_user_model().objects.filter(username=o['username'],is_active=True).first()
        if not user:raise CommandError('Crea antes un usuario local autorizado; no se generan contraseñas.')
        # Cuenta sintética: BBAN todo ceros, no cuenta operativa.
        bban='0'*20;iban='ES'+f'{98-int(bban+"142800")%97:02d}'+bban
        number='FAMILY-FIXTURE-'+str(uuid.uuid4())
        order=Order.objects.create(number=number,environment='family',owner=user,session_hash='fixture',request_key=str(uuid.uuid4()),fingerprint='fixture',method='bank_transfer',status=Order.Status.PENDING,total_minor=600,is_fixture=True,customer={'name':'Persona ficticia de pruebas','email':'ejemplo@example.com','phone':'600000000','address':'Calle de Ejemplo, 1','postal':'28001','city':'Ciudad de ejemplo','province':'Provincia de ejemplo'},bank_snapshot={'beneficiary':'FICTICIO - NO TRANSFERIR','iban':iban,'reference':number,'amountMinor':600,'currency':'EUR'})
        for p in catalogue()['products']:OrderLine.objects.create(order=order,product_id=p['id'],name=p['name'],size='S' if len(p['variants'])>1 else 'Única',quantity=1,unit_price_minor=100)
        OrderEvent.objects.create(order=order,actor=user,new_status=order.status,reason='Fixture ficticio creado explícitamente para ensayar el panel sin dinero.')
        enqueue(order,'order_buyer');enqueue(order,'order_seller')
        self.stdout.write('Fixture creado: '+order.number+'. No realizar transferencias ni envíos.')
