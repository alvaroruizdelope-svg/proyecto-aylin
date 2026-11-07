"""Configuración local gratuita. No es una autorización de despliegue público."""
from datetime import timedelta
from pathlib import Path
import os
import secrets
from django.core.exceptions import ImproperlyConfigured
BASE_DIR = Path(__file__).resolve().parent.parent
MODE = 'demo'
DEBUG = False
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]', 'testserver']
INSTALLED_APPS = ['shop', 'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles', 'axes']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware', 'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware', 'django.contrib.auth.middleware.AuthenticationMiddleware', 'axes.middleware.AxesMiddleware', 'django.contrib.messages.middleware.MessageMiddleware', 'django.middleware.clickjacking.XFrameOptionsMiddleware', 'shop.middleware.LocalOnlyMiddleware']
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [], 'APP_DIRS': True, 'OPTIONS': {'context_processors': ['django.template.context_processors.request', 'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION = 'config.wsgi.application'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LANGUAGE_CODE = 'es'
TIME_ZONE = 'Europe/Madrid'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
AUTHENTICATION_BACKENDS = ['axes.backends.AxesStandaloneBackend', 'django.contrib.auth.backends.ModelBackend']
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=15)
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_PARAMETERS = ['username', 'ip_address']
AXES_LOCKOUT_CALLABLE = 'shop.views.locked_out'
AXES_ENABLE_ACCESS_FAILURE_LOG = False
AUTH_PASSWORD_VALIDATORS = [{'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'}, {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 12}}, {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'}, {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'}]
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
SESSION_COOKIE_AGE = 3600
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
CSRF_USE_SESSIONS = True
CSRF_HEADER_NAME = 'HTTP_X_CSRF_TOKEN'
CSRF_FAILURE_VIEW = 'shop.views.csrf_failure'
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
# Solo HTTP de loopback. No activar Internet cambiando estas variables.
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'
# Doble cierre: no hay ajuste de entorno que active dinero familiar en esta entrega.
FAMILY_CHECKOUT_ENABLED = False
FAMILY_MONEY_RELEASED = False
MAIL_ENABLED = os.environ.get('SHOP_MAIL_ENABLED') == 'true'
MAIL_PROVIDER = os.environ.get('SHOP_MAIL_PROVIDER', 'resend')
MAIL_FROM = os.environ.get('SHOP_MAIL_FROM', '')
SELLER_EMAIL = os.environ.get('SHOP_SELLER_EMAIL', '')
TEST_BUYER_EMAILS = [s.strip().lower() for s in os.environ.get('SHOP_TEST_BUYER_EMAILS', '').split(',') if s.strip()]
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
SMTP_HOST = os.environ.get('SHOP_SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SHOP_SMTP_PORT', '465'))
SMTP_USER = os.environ.get('SHOP_SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SHOP_SMTP_PASSWORD', '')
BANK_BENEFICIARY = os.environ.get('SHOP_BANK_BENEFICIARY', '')
BANK_IBAN = os.environ.get('SHOP_BANK_IBAN', '')

def private_settings(mode):
    default = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData/Local')) / 'AylinShopDjango' if os.name == 'nt' else Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share')) / 'aylin-shop-django'
    raw = Path(os.environ.get('SHOP_PRIVATE_DIR', default)).expanduser()
    if raw.is_symlink():
        raise ImproperlyConfigured('El directorio privado no puede ser un enlace simbólico.')
    base = raw.resolve()
    if base == BASE_DIR or BASE_DIR in base.parents:
        raise ImproperlyConfigured('El directorio privado debe estar fuera del proyecto.')
    folder = base / mode
    folder.mkdir(parents=True, mode=0o700, exist_ok=True)
    if folder.is_symlink() or (hasattr(os, 'getuid') and folder.stat().st_uid != os.getuid()):
        raise ImproperlyConfigured('Directorio privado no seguro.')
    folder.chmod(0o700)
    secret = folder / 'secret.key'
    db = folder / 'shop.sqlite3'
    if secret.is_symlink() or db.is_symlink():
        raise ImproperlyConfigured('Archivo privado no seguro.')
    try:
        fd = os.open(secret, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, 'w') as f: f.write(secrets.token_urlsafe(64))
    except FileExistsError:
        pass
    secret.chmod(0o600)
    if not db.exists():
        fd = os.open(db, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600); os.close(fd)
    db.chmod(0o600)
    return folder, secret.read_text().strip(), {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': db, 'OPTIONS': {'timeout': 20, 'transaction_mode': 'IMMEDIATE'}}}
PRIVATE_DIR, SECRET_KEY, DATABASES = private_settings(MODE)
SESSION_COOKIE_NAME = 'aylin_demo_session'

DATA_UPLOAD_MAX_MEMORY_SIZE = 24000
LOGGING = {'version':1,'disable_existing_loggers':False,'handlers':{'null':{'class':'logging.NullHandler'},'security_console':{'class':'logging.StreamHandler'}},'loggers':{'axes':{'handlers':['null'],'propagate':False},'django.security.csrf':{'handlers':['security_console'],'propagate':False,'level':'WARNING'}}}

AXES_CLIENT_IP_CALLABLE = 'shop.middleware.client_ip'
