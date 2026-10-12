# Next.js interface and Django API

The new frontend lives in `frontend/`. It adds a public landing page and a full workspace while retaining Django models, forms, authentication and existing HTML routes. Data is real Django data; only landing-page preview examples are illustrative.

## Local setup (Windows PowerShell)

Install Python 3.12+ and Node.js 22+ (validated with Python 3.12.14, Node 24.19.0, Next.js 16.4.0 / React 19). From the repository root:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
npm ci --prefix frontend
node scripts/dev.mjs
```

Open `http://127.0.0.1:3000` and keep the terminal open. The launcher starts Django on 8000 and Next.js on 3000; stop earlier servers occupying those ports first. Ctrl+C stops both. On subsequent starts just run `node scripts/dev.mjs`.

On Linux/macOS replace the first three Python commands with:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python manage.py migrate
```

For optional fictional sample data, run the existing `manage.py seed_demo` with the venv Python before starting. It prompts for an invented password. No personal information or secrets are committed.

## Updating

Stop both services, preserve local changes, then:

```powershell
git pull
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
npm ci --prefix frontend
node scripts/dev.mjs
```

If using ZIP, retain your previous `db.sqlite3` and `media/` before following the README upgrade instructions. Never overwrite these blindly. The legacy Django interface remains available on port 8000.

## Architecture and security

- Next.js routes: `/`, `/login`, `/signup`, `/app/today`, `/app/tasks`, `/app/journal`, `/app/achievements`, `/app/calendar`, `/app/profile`, `/privacy`, `/about`.
- Django API: `/api/session/`, `/api/auth/*/`, `/api/tasks/`, `/api/tasks/<id>/`, `/api/tasks/suggest/`, `/api/today/`, `/api/journal/`, `/api/journal/<id>/`, `/api/suggestions/<id>/`, `/api/achievements/`, `/api/calendar/`, `/api/profile/`, `/api/profile/avatar/`, `/api/theme/`.
- Next proxies `/api/…` to Django on the server. API URLs retain the trailing slash; the rewrite adds it to avoid the Next/Django normalization redirect loop.
- Django session cookies and CSRF remain active. Every mutation is POST with a CSRF token from `/api/session/`. Sign-in/sign-up rotate the token. Records are filtered by the authenticated owner; images use authenticated private delivery. No tokens or AI credentials enter browser bundles.
- Existing forms validate API submissions. Existing task completion behavior generates repeating occurrences. Reports share `dashboard/reports.py` between the API and legacy pages. API suggestion acceptance claims the pending row transactionally before creating a task, protecting repeat submissions.
- Search, filtering and pagination are server-side. Success, loading, empty and failure states are visible; deletion requires an inline confirmation.

## Themes

The supplied palettes become **Grove** (`dad7cd/a3b18a/588157/3a5a40/344e41`), **Petal** (`cdb4db/ffc8dd/ffafcc/bde0fe/a2d2ff`) and **Dusk** (`22223b/4a4e69/9a8c98/c9ada7/f2e9e4`). The green link was duplicated; it represents one theme. Neutral surfaces and dark readable text complement the exact palette tokens. Browser theme selection uses localStorage; authenticated theme selection is saved in preferences. Existing theme values map to the new themes in the API without deleting old preferences.

DM Sans and Fraunces are served from npm-installed local font files. Phosphor supplies consistent icons. No external font calls, image services or tracking scripts are required.

## Configuration

`DJANGO_URL` configures the Next server’s backend destination; default `http://127.0.0.1:8000`. For production, set it when building as rewrites are saved in the build. `NEXT_PUBLIC_SITE_URL` configures canonical metadata base. These URLs are non-secret.

Django defaults allow localhost and trust the two local Next origins on port 3000. For other origins/hosts, set comma-separated `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` explicitly. Production requires DEBUG off, HTTPS/secure cookies, a private secret key, deployment file storage and appropriate host/origin values; this work does not publish a production site.

AI provider configuration remains on Django. Demo is simulated. Cloud mode displays the configured provider before sending journal text or task notes. Reminders remain in-app on visits; recurrence advances on completion. No external notifications or live-provider validation is implied.

## Checks

```bash
.venv/bin/python manage.py test --noinput
.venv/bin/python manage.py makemigrations --check --dry-run
npm run typecheck --prefix frontend
npm run build --prefix frontend
```

After building, use `npm run start --prefix frontend` alongside Django to validate production startup. See `docs/verification.md` for executed results. Manual real-device acceptance remains a separate student submission step.

## Account persistence and old bookmarks

The launcher now prints the exact project/database path and saved account count, and pins its local Next proxy to that same Django checkout. On Windows it opens the new interface automatically after both landing and API readiness succeed (`--no-browser` disables this). With the launcher active, old port-8000 home/login/signup links redirect to the corresponding new frontend pages; other original pages display a link to the new site. Django-only startup retains its original routes.

Accounts persist in `db.sqlite3`; stopping the server or logging out does not delete them. A fresh project download is a different database unless existing data is preserved. Always restart with `node scripts/dev.mjs` from the same checkout. If login fails, verify the same startup database path and account count before/after restart, and use your username rather than display name or email. API login trims accidental spaces around the username, while preserving password characters exactly. Never delete or replace a database to troubleshoot login. To diagnose a user-specific issue, share only the startup path/count and error text, never passwords or database contents.

The launcher deliberately uses its local backend; custom `DJANGO_URL` values are for separately managed Next startup/production builds, not the local two-service launcher.
