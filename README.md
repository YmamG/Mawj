# Mawj — Django template edition

Mawj helps students turn daily notes into reviewed tasks and track planned-work completion. The student audience and market demand remain hypotheses; a free student pilot is the proposed initial adoption model.

This is the **`django-templates` branch**, a separate edition of the same project. `main` retains Next.js. This edition uses Django templates, CSS and plain JavaScript, with **one server and no Node.js/npm/React runtime**. The design, five palettes, Arabic/English, Saudi headings, account/profile/photo features, task and journal workflows, calendar, recurrence/reminders, reports and AI provider integration are retained.

## Windows setup

Use Python 3.12+ (validated with 3.12.14 and Django 6.1.2). In this edition's project folder:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

Open `http://127.0.0.1:8000`. Later, only the last command is needed. Stop with Ctrl+C. Start from the root `manage.py`. For phone access on the same Wi-Fi use:

```powershell
.\.venv\Scripts\python.exe scripts/dev.py --lan
```

The helper prints the phone URL and allows its host. Permit Python on Windows private networks if prompted. Existing accounts are kept in local `db.sqlite3`: retain the same project folder/data when updating. For a separate download, keep a backup, stop servers and copy your original database and `media/` locally if you want the same records. Never commit real data.

Linux/macOS: create `.venv` with `python3 -m venv .venv`; use `.venv/bin/python` for the corresponding commands.

## AI and fictional data

`AI_PROVIDER=demo` is a clearly labeled local **simulation**. Journal bullet lines and certain intent phrases become suggestions; task priority/duration suggestions are fixed at medium/30 minutes. `manual` saves without AI. Optional `gemini`, `openai` or `claude` requires that provider's local credentials. Copy `.env.example` to `.env` and configure the provider privately; restart the server. Environment variables take precedence. No real key enters browser code, the example or Git. Live AI has not been verified with credentials.

A suggested task becomes a real task only after the user accepts it. Cloud failure during journal creation preserves the original note with a warning. Reports calculate completed / total tasks scheduled within the calendar period (undated tasks use local creation date), not completion-event history. Weeks start Sunday in Riyadh time. Recurrence advances on completion and reminders are shown during site visits.

`python manage.py seed_demo` is different from AI Demo: it creates fictional sample records once, with a privately prompted password. The initial report is 6/12 = 50%; a historical task sits outside the current period. Existing accounts/data are not overwritten.

## Architecture and submission

See [the Django edition guide](docs/django-edition.md) for routes, file roles and design decisions. `web/views.py` renders inherited HTML templates from existing owner-filtered Django query/report logic. `static/web/app.js` handles ordinary DOM interactions and authenticated API mutations, which still use Django forms and CSRF. Original Django pages remain as legacy examples.

[Design and ERD](docs/design.md), [verification history](docs/verification.md) and [submission review](docs/submission-ar.md) cover the earlier shared project; Next.js sections in historical records describe `main`. This branch's current setup and architecture are in this README and `docs/django-edition.md`. Manual acceptance and instructor access must still be completed before submission; deploying publicly is separate.

```powershell
.\.venv\Scripts\python.exe manage.py test --noinput
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

The source includes migrations and requirements. For production, DEBUG, private secret, HTTPS/secure cookies, allowed hosts and file backups need separate configuration.

## Sources and assistance

Django, Requests, Pillow and python-dotenv support the backend. Phosphor SVG icons and DM Sans, Fraunces, Noto Sans Arabic fonts are served locally with upstream license files; the owner supplied Saudi Web. Significant OpenAI Codex assistance was used for implementation, conversion, tests and documentation. Public HTML was exported once from the previous design during development; no React library is loaded at runtime. Review and understand this work for the individual capstone discussion.
