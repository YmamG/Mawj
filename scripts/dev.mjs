import { spawn } from 'node:child_process';
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
const environment = { ...process.env, DJANGO_URL: process.env.DJANGO_URL || 'http://127.0.0.1:8000' };
const children = [
  spawn(python, ['manage.py', 'runserver', '127.0.0.1:8000', '--noreload'], { cwd: root, env: environment, stdio: 'inherit' }),
  spawn(process.execPath, [next, 'dev', '--hostname', '127.0.0.1', '--port', '3000'], { cwd: join(root, 'frontend'), env: environment, stdio: 'inherit' }),
];
let stopping = false;
function stop(code = 0) {
  if (stopping) return;
  stopping = true;
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
