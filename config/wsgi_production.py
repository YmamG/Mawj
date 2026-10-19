"""WSGI entry point for the deployed site, independent of local DEBUG settings."""
import os

from django.core.wsgi import get_wsgi_application

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings_production"
application = get_wsgi_application()
