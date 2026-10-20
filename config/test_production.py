"""Production configuration checks run in isolated processes without real secrets."""
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parent.parent


class ProductionSettingsTests(SimpleTestCase):
    def run_isolated(self, code, **overrides):
        environment = os.environ.copy()
        environment.update(
            DJANGO_SETTINGS_MODULE="config.settings_production",
            DJANGO_SECRET_KEY=secrets.token_urlsafe(64),
            DJANGO_ALLOWED_HOSTS="mawj.example.test",
            DJANGO_CSRF_TRUSTED_ORIGINS="",
            AI_PROVIDER="demo",
        )
        environment.update(overrides)
        return subprocess.run(
            [sys.executable, "-c", code], cwd=ROOT, env=environment,
            capture_output=True, text=True, timeout=30,
        )

    def test_missing_or_weak_key_prevents_production_startup(self):
        for value in ("", "short", "a" * 64, "django-insecure-" + "abc123" * 12):
            with self.subTest(weak_key_type=len(value)):
                result = self.run_isolated("import config.settings_production", DJANGO_SECRET_KEY=value)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Production requires a new random DJANGO_SECRET_KEY", result.stderr)

    def test_hosts_must_be_explicit(self):
        for value in ("", "*", ".example.test", "https://example.test", "example.test:8000"):
            with self.subTest(host=value):
                result = self.run_isolated("import config.settings_production", DJANGO_ALLOWED_HOSTS=value)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Set DJANGO_ALLOWED_HOSTS", result.stderr)

    def test_production_csrf_origins_require_https_and_exact_origins(self):
        for value in ("http://mawj.example.test", "https://*.example.test", "https://mawj.example.test/path", "https://bad host", "https://host:wrong"):
            with self.subTest(origin=value):
                result = self.run_isolated("import config.settings_production", DJANGO_CSRF_TRUSTED_ORIGINS=value)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("must contain HTTPS origins", result.stderr)

    def test_local_defaults_remain_local(self):
        result = self.run_isolated(
            "import json; from config import settings; print(json.dumps({'debug':settings.DEBUG, 'secure':getattr(settings, 'SESSION_COOKIE_SECURE', False)}))",
            DJANGO_SECRET_KEY="", DJANGO_ALLOWED_HOSTS="",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"debug": True, "secure": False})

    def test_production_requests_https_host_checks_and_csrf(self):
        code = '''
import json
from config.wsgi_production import application
from django.conf import settings
assert settings.DEBUG is False
assert settings.ADMIN_ENABLED is False
assert settings.MAILERS['default']['BACKEND'] == 'django.core.mail.backends.smtp.EmailBackend'
from django.test import Client
client = Client(enforce_csrf_checks=True, HTTP_HOST='mawj.example.test')
plain = client.get('/', HTTP_X_FORWARDED_PROTO='https')
assert plain.status_code == 301
assert plain['Location'] == 'https://mawj.example.test/'
assert client.get('/', secure=True).status_code == 200
directory = client.get('/operator/accounts/', secure=True)
assert directory.status_code == 302
assert directory['Location'] == '/login/?next=/operator/accounts/'
from django.urls import resolve
for path in ('/admin/', '/admin/login/', '/admin/auth/user/', '/admin/tasks/task/', '/admin/journal/journalentry/'):
    assert resolve(path).namespace != 'admin'
    assert client.get(path, secure=True).status_code == 404
assert client.get('/', secure=True, HTTP_HOST='other.example.test').status_code == 400
response = client.get('/api/session/', secure=True)
assert response.status_code == 200
assert response.cookies['csrftoken']['secure']
assert response.cookies['csrftoken']['httponly']
assert client.post('/api/auth/signup/', data='{}', content_type='application/json', secure=True).status_code == 403
valid = client.post('/api/auth/signup/', data='{}', content_type='application/json', secure=True, HTTP_X_CSRFTOKEN=response.json()['csrf'], HTTP_ORIGIN='https://mawj.example.test')
assert valid.status_code == 400
assert 'fields' in valid.json()
print('HTTPS, exact hosts, protected cookie and valid/invalid CSRF flow passed.')
'''
        result = self.run_isolated(code)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("valid/invalid CSRF flow passed", result.stdout)
