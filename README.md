# mawj

**mawj (موج)** is a personal planning web application for students balancing study and daily responsibilities. It brings journals, reviewed task suggestions and progress reports into one workflow.

## Problem, audience and value

Students can record intentions in daily notes without turning them into practical steps. mawj helps them review those intentions, choose tasks and see how much planned work remains. Its value over a plain note or separate checklist is the connected journey: **write → review suggestions → accept → complete → reflect**.

The initial adoption model is a free student pilot. Audience demand and benefits are hypotheses, not validated market research; no commercial launch or paying customers are claimed. The core workflow can be demonstrated without an external AI service.

## Features

- Django accounts, saved sessions and owner-only access to tasks, journals and profile photos.
- Production disables Django administration, including user password changes and private-record browsing. App ownership checks also apply to staff/superusers. Server/database operators retain direct access; this is not end-to-end encryption.
- Task creation, editing, completion/reopening and confirmed deletion; search, status/category/priority filters and pagination.
- Title-only quick entry with optional scheduling, duration, priority, category, daily/weekly recurrence and in-app reminders.
- Journal creation, search, editing and deletion; suggestion analysis, explicit acceptance and dismissal.
- Calendar days showing tasks and complete journal text, including undated tasks on their creation day.
- Weekly, monthly and yearly reports with completion percentage, charts and a data table.
- Editable profile, private PNG/JPEG avatar upload/removal, five themes and English/Arabic switching.
- Locally served fonts, including Saudi for Arabic headings and the Arabic wordmark; responsive layouts and modal confirmations.

## Technology and architecture

This version uses **Python, Django, SQLite, Django templates, CSS and plain JavaScript**, with one development server. Node.js and npm are not required.

Django renders the initial HTML and enforces authentication, ownership, validation and data persistence. JavaScript adds interactive forms, appearance controls and dialogs, and calls Django's session-authenticated API for changes. There is no frontend proxy or separate frontend server.

| Path | Purpose |
|---|---|
| `manage.py`, `config/` | Django commands, settings, routes and API |
| `accounts/` | Authentication, profile, preferences and private photos |
| `tasks/` | Task models, forms, recurrence and reminders |
| `journal/` | Journal entries and reviewed task suggestions |
| `dashboard/reports.py` | Calendar-period summaries and chart calculations |
| `ai/provider.py` | Local simulation/manual mode and optional external providers |
| `web/`, `templates/web/` | Server-rendered presentation, translations and shared template layout |
| `static/web/` | CSS, JavaScript, fonts and icons |
| `*/migrations/` | Reproducible database schema changes |
| `docs/` | Design, verification history, demonstration and implementation explanation |

See [architecture details](docs/django-edition.md) and the [ERD](docs/design.md).

## Requirements

- Python **3.12 or later**; validated with Python 3.12.14 and Django 6.1.2.
- Packages declared in `requirements.txt`: Django, Requests, Pillow and python-dotenv.
- Git if you want to clone and pull updates. SQLite is included with Python.

Clone this repository using its GitHub **Code** URL, or extract its ZIP. Open the actual project folder containing both `manage.py` and `requirements.txt` before running commands.

## Windows setup

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

Open **http://127.0.0.1:8000**. Keep the terminal open; Ctrl+C stops the server. On later starts only the last command is needed.

## Linux/macOS setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

## Updating an existing Git installation

Stop the server first, then run in the same project folder:

