import { spawn, spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const python = join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
const next = join(root, 'frontend/node_modules/next/dist/bin/next');
if (!existsSync(python) || !existsSync(next)) {
  console.error('Setup is needed first. Follow the Next.js setup in README.md, then run this command again.');
  process.exit(1);
}
const website = 'http://127.0.0.1:3000';
const environment = { ...process.env, DJANGO_URL: 'http://127.0.0.1:8000', MAWJ_FRONTEND_URL: website };
// Both services always use this checkout; an old backend override must not split account data.
const status = spawnSync(python, ['-c', `import os, django, json
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
from django.conf import settings
from django.contrib.auth import get_user_model
print(json.dumps({"database": str(settings.DATABASES["default"]["NAME"]), "accounts": get_user_model().objects.count()}))`], { cwd: root, env: environment, encoding: 'utf8' });
if (status.status !== 0) {
  console.error('The database is not ready. Run .venv Python with manage.py migrate first.');
  console.error(status.stderr);
  process.exit(1);
}
const saved = JSON.parse(status.stdout);
console.log(`Project: ${root}\nDatabase: ${saved.database}\nSaved accounts: ${saved.accounts}`);
if (saved.accounts === 0) console.log('This copy has no accounts yet. If you used Mawj before, keep your original db.sqlite3 and use its project folder; a new download has a separate database.');
const children = [
  spawn(python, ['manage.py', 'runserver', '127.0.0.1:8000', '--noreload'], { cwd: root, env: environment, stdio: 'inherit' }),
  spawn(process.execPath, [next, 'dev', '--hostname', '127.0.0.1', '--port', '3000'], { cwd: join(root, 'frontend'), env: environment, stdio: 'inherit' }),
];
let stopping = false;
let attempts = 0;
let checking = false;
const readiness = setInterval(async () => {
  if (checking || stopping) return;
  checking = true;
  attempts += 1;
  try {
    const [landing, session] = await Promise.all([
      fetch(website, { signal: AbortSignal.timeout(2500) }),
      fetch(`${website}/api/session/`, { signal: AbortSignal.timeout(2500) }),
    ]);
    const data = session.ok ? await session.json() : null;
    if (landing.ok && data && Object.hasOwn(data, 'user')) {
      clearInterval(readiness);
      console.log(`New interface ready: ${website} (port 8000 is the original interface).`);
      if (process.platform === 'win32' && !process.argv.includes('--no-browser')) {
        const opener = spawn(python, ['-m', 'webbrowser', website], { cwd: root, stdio: 'ignore' });
        opener.on('error', () => console.log(`Open ${website} in your browser.`));
      }
    }
  } catch {
    if (attempts >= 60) {
      clearInterval(readiness);
      console.error(`Mawj is taking longer to start. Check the messages above before opening ${website}.`);
    }
  } finally { checking = false; }
}, 1000);
function stop(code = 0) {
  if (stopping) return;
  stopping = true;
  clearInterval(readiness);
  for (const child of children) child.kill('SIGTERM');
  process.exitCode = code;
}
for (const child of children) {
  child.on('error', error => { console.error(`Could not start Mawj: ${error.message}`); stop(1); });
  child.on('exit', code => { if (!stopping) stop(code ?? 1); });
}
process.on('SIGINT', () => stop());
process.on('SIGTERM', () => stop());
console.log('Mawj is starting. Open http://127.0.0.1:3000 when Next.js reports Ready. Keep this terminal open; Ctrl+C stops both services.');
