import copy
import io
import json
import os
from pathlib import Path
import sqlite3
import tempfile
from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.utils import timezone
from django.conf import settings
from .models import Order,OrderLine,OrderEvent,Review,ReviewEvent,Notification
from .services import enqueue, transition_order
from .mail import process_one
from .backups import backup_file

TEST_PASSWORD='fixture-local-no-production-47!'
def body():
    return {'requestKey':'fixture-order-11111111-2222-3333-4444','demoConsent':True,
        'items':[{'id':p,'size':'S' if p in ('leggings','top','camiseta','arnes') else 'Única','quantity':1} for p in ['leggings','top','camiseta','correa','arnes','juguete']],
        'customer':{'name':'Persona de prueba','email':'buyer@example.com','phone':'600000000','address':'Calle de Ejemplo, 1','postal':'28001','city':'Ciudad ejemplo','province':'Provincia ejemplo'}}

def api(client,path,payload):
    token=client.get('/api/session').json()['csrf']
    return client.post(path,json.dumps(payload),content_type='application/json',HTTP_X_CSRF_TOKEN=token)

def admin_user(name='admin-fixture'):
    return get_user_model().objects.create_superuser(name,'admin@example.com',TEST_PASSWORD)

@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class StoreTests(TestCase):
    def test_catalogue_assets_private_data_and_zero_total(self):
        client=Client(enforce_csrf_checks=True)
        self.assertEqual(client.get('/').status_code,200)
        self.assertIn(b'"priceMinor": 0',client.get('/js/catalogo.js').content)
        for path in ['/server/app.py','/.env','/.git/config','/data/catalogo.json','/api/orders/guess']:
            self.assertEqual(client.get(path).status_code,404)
        for path in ['/css/estilos.css','/js/script.js','/img/shop-top.webp']:
            self.assertEqual(client.get(path).status_code,200)
        response=api(client,'/api/orders',body());self.assertEqual(response.status_code,201,response.content)
        receipt=response.json();self.assertEqual(receipt['totalMinor'],0);self.assertEqual(len(receipt['items']),6)
        self.assertNotIn('customer',receipt);self.assertNotIn('buyer@example.com',str(receipt))
        self.assertEqual(Order.objects.count(),1);self.assertEqual(OrderLine.objects.count(),6)
        self.assertEqual(Notification.objects.count(),2)
        self.assertEqual(Order.objects.get().status,Order.Status.DEMO)
        self.assertEqual(api(client,'/api/orders',body()).json()['id'],receipt['id'])
        self.assertEqual(Order.objects.count(),1);self.assertEqual(Notification.objects.count(),2)
        bad=body();bad['items'][0]['quantity']=2
        self.assertEqual(api(client,'/api/orders',bad).status_code,400)
        other=Client();self.assertEqual(other.get('/api/orders').status_code,405)
        self.assertNotIn(receipt['id'],other.get('/').content.decode())

    def test_csrf_input_validation_and_session_isolation(self):
        c=Client(enforce_csrf_checks=True)
        self.assertEqual(c.post('/api/orders',json.dumps(body()),content_type='application/json').status_code,403)
        token=c.get('/api/session').json()['csrf']
        self.assertEqual(c.post('/api/orders',json.dumps(body()),content_type='application/json',HTTP_X_CSRF_TOKEN=token,HTTP_ORIGIN='https://evil.invalid').status_code,403)
        for mutate in [lambda p:p['items'][0].update(size='XXL'),lambda p:p['items'][0].update(quantity=True),lambda p:p.update(totalMinor=1),lambda p:p.update(paymentMethod='bank_transfer'),lambda p:p['customer'].update(email='invalid')]:
            bad=body();mutate(bad);self.assertEqual(api(c,'/api/orders',bad).status_code,400)
        self.assertEqual(api(c,'/api/orders',body()).status_code,201)
        b=Client(enforce_csrf_checks=True)
        r={'publicName':'Alias local','rating':1,'comment':'Comentario legítimo sin datos personales.'}
        self.assertEqual(api(b,'/api/reviews',r).status_code,201)
        self.assertFalse(Review.objects.get().verified_demo)
        self.assertEqual(api(c,'/api/reviews',r).status_code,201)
        self.assertTrue(Review.objects.latest('pk').verified_demo)
        self.assertEqual(api(c,'/api/reviews',dict(r,verified=True)).status_code,400)

    def test_reviews_real_persistence_moderation_date_and_xss(self):
        c=Client();r={'publicName':'Alias de prueba','rating':1,'comment':'No me gusta. <img src=x onerror=alert(1)> Crítica de prueba.'}
        self.assertEqual(api(c,'/api/reviews',r).status_code,201)
        self.assertEqual(Client().get('/api/reviews').json()['reviews'],[])
        review=Review.objects.get();self.assertEqual(review.status,'pending')
        u=admin_user();c.force_login(u)
        form={'action':'approve','_selected_action':[str(review.pk)],'apply':'1','reason':'Crítica negativa legítima, sin manipular valoración','confirmed':'on'}
        self.assertEqual(c.post('/admin/shop/review/',form).status_code,302)
        result=Client().get('/api/reviews').json()['reviews'][0]
        self.assertEqual(result['rating'],1);self.assertEqual(result['publicName'],'Alias de prueba');self.assertEqual(result['comment'],r['comment'])
        self.assertIsNotNone(result['publishedAt']);self.assertNotIn('email',str(result))
        published=result['publishedAt'];c.post('/admin/shop/review/',form)
        self.assertEqual(Client().get('/api/reviews').json()['reviews'][0]['publishedAt'],published)
        self.assertEqual(ReviewEvent.objects.count(),2)
        self.assertEqual(Client().post('/admin/shop/review/',form).status_code,302)
        for _ in range(4):self.assertEqual(api(Client(),' /api/reviews'.strip(),r).status_code,201)
        self.assertEqual(Review.objects.count(),5)

    def test_admin_permissions_and_logout(self):
        self.assertEqual(Client().get('/admin/').status_code,302)
        visitor=get_user_model().objects.create_user('reader','reader@example.com',TEST_PASSWORD,is_staff=True)
        visitor.user_permissions.add(Permission.objects.get(codename='view_order'))
        self.assertNotEqual(visitor.password,TEST_PASSWORD)
        owner=admin_user();order=Order.objects.create(number='DEMO-fixture',environment='demo',session_hash='fixture',request_key='fixture',fingerprint='fixture',status=Order.Status.DEMO,method='free_demo',customer={'name':'Privado'})
        c=Client();c.force_login(visitor)
        self.assertEqual(c.get('/admin/').status_code,200)
        self.assertEqual(c.post(f'/admin/shop/order/{order.pk}/cancel/',{'reason':'Intento sin permiso','confirmed':'on'}).status_code,403)
        c.force_login(owner)
        self.assertEqual(c.post(f'/admin/shop/order/{order.pk}/change/',{'status':'paid'}).status_code,403)
        order.refresh_from_db();self.assertEqual(order.status,Order.Status.DEMO)
        self.assertEqual(c.get('/admin/').context['shop_summary']['total'],1)
        self.assertEqual(c.get(f'/admin/shop/order/{order.pk}/cancel/').status_code,200)
        self.assertEqual(c.post(f'/admin/shop/order/{order.pk}/cancel/',{'reason':'Ensayo de cancelación','confirmed':'on'}).status_code,302)
        order.refresh_from_db();self.assertEqual(order.status,Order.Status.CANCELLED)
        self.assertEqual(OrderEvent.objects.get().actor,owner)
        self.assertEqual(c.post('/admin/logout/').status_code,302)
        self.assertEqual(c.get('/admin/').status_code,302)

    def test_login_rotation_preserves_order_idempotency(self):
        c=Client(enforce_csrf_checks=True)
        original=api(c,'/api/orders',body()).json()['id']
        c.force_login(admin_user())
        self.assertEqual(api(c,'/api/orders',body()).json()['id'],original)
        self.assertEqual(Order.objects.count(),1)

    def test_actual_admin_login_csrf(self):
        import re
        u=admin_user();c=Client(enforce_csrf_checks=True)
        html=c.get('/admin/login/').content.decode()
        token=re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"',html).group(1)
        from .views import csrf_failure
        with patch('shop.views.csrf_failure',wraps=csrf_failure) as rejected:
            response=c.post('/admin/login/',{'username':u.username,'password':TEST_PASSWORD,'csrfmiddlewaretoken':token,'next':'/admin/'})
            if rejected.called: print('CSRF REASON TEST',rejected.call_args.kwargs.get('reason'))
        self.assertEqual(response.status_code,302,response.content)

    def test_admin_csrf_and_login_throttling(self):
        u=admin_user();c=Client(enforce_csrf_checks=True);c.force_login(u)
        self.assertEqual(c.post('/admin/shop/review/',{'action':'approve'}).status_code,403)
        c=Client()
        for _ in range(5):c.post('/admin/login/',{'username':u.username,'password':'wrong-test-password','next':'/admin/'})
        self.assertEqual(c.post('/admin/login/',{'username':u.username,'password':TEST_PASSWORD,'next':'/admin/'}).status_code,429)
        self.assertEqual(c.get('/admin/').status_code,302)

