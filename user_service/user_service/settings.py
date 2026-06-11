import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('JWT_SECRET', 'django-insecure-user-service-key')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['*', 'localhost', 'user_service', '127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'rest_framework',
    'apps.users',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',

]

ROOT_URLCONF = 'user_service.urls'
WSGI_APPLICATION = 'user_service.wsgi.application'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': []},
}]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'users_db'),
        'USER': os.environ.get('DB_USER', 'root'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'rootpassword'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {'charset': 'utf8mb4'},
    }
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [],
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

INTERNAL_SERVICE_TOKEN = os.environ.get('INTERNAL_SERVICE_TOKEN', 'internal-service-secret-token')
JWT_SECRET = os.environ.get('JWT_SECRET', SECRET_KEY)
JWT_ALGORITHM = 'HS256'
JWT_ACCESS_TOKEN_LIFETIME_HOURS = int(os.environ.get('JWT_ACCESS_TOKEN_LIFETIME_HOURS', 24))
JWT_REFRESH_TOKEN_LIFETIME_DAYS = int(os.environ.get('JWT_REFRESH_TOKEN_LIFETIME_DAYS', 7))

RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.environ.get('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.environ.get('RABBITMQ_USER', 'guest')
RABBITMQ_PASSWORD = os.environ.get('RABBITMQ_PASSWORD', 'guest')

PRODUCT_SERVICE_URL = os.environ.get('PRODUCT_SERVICE_URL', 'http://localhost:8001')
USER_SERVICE_URL    = os.environ.get('USER_SERVICE_URL',    'http://localhost:8002')
CART_SERVICE_URL    = os.environ.get('CART_SERVICE_URL',    'http://localhost:8003')
ORDER_SERVICE_URL   = os.environ.get('ORDER_SERVICE_URL',   'http://localhost:8004')
PAYMENT_SERVICE_URL = os.environ.get('PAYMENT_SERVICE_URL', 'http://localhost:8005')
SHIPPING_SERVICE_URL= os.environ.get('SHIPPING_SERVICE_URL','http://localhost:8006')
