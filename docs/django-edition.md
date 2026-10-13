# Django template edition

This branch is a separate edition of Mawj. `main` retains the Next.js edition. The unused `myproject/` scaffold and old project-generation PowerShell script were removed from this branch to avoid starting a different project. This edition requires Python and the root requirements only; no Node.js, npm, React or Next server is needed at runtime.

## Architecture

`/` serves the matching landing page. `/login/`, `/signup/`, `/about/` and `/privacy/` use ordinary Django templates. `/app/today/`, `/app/tasks/`, `/app/journal/`, `/app/achievements/`, `/app/calendar/` and `/app/profile/` are server-rendered workspace pages.

`web/views.py` calls the existing authenticated Django read endpoints directly with the same request to reuse their owner-filtered queries, pagination and report calculations. It passes the resulting data to inherited templates; there is no HTTP request back to our own server. HTML contains the initial records before JavaScript runs. `static/web/app.js` uses ordinary fetch and DOM APIs for mutations, dialogs, forms, AI and appearance controls. The existing `/api/` views still validate all mutations through Django forms, sessions and CSRF.

The original Django routes/templates remain available as legacy educational examples. The new interface starts at the root and `/app/` routes. The two editions share the same models/migrations and AI provider logic. No schema migration is added by this edition.

## Preserved behavior

Five palettes; local Saudi/Noto/DM Sans/Fraunces fonts and SVG icons; English/Arabic; profile edits and private PNG/JPEG avatar upload/removal; task CRUD/filtering/pagination; past schedule validation; daily/weekly recurrence and reminders; journal CRUD, provider mode, analysis, accept/dismiss; week/month/year reports and charts/data table; calendar day details with undated tasks and full journal text; modal destructive confirmations; Ymam attribution/GitHub link.

Page navigation now renders Django templates rather than React components. Dates in compact record summaries may use numeric formatting. Forms retain text drafts across a language change; passwords and file input bytes are not stored in draft storage. File selections need reselecting after a full-page navigation. Live AI still requires local provider configuration and was not validated with real credentials.

## Setup

From the project root on Windows:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

Open `http://127.0.0.1:8000`. On later starts only the last command is needed. Keep the terminal open. Use the same project folder/database to preserve your account. For existing real data, stop the other edition and copy its `db.sqlite3` and `media/` into this local edition; keep a backup. Never add personal data to Git.

Linux/macOS: `python3 -m venv .venv`, `.venv/bin/python -m pip install -r requirements.txt`, `.venv/bin/python manage.py migrate`, `.venv/bin/python manage.py runserver`.

For phone access, use `python scripts/dev.py --lan` with the virtual environment's Python. The helper prints local network URLs and configures allowed hosts for the same run; no Node setup is needed. Phone and computer must share a reachable Wi-Fi network, and Windows must permit the Python process on the private network.

## Useful files

- `templates/web/base.html`: shared HTML, local fonts/styles, safe boot JSON, CSRF and plain JS.
- `templates/web/workspace.html`: navigation/header/footer and page includes.
- `templates/web/tasks.html`, `journal.html`, `report.html`, `calendar.html`, `profile.html`: server-rendered feature pages.
- `templates/web/task-form.html`, `journal-form.html`, `dialogs.html`: interactive forms and native dialogs.
- `web/templatetags/mawj.py`: translation, trusted local SVG icons and date formatting.
- `web/translations.json`: existing reviewed formal Arabic messages.
- `static/web/`: portable CSS, JS, fonts and favicon. Upstream font/SVG license files are retained.
- `web/tests.py`: ownership, escaped server rendering, RTL/local assets and safe full calendar JSON checks.

Public marketing HTML/SVGs were exported once from the previous edition during development, then committed as standalone HTML templates. React is not loaded by this edition. Changes to those templates are now edited directly in HTML. Significant Codex assistance was used for this conversion; review and understand the implementation before submission.
