"""Estructura de transferencia, SIN habilitación comercial en esta versión.

La cuenta solo se lee del entorno privado. El checkout público sigue siendo gratuito.
prepare_pending(..., test_only=True) es exclusivamente una herramienta interna de pruebas;
no tiene ruta HTTP, no envía correos ni realiza operaciones bancarias.
"""
from dataclasses import dataclass, field
import copy
import hashlib
import json
import os
import re
import time
import uuid

PENDING_PAYMENT = 'pending_payment'
PENDING_PAYMENT_LABEL = 'Pendiente de pago'
MAX_AMOUNT_MINOR = 100_000_000  # Límite técnico de fixtures; requiere revisión antes de producción.
# Longitudes IBAN de los países admitidos por esta estructura. No prueba titularidad ni existencia.
IBAN_LENGTHS = {'AD': 24, 'AL': 28, 'AT': 20, 'BA': 20, 'BE': 16, 'BG': 22, 'CH': 21,
                'CY': 28, 'CZ': 24, 'DE': 22, 'DK': 18, 'EE': 20, 'ES': 24, 'FI': 18,
                'FR': 27, 'GB': 22, 'GI': 23, 'GR': 27, 'HR': 21, 'HU': 28, 'IE': 22,
                'IS': 26, 'IT': 27, 'LI': 21, 'LT': 20, 'LU': 20, 'LV': 21, 'MC': 27,
                'MD': 24, 'ME': 22, 'MK': 19, 'MT': 31, 'NL': 18, 'NO': 15, 'PL': 28,
                'PT': 25, 'RO': 24, 'RS': 22, 'SE': 24, 'SI': 19, 'SK': 24, 'SM': 27,
                'VA': 22, 'XK': 20}

class TransferDisabled(ValueError):
    pass

class InvalidTransfer(ValueError):
    pass

@dataclass(frozen=True)
class BankTransferConfig:
    enabled: bool = False
    beneficiary: str = field(default='', repr=False)
    iban: str = field(default='', repr=False)

    @classmethod
    def from_env(cls):
        return cls(os.environ.get('SHOP_BANK_TRANSFER_ENABLED') == 'true',
                   os.environ.get('SHOP_BANK_BENEFICIARY', ''), os.environ.get('SHOP_BANK_IBAN', ''))

    def validated_details(self):
        # Errores deliberadamente genéricos: no devolver cuenta/titular ni valores de entorno.
        if not self.enabled:
            raise TransferDisabled('Transferencia bancaria desactivada.')
        name = self.beneficiary.strip()
        iban = re.sub(r'\s+', '', self.iban).upper()
        if not 2 <= len(name) <= 140 or any(ord(c) < 32 for c in name):
            raise InvalidTransfer('Configuración privada de transferencia no válida.')
        if not re.fullmatch(r'[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}', iban) or len(iban) != IBAN_LENGTHS.get(iban[:2]):
            raise InvalidTransfer('Configuración privada de transferencia no válida.')
        numeric = ''.join(str(ord(c)-55) if c.isalpha() else c for c in iban[4:] + iban[:4])
        if int(numeric) % 97 != 1:
            raise InvalidTransfer('Configuración privada de transferencia no válida.')
        return {'beneficiary': name, 'iban': iban}


def quote_items(items, catalog):
    """Importes desde catálogo de servidor, siempre céntimos enteros, sin confiar en el cliente."""
    if not isinstance(items, list) or not 1 <= len(items) <= 24:
        raise InvalidTransfer('Carrito no válido.')
    lines, seen, total = [], set(), 0
    for item in items:
        if not isinstance(item, dict) or set(item) != {'id', 'size', 'quantity'}:
            raise InvalidTransfer('Solo se admiten identificador, talla y cantidad.')
        if not isinstance(item['id'], str) or not isinstance(item['size'], str):
            raise InvalidTransfer('Variante no válida.')
        product = catalog.get(item['id'])
        variant = next((v for v in product['variants'] if v['size'] == item['size']), None) if product else None
        key = (item['id'], item['size'])
        quantity = item['quantity']
        if not variant or not variant['available'] or type(quantity) is not int or not 1 <= quantity <= variant['demoLimit'] or key in seen:
            raise InvalidTransfer('Talla o cantidad no disponible.')
        unit = product['priceMinor']
        if type(unit) is not int or not 0 <= unit <= MAX_AMOUNT_MINOR:
            raise InvalidTransfer('Precio de catálogo no válido.')
        amount = unit * quantity
        total += amount
        if total > MAX_AMOUNT_MINOR:
            raise InvalidTransfer('Importe fuera del límite de pruebas.')
        seen.add(key)
        lines.append({'id': product['id'], 'name': product['name'], 'size': variant['size'],
                      'quantity': quantity, 'unitPriceMinor': unit, 'lineTotalMinor': amount})
    return {'currency': 'EUR', 'totalMinor': total, 'items': lines}


