"""Pruebas de seguridad y correo. Solo proveedores simulados, ningún correo externo."""
import copy
import http.cookiejar
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
from app import Application, CATALOG, DemoServer, ResendMailer, Store
from moderate import decide

class Client:
    def __init__(self, url):
        self.url = url
        self.csrf = ''
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def request(self, path, body=None, headers=None):
        h = {'Origin': self.url, 'X-CSRF-Token': self.csrf, 'Content-Type': 'application/json'}
        h.update(headers or {})
        req = urllib.request.Request(self.url + path, data=json.dumps(body).encode() if body is not None else None, headers=h)
        try:
            r = self.opener.open(req)
        except urllib.error.HTTPError as e:
            r = e
        content = r.read()
        try: data = json.loads(content)
        except (ValueError, UnicodeDecodeError): data = content
        return r.status, data
    def session(self):
        status, data = self.request('/api/session')
        assert status == 200
        self.csrf = data['csrf']
        return data

def payload():
    return {'requestKey': '11111111-2222-3333-4444-555555555555', 'demoConsent': True,
            'items': [{'id': p['id'], 'size': 'S' if len(p['variants']) > 1 else 'Única', 'quantity': 1} for p in CATALOG.values()],
            'customer': {'name': 'Persona PRIVADA123', 'email': 'test@example.com', 'phone': '600000000',
                         'address': 'Calle PRIVADA123, 1', 'postal': '28001', 'city': 'Ciudad demo', 'province': 'Provincia demo'}}

class ServerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(self.temp.name)
        with patch.dict(os.environ, {}, clear=True): self.app = Application(self.store)
        self.server = DemoServer(('127.0.0.1', 0), self.app)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'
        self.a = Client(self.url); self.b = Client(self.url)
        self.a.session(); self.b.session()
    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.temp.cleanup()
    def test_private_orders_and_validation(self):
        status, receipt = self.a.request('/api/orders', payload())
        self.assertEqual(status, 201)
        self.assertTrue(receipt['demo']); self.assertEqual(receipt['totalMinor'], 0)
        self.assertEqual(len(receipt['items']), 6)
        self.assertNotIn('PRIVADA123', json.dumps(receipt))
        self.assertNotIn('customer', receipt)
        for path in ['/api/orders', '/api/orders/' + receipt['id'], '/api/admin/orders', '/admin', '/server/app.py', '/.env', '/.git/config', '/data/catalogo.json', '/css/../server/app.py', '/img/%2e%2e/server/app.py']:
            status, data = self.b.request(path)
            self.assertIn(status, [401, 404])
            self.assertNotIn('PRIVADA123', str(data))
        self.assertEqual(receipt['mail']['buyer']['status'], 'not_configured')
        self.assertEqual(self.store.directory.stat().st_mode & 0o777, 0o700)
        self.assertEqual(self.store.path.stat().st_mode & 0o777, 0o600)
        for mutate in [lambda p: p['items'][0].update(size='XXL'), lambda p: p['items'][0].update(quantity=-1), lambda p: p['items'][0].update(quantity=True), lambda p: p.update(totalMinor=0), lambda p: p['customer'].update(email='x\nheader@example.com')]:
            data = payload(); mutate(data)
            self.assertEqual(self.a.request('/api/orders', data)[0], 400)
    def test_variant_out_of_stock(self):
        original = CATALOG['leggings']
        changed = copy.deepcopy(original)
        changed['variants'][1]['available'] = False
        with patch.dict(CATALOG, {'leggings': changed}):
            self.assertEqual(self.a.request('/api/orders', payload())[0], 400)

    def test_csrf_host_and_idempotency(self):
        self.assertEqual(self.a.request('/api/session', headers={'Origin': 'https://evil.invalid'})[0], 403)
        self.assertEqual(self.a.request('/api/orders', payload(), {'X-CSRF-Token': ''})[0], 403)
        self.assertEqual(self.a.request('/api/orders', payload(), {'Origin': 'https://evil.invalid'})[0], 403)
        self.assertEqual(self.a.request('/api/session', headers={'Host': 'evil.invalid'})[0], 403)
        old = self.a.csrf; self.a.session(); self.assertEqual(old, self.a.csrf)
        with patch.object(self.app.mailer, 'notify', wraps=self.app.mailer.notify) as spy:
            first = self.a.request('/api/orders', payload())[1]
            again = self.a.request('/api/orders', payload())[1]
            self.assertEqual(first['id'], again['id']); self.assertEqual(spy.call_count, 1)
            different = payload(); different['items'][0]['quantity'] = 2
            self.assertEqual(self.a.request('/api/orders', different)[0], 400)
    def test_reviews_verification_moderation_and_negative_rating(self):
        self.assertEqual(self.a.request('/api/orders', payload())[0], 201)
        review = {'product': 'leggings', 'rating': 1, 'comment': 'No me ha gustado este producto de demostración.'}
        self.assertEqual(self.a.request('/api/reviews', review)[0], 201)
        self.assertEqual(self.b.request('/api/reviews', review)[0], 201)
        self.assertEqual(self.a.request('/api/reviews?product=leggings')[1]['reviews'], [])
        forged = dict(review, verified=True, email='test@example.com', orderId='guess')
        self.assertEqual(self.b.request('/api/reviews', forged)[0], 400)
        with self.store.connect() as db:
            rows = db.execute('SELECT id,verified FROM reviews ORDER BY id').fetchall()
        self.assertEqual([r['verified'] for r in rows], [1, 0])
        decide(self.store, rows[0]['id'], 'approved', 'Crítica legítima sin datos personales')
        decide(self.store, rows[1]['id'], 'rejected', 'Duplicado de prueba identificado por el operador')
        public = self.b.request('/api/reviews?product=leggings')[1]['reviews']
        self.assertEqual(public, [{'rating': 1, 'comment': review['comment'], 'verifiedDemo': True}])
        self.assertNotIn('sid', str(public)); self.assertNotIn('email', str(public))
        for _ in range(4): self.assertEqual(self.a.request('/api/reviews', review)[0], 201)
        self.assertEqual(self.a.request('/api/reviews', review)[0], 400)