@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],MODE='family')
class FamilyTests(TestCase):
    def setUp(self):
        self.buyer=get_user_model().objects.create_user('buyer','buyer@example.com',TEST_PASSWORD)
        self.c=Client(enforce_csrf_checks=True);self.c.force_login(self.buyer)
    def test_private_profile_prices_and_money_blocked(self):
        self.assertEqual(Client().get('/').status_code,302);self.assertEqual(Client().get('/api/session').status_code,401)
        text=self.c.get('/js/catalogo.js').content.decode();self.assertEqual(text.count('"priceMinor": 100'),6)
        p=dict(body(),paymentMethod='bank_transfer')
        self.assertEqual(api(self.c,'/api/orders',p).status_code,503)
        self.assertEqual(Order.objects.count(),0)
        with override_settings(MODE='demo'):
            self.assertEqual(self.c.get('/js/catalogo.js').content.decode().count('"priceMinor": 0'),6)
    @override_settings(FAMILY_CHECKOUT_ENABLED=True,FAMILY_MONEY_RELEASED=True,BANK_BENEFICIARY='FICTICIO NO TRANSFERIR',BANK_IBAN='ES8200000000000000000000')
    def test_family_six_euros_and_admin_confirmation_idempotent(self):
        p=dict(body(),paymentMethod='bank_transfer')
        response=api(self.c,'/api/orders',p);self.assertEqual(response.status_code,201,response.content)
        r=response.json();self.assertEqual(r['totalMinor'],600);self.assertEqual(r['paymentStatus'],'pending_payment')
        self.assertEqual(r['bankTransfer']['reference'],r['id'])
        order=Order.objects.get();self.assertEqual(order.owner,self.buyer);self.assertEqual(order.environment,'family')
        other=Client();other.force_login(get_user_model().objects.create_user('other',password=TEST_PASSWORD))
        self.assertEqual(other.get('/api/orders/'+r['id']).status_code,404)
        self.assertEqual(other.post(f'/admin/shop/order/{order.pk}/confirm-payment/',{}).status_code,302)
        admin=admin_user();a=Client(enforce_csrf_checks=True);a.force_login(admin)
        url=f'/admin/shop/order/{order.pk}/confirm-payment/'
        self.assertEqual(a.get(url).status_code,200);order.refresh_from_db();self.assertEqual(order.status,'pending_payment')
        data={'reason':'Comprobación ficticia del banco en test automatizado','confirmed':'on'}
        self.assertEqual(a.post(url,data).status_code,403)
        token=a.get('/api/session').json()['csrf']
        self.assertEqual(a.post(url,data,HTTP_X_CSRF_TOKEN=token).status_code,302)
        self.assertEqual(a.post(url,data,HTTP_X_CSRF_TOKEN=token).status_code,302)
        order.refresh_from_db();self.assertEqual(order.status,'paid')
        self.assertEqual(OrderEvent.objects.filter(new_status='paid').count(),1)
        self.assertEqual(OrderEvent.objects.get(new_status='paid').actor,admin)
        self.assertEqual(Notification.objects.filter(event='paid_buyer').count(),1)
        summary=a.get('/admin/').context['shop_summary'];self.assertEqual(summary['paid_minor'],600)
        self.assertEqual(api(self.c,'/api/orders',p).json()['id'],r['id'])
        self.assertEqual(Notification.objects.count(),3)
    def test_local_fixture_is_explicit_no_money_or_mail(self):
        call_command('create_family_fixture',username=self.buyer.username,confirm_fictional=True,stdout=io.StringIO())
        order=Order.objects.get();self.assertTrue(order.is_fixture);self.assertEqual(order.total_minor,600)
        admin=admin_user();self.assertTrue(transition_order(admin,order.pk,'paid','Ensayo ficticio sin cobro real'))
        self.assertEqual(process_one(order.notifications.first().pk),'fixture_no_mail')

