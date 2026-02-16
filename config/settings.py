"""
CEYLAN GARAJ - Django settings (FINAL)
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------------------------------
# ENV LOADER (Windows/local için .env okur)
# Sunucuda systemd EnvironmentFile zaten env basar.
# -------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except Exception:
    pass


def env(key: str, default=None):
    return os.environ.get(key, default)


# -------------------------------------------------
# SECURITY
# -------------------------------------------------
SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-unsafe-secret")
DEBUG = str(env("DJANGO_DEBUG", "1")).lower() in ("1", "true", "yes", "on")

allowed_hosts_raw = env("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost")
ALLOWED_HOSTS = [h.strip() for h in allowed_hosts_raw.split(",") if h.strip()]

# Proxy arkasında (nginx) kullanacaksan
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# -------------------------------------------------
# APPLICATIONS
# -------------------------------------------------
INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Local
    "accounts",
    "apps.core",
    "apps.customers",
    "apps.workorders",
    "apps.tirehotel",
    "apps.notifications",
    "apps.inventory.apps.InventoryConfig",
    "apps.reports",
    "apps.marketing.apps.MarketingConfig",
]

# ✅ Custom User kullanıyorsan (sende var gibi duruyor)
AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",

    # ✅ usta/admin kitleme
    "apps.core.middleware.WorkerLockdownMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"


# -------------------------------------------------
# TEMPLATES
# -------------------------------------------------
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
                "apps.core.context_processors.active_branch",
               
            ],
        },
    },
]


# -------------------------------------------------
# DATABASE (PostgreSQL / SQLite fallback)
# -------------------------------------------------
DB_ENGINE = env("DB_ENGINE", "django.db.backends.sqlite3")

if "postgres" in (DB_ENGINE or ""):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME", "ceylan_garaj_db"),
            "USER": env("DB_USER", "postgres"),
            "PASSWORD": env("DB_PASSWORD", ""),
            "HOST": env("DB_HOST", "127.0.0.1"),
            "PORT": env("DB_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": env("DB_NAME", str(BASE_DIR / "db.sqlite3")),
        }
    }


# -------------------------------------------------
# AUTH / LOGIN
# -------------------------------------------------
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"


# -------------------------------------------------
# PASSWORD VALIDATORS
# -------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# -------------------------------------------------
# LANGUAGE / TIME
# -------------------------------------------------
LANGUAGE_CODE = env("LANGUAGE_CODE", "tr")
TIME_ZONE = env("TZ", "Europe/Istanbul")
USE_I18N = True
USE_TZ = True


# -------------------------------------------------
# STATIC / MEDIA
# -------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# -------------------------------------------------
# DEFAULT PK
# -------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# -------------------------------------------------
# NOTIFICATIONS (opsiyonel)
# -------------------------------------------------
NOTIFY_WHATSAPP_PROVIDER = env("NOTIFY_WHATSAPP_PROVIDER", "meta_cloud")
NOTIFY_SMS_PROVIDER = env("NOTIFY_SMS_PROVIDER", "generic")

WHATSAPP_TOKEN = env("WHATSAPP_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = env("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_API_VERSION = env("WHATSAPP_API_VERSION", "v19.0")

SMS_API_KEY = env("SMS_API_KEY", "")
SMS_SENDER = env("SMS_SENDER", "")

# -------------------------------------------------
# ROLE SETTINGS
# -------------------------------------------------
# Admin: her şeyi görür
ROLE_ADMIN_GROUP = env("ROLE_ADMIN_GROUP", "ADMIN")
# Usta: sadece kendi ekranı (fiyat göremez)
ROLE_WORKER_GROUP = env("ROLE_WORKER_GROUP", "USTA")
# Usta ekranı / admin ekranı ayrımı
WORKER_HOME_URL = env("WORKER_HOME_URL", "/workorders/my/")
ADMIN_HOME_URL = env("ADMIN_HOME_URL", "/workorders/")
INSTAGRAM_URL = "https://www.instagram.com/ceylan_garaj/"