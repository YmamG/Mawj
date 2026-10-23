"""Production-only settings. Select explicitly; local development uses settings.py."""
import os
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured

from .settings import *  # noqa: F403 - inherit the shared application configuration

DEBUG = False
# Public instances have no administrator UI for browsing private records or
# changing another user's credentials. This does not restrict the host operator.
ADMIN_ENABLED = False

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if (
    len(SECRET_KEY) < 50
    or len(set(SECRET_KEY)) < 5
    or SECRET_KEY.startswith("django-insecure-")
):
    raise ImproperlyConfigured(
        "Production requires a new random DJANGO_SECRET_KEY of at least 50 characters."
    )
_journal_key = os.environ.get("MAWJ_JOURNAL_KEY", "")
if _journal_key and (len(_journal_key) < 32 or len(set(_journal_key)) < 5):
    raise ImproperlyConfigured(
        "MAWJ_JOURNAL_KEY must be a random value of at least 32 characters."
    )
JOURNAL_ENCRYPTION_KEY = _journal_key or SECRET_KEY

ALLOWED_HOSTS = [
    host.strip().lower()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")
    if host.strip()
]
if not ALLOWED_HOSTS or any(
    host.startswith(".")
    or any(character in host for character in "*/\\?#@ \t\r\n")
    or (":" in host and not (host.startswith("[") and host.endswith("]")))
    for host in ALLOWED_HOSTS
):
    raise ImproperlyConfigured(
        "Set DJANGO_ALLOWED_HOSTS to explicit hostnames, without schemes, ports or wildcards."
    )

_origins = os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").strip()
CSRF_TRUSTED_ORIGINS = (
    [origin.strip() for origin in _origins.split(",") if origin.strip()]
    if _origins
    else [f"https://{host}" for host in ALLOWED_HOSTS]
)
for origin in CSRF_TRUSTED_ORIGINS:
    try:
        parsed = urlsplit(origin)
        valid = (
            parsed.scheme == "https"
            and parsed.hostname
            and "*" not in parsed.netloc
            and not any(character.isspace() for character in origin)
            and (parsed.port is None or 1 <= parsed.port <= 65535)
            and not parsed.username
            and not parsed.password
            and not parsed.path
            and not parsed.query
            and not parsed.fragment
        )
    except ValueError:
        valid = False
    if not valid:
        raise ImproperlyConfigured(
            "DJANGO_CSRF_TRUSTED_ORIGINS must contain HTTPS origins without paths or wildcards."
        )

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # noqa: F405

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_SSL_REDIRECT = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Enable a short HSTS period only after the actual deployed HTTPS site is verified.
# Subdomain coverage/preloading are separate decisions; do not pin an untested site.
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
# No forwarded-header trust is enabled without a verified hosting proxy contract.

# Django's console mail backend is development-only. This app has no email-sending
# workflow; SMTP delivery must be configured separately if email is added later.
MAILERS = {"default": {"BACKEND": "django.core.mail.backends.smtp.EmailBackend"}}
