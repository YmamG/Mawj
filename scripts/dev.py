"""Start the Django-only edition locally, optionally on the same Wi-Fi."""
import argparse
import ipaddress
import os
from pathlib import Path
import socket
import subprocess
import sys

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
parser = argparse.ArgumentParser()
parser.add_argument('--lan', action='store_true', help='Allow phone access on the same local network')
parser.add_argument('--port', type=int, default=8000)
args = parser.parse_args()
import django
django.setup()
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.utils import OperationalError

addresses = set()
if args.lan:
    try:
        addresses.update(socket.gethostbyname_ex(socket.gethostname())[2])
    except OSError:
        pass
    try:
        # UDP connect selects a local route; no packet is sent to this documentation address.
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
            connection.connect(('192.0.2.1', 80))
            addresses.add(connection.getsockname()[0])
    except OSError:
        pass
    addresses = {address for address in addresses if not ipaddress.ip_address(address).is_loopback}
try:
    count = get_user_model().objects.count()
except OperationalError:
    sys.exit('Database not ready. Run this Python with manage.py migrate first.')
print(f'Project: {root}\nDatabase: {settings.DATABASES["default"]["NAME"]}\nSaved accounts: {count}', flush=True)
print(f'Computer: http://127.0.0.1:{args.port}', flush=True)
for address in sorted(addresses):
    print(f'Phone on the same Wi-Fi: http://{address}:{args.port}', flush=True)
if args.lan and not addresses:
    print('No LAN address found. Connect to Wi-Fi and restart.', flush=True)
environment = os.environ.copy()
if args.lan:
    environment['DJANGO_ALLOWED_HOSTS'] = ','.join(dict.fromkeys([*settings.ALLOWED_HOSTS, *addresses]))
bind = '0.0.0.0' if args.lan else '127.0.0.1'
try:
    code = subprocess.call([sys.executable, str(root/'manage.py'), 'runserver', f'{bind}:{args.port}', '--noreload'], cwd=root, env=environment)
except KeyboardInterrupt:
    code = 0
sys.exit(code)
