# Mawj

Mawj helps people who write daily notes turn their intentions into a manageable task list and track progress. The initial audience is students balancing study and personal responsibilities. The core journey is journal → review suggested tasks → accept selected suggestions → complete tasks → review achievements.

## Value and scope

Unlike copying actions manually from notes, Mawj keeps journaling, reviewed task suggestions, and progress in one workflow. The audience and demand are hypotheses, not validated market research. A plausible first adoption model is a free student pilot; optional paid AI usage could follow only after user feedback and cost validation. No paying customers or demonstrated demand are claimed.

Features: Django accounts and private records; task CRUD with title-only quick entry, optional scheduling and details, search/status/priority filters and pagination; journal create/read/edit/delete with search and annotated pending-suggestion counts; explicit suggestion acceptance/dismissal; calendar; weekly/monthly/yearly achievements; profile and themes.

## Setup

Validated with Python 3.12.14, Django 6.1.2 and requests 2.34.2 on Linux. SQLite is included with Python. Use the root `manage.py`; `myproject/` is a legacy scaffold and is not the active application.

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

The default `AI_PROVIDER=demo` is a **simulation**, not a live AI model: journal lines starting with `-` or `*` become suggestions. `manual` saves journal text without AI. The core app works without external credentials. Optional providers: `gemini` uses `GEMINI_API_KEY`, `openai` uses `OPENAI_API_KEY`, and `claude` uses `ANTHROPIC_API_KEY`. Optional model variables are `GEMINI_MODEL`, `OPENAI_MODEL`, and `CLAUDE_MODEL`. Configure secrets outside Git; never commit credentials. Check provider model availability before using live integrations. Title/description or journal text is sent to the selected external provider; the interface displays a notice. Live provider availability is not validated by mocked tests.

`DJANGO_SECRET_KEY` overrides the development key. The default configuration uses DEBUG and is for local development; public deployment requires separate secure configuration (hosts, HTTPS, secret key, DEBUG off). Deployment is not part of this submission setup.

## Business rules and reports

Only the owner can view or modify their tasks, entries and suggestions. AI suggestions do not create tasks until accepted. Sequential repeat acceptance does not duplicate tasks; concurrent acceptance is a known limitation. Editing journal text saves it as written and dismisses obsolete pending suggestions without calling AI or deleting previously accepted tasks. Deleting an entry cascades to its suggestions, but accepted tasks remain independent.

Task duration, if supplied, must be 1–1440 minutes; title is required. Unspecified priority defaults to medium. Account passwords require at least 8 characters; no additional character rules are imposed. Completion percentage is completed / total tasks scheduled in the selected calendar period, rounded to an integer. Undated tasks use their creation date in Asia/Riyadh. Weeks start Sunday; calendar months/years include the whole period, including scheduled future tasks. An empty period displays an empty state rather than a misleading percentage. This is scheduled-work completion, not a count of completion events during that period.

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

See [design](docs/design.md), [verification](docs/verification.md), [demo](docs/demo.md), and [work list](docs/work-list.md). Automated checks complement the manual acceptance record; they do not establish live AI reliability. Install from a clean directory and migrate an empty database before submission. No deployment link is supplied because the project has not been deployed.

## Sources and assistance

Built with Django and Requests; use their official documentation for authentication, forms, ORM, migrations and HTTP behavior. OpenAI Codex assistance was used for environment setup, feature implementation, tests and documentation. The student must review and understand these contributions and be able to explain the URL → view → ORM → template flow and design choices. Requirements were reviewed against the supplied Capstone Project Guide.
