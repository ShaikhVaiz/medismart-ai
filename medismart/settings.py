from pathlib import Path
import os
from dotenv import load_dotenv
import certifi

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-this-before-deployment")
DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")

# Allowed hosts: comma-separated list in .env (e.g. 127.0.0.1,localhost,yourdomain.com)
raw_hosts = os.environ.get("ALLOWED_HOSTS", "127.0.0.1,localhost,.vercel.app")
ALLOWED_HOSTS = [h.strip() for h in raw_hosts.split(",") if h.strip()]
if ".vercel.app" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(".vercel.app")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "tracker",
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

ROOT_URLCONF = "medismart.urls"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

WSGI_APPLICATION = "medismart.wsgi.application"
ASGI_APPLICATION = "medismart.asgi.application"

# -------------------------------------------------------------
# DATABASE CONFIGURATION (Supports TiDB Cloud or local SQLite)
# Set USE_TIDB=True in .env to switch to TiDB Cloud.
# -------------------------------------------------------------
USE_TIDB = os.environ.get("USE_TIDB", "False").lower() in ("true", "1", "yes")

if USE_TIDB:
    import socket
    # TiDB Cloud DNS resolver fallback (bypasses local router DNS timeouts)
    _orig_getaddrinfo = socket.getaddrinfo
    def _tidb_getaddrinfo(host, port, *args, **kwargs):
        if host == "gateway01.ap-southeast-1.prod.aws.tidbcloud.com":
            try:
                return _orig_getaddrinfo(host, port, *args, **kwargs)
            except Exception:
                return _orig_getaddrinfo("75.2.106.174", port, *args, **kwargs)
        return _orig_getaddrinfo(host, port, *args, **kwargs)
    socket.getaddrinfo = _tidb_getaddrinfo

    import pymysql
    pymysql.install_as_MySQLdb()

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.environ.get("TIDB_DB_NAME", "test"),
            "USER": os.environ.get("TIDB_USER", "root"),
            "PASSWORD": os.environ.get("TIDB_PASSWORD", ""),
            "HOST": os.environ.get("TIDB_HOST", ""),
            "PORT": int(os.environ.get("TIDB_PORT", "4000")),
            "OPTIONS": {
                "ssl": {
                    "ca": certifi.where(),
                },
                "charset": "utf8mb4",
                "autocommit": True,
                "connect_timeout": 60,
                "read_timeout": 120,
                "write_timeout": 120,
            },
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# -------------------------------------------------------------
# RESEND EMAIL SERVICE CONFIGURATION
# -------------------------------------------------------------
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "onboarding@resend.dev")

# -------------------------------------------------------------
# GOOGLE GEMINI AI CONFIGURATION (Prescription Vision Scanner)
# -------------------------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Password validators: relaxed for local development so simple test passwords work smoothly
AUTH_PASSWORD_VALIDATORS = [] if DEBUG else [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-in"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "home"