@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class MailTests(TestCase):
    def setUp(self):
        api(Client(),'/api/orders',body());self.notification=Notification.objects.get(event='order_buyer')
    def test_disabled_never_requests_provider(self):
        with override_settings(MAIL_ENABLED=False),patch('shop.mail.urllib.request.urlopen') as network:
            self.assertEqual(process_one(self.notification.pk),'not_configured');network.assert_not_called()
    @override_settings(MAIL_ENABLED=True,MAIL_PROVIDER='resend',MAIL_FROM='test@example.com',SELLER_EMAIL='seller@example.com',TEST_BUYER_EMAILS=['buyer@example.com'],RESEND_API_KEY='fixture-not-real')
    def test_provider_acceptance_retry_and_no_duplicate(self):
        class Response(io.BytesIO):status=200
        with patch('shop.mail.urllib.request.urlopen',return_value=Response(b'{"id":"mock-provider-acceptance"}')) as network:
            self.assertEqual(process_one(self.notification.pk),'accepted')
            self.assertEqual(process_one(self.notification.pk),'accepted');self.assertEqual(network.call_count,1)
        self.notification.refresh_from_db();self.assertEqual(self.notification.provider_id,'mock-provider-acceptance')
        seller=Notification.objects.get(event='order_seller')
        with patch('shop.mail.urllib.request.urlopen',side_effect=TimeoutError):
            self.assertEqual(process_one(seller.pk),'unconfirmed')
        Notification.objects.filter(pk=seller.pk).update(first_attempt=timezone.now()-timedelta(hours=24),next_attempt=timezone.now()-timedelta(minutes=1))
        with patch('shop.mail.urllib.request.urlopen') as network:
            self.assertEqual(process_one(seller.pk),'needs_reconciliation');network.assert_not_called()
    @override_settings(MAIL_ENABLED=True,MAIL_PROVIDER='smtp',MAIL_FROM='sender@example.com',SELLER_EMAIL='seller@example.com',TEST_BUYER_EMAILS=['buyer@example.com'],SMTP_USER='sender@example.com',SMTP_PASSWORD='fixture-no-real',SMTP_HOST='smtp.gmail.com',SMTP_PORT=465)
    def test_smtp_acceptance_and_uncertain_no_auto_retry(self):
        with patch('shop.mail.smtplib.SMTP_SSL') as network:
            network.return_value.send_message.return_value={}
            self.assertEqual(process_one(self.notification.pk),'accepted')
        seller=Notification.objects.get(event='order_seller')
        with patch('shop.mail.smtplib.SMTP_SSL',side_effect=TimeoutError):self.assertEqual(process_one(seller.pk),'needs_reconciliation')
        with patch('shop.mail.smtplib.SMTP_SSL') as network:
            self.assertEqual(process_one(seller.pk),'needs_reconciliation');network.assert_not_called()

