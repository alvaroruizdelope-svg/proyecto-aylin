"""Perfil local separado. Precios de 1 EUR; checkout monetario bloqueado."""
from .settings import *
MODE = 'family'
PRIVATE_DIR, SECRET_KEY, DATABASES = private_settings(MODE)
SESSION_COOKIE_NAME = 'aylin_family_session'
# Las pruebas automatizadas pueden override_settings con cuenta ficticia.
# Ninguna variable de entorno desbloquea pagos en una ejecución normal.
FAMILY_CHECKOUT_ENABLED = False
FAMILY_MONEY_RELEASED = False
