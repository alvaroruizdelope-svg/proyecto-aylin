"""Importación explícita y de solo lectura de la base anterior; nunca ejecuta su limpieza."""
import hashlib
import json
from pathlib import Path
import sqlite3
from datetime import datetime, timezone as tz
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from shop.models import Order, OrderLine, Review, ReviewEvent, OrderEvent, LegacyArchive
from shop.catalog import catalogue

class Command(BaseCommand):
    help='Importa la base del servidor anterior sin modificarla ni borrar datos. Idempotente.'
    def add_arguments(self,parser): parser.add_argument('--source',required=True)
    @transaction.atomic
    def handle(self,*args,**options):
        if settings.MODE!='demo': raise CommandError('Importa el servidor anterior en el perfil demo, separado de la familia.')
        source=Path(options['source']).expanduser().resolve()
        if not source.is_file(): raise CommandError('No existe el archivo de origen.')
        identity=hashlib.sha256(str(source).encode()).hexdigest()
        db=sqlite3.connect(source.as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
        tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        products={p['id']:p for p in catalogue()['products']}
        counts={'orders':0,'reviews':0,'moderation':0,'archived_fixtures':0}
        try:
            if 'orders' in tables:
                for raw in db.execute('SELECT * FROM orders'):
                    key=identity+':order:'+str(raw['id'])
                    if Order.objects.filter(legacy_key=key).exists(): continue
                    p=json.loads(raw['payload']);receipt=json.loads(raw['receipt'])
                    order=Order.objects.create(number=str(raw['id']),environment='demo',session_hash='legacy-'+hashlib.sha256((identity+raw['sid']).encode()).hexdigest()[:50],request_key=raw['request_key'],fingerprint=raw['fingerprint'],created=datetime.fromtimestamp(raw['created'],tz.utc),method='free_demo',status=Order.Status.DEMO,total_minor=0,customer=p['customer'],receipt=receipt,legacy_key=key)
                    for item in p['items']:
                        product=products.get(item['id'],{})
                        OrderLine.objects.create(order=order,product_id=item['id'],name=product.get('name',item['id']),size=item.get('size','No registrada'),quantity=item['quantity'],unit_price_minor=0)
                    OrderEvent.objects.create(order=order,new_status=Order.Status.DEMO,reason='Importado sin modificar la base anterior; no conserva una identidad de administrador anterior.')
                    counts['orders']+=1
            if 'reviews' in tables:
                for raw in db.execute('SELECT * FROM reviews'):
                    key=identity+':review:'+str(raw['id']);cols=raw.keys()
                    _,created=Review.objects.get_or_create(legacy_key=key,defaults={
                        'public_name':raw['public_name'] if 'public_name' in cols else '', 'rating':raw['rating'],'comment':raw['comment'],
                        'verified_demo':bool(raw['verified']),'created':datetime.fromtimestamp(raw['created'],tz.utc),
                        'published_at':datetime.fromtimestamp(raw['published_at'],tz.utc) if 'published_at' in cols and raw['published_at'] else None,
                        'status':raw['status'],'reason':raw['reason'],'legacy_product':raw['product']})
                    counts['reviews']+=int(created)
            if 'moderation' in tables:
                for raw in db.execute('SELECT * FROM moderation'):
                    review=Review.objects.filter(legacy_key=identity+':review:'+str(raw['review_id'])).first()
                    if review:
                        _,created=ReviewEvent.objects.get_or_create(legacy_key=identity+':moderation:'+str(raw['id']),defaults={'review':review,'decision':raw['decision'],'reason':raw['reason'],'created':datetime.fromtimestamp(raw['created'],tz.utc)})
                        counts['moderation']+=int(created)
            if 'transfer_orders' in tables:
                for raw in db.execute('SELECT * FROM transfer_orders'):
                    _,created=LegacyArchive.objects.get_or_create(legacy_key=identity+':transfer:'+str(raw['id']),defaults={'kind':'legacy_transfer_fixture','payload':dict(raw)})
                    counts['archived_fixtures']+=int(created)
        except Exception as e:
            raise CommandError('Importación cancelada sin borrar el origen. Revisa esquema/duplicados; no se han publicado datos.') from e
        finally: db.close()
        self.stdout.write(str(counts))
