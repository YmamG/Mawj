# Mawj

Mawj helps people who write daily notes turn their intentions into a manageable task list and track progress. The initial audience is students balancing study and personal responsibilities. The core journey is journal → review suggested tasks → accept selected suggestions → complete tasks → review achievements.

## Value and scope

Unlike copying actions manually from notes, Mawj keeps journaling, reviewed task suggestions, and progress in one workflow. The audience and demand are hypotheses, not validated market research. A plausible first adoption model is a free student pilot; optional paid AI usage could follow only after user feedback and cost validation. No paying customers or demonstrated demand are claimed.

Features: Django accounts and private records; task CRUD with title-only quick entry, optional scheduling and details, search/status/priority filters and pagination; journal create/read/edit/delete with search and annotated pending-suggestion counts; explicit suggestion acceptance/dismissal; calendar; weekly/monthly/yearly achievements with a chart and data table; Today/overdue/completed sections; daily/weekly repeating tasks; Study/Personal/Work categories; optional in-app reminders; profile photos, five themes and an English/Arabic interface.

## New Next.js interface

A redesigned landing page and full Next.js workspace now sit in front of the Django app. Choose Grove, Petal, Dusk, Ember or Midnight, or switch the whole interface to Arabic; all tasks, journals, profiles, photos, reminders and reports use the same Django data. See [Next.js setup](docs/nextjs.md) for one-time setup and the single `node scripts/dev.mjs` startup command. Use port **3000** for the new interface; port 8000 retains the original Django screens.

## Original Django-only setup

Validated with Python 3.12.14, Django 6.1.2, requests 2.34.2 and Pillow 12.3.0 on Linux. SQLite is included with Python. Use the root `manage.py`; `myproject/` is a legacy scaffold and is not the active application.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
export AI_PROVIDER=demo
python manage.py migrate --noinput
python manage.py check
python manage.py seed_demo
python manage.py runserver
```

On Windows activate with `.venv\Scripts\Activate.ps1`. `seed_demo` prompts privately for a password; use a strong, invented password. The username defaults to `mawj_demo`. For noninteractive execution supply `MAWJ_DEMO_PASSWORD` securely through the process environment, not in source or a command argument. Rerunning the command preserves existing accounts and data. Do not use real personal data for demonstrations.

The demo creates 12 tasks dated today (6 completed), one previous-year task, two journal entries, and three suggestions (two pending). With these unchanged records the current week/month/year report is 50%. Existing accounts are never overwritten.

## Configuration and AI

The default `AI_PROVIDER=demo` is a **simulation**, not a live AI model: journal bullet lines and explicit English/Arabic intent phrases (such as `I need to…` or `أبغى…`) become rule-based suggestions. Journal mode is visible and Find next steps can re-analyze an entry without recreating accepted or dismissed actions. `manual` saves journal text without AI. The core app works without external credentials. Optional providers: `gemini` uses `GEMINI_API_KEY`, `openai` uses `OPENAI_API_KEY`, and `claude` uses `ANTHROPIC_API_KEY`. Optional model variables are `GEMINI_MODEL`, `OPENAI_MODEL`, and `CLAUDE_MODEL`. Configure secrets outside Git; never commit credentials. Check provider model availability before using live integrations. Title/description or journal text is sent to the selected external provider; the interface displays a notice. Live provider availability is not validated by mocked tests.

To retain local AI settings after restarting the server, copy `.env.example` to `.env` in the project root and edit the provider and its key locally. Django reads this ignored file on startup; existing process environment variables take precedence. Never put a real key in `.env.example` or Git. Restart the launcher after changing configuration.

`DJANGO_SECRET_KEY` overrides the development key. The default configuration uses DEBUG and is for local development; public deployment requires separate secure configuration (hosts, HTTPS, secret key, DEBUG off). Deployment is not part of this submission setup.

## Update an existing installation

Stop the server with Ctrl+C, save any local code changes, then run from the project root:

```powershell
git pull
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

On Linux/macOS use `.venv/bin/python` instead. If downloaded as ZIP, extract the new version to a separate folder and follow Setup; do not overwrite or delete your existing database/photos. To retain data in the new folder, stop both servers and copy your existing `db.sqlite3` and `media/` before applying migrations. Do not commit either to Git.

## Extra features