```powershell
git pull --ff-only
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

`git pull` follows your configured upstream branch; it does not require a particular repository name. If local edits prevent an update, inspect `git status` before proceeding.

Accounts and records are stored in local `db.sqlite3`; uploaded photos are in `media/`. Keep these files and `.env` when updating and back them up. A fresh ZIP/clone creates a separate database unless you transfer your existing local data after stopping the server. These personal files and virtual environments are excluded by `.gitignore`.

## Phone access on the same Wi-Fi

```powershell
.\.venv\Scripts\python.exe scripts/dev.py --lan
```

Open the printed **Phone on the same Wi-Fi** URL on the phone. Both devices must share a reachable local network. If Windows prompts, permit Python on the private network. Use the printed computer IP, not `127.0.0.1` or `0.0.0.0`, on the phone. Sign in with your existing account.

## AI modes and configuration

No custom model was trained for this project. External AI is an optional integration.

| `AI_PROVIDER` | Behavior |
|---|---|
| `manual` | Save the journal as written, without suggestions |
| `demo` (default) | Clearly labeled local rules extract bullet lines or certain intent phrases; task details return medium priority and **30 minutes fixed** |
| `gemini` | Send journal/task text to Gemini using `GEMINI_API_KEY` |
| `openai` | Send journal/task text to OpenAI using `OPENAI_API_KEY` |
| `claude` | Send journal/task text to Claude using `ANTHROPIC_API_KEY` |

Demo is a simulation, not a live AI model. To configure an external provider, create a local `.env` from `.env.example` if it does not already exist, set the selected provider and its key privately, and restart the server. Process environment variables take precedence. Optional model settings are `GEMINI_MODEL`, `OPENAI_MODEL` and `CLAUDE_MODEL`; use a model available to your provider account. Do not commit credentials or put real keys in the example file.

Suggestions remain separate from tasks until a user accepts them. AI output is parsed and validated; past suggested schedules are removed. If external AI fails during journal creation, the original note is saved with a warning. The interface identifies the provider before cloud processing. Live external calls have not been verified; simulated and mocked checks do not prove provider reliability.

## Fictional demonstration data

```powershell
.\.venv\Scripts\python.exe manage.py seed_demo
```

This prompts privately for a password and creates the fictional `mawj_demo` account, 13 tasks, two journals and three suggestions. Initially 12 tasks are in the current period and six are complete: **50%**. One historical task is outside that period. Repeating the command preserves an existing account and its data.

`seed_demo` creates sample records; it is different from `AI_PROVIDER=demo`. No sample password is stored in source. Use fictional records for presentations.

## Business rules and current limitations

- Required fields and business values are validated on the server. Task duration is 1–1440 minutes; new/changed schedules cannot be in the past. Existing unchanged overdue schedules remain editable.
- Completion percentage is completed / total tasks scheduled within the selected calendar period, rounded to an integer. Undated tasks use their creation date in Riyadh time. Weeks start Sunday; whole months/years include future scheduled tasks. This is not completion-event history.
- Recurrence advances when a task is completed; reminders appear on site visits, without email or push delivery.
- Editing a journal saves revised text as written and dismisses old pending suggestions. Reanalysis is explicit. Deleting a journal removes its suggestions, while already accepted tasks remain.
- Original Django HTML routes remain as legacy examples; the current interface starts at `/` and `/app/`. Known legacy-route limitations are recorded in the verification/design documentation.
- Local development uses `config.settings`. Optional production configuration uses `config.settings_production` and `config.wsgi_production`. Follow the [PythonAnywhere deployment guide](docs/pythonanywhere.md) to create private host settings, collect static assets and verify HTTPS. No public deployment has been performed.

## Verification and submission

```powershell
.\.venv\Scripts\python.exe manage.py test --noinput
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

The [verification record](docs/verification.md) distinguishes full-suite runs, targeted checks, browser checks and untested behavior. A full 95-test run passed after the template conversion; later navigation fixes passed six targeted template checks. Browser review covered desktop/mobile widths and core workflows, including calendar, themes, suggestions, recurrence, reminders and avatar upload/removal. These records do not replace the required manual acceptance test on the student's devices.

Use [the demonstration guide](docs/demo.md) and [submission review](docs/submission-ar.md) to prepare the individual discussion. Confirm instructor repository access, approved scope and the exact submitted revision. Explain relationships, validation, aggregation and per-entry annotation, and distinguish market assumptions from evidence. Historical Next.js sections describe an earlier implementation; this version's setup is the one above.

## Sources and assistance

Django, Requests, Pillow and python-dotenv support the backend. Phosphor SVG icons and DM Sans, Fraunces and Noto Sans Arabic fonts are served locally with upstream license files. The project owner supplied Saudi Web.

Significant OpenAI Codex assistance was used for implementation, conversion, tests and documentation. Public HTML was exported once from the earlier design during development and is now maintained as Django templates; React is not loaded at runtime. Review and understand these contributions before the capstone technical discussion.
