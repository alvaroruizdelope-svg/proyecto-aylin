"""Servidor de DEMO local. Solo loopback; no preparado para publicación.
Sin dependencias externas. python3 server/app.py --port 8000
"""
import argparse
from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import stat
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from collections import defaultdict
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from bank_transfer import BankTransferService

ROOT = Path(__file__).resolve().parents[1]
CATALOG = {p['id']: p for p in json.loads((ROOT / 'data/catalogo.json').read_text())['products']}
assert len(CATALOG) == 6 and all(p['priceMinor'] == 0 for p in CATALOG.values())
FIELDS = {'name': (3, 100), 'email': (5, 150), 'phone': (7, 25), 'address': (5, 180), 'postal': (5, 5), 'city': (2, 80), 'province': (2, 80)}
TTL = 86400  # Caducidad de pedidos/sesiones de prueba; las opiniones se conservan.

def default_private_directory():
    if os.name == 'nt':
        return str(Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData/Local')) / 'AylinShop/private')
    return f'/tmp/aylin-shop-private-{os.getuid()}'


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()

class Invalid(Exception):
    pass

class Store:
    def __init__(self, directory):
        supplied = Path(directory).expanduser()
        if supplied.is_symlink():
            raise ValueError('Directorio privado no puede ser enlace simbólico.')
        self.directory = supplied.resolve()
        if self.directory == ROOT or ROOT in self.directory.parents:
            raise ValueError('Los datos privados deben estar fuera del checkout público.')
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        if hasattr(os, 'getuid') and self.directory.stat().st_uid != os.getuid():
            raise ValueError('Directorio privado de otro usuario.')
        self.directory.chmod(0o700)
        self.path = self.directory / 'shop.sqlite3'
        if self.path.is_symlink():
            raise ValueError('Base de datos no puede ser enlace simbólico.')
        # Creación explícita a 0600 incluso con una umask permisiva.
        fd = os.open(self.path, os.O_CREAT | os.O_RDWR, 0o600)
        os.close(fd)
        self.path.chmod(0o600)
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS sessions (sid TEXT PRIMARY KEY, csrf TEXT NOT NULL, created REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS orders (id TEXT PRIMARY KEY, sid TEXT NOT NULL, request_key TEXT NOT NULL,
                  fingerprint TEXT NOT NULL, created REAL NOT NULL, payload TEXT NOT NULL, receipt TEXT NOT NULL,
                  UNIQUE(sid, request_key));
                CREATE TABLE IF NOT EXISTS reviews (id INTEGER PRIMARY KEY, sid TEXT NOT NULL, product TEXT NOT NULL,
                  rating INTEGER NOT NULL, comment TEXT NOT NULL, verified INTEGER NOT NULL, created REAL NOT NULL,
                  status TEXT NOT NULL DEFAULT 'pending', reason TEXT NOT NULL DEFAULT '');
                CREATE TABLE IF NOT EXISTS moderation (id INTEGER PRIMARY KEY, review_id INTEGER NOT NULL,
                  decision TEXT NOT NULL, reason TEXT NOT NULL, created REAL NOT NULL);
            ''')
        # Migración aditiva: conserva comentarios, estrellas, verificación y asociación antigua.
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            columns = {row['name'] for row in db.execute('PRAGMA table_info(reviews)')}
            if 'public_name' not in columns:
                db.execute("ALTER TABLE reviews ADD COLUMN public_name TEXT NOT NULL DEFAULT ''")
            if 'published_at' not in columns:
                db.execute('ALTER TABLE reviews ADD COLUMN published_at REAL')
        self.cleanup()

    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.execute('PRAGMA secure_delete=ON')
        db.row_factory = sqlite3.Row
        return db

    def cleanup(self):
        with self.connect() as db:
            # Las opiniones y sus decisiones no se borran por antigüedad: preservar las existentes.
            for table in ('orders', 'sessions'):
                db.execute(f'DELETE FROM {table} WHERE created < ?', (time.time() - TTL,))

class ResendMailer:
    def __init__(self):
        # Solo variables privadas del proceso. Nunca devueltas por API ni escritas en logs.
        self.key = os.environ.get('RESEND_API_KEY', '')
        self.sender = os.environ.get('SHOP_MAIL_FROM', '')
        self.seller = os.environ.get('SHOP_SELLER_EMAIL', '')
        self.allowed = {s.strip().lower() for s in os.environ.get('SHOP_TEST_BUYER_EMAILS', '').split(',') if s.strip()}
        self.enabled = os.environ.get('SHOP_MAIL_ENABLED') == 'true' and bool(self.key and self.sender and self.seller and self.allowed)

    def send(self, recipient, subject, text, key):
        body = json.dumps({'from': self.sender, 'to': [recipient], 'subject': subject, 'text': text}).encode()
        req = urllib.request.Request('https://api.resend.com/emails', data=body, method='POST', headers={
            'Authorization': 'Bearer ' + self.key, 'Content-Type': 'application/json', 'Idempotency-Key': key,
            'User-Agent': 'AylinShopLocalDemo/1.0'})
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read(65536))
                if 200 <= response.status < 300 and isinstance(data.get('id'), str) and data['id']:
                    return {'status': 'accepted', 'providerId': data['id']}
        except Exception:
            # No publicar cuerpo del proveedor: puede contener direcciones u otros datos privados.
            pass
        return {'status': 'unconfirmed'}

    def notify(self, order):
        if not self.enabled:
            return {k: {'status': 'not_configured'} for k in ('buyer', 'seller')}
        if order['customer']['email'].lower() not in self.allowed:
            return {k: {'status': 'recipient_not_allowed'} for k in ('buyer', 'seller')}
        products = '\n'.join(f"- {CATALOG[i['id']]['name']} | Talla: {i['size']} | Cantidad: {i['quantity']} | 0,00 EUR" for i in order['items'])
        common = (f"AYLIN SHOP — PEDIDO DE DEMOSTRACION\nPedido: {order['id']}\n{products}\n"
                  "Total: 0,00 EUR\nNo se ha realizado un cobro y no se enviará ningún producto.\n"
                  "Estado: confirmado, demostración sin pago.\n")
        customer = order['customer']
        shipping = '\nDatos de envío de prueba:\n' + '\n'.join(customer[k] for k in FIELDS)
        return {'buyer': self.send(customer['email'], 'DEMO · Confirmación ' + order['id'], common, order['id'] + '-buyer'),
                'seller': self.send(self.seller, 'DEMO · Nuevo pedido ' + order['id'], common + shipping, order['id'] + '-seller')}

class Application:
    def __init__(self, store, mailer=None):
        self.store = store
        self.mailer = mailer or ResendMailer()
        self.bank_transfer = BankTransferService(store, CATALOG)
        self.csrf_secret = secrets.token_bytes(32)
        self.lock = threading.Lock()
        self.rates = defaultdict(list)

    def limit(self, key, count, seconds):
        with self.lock:
            now = time.time()
            self.rates[key] = [t for t in self.rates[key] if t > now - seconds]
            if len(self.rates[key]) >= count:
                return False
            self.rates[key].append(now)
            # Espacio acotado, suficiente para la demo exclusivamente local.
            if len(self.rates) > 10000:
                self.rates = defaultdict(list, {key: self.rates[key]})
            return True

    def order(self, sid, body):
        if set(body) != {'items', 'customer', 'demoConsent', 'requestKey'} or body['demoConsent'] is not True:
            raise Invalid('Pedido de demostración no válido.')
        key = body['requestKey']
        if not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9-]{16,100}', key):
            raise Invalid('Identificador de solicitud no válido.')
        raw = body['items']
        if not isinstance(raw, list) or not 1 <= len(raw) <= 24:
            raise Invalid('Carrito no válido.')
        items, seen = [], set()
        for item in raw:
            if not isinstance(item, dict) or set(item) != {'id', 'size', 'quantity'}:
                raise Invalid('Variante no válida.')
            product = CATALOG.get(item['id']) if isinstance(item['id'], str) else None
            if product and (type(product['priceMinor']) is not int or product['priceMinor'] != 0):
                raise Invalid('Este checkout admite únicamente productos gratuitos de demostración.')
            variant = next((v for v in product['variants'] if v['size'] == item['size']), None) if product else None
            pair = (item['id'], item['size']) if isinstance(item['id'], str) and isinstance(item['size'], str) else None
            if not variant or not variant['available'] or type(item['quantity']) is not int or not 1 <= item['quantity'] <= variant['demoLimit'] or pair in seen:
                raise Invalid('Talla o cantidad no disponible para esta demo.')
            seen.add(pair)
            items.append({'id': product['id'], 'size': variant['size'], 'quantity': item['quantity']})
        customer = body['customer']
        if not isinstance(customer, dict) or set(customer) != set(FIELDS):
            raise Invalid('Datos de prueba incompletos.')
        clean = {}
        for field, (low, high) in FIELDS.items():
            value = customer[field]
            if not isinstance(value, str) or not low <= len(value.strip()) <= high or any(ord(c) < 32 for c in value):
                raise Invalid('Comprueba los datos de prueba del formulario.')
            clean[field] = value.strip()
        if not re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+', clean['email']) or not re.fullmatch(r'\+?[0-9]{7,15}', clean['phone']) or not re.fullmatch(r'[0-9]{5}', clean['postal']):
            raise Invalid('Correo, teléfono o código postal no válidos.')
        fingerprint = digest(json.dumps({'items': items, 'customer': clean}, sort_keys=True))
        # Transacción serializa creación y reintentos. La clave de idempotencia evita nuevos correos/pedidos.
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            old = db.execute('SELECT * FROM orders WHERE sid=? AND request_key=?', (sid, key)).fetchone()
            if old:
                if old['fingerprint'] != fingerprint:
                    raise Invalid('La solicitud ya se utilizó con otros datos. Vuelve a iniciar el pedido.')
                return json.loads(old['receipt'])
            if db.execute('SELECT count(*) FROM orders WHERE sid=? AND created>?', (sid, time.time()-900)).fetchone()[0] >= 3:
                raise Invalid('Límite de pedidos de prueba alcanzado. Espera antes de intentarlo de nuevo.')
            oid = 'DEMO-' + str(uuid.uuid4())
            order = {'id': oid, 'items': items, 'customer': clean}
            receipt = {'id': oid, 'demo': True, 'totalMinor': 0, 'items': items,
                       'mail': {k: {'status': 'pending'} for k in ('buyer', 'seller')}}
            db.execute('INSERT INTO orders VALUES (?,?,?,?,?,?,?)',
                       (oid, sid, key, fingerprint, time.time(), json.dumps(order), json.dumps(receipt),))
        # Correos después del commit. Un fallo no borra el pedido ni se presenta como envío correcto.
        try:
            receipt['mail'] = self.mailer.notify(order)
        except Exception:
            receipt['mail'] = {k: {'status': 'unconfirmed'} for k in ('buyer', 'seller')}
        with self.store.connect() as db:
            db.execute('UPDATE orders SET receipt=? WHERE id=?', (json.dumps(receipt), oid))
        return receipt

    def review(self, sid, body):
        legacy = set(body) == {'product', 'rating', 'comment'}
        if not legacy and set(body) != {'publicName', 'rating', 'comment'}:
            raise Invalid('Solo se admiten alias público, valoración y comentario.')
        # Compatibilidad con clientes anteriores; las nuevas opiniones son generales.
        product = body.get('product', '')
        name = body.get('publicName', '')
        rating, comment = body['rating'], body['comment']
        if legacy and (not isinstance(product, str) or product not in CATALOG):
            raise Invalid('Producto no válido.')
        if not legacy and (not isinstance(name, str) or not re.fullmatch(r"[\w .'-]{2,60}", name.strip()) or re.search(r'\d{7,}', name)):
            raise Invalid('Utiliza un alias público de 2–60 caracteres, sin datos de contacto.')
        if type(rating) is not int or rating not in range(1, 6) or not isinstance(comment, str) or not 10 <= len(comment.strip()) <= 2000:
            raise Invalid('Selecciona 1–5 estrellas y un comentario de 10–2000 caracteres.')
        if any(ord(c) < 32 and c not in '\n\t' for c in comment):
            raise Invalid('El comentario contiene caracteres no válidos.')
        with self.store.connect() as db:
            if db.execute('SELECT count(*) FROM reviews WHERE sid=? AND created>?', (sid, time.time()-86400)).fetchone()[0] >= 5:
                raise Invalid('Límite de opiniones de prueba alcanzado.')
            rows = db.execute('SELECT payload FROM orders WHERE sid=?', (sid,)).fetchall()
            verified = bool(rows) if not product else any(any(i['id'] == product for i in json.loads(row['payload'])['items']) for row in rows)
            db.execute('INSERT INTO reviews (sid,product,rating,comment,verified,created,public_name) VALUES (?,?,?,?,?,?,?)',
                       (sid, product, rating, comment.strip(), int(verified), time.time(), name.strip()))
        return {'status': 'pending', 'message': 'Opinión recibida y pendiente de moderación. Todavía no está publicada.'}

class Handler(BaseHTTPRequestHandler):
    server_version = 'AylinLocalDemo'
    def log_message(self, *args):
        pass  # Nunca registrar direcciones, cuerpos, cookies ni claves.

    def headers_common(self, content_type):
        self.send_header('Content-Type', content_type)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; form-action 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'none'")

    def reply(self, code, body, cookie=None):
        data = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.headers_common('application/json; charset=utf-8')
        if cookie:
            self.send_header('Set-Cookie', cookie)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def valid_host(self):
        host = self.headers.get('Host', '').lower()
        return host in {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}

    def session(self):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get('Cookie', ''))
            value = cookie['aylin_session'].value if 'aylin_session' in cookie else ''
        except Exception:
            return None
        if not re.fullmatch(r'[A-Za-z0-9_-]{43}', value):
            return None
        with self.server.app.store.connect() as db:
            return db.execute('SELECT * FROM sessions WHERE sid=? AND created>?', (digest(value), time.time()-TTL)).fetchone()

    def do_GET(self):
        if not self.valid_host():
            return self.reply(403, {'error': 'Host no permitido. Esta demo solo admite acceso local.'})
        self.server.app.store.cleanup()
        path = urllib.parse.urlsplit(self.path).path
        origin = self.headers.get('Origin')
        if path.startswith('/api/') and (self.headers.get('Sec-Fetch-Site') == 'cross-site' or (origin and origin != 'http://' + self.headers.get('Host', ''))):
            return self.reply(403, {'error': 'Origen no permitido.'})
        if path == '/api/session':
            if not self.server.app.limit(('session', self.client_address[0]), 120, 3600):
                return self.reply(429, {'error': 'Demasiadas solicitudes.'})
            # CSRF estable para la sesión; pestañas del mismo navegador no se invalidan entre sí.
            session = self.session()
            raw = None
            if not session:
                raw = secrets.token_urlsafe(32)
                sid = digest(raw)
            else:
                sid = session['sid']
            csrf = hmac.new(self.server.app.csrf_secret, sid.encode(), hashlib.sha256).hexdigest()
            with self.server.app.store.connect() as db:
                db.execute('INSERT OR REPLACE INTO sessions VALUES (?,?,?)', (sid, digest(csrf), time.time()))
            return self.reply(200, {'csrf': csrf, 'mailConfigured': self.server.app.mailer.enabled},
                              f'aylin_session={raw}; HttpOnly; SameSite=Strict; Path=/api; Max-Age={TTL}' if raw else None)
        if path == '/api/reviews':
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
            product = query.get('product', [''])[0]  # Compatibilidad; la sección general no filtra por producto.
            cursor = query.get('cursor', [''])[0]
            if (product and product not in CATALOG) or (cursor and not re.fullmatch(r'[0-9]{1,18}', cursor)):
                return self.reply(400, {'error': 'Consulta de opiniones no válida.'})
            where, values = ["status='approved'"], []
            if product:
                where.append('product=?'); values.append(product)
            if cursor:
                where.append('id<?'); values.append(int(cursor))
            with self.server.app.store.connect() as db:
                rows = db.execute('SELECT id,rating,comment,verified,public_name,published_at FROM reviews WHERE ' + ' AND '.join(where) + ' ORDER BY id DESC LIMIT 21', values).fetchall()
            more = len(rows) > 20
            rows = rows[:20]
            result = [{'rating': r['rating'], 'comment': r['comment'], 'verifiedDemo': bool(r['verified']),
                       'publicName': r['public_name'] or None,
                       'publishedAt': datetime.fromtimestamp(r['published_at'], timezone.utc).isoformat() if r['published_at'] else None} for r in rows]
            return self.reply(200, {'reviews': result, 'nextCursor': rows[-1]['id'] if more else None})
        if path.startswith('/api/admin') or path.startswith('/admin'):
            return self.reply(401, {'error': 'Administración no disponible: requiere autenticación y autorización de servidor, todavía no implementadas.'})
        if path.startswith('/api/'):
            return self.reply(404, {'error': 'Recurso no disponible.'})
        if path == '/js/runtime.js':
            return self.static_bytes(b"'use strict';window.AYLIN_BACKEND=true;", 'text/javascript; charset=utf-8')
        # Lista positiva: jamás servir server/, tests/, .env, .git, bases de datos o documentación.
        decoded = urllib.parse.unquote(path)
        file = (ROOT / decoded.lstrip('/')).resolve() if decoded != '/' else ROOT / 'index.html'
        folder = decoded.split('/')[1] if decoded.startswith('/') else ''
        public_type = {'css': '.css', 'js': '.js'}
        allowed = decoded in ('/', '/index.html') or (
            folder in public_type and file.suffix == public_type[folder] and (ROOT / folder) in file.parents
        ) or (folder == 'img' and (ROOT / 'img') in file.parents and file.suffix in ('.webp', '.svg', '.jpg', '.jpeg', '.png'))
        if not allowed or ROOT not in file.parents or not file.is_file():
            return self.reply(404, {'error': 'Recurso no disponible.'})
        mime = {'.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.svg': 'image/svg+xml', '.webp': 'image/webp', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png'}
        return self.static_bytes(file.read_bytes(), mime[file.suffix])

    def static_bytes(self, data, content_type):
        self.send_response(200)
        self.headers_common(content_type)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if not self.valid_host() or self.headers.get('Origin') != 'http://' + self.headers.get('Host', ''):
            return self.reply(403, {'error': 'Origen no permitido.'})
        path = urllib.parse.urlsplit(self.path).path
        if path.startswith('/api/admin'):
            return self.reply(401, {'error': 'Administración no implementada.'})
        if path not in ('/api/orders', '/api/reviews'):
            return self.reply(404, {'error': 'Recurso no disponible.'})
        self.server.app.store.cleanup()
        session = self.session()
        token = self.headers.get('X-CSRF-Token', '')
        if not session or not hmac.compare_digest(session['csrf'], digest(token)):
            return self.reply(403, {'error': 'Sesión caducada. Recarga la página e inténtalo de nuevo.'})
        if not self.server.app.limit(('post', self.client_address[0]), 50, 3600):
            return self.reply(429, {'error': 'Límite de solicitudes de prueba alcanzado.'})
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            return self.reply(415, {'error': 'Se requiere JSON.'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 24000 or self.headers.get('Transfer-Encoding'):
                return self.reply(413, {'error': 'Solicitud demasiado grande o no válida.'})
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise Invalid('Solicitud no válida.')
            if path == '/api/orders':
                result = self.server.app.order(session['sid'], body)
            else:
                result = self.server.app.review(session['sid'], body)
            if path == '/api/orders':
                result = dict(result, mail={k: {'status': value['status']} for k, value in result['mail'].items()})
            return self.reply(201, result)
        except (Invalid, ValueError, TypeError):
            return self.reply(400, {'error': 'Comprueba los campos, tallas y cantidades. Solo se admiten datos de demostración válidos.'})
        except Exception:
            return self.reply(500, {'error': 'No se pudo confirmar la operación. Reintenta con la misma solicitud; no se mostrará un éxito sin confirmación.'})

class DemoServer(ThreadingHTTPServer):
    def __init__(self, address, app):
        super().__init__(address, Handler)
        self.app = app

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    os.umask(0o077)
    directory = os.environ.get('SHOP_PRIVATE_DIR', default_private_directory())
    app = Application(Store(directory))
    server = DemoServer(('127.0.0.1', args.port), app)
    print(f'AYLIN SHOP: demo local en http://127.0.0.1:{server.server_port}. No publicar este servidor.')
    server.serve_forever()