class MailerTests(unittest.TestCase):
    def test_no_configuration_no_requests(self):
        with patch.dict(os.environ, {}, clear=True), patch('app.urllib.request.urlopen') as call:
            mail = ResendMailer().notify(dict(payload(), id='DEMO-test'))
            self.assertEqual(mail['buyer']['status'], 'not_configured'); call.assert_not_called()
    def test_provider_confirmation_and_allowlist(self):
        config = {'RESEND_API_KEY': 'unit-test-not-a-real-key', 'SHOP_MAIL_ENABLED': 'true', 'SHOP_MAIL_FROM': 'shop@example.com', 'SHOP_SELLER_EMAIL': 'seller@example.com', 'SHOP_TEST_BUYER_EMAILS': 'test@example.com'}
        class Response(io.BytesIO):
            status = 200
        calls = []
        def provider(req, **kwargs):
            calls.append(json.loads(req.data))
            return Response(b'{"id":"simulated-provider-id"}')
        with patch.dict(os.environ, config, clear=True), patch('app.urllib.request.urlopen', side_effect=provider):
            mailer = ResendMailer(); mail = mailer.notify(dict(payload(), id='DEMO-test'))
            self.assertEqual(len(calls), 2)
            self.assertEqual(mail['buyer']['status'], 'accepted')
            self.assertEqual(calls[1]['to'], ['seller@example.com'])
            self.assertIn('PRIVADA123', calls[1]['text'])
            self.assertIn('Talla: S', calls[0]['text']); self.assertIn('0,00 EUR', calls[0]['text'])
            self.assertIn('no se enviará ningún producto', calls[0]['text'])
            blocked = payload(); blocked['customer']['email'] = 'unauthorized@example.com'
            self.assertEqual(mailer.notify(dict(blocked, id='DEMO-test'))['buyer']['status'], 'recipient_not_allowed')
            self.assertEqual(len(calls), 2)
        with patch.dict(os.environ, config, clear=True), patch('app.urllib.request.urlopen', side_effect=TimeoutError):
            self.assertEqual(ResendMailer().notify(dict(payload(), id='DEMO-test'))['buyer']['status'], 'unconfirmed')

if __name__ == '__main__': unittest.main()