def validate_test_shipping(customer):
    # Este método interno también valida datos antes de guardarlos; no acepta PII por rutas nuevas.
    fields = {'name': (3,100), 'email': (5,150), 'phone': (7,25), 'address': (5,180),
              'postal': (5,5), 'city': (2,80), 'province': (2,80)}
    if not isinstance(customer, dict) or set(customer) != set(fields):
        raise InvalidTransfer('Datos de envío de prueba incompletos.')
    clean = {}
    for key, (low, high) in fields.items():
        value = customer[key]
        if not isinstance(value, str) or not low <= len(value.strip()) <= high or any(ord(c) < 32 for c in value):
            raise InvalidTransfer('Datos de envío de prueba no válidos.')
        clean[key] = value.strip()
    if not re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+', clean['email']) or not re.fullmatch(r'\+?[0-9]{7,15}', clean['phone']) or not re.fullmatch(r'[0-9]{5}', clean['postal']):
        raise InvalidTransfer('Datos de envío de prueba no válidos.')
    return clean

class BankTransferService:
    def __init__(self, store, catalog, config=None):
        self.store = store
        self.catalog = copy.deepcopy(catalog)
        self.config = config if config is not None else BankTransferConfig.from_env()
        with store.connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS transfer_orders (
              id TEXT PRIMARY KEY, sid TEXT NOT NULL, request_key TEXT NOT NULL, fingerprint TEXT NOT NULL,
              created REAL NOT NULL, state TEXT NOT NULL CHECK(state='pending_payment'),
              total_minor INTEGER NOT NULL CHECK(total_minor>0), currency TEXT NOT NULL CHECK(currency='EUR'),
              test_only INTEGER NOT NULL CHECK(test_only=1), private_payload TEXT NOT NULL, receipt TEXT NOT NULL,
              UNIQUE(sid,request_key))''')

    def available_for_total(self, total_minor):
        # Bloqueo de esta entrega: ni variables de entorno ni importe positivo habilitan ventas.
        # Se necesita una futura implementación revisada de autorización y persistencia comercial.
        return False

    def prepare_pending(self, sid, request_key, items, customer, *, test_only=False):
        if test_only is not True:
            raise TransferDisabled('Las transferencias comerciales no están habilitadas en esta versión.')
        if not isinstance(sid, str) or not re.fullmatch(r'[a-f0-9]{64}', sid) or not isinstance(request_key, str) or not re.fullmatch(r'[A-Za-z0-9-]{16,100}', request_key):
            raise InvalidTransfer('Sesión o identificador de solicitud no válidos.')
        quote = quote_items(items, self.catalog)
        if quote['totalMinor'] == 0:
            raise InvalidTransfer('Los pedidos gratuitos no requieren transferencia bancaria.')
        shipping = validate_test_shipping(customer)
        # Comparar la solicitud, no las variables bancarias actuales: los reintentos conservan la cuenta original.
        requested = {'items': sorted(items, key=lambda i: (i['id'], i['size'])), 'customer': shipping}
        fingerprint = hashlib.sha256(json.dumps(requested, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            existing = db.execute('SELECT fingerprint,receipt FROM transfer_orders WHERE sid=? AND request_key=?', (sid, request_key)).fetchone()
            if existing:
                if existing['fingerprint'] != fingerprint:
                    raise InvalidTransfer('La solicitud ya se utilizó con otro contenido.')
                return json.loads(existing['receipt'])
            bank = self.config.validated_details()
            oid = 'TEST-TRANSFER-' + str(uuid.uuid4())
            reference = oid
            total = quote['totalMinor']
            formatted = f'{total // 100},{total % 100:02d} €'
            instructions = dict(bank, amountMinor=total, currency='EUR', amountText=formatted, reference=reference)
            receipt = {'id': oid, 'testOnly': True, 'commercial': False, 'paymentMethod': 'bank_transfer',
                       'paymentStatus': PENDING_PAYMENT, 'paymentStatusLabel': PENDING_PAYMENT_LABEL,
                       **quote, 'bankTransfer': instructions,
                       'notice': 'Fixture de prueba: no realices ninguna transferencia. No hay pago confirmado.'}
            private = {'customer': shipping, 'quote': quote, 'bankSnapshot': instructions}
            db.execute('''INSERT INTO transfer_orders
              (id,sid,request_key,fingerprint,created,state,total_minor,currency,test_only,private_payload,receipt)
              VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
              (oid, sid, request_key, fingerprint, time.time(), PENDING_PAYMENT, total, 'EUR', 1,
               json.dumps(private, ensure_ascii=False), json.dumps(receipt, ensure_ascii=False)))
        # No notificaciones ni transacciones bancarias; la cuenta y el precio quedan congelados en SQLite privado.
        return receipt