class ImportAndBackupTests(TestCase):
    def test_readonly_import_preserves_and_repeats_without_duplicates(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'old.sqlite3';db=sqlite3.connect(path)
            db.executescript("CREATE TABLE reviews(id INTEGER PRIMARY KEY,sid TEXT,product TEXT,rating INTEGER,comment TEXT,verified INTEGER,created REAL,status TEXT,reason TEXT,public_name TEXT,published_at REAL); CREATE TABLE orders(id TEXT,sid TEXT,request_key TEXT,fingerprint TEXT,created REAL,payload TEXT,receipt TEXT);")
            db.execute('INSERT INTO reviews VALUES (?,?,?,?,?,?,?,?,?,?,?)',(5,'old','leggings',1,'Crítica antigua que no debe perderse',1,1000,'approved','motivo','Alias antiguo',None))
            p=body();db.execute('INSERT INTO orders VALUES (?,?,?,?,?,?,?)',('DEMO-antiguo','old','old-key','hash',1000,json.dumps({'items':p['items'],'customer':p['customer']}),json.dumps({'totalMinor':0})));db.commit();db.close()
            before=path.read_bytes()
            call_command('import_legacy',source=str(path),stdout=io.StringIO());call_command('import_legacy',source=str(path),stdout=io.StringIO())
            self.assertEqual(path.read_bytes(),before)
            self.assertEqual(Review.objects.count(),1);self.assertEqual(Review.objects.get().rating,1);self.assertIsNone(Review.objects.get().published_at)
            self.assertEqual(Order.objects.count(),1);self.assertEqual(OrderLine.objects.count(),6)
            copy=Path(folder)/'backups/copy.sqlite3';backup_file(path,copy)
            r=sqlite3.connect(copy);self.assertEqual(r.execute('PRAGMA integrity_check').fetchone()[0],'ok');self.assertEqual(r.execute('SELECT count(*) FROM reviews').fetchone()[0],1);r.close()
            if os.name!='nt': self.assertEqual(copy.stat().st_mode&0o777,0o600)
