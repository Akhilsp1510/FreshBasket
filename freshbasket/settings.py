"""
FreshBasket Django Settings
Local development, Render PostgreSQL, AWS MySQL and S3 support
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent


# =========================================================
# SECURITY SETTINGS
# =========================================================

SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'django-insecure-freshbasket-dev-key-change-in-production-123456'
)

DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    if h.strip()
]

# Automatically allow Render's assigned hostname
RENDER_EXTERNAL_HOSTNAME = os.getenv('RENDER_EXTERNAL_HOSTNAME')

if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

if 'testserver' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('testserver')


CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        'CSRF_TRUSTED_ORIGINS',
        'http://localhost:8000,http://127.0.0.1:8000'
    ).split(',')
    if o.strip()
]

# Automatically trust Render's HTTPS URL
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(
        f'https://{RENDER_EXTERNAL_HOSTNAME}'
    )


# =========================================================
# APPLICATIONS
# =========================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # FreshBasket applications
    'accounts.apps.AccountsConfig',
    'products.apps.ProductsConfig',
    'inventory.apps.InventoryConfig',
    'orders.apps.OrdersConfig',
    'dashboard.apps.DashboardConfig',
]


# Optional Crispy Forms
try:
    import crispy_forms
    import crispy_bootstrap5

    INSTALLED_APPS += [
        'crispy_forms',
        'crispy_bootstrap5',
    ]

    CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
    CRISPY_TEMPLATE_PACK = 'bootstrap5'

except ImportError:
    pass


# =========================================================
# MIDDLEWARE
# =========================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
]

# WhiteNoise for serving static files
try:
    import whitenoise

    MIDDLEWARE.append(
        'whitenoise.middleware.WhiteNoiseMiddleware'
    )

except ImportError:
    pass


MIDDLEWARE += [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# =========================================================
# URL AND WSGI CONFIGURATION
# =========================================================

ROOT_URLCONF = 'freshbasket.urls'

WSGI_APPLICATION = 'freshbasket.wsgi.application'


# =========================================================
# TEMPLATES
# =========================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'orders.context_processors.cart_count',
            ],
        },
    },
]


# =========================================================
# DATABASE CONFIGURATION
# =========================================================

DB_ENGINE = os.getenv('DB_ENGINE', 'sqlite').lower()
DATABASE_URL = os.getenv('DATABASE_URL')


if DATABASE_URL:

    # Render PostgreSQL
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=True
        )
    }

elif DB_ENGINE == 'mysql' or os.getenv(
    'USE_RDS', 'False'
).lower() in ('true', '1'):

    # MySQL - local development or AWS RDS
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('DB_NAME', 'freshbasket_db'),
            'USER': os.getenv('DB_USER', 'root'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': (
                    "SET sql_mode='STRICT_TRANS_TABLES'"
                ),
            },
        }
    }

else:

    # SQLite - local development fallback
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# =========================================================
# PASSWORD VALIDATION
# =========================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'UserAttributeSimilarityValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'MinimumLengthValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'CommonPasswordValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'NumericPasswordValidator'
        ),
    },
]


# =========================================================
# INTERNATIONALIZATION
# =========================================================

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_TZ = True


# =========================================================
# CUSTOM USER MODEL
# =========================================================

AUTH_USER_MODEL = 'accounts.User'


# =========================================================
# AUTHENTICATION URLS
# =========================================================

LOGIN_URL = '/accounts/login/'

LOGIN_REDIRECT_URL = '/'

LOGOUT_REDIRECT_URL = '/'


# =========================================================
# STATIC FILE CONFIGURATION
# =========================================================

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static'
]

STATIC_ROOT = BASE_DIR / 'staticfiles'


# =========================================================
# MEDIA FILE CONFIGURATION
# =========================================================

USE_S3 = os.getenv('USE_S3', 'False').lower() in ('true', '1')


if USE_S3:

    # Amazon S3 media storage
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID') or None

    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY') or None

    AWS_STORAGE_BUCKET_NAME = os.getenv(
        'AWS_STORAGE_BUCKET_NAME'
    )

    AWS_S3_REGION_NAME = os.getenv(
        'AWS_S3_REGION_NAME',
        'ap-south-1'
    )

    AWS_DEFAULT_ACL = None

    AWS_S3_FILE_OVERWRITE = False

    AWS_S3_CUSTOM_DOMAIN = (
        os.getenv('AWS_CLOUDFRONT_DOMAIN')
        or f'{AWS_STORAGE_BUCKET_NAME}.s3.'
        f'{AWS_S3_REGION_NAME}.amazonaws.com'
    )

    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400'
    }

    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

else:

    # Local media storage
    MEDIA_URL = '/media/'

    MEDIA_ROOT = BASE_DIR / 'media'


# =========================================================
# STORAGE CONFIGURATION
# =========================================================

STORAGES = {
    'default': {
        'BACKEND': (
            'storages.backends.s3boto3.S3Boto3Storage'
            if USE_S3
            else 'django.core.files.storage.FileSystemStorage'
        ),
    },

    'staticfiles': {
        'BACKEND': (
            'whitenoise.storage.CompressedManifestStaticFilesStorage'
            if 'whitenoise' in sys.modules
            else 'django.contrib.staticfiles.storage.StaticFilesStorage'
        ),
    },
}


# =========================================================
# DEFAULT PRIMARY KEY
# =========================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# =========================================================
# SESSION CONFIGURATION
# =========================================================

SESSION_COOKIE_AGE = 86400  # 24 hours

SESSION_SAVE_EVERY_REQUEST = True


# =========================================================
# PRODUCTION SECURITY
# =========================================================

if not DEBUG:

    SECURE_SSL_REDIRECT = os.getenv(
        'SECURE_SSL_REDIRECT', 'True'
    ).lower() in ('true', '1')

    SECURE_PROXY_SSL_HEADER = (
        'HTTP_X_FORWARDED_PROTO',
        'https'
    )

    SECURE_HSTS_SECONDS = int(
        os.getenv('SECURE_HSTS_SECONDS', '31536000')
    )

    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

    SECURE_HSTS_PRELOAD = True

    SESSION_COOKIE_SECURE = True

    CSRF_COOKIE_SECURE = True


# =========================================================
# INVENTORY RESERVATION SETTINGS
# =========================================================

RESERVATION_EXPIRY_MINUTES = 10


# =========================================================
# LOGGING
# =========================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'verbose': {
            'format': (
                '{levelname} {asctime} {module} '
                '{process:d} {thread:d} {message}'
            ),
            'style': '{',
        },
    },

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },

    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },

    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },

        'inventory': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}