"""Configurações do Django. Tudo vem de variáveis de ambiente (veja env.exemplo)."""

import dj_database_url

from cinema.frameworks_drivers.config import Config

CONFIG = Config.do_ambiente()

SECRET_KEY = CONFIG.segredo
DEBUG = CONFIG.debug

# Trava de segurança: em produção, a chave de desenvolvimento não pode ser usada
# (ela também assina os tokens de login).
if not DEBUG and (SECRET_KEY == Config.segredo or len(SECRET_KEY) < 32):
    raise RuntimeError("Defina DJANGO_SECRET_KEY (32+ caracteres aleatórios) para rodar com DJANGO_DEBUG=0.")
ALLOWED_HOSTS = CONFIG.hosts

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",  # usamos só o sistema de hash de senha
    "corsheaders",
    "rest_framework",
    "cinema.adaptadores.persistencia",
    "cinema.frameworks_drivers.django_app",
]

MIDDLEWARE = [
    "cinema.frameworks_drivers.django_projeto.saude.SaudeMiddleware",  # antes da checagem de host
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "cinema.frameworks_drivers.django_projeto.urls"
WSGI_APPLICATION = "cinema.frameworks_drivers.django_projeto.wsgi.application"

DATABASES = {"default": dj_database_url.parse(CONFIG.banco_url, conn_max_age=60, conn_health_checks=True)}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CACHES = {
    # Cache do catálogo de filmes (rápido, em memória de cada processo)
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "cinema"},
    # Contagem de tentativas de login: no PostgreSQL, para todos os processos verem o mesmo número.
    # A tabela é criada com "python manage.py createcachetable" (o Dockerfile já faz).
    "seguranca": {"BACKEND": "django.core.cache.backends.db.DatabaseCache", "LOCATION": "cinema_cache_seguranca"},
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],  # a autenticação é um caso de uso nosso (JWT)
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "EXCEPTION_HANDLER": "cinema.adaptadores.controllers.base.tratar_excecao",
    # Login, cadastro e recuperação de senha: no máximo 20 pedidos por minuto por IP.
    "DEFAULT_THROTTLE_RATES": {"acesso": CONFIG.limite_acesso},
    # Quantos proxies ficam na frente do Django (nginx = 1). Serve para achar o IP real do visitante.
    "NUM_PROXIES": CONFIG.proxies,
}

CORS_ALLOWED_ORIGINS = CONFIG.cors
APPEND_SLASH = False

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_TZ = True

# Atrás do load balancer da AWS (HTTPS termina no ALB)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Cabeçalhos de segurança nas respostas da API
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"
if not DEBUG:
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30  # só em produção (HTTPS)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {"cinema": {"handlers": ["console"], "level": "INFO"}},
}
