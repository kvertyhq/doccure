import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file if it exists
env_file = BASE_DIR / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()


SECRET_KEY = os.environ.get("SECRET_KEY", "g!y0otek@9t^b+b*7)&q2a5^=8_9&xcdii8@6h^_*wphl-(fu9")
DEBUG = os.environ.get("DEBUG", "True") == "True"

allowed_hosts_str = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1,doccure.kverty.com")
raw_hosts = [host.strip() for host in allowed_hosts_str.split(",") if host.strip()]
ALLOWED_HOSTS = []
for host in raw_hosts:
    if host == "*":
        ALLOWED_HOSTS.append("*")
        continue
    if host.startswith(("http://", "https://")):
        host = host.split("//", 1)[1].split("/", 1)[0]
    ALLOWED_HOSTS.append(host)

for host in ["doccure.kverty.com", "www.doccure.kverty.com", "localhost", "127.0.0.1", "testserver", ".ngrok-free.app", ".ngrok.io"]:
    if host not in ALLOWED_HOSTS and host != "*":
        ALLOWED_HOSTS.append(host)

trusted_origins_str = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
if trusted_origins_str:
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in trusted_origins_str.split(",") if origin.strip()]
else:
    CSRF_TRUSTED_ORIGINS = []
    for host in ALLOWED_HOSTS:
        if host.startswith("http://") or host.startswith("https://"):
            CSRF_TRUSTED_ORIGINS.append(host)
        elif host != "*":
            CSRF_TRUSTED_ORIGINS.append(f"https://{host}")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "debug_toolbar",
    "rest_framework",
    "core",
    "accounts",
    "doctors",
    "patients",
    "bookings",
    "ckeditor",
    "drf_spectacular",
    "rest_framework.authtoken",
    "api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

ROOT_URLCONF = "doccure.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "doccure.wsgi.application"

import dj_database_url

db_url = os.environ.get("DATABASE_URL")
if not db_url and os.environ.get("DB_HOST", "").startswith(("postgres://", "postgresql://")):
    db_url = os.environ.get("DB_HOST")

if db_url:
    DATABASES = {
        "default": dj_database_url.config(
            default=db_url,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
elif os.environ.get("DB_ENGINE"):
    DATABASES = {
        "default": {
            "ENGINE": os.environ.get("DB_ENGINE"),
            "NAME": os.environ.get("DB_NAME"),
            "USER": os.environ.get("DB_USER", ""),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", ""),
            "PORT": os.environ.get("DB_PORT", ""),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }



AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    # },
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

AUTH_USER_MODEL = "accounts.User"

INTERNAL_IPS = [
    "127.0.0.1",
]

TIME_INPUT_FORMATS = [
    "%I:%M %p",
]

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# CKEditor Configuration
CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_IMAGE_BACKEND = "pillow"
CKEDITOR_JQUERY_URL = (
    "//ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js"
)

CKEDITOR_CONFIGS = {
    "default": {
        "toolbar": "full",
        "height": 300,
        "width": "100%",
        "extraPlugins": ",".join(
            ["widget", "dialog", "dialogui", "codesnippet"]
        ),
    },
}

CKEDITOR_BASEPATH = "/static/ckeditor/ckeditor/"
DEBUG_TOOLBAR_CONFIG = {
    "IS_RUNNING_TESTS": False,
}

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "api.auth.BearerTokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Doccure API",
    "DESCRIPTION": "API documentation for the Doccure healthcare platform.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/1"),
    }
}
