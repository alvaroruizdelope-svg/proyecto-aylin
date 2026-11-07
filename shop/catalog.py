import copy
import json
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

def catalogue():
    data = json.loads((settings.BASE_DIR / 'data/catalogo.json').read_text(encoding='utf-8'))
    if len(data['products']) != 6 or any(p['priceMinor'] != 0 for p in data['products']):
        raise ImproperlyConfigured('El catálogo base de esta entrega debe contener seis productos gratuitos.')
    if settings.MODE == 'family':
        for product in data['products']: product['priceMinor'] = 100
    return data
