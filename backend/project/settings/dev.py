"""
Dev settings
"""

import os

from project.settings.base import *  # noqa
from project.settings.base import BACKEND_DIR, INSTALLED_APPS, MIDDLEWARE

# General

DEBUG = True
ALLOWED_HOSTS = ["*"]


# Database

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "xmas_films_test",
        "USER": "djangouser",
        "PASSWORD": "your_password_here",
        "HOST": "localhost",
        "PORT": "",
    }
}


# Email

EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
EMAIL_FILE_PATH = BACKEND_DIR / "sent_emails"


# DDT

SHOW_DDT = os.environ.get("SHOW_DDT") == "True"

if SHOW_DDT:
    INSTALLED_APPS = INSTALLED_APPS + ["debug_toolbar", "django_extensions"]
    MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE
    INTERNAL_IPS = ["127.0.0.1"]


# Logging

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
        },
    },
}
