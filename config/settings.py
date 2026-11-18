"""Configuração do projeto. Tudo que varia por ambiente vem de variáveis de ambiente."""
import hashlib
import os
import sys
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(nome, padrao=False):
    v = os.environ.get(nome)
    if v is None or v == "":
        return padrao
    return v.strip().lower() in ("1", "true", "yes", "sim", "on")


def env_int(nome, padrao):
    try:
        return int(os.environ.get(nome, padrao))
    except (TypeError, ValueError):
        return padrao


DEBUG = env_bool("DEBUG", False)
TESTING = "test" in sys.argv

# Se a chave não vier do ambiente, derivamos uma estável (igual em todos os workers).
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or hashlib.sha256(
    ("atendimento|" + os.environ.get("DATABASE_URL", str(BASE_DIR))).encode()
).hexdigest() * 2

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get(
        "DJANGO_ALLOWED_HOSTS", ".satela.com.br,localhost,127.0.0.1,[::1]"
    ).split(",")
    if h.strip()
]


def _origens(hosts):
    saida = []
    for h in hosts:
        if h in ("*",) or h.startswith("["):
            continue
        if h in ("localhost", "127.0.0.1"):
            saida += [f"http://{h}", f"https://{h}"]
        elif h.startswith("."):
            saida.append(f"https://*{h}")
        else:
            saida.append(f"https://{h}")
    return saida


CSRF_TRUSTED_ORIGINS = _origens(ALLOWED_HOSTS) + [
    o.strip() for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "central",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "central.contexto.global_ctx",
            ],
        },
    }
]

_data = Path("/data")
_db_padrao = f"sqlite:///{(_data if _data.is_dir() and os.access(_data, os.W_OK) else BASE_DIR) / 'db.sqlite3'}"
DATABASES = {
    "default": dj_database_url.config(default=_db_padrao, conn_max_age=60)
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        if (TESTING or DEBUG)
        else "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}
MEDIA_URL = "/media/"
MEDIA_ROOT = _data / "media" if _data.is_dir() else BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "/entrar/"
LOGIN_REDIRECT_URL = "/caixa/"

# --- Segurança / proxy ---
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
_seguro = not DEBUG and not TESTING
SESSION_COOKIE_SECURE = env_bool("COOKIES_SEGUROS", _seguro)
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SECURE_SSL_REDIRECT = env_bool("FORCAR_HTTPS", False)  # a plataforma já termina o TLS
SECURE_HSTS_SECONDS = env_int("HSTS_SEGUNDOS", 0 if not _seguro else 3600)
# Sem e-mail real: tudo vai para o console/memória.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# --- Modo demonstração ---
DEMO_MODE = env_bool("DEMO_MODE", True)
DEMO_ADMIN_PASSWORD = os.environ.get("DEMO_ADMIN_PASSWORD", "")

# --- Satela AI (compatível com OpenAI). Injetadas pela plataforma em produção ---
SATELA_API_URL = os.environ.get("SATELA_API_URL", "https://api.satela.com.br")
SATELA_API_KEY = os.environ.get("SATELA_API_KEY", "")
SATELA_MODEL = os.environ.get("SATELA_MODEL", "AC310")
SATELA_EMBED_MODEL = os.environ.get("SATELA_EMBED_MODEL", "EMB100")
IA_TIMEOUT = env_int("IA_TIMEOUT", 25)
IA_MAX_TOKENS = env_int("IA_MAX_TOKENS", 500)
IA_STREAM = env_bool("IA_STREAM", False)
KB_EMBEDDINGS = env_bool("KB_EMBEDDINGS", False)

# --- Proteção de custo (a demo é pública) ---
LIMITE_IP_POR_MINUTO = env_int("LIMITE_IP_POR_MINUTO", 12)
LIMITE_IP_POR_DIA = env_int("LIMITE_IP_POR_DIA", 150)
LIMITE_SESSAO_POR_MINUTO = env_int("LIMITE_SESSAO_POR_MINUTO", 6)
LIMITE_SESSAO_POR_DIA = env_int("LIMITE_SESSAO_POR_DIA", 60)
TETO_IA_DIARIO = env_int("TETO_IA_DIARIO", 300)
MENSAGEM_MAX_CHARS = env_int("MENSAGEM_MAX_CHARS", 1000)
HISTORICO_MAX_MENSAGENS = env_int("HISTORICO_MAX_MENSAGENS", 12)
PROXY_HOPS = env_int("PROXY_HOPS", 1)  # quantos proxies confiáveis à frente do app

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
}