- **Profile photo:** Profile → Edit profile. Upload a PNG/JPEG up to 2 MB and 4096×4096 pixels; it is re-encoded as PNG, stripped of source metadata and resized to fit 512×512. Remove the photo to restore the initial-based default avatar. Images are stored locally in ignored `media/` and served only to the authenticated owner. Back up both the database and media folder.
- **Achievement chart:** The existing week/month/year controls update stacked completed/remaining bars. Week/month use daily buckets; year uses monthly buckets. The expandable table exposes the same numbers accessibly. This chart uses the same scheduled-task definition as the percentage, not historical completion events.
- **Repeating tasks:** Set Daily or Weekly under optional details and provide a date. Completing it creates at most one next occurrence, preserving the schedule interval and skipping missed dates. Future occurrences are generated on completion, not by a background scheduler. Undo retains the successor; re-completion does not duplicate it. To stop a series, edit its pending occurrence and choose Does not repeat. Deleting a prior occurrence does not delete successors.
- **Today:** Menu → Today. Sections show pending tasks scheduled today or undated without deadlines, overdue pending tasks, and tasks actually completed today. Today/overdue exclude each other; future tasks remain in the full task list. Counts use Asia/Riyadh.
- **Categories:** Optional Study, Personal, Work or Uncategorized; filter by category in Tasks. Custom categories are not implemented.
- **Reminders:** Choose a future date/time under optional task details. Once due, a banner and Today reminders appear when the user opens a page; dismiss them to hide them. Completed tasks do not show reminders. Changing the reminder time enables it again; clearing it disables it. No notifications are sent when the site is closed, and no email/push delivery is implemented.

## Business rules and reports

Only the owner can view or modify their tasks, entries and suggestions. AI suggestions do not create tasks until accepted. Sequential repeat acceptance does not duplicate tasks; concurrent acceptance is a known limitation. Editing journal text saves it as written and dismisses obsolete pending suggestions without calling AI or deleting previously accepted tasks. Deleting an entry cascades to its suggestions, but accepted tasks remain independent.

Task duration, if supplied, must be 1–1440 minutes; title is required. New/changed dates and start times cannot be in the past; existing unchanged overdue schedules remain editable. Unspecified priority defaults to medium. Account passwords require at least 8 characters; no additional character rules are imposed. Completion percentage is completed / total tasks scheduled in the selected calendar period, rounded to an integer. Undated tasks use their creation date in Asia/Riyadh. Weeks start Sunday; calendar months/years include the whole period, including scheduled future tasks. An empty period displays an empty state rather than a misleading percentage. This is scheduled-work completion, not a count of completion events during that period.

## ORM evidence

| Capability | Working feature |
|---|---|
| CRUD | Task and journal views |
| Filtering/ordering | Task search/status/priority, journal search; deterministic paginated order |
| Relationship queries | `entry.suggestions.filter(status="pending")` in journal detail |
| Aggregation | Queryset `count()` summaries in achievements and profile |
| Annotation | `Count("suggestions", filter=Q(suggestions__status="pending"))` per journal entry |

The journal count helps identify notes with unreviewed actions. Achievement summaries help decide how much planned work remains. Tests cover multiple related suggestion rows, zero counts, user isolation and calendar boundaries.

## Verify and demonstrate

```bash
python manage.py test --noinput
python manage.py makemigrations --check --dry-run
```

See [the Arabic submission review and file/AI walkthrough](docs/submission-ar.md), [design](docs/design.md), [verification](docs/verification.md), [demo](docs/demo.md), and [work list](docs/work-list.md). Automated checks complement the manual acceptance record; they do not establish live AI reliability. Install from a clean directory and migrate an empty database before submission. No deployment link is supplied because the project has not been deployed.

## Sources and assistance

Built with Django and Requests; use their official documentation for authentication, forms, ORM, migrations and HTTP behavior. OpenAI Codex assistance was used for environment setup, feature implementation, tests, documentation and the Next.js redesign. The installed Leonxlnx/taste-skill `redesign-existing-projects` skill guided the visual audit; Next.js, React, Phosphor, DM Sans, Fraunces and Noto Sans Arabic support the new frontend. The project owner supplied the Saudi Web heading font. The student must review and understand these contributions and be able to explain the URL → view → ORM → template flow and design choices. Requirements were reviewed against the supplied Capstone Project Guide.
