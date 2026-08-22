"""
Configuracoes do Django para o projeto ServConecta.

Ambientes controlados por DJANGO_ENV:
- desenvolvimento (padrao): SQLite, HTTPS desligado.
- producao: PostgreSQL, HTTPS/HSTS ligado, estaticos via WhiteNoise.

Variaveis usadas em producao:
  DJANGO_ENV=producao
  DJANGO_SECRET_KEY=...
  DJANGO_ALLOWED_HOSTS=exemplo.com,www.exemplo.com
  DJANGO_CSRF_TRUSTED_ORIGINS=https://exemplo.com
  POSTGRES_DB / POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_HOST / POSTGRES_PORT
"""
import os
from pathlib import Path

# Diretorio base do projeto (onde fica o manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Ambiente
# ---------------------------------------------------------------------------
# Desenvolvimento e o padrao; producao exige DJANGO_ENV=producao.
EM_PRODUCAO = os.environ.get("DJANGO_ENV", "desenvolvimento").lower() == "producao"
DEBUG = not EM_PRODUCAO

def _env_list(nome: str) -> list[str]:
    return [item.strip() for item in os.environ.get(nome, "").split(",") if item.strip()]

# ---------------------------------------------------------------------------
# Seguranca
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if EM_PRODUCAO:
        raise RuntimeError("Defina DJANGO_SECRET_KEY no ambiente de producao.")
    # Apenas para desenvolvimento.
    SECRET_KEY = "django-insecure-troque-esta-chave-em-producao"

# Em producao, liste os dominios em DJANGO_ALLOWED_HOSTS (separados por virgula).
ALLOWED_HOSTS = _env_list("DJANGO_ALLOWED_HOSTS") or ([] if EM_PRODUCAO else ["*"])

# Necessario quando o trafego HTTPS passa por um proxy reverso (nginx, Caddy, etc.)
CSRF_TRUSTED_ORIGINS = _env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

# ---------------------------------------------------------------------------
# Aplicativos
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    # Serve os estaticos direto pelo runserver (WhiteNoise), inclusive em dev
    "whitenoise.runserver_nostatic",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # App do projeto
    "servconecta",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise logo apos SecurityMiddleware serve/comprime os estaticos
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # templates/ na raiz do projeto (onde estao os .html do servconecta)
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "servconecta.context_processors.notificacoes_nao_lidas",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------------------
# Banco de dados
# ---------------------------------------------------------------------------
# Desenvolvimento: SQLite (arquivo local).
# Producao: PostgreSQL via variaveis de ambiente.
if EM_PRODUCAO:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ["POSTGRES_DB"],
            "USER": os.environ["POSTGRES_USER"],
            "PASSWORD": os.environ["POSTGRES_PASSWORD"],
            "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ---------------------------------------------------------------------------
# Validacao de senha
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internacionalizacao
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Arquivos estaticos e de midia
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

# Em producao o WhiteNoise serve os estaticos comprimidos com hash no nome
# (requer `collectstatic` antes do deploy).
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if EM_PRODUCAO
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        )
    },
}

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# ---------------------------------------------------------------------------
# Autenticacao (rotas usadas pelos templates)
# ---------------------------------------------------------------------------
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "home"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Cookies e HTTPS
# ---------------------------------------------------------------------------
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 7 dias

if EM_PRODUCAO:
    # Forca HTTPS em todas as requisicoes
    SECURE_SSL_REDIRECT = True
    # Respeita o header do proxy reverso que termina o TLS
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    # Cookies apenas via HTTPS
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # HSTS: navegador so acessa por HTTPS por 1 ano
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_REFERRER_POLICY = "same-origin"
else:
    # Rede local HTTP (ex.: testar pelo celular)
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
