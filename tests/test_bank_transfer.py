"""Fixtures de transferencia: importes inventados y un IBAN sintético con BBAN todo ceros.
No se conecta con bancos, no se envían correos ni se cambia el catálogo real.
"""
import copy
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
from app import Application, CATALOG, DemoServer, Store
from bank_transfer import BankTransferConfig, BankTransferService, InvalidTransfer, TransferDisabled, quote_items
from test_server import Client, payload

# IBAN exclusivo de fixtures, matemáticamente válido pero sin cuenta bancaria operativa.
# La validación de checksum nunca equivale a confirmar una cuenta o su beneficiario.
ZERO_BBAN = '0' * 20
FAKE_IBAN = 'ES' + f'{98 - int(ZERO_BBAN + "142800") % 97:02d}' + ZERO_BBAN
FAKE_BENEFICIARY = 'BENEFICIARIO FICTICIO - NO REALIZAR TRANSFERENCIAS'
SID = 'a' * 64
KEY = 'test-request-11111111-2222-3333-4444'

def test_catalog():
    catalog = copy.deepcopy(CATALOG)
    catalog['leggings']['priceMinor'] = 1299
    catalog['top']['priceMinor'] = 1599
    catalog['correa']['priceMinor'] = 499
    return catalog

def items():
    return [{'id': 'leggings', 'size': 'S', 'quantity': 2},
            {'id': 'top', 'size': 'M', 'quantity': 1},
            {'id': 'correa', 'size': 'Única', 'quantity': 1}]

class BankTransferTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(self.temp.name)
        self.config = BankTransferConfig(True, FAKE_BENEFICIARY, FAKE_IBAN)
        self.service = BankTransferService(self.store, test_catalog(), self.config)
        self.shipping = payload()['customer']
    def tearDown(self):
        self.temp.cleanup()
    def count(self):
        with self.store.connect() as db:
            return db.execute('SELECT count(*) FROM transfer_orders').fetchone()[0]
    def prepare(self, **kwargs):
        return self.service.prepare_pending(SID, KEY, items(), self.shipping, test_only=True, **kwargs)

    def test_config_private_and_disabled_by_default(self):
        with patch.dict(os.environ, {}, clear=True):
            disabled = BankTransferConfig.from_env()
            self.assertFalse(disabled.enabled)
            with self.assertRaises(TransferDisabled): disabled.validated_details()
        with patch.dict(os.environ, {'SHOP_BANK_TRANSFER_ENABLED': 'true', 'SHOP_BANK_BENEFICIARY': FAKE_BENEFICIARY, 'SHOP_BANK_IBAN': FAKE_IBAN}, clear=True):
            config = BankTransferConfig.from_env()
            self.assertEqual(config.validated_details()['iban'], FAKE_IBAN)
            self.assertNotIn(FAKE_IBAN, repr(config)); self.assertNotIn(FAKE_BENEFICIARY, repr(config))
        spaced = BankTransferConfig(True, FAKE_BENEFICIARY, ' '.join(FAKE_IBAN[i:i+4] for i in range(0,len(FAKE_IBAN),4)).lower())
        self.assertEqual(spaced.validated_details()['iban'], FAKE_IBAN)
        for iban, name in [('ES00' + ZERO_BBAN, FAKE_BENEFICIARY), (FAKE_IBAN[:-1], FAKE_BENEFICIARY), (FAKE_IBAN, ''), (FAKE_IBAN, 'nombre\ncontrol')]:
            with self.assertRaises(InvalidTransfer) as error:
                BankTransferConfig(True, name, iban).validated_details()
            self.assertNotIn(iban, str(error.exception))

    def test_server_quote_exact_cents_and_variants(self):
        quote = quote_items(items(), test_catalog())
        self.assertEqual(quote['totalMinor'], 4696)
        self.assertEqual(quote['currency'], 'EUR')
        self.assertEqual(quote['items'][0]['lineTotalMinor'], 2598)
        self.assertEqual(quote['items'][1]['size'], 'M')
        for field, value in [('priceMinor', 1), ('totalMinor', 1), ('bankTransfer', {})]:
            forged = items(); forged[0][field] = value
            with self.assertRaises(InvalidTransfer): quote_items(forged, test_catalog())
        for change in [{'size':'XXL'}, {'quantity':True}, {'quantity':1.5}, {'quantity':-1}]:
            bad = items(); bad[0].update(change)
            with self.assertRaises(InvalidTransfer): quote_items(bad, test_catalog())
        invalid = test_catalog(); invalid['leggings']['priceMinor'] = 12.99
        with self.assertRaises(InvalidTransfer): quote_items(items(), invalid)
        self.assertTrue(all(p['priceMinor'] == 0 for p in CATALOG.values()))

    def test_pending_record_persists_with_frozen_instructions(self):
        result = self.prepare()
        self.assertEqual(result['paymentStatus'], 'pending_payment')
        self.assertEqual(result['paymentStatusLabel'], 'Pendiente de pago')
        self.assertTrue(result['testOnly']); self.assertFalse(result['commercial'])
        bank = result['bankTransfer']
        self.assertEqual(bank['beneficiary'], FAKE_BENEFICIARY)
        self.assertEqual(bank['iban'], FAKE_IBAN)
        self.assertEqual(bank['amountMinor'], 4696)
        self.assertEqual(bank['amountText'], '46,96 €')
        self.assertEqual(bank['reference'], result['id'])
        self.assertNotIn('customer', result)
        reopened = Store(self.temp.name)
        with reopened.connect() as db:
            row = db.execute('SELECT * FROM transfer_orders').fetchone()
            self.assertEqual(row['state'], 'pending_payment')
            self.assertEqual(row['test_only'], 1)
            self.assertEqual(json.loads(row['private_payload'])['customer'], self.shipping)
            self.assertEqual(json.loads(row['receipt']), result)
            self.assertEqual(db.execute('SELECT count(*) FROM orders').fetchone()[0], 0)

    def test_idempotency_session_binding_and_original_bank_snapshot(self):
        original = self.prepare()
        changed = test_catalog(); changed['top']['priceMinor'] = 9999
        service = BankTransferService(self.store, changed, BankTransferConfig(True, 'OTRO BENEFICIARIO FICTICIO', FAKE_IBAN))
        same = service.prepare_pending(SID, KEY, items(), self.shipping, test_only=True)
        self.assertEqual(same, original)
        self.assertEqual(self.count(), 1)
        different = items(); different[0]['quantity'] = 1
        with self.assertRaises(InvalidTransfer): service.prepare_pending(SID, KEY, different, self.shipping, test_only=True)
        other = service.prepare_pending('b' * 64, KEY, items(), self.shipping, test_only=True)
        self.assertNotEqual(other['id'], original['id'])
        self.assertEqual(self.count(), 2)

    def test_zero_total_and_missing_configuration_do_not_create_transfer(self):
        zero = BankTransferService(self.store, CATALOG, self.config)
        with self.assertRaises(InvalidTransfer): zero.prepare_pending(SID, KEY, items(), self.shipping, test_only=True)
        disabled = BankTransferService(self.store, test_catalog(), BankTransferConfig())
        with self.assertRaises(TransferDisabled): disabled.prepare_pending(SID, KEY, items(), self.shipping, test_only=True)
        invalid = BankTransferService(self.store, test_catalog(), BankTransferConfig(True, FAKE_BENEFICIARY, 'INVALID'))
        with self.assertRaises(InvalidTransfer): invalid.prepare_pending(SID, KEY, items(), self.shipping, test_only=True)
        self.assertEqual(self.count(), 0)

    def test_no_paid_transition_or_demo_cleanup_of_pending_records(self):
        result = self.prepare()
        with self.store.connect() as db:
            db.execute('UPDATE transfer_orders SET created=?', (time.time()-3*86400,))
        self.store.cleanup()
        self.assertEqual(self.count(), 1)
        with self.assertRaises(sqlite3.IntegrityError):
            with self.store.connect() as db:
                db.execute("UPDATE transfer_orders SET state='paid' WHERE id=?", (result['id'],))
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT state FROM transfer_orders').fetchone()[0], 'pending_payment')

    def test_commercial_hard_lock_even_when_env_requests_enablement(self):
        for total in [0, 4696, -1]: self.assertFalse(self.service.available_for_total(total))
        with self.assertRaises(TransferDisabled): self.service.prepare_pending(SID, KEY, items(), self.shipping)
        self.assertEqual(self.count(), 0)

    def test_public_http_remains_free_and_cannot_access_bank_or_mark_paid(self):
        env = {'SHOP_BANK_TRANSFER_ENABLED': 'true', 'SHOP_BANK_BENEFICIARY': FAKE_BENEFICIARY, 'SHOP_BANK_IBAN': FAKE_IBAN}
        with patch.dict(os.environ, env, clear=True): app = Application(self.store)
        app.mailer.enabled = False
        server = DemoServer(('127.0.0.1', 0), app)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            url = f'http://127.0.0.1:{server.server_port}'
            a, b = Client(url), Client(url)
            session = a.session(); b.session()
            self.assertNotIn(FAKE_IBAN, str(session)); self.assertFalse(app.bank_transfer.available_for_total(4696))
            status, receipt = a.request('/api/orders', payload())
            self.assertEqual(status, 201); self.assertEqual(receipt['totalMinor'], 0)
            self.assertNotIn('bankTransfer', receipt)
            self.assertNotIn(FAKE_IBAN, str(receipt)); self.assertNotIn('pending_payment', str(receipt))
            self.assertEqual(self.count(), 0)
            for path in ['/api/bank-transfer', '/api/transfers', '/api/orders/' + receipt['id'] + '/paid', '/api/admin/orders/' + receipt['id'] + '/confirm-payment']:
                self.assertIn(b.request(path)[0], [401,404])
                self.assertIn(b.request(path, {'paid':True})[0], [401,404])
            for added in [{'paymentMethod':'bank_transfer'}, {'test_only':True}, {'paymentStatus':'paid'}]:
                self.assertEqual(a.request('/api/orders', dict(payload(), **added))[0], 400)
            changed = copy.deepcopy(CATALOG['leggings']); changed['priceMinor'] = 1299
            with patch.dict(CATALOG, {'leggings': changed}):
                self.assertEqual(a.request('/api/orders', payload())[0], 400)
            self.assertEqual(self.count(), 0)
        finally:
            server.shutdown(); server.server_close()

if __name__ == '__main__': unittest.main()
