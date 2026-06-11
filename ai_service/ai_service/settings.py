import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('JWT_SECRET', 'django-insecure-ai-service-key')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'rest_framework',
    'apps.behavior',
    'apps.recommendations',
    # chatbot moved to rag_service
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'ai_service.urls'
WSGI_APPLICATION = 'ai_service.wsgi.application'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': []},
}]

if os.environ.get('DB_ENGINE') == 'sqlite':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.environ.get('SQLITE_PATH', BASE_DIR / 'data' / 'ai_service.sqlite3'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('DB_NAME', 'ai_service_db'),
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

# ─── Service URLs ────────────────────────────────────────────
PRODUCT_SERVICE_URL = os.environ.get('PRODUCT_SERVICE_URL', 'http://localhost:8001')
USER_SERVICE_URL    = os.environ.get('USER_SERVICE_URL',    'http://localhost:8002')
INTERNAL_SERVICE_TOKEN = os.environ.get('INTERNAL_SERVICE_TOKEN', 'internal-service-secret-token')
JWT_SECRET = os.environ.get('JWT_SECRET', SECRET_KEY)
JWT_ALGORITHM = 'HS256'

# ─── Neo4j ───────────────────────────────────────────────────
NEO4J_URI      = os.environ.get('NEO4J_URI',      'bolt://localhost:7687')
NEO4J_USER     = os.environ.get('NEO4J_USER',     'neo4j')
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', 'neo4jpassword')

# ─── OpenAI ──────────────────────────────────────────────────
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
OPENAI_MODEL   = os.environ.get('OPENAI_MODEL',   'gpt-4o-mini')
# Local sentence-transformers model (multilingual, supports Vietnamese)
EMBED_MODEL    = os.environ.get('EMBED_MODEL', 'paraphrase-multilingual-MiniLM-L12-v2')

# ─── ML Paths ────────────────────────────────────────────────
MODEL_DIR = BASE_DIR / 'data' / 'models'
FAISS_DIR = BASE_DIR / 'data' / 'faiss'

# ─── Hybrid weights ──────────────────────────────────────────
LSTM_WEIGHT  = float(os.environ.get('LSTM_WEIGHT',  '0.4'))
GRAPH_WEIGHT = float(os.environ.get('GRAPH_WEIGHT', '0.35'))
RAG_WEIGHT   = float(os.environ.get('RAG_WEIGHT',   '0.25'))
TOP_N        = int(os.environ.get('TOP_N', '10'))

# Active sequence model: rnn | lstm | bilstm | gru | narm | sasrec | bert4rec
# Run `python manage.py train_models` to compare, then set this to the winner.
ACTIVE_MODEL = os.environ.get('ACTIVE_MODEL', 'lstm')

# ─── RAG Service ─────────────────────────────────────────────
# Internal docker-network URL (not exposed through nginx)
RAG_SERVICE_URL = os.environ.get('RAG_SERVICE_URL', 'http://rag_service:8008')
