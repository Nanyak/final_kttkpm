import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY    = os.environ.get('JWT_SECRET', 'django-insecure-rag-service-key')
DEBUG         = os.environ.get('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'rest_framework',
    'apps.chatbot',
    'apps.scores',
    # Management command only; product data is fetched live from product_service.
    'apps.products',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF     = 'rag_service.urls'
WSGI_APPLICATION = 'rag_service.wsgi.application'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [], 'APP_DIRS': True,
    'OPTIONS': {'context_processors': []},
}]

# rag_service has no models and never touches a database.
# Django requires the key to exist but an empty dict is valid when no DB is used.
DATABASES = {}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [],
    'UNAUTHENTICATED_USER': None,
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'UTC'
USE_I18N      = True
USE_TZ        = True

# ─── Upstream services ────────────────────────────────────────
PRODUCT_SERVICE_URL = os.environ.get('PRODUCT_SERVICE_URL', 'http://product_service:8001')

# ─── Neo4j ────────────────────────────────────────────────────
NEO4J_URI      = os.environ.get('NEO4J_URI',      'bolt://localhost:7687')
NEO4J_USER     = os.environ.get('NEO4J_USER',     'neo4j')
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', 'neo4jpassword')

# ─── OpenAI ───────────────────────────────────────────────────
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
OPENAI_MODEL   = os.environ.get('OPENAI_MODEL',   'gpt-4o-mini')

# ─── Embeddings / FAISS ───────────────────────────────────────
EMBED_MODEL = os.environ.get('EMBED_MODEL', 'paraphrase-multilingual-MiniLM-L12-v2')
FAISS_DIR   = BASE_DIR / 'data' / 'faiss'

# ─── Hybrid retrieval weights ─────────────────────────────────
FAISS_WEIGHT = float(os.environ.get('FAISS_WEIGHT', '0.6'))
GRAPH_WEIGHT = float(os.environ.get('GRAPH_WEIGHT', '0.4'))
TOP_K        = int(os.environ.get('TOP_K', '10'))
