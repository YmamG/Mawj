# Verification record

Executed 2026-10-12. Local demo mode; fictional records only. No live AI calls were made.

| Scenario | Expected | Actual | Status / method |
|---|---|---|---|
| Existing + new regression suite | All tests complete successfully | Final complete suite: 63 tests passed, including demo seed and journal edit checks | PASS, Django tests |
| Fresh dependency installation | Empty venv installs root requirements | Python 3.12 / Django 6.1.2 / requests 2.34.2 installed | PASS, clean source copy without `.git`, venv, DB or caches; not a remote clone |
| Fresh schema | Migrations build an empty SQLite database | All migrations applied; system check has no issues | PASS, fresh-copy commands |
| Migration consistency | No uncommitted model changes require migration | `makemigrations --check --dry-run`: no changes | PASS |
| Demo seeding and repeat | 13 tasks, 2 entries, 3 suggestions; second run changes nothing | First run created sample records; second preserved them | PASS, commands and unit test |
| Seed report | Current period 6/12 completed = 50% | Browser displayed 50% before additional actions | PASS, browser |
| Journal annotation | One entry has 2 pending, another 0; accepted/dismissed excluded | Expected counts shown; private entry excluded | PASS, browser + Django tests |
| Task search/status/priority | Combined filters match only owned records | Two seeded completed high-priority study tasks shown | PASS, browser; privacy separately tested |
| Search empty state | No matching records gives useful feedback | No-match message displayed | PASS, browser + Django tests |
| Pagination | 10 records per page, parameters retained | 12 matching test records split 10/2 | PASS, Django tests |
| Title-only task | Task saved with medium default priority | Created in browser, found by search, marked done and persisted | PASS, browser + Django tests |
| Duration business values | Reject 0, negatives, >1440; permit 1440 | Rejected by server form; browser displayed helpful zero-duration message | PASS, browser + Django tests |
| Journal end-to-end | Create, accept suggestion, edit, delete; accepted task persists | Browser confirmed persisted accepted task after deleting journal | PASS, browser |
| Journal edit dependencies | Dismiss old pending; preserve accepted and existing tasks | Expected status/data changes verified | PASS, Django tests |
| Required text/ownership | Invalid edit changes nothing; another user receives 404 | Expected behavior verified | PASS, Django tests |
| Reporting boundaries | Correct week/month/year, local undated dates, zero result | Known dataset expectations passed | PASS, Django tests |
| Desktop/mobile page overflow | No document overflow at 1280/375 px | Tasks, task form, journal, achievements and calendar passed | PASS, Chromium viewport checks |
| Visual form/achievements review | Readable fields, collapsed details, wrapping tabs/counts | Screenshots at 375 px inspected manually; content readable | PASS, manual screenshot review |
| Real phone and keyboard walkthrough | Usable on actual devices and assistive navigation | Not performed; rehearse before submission | PENDING, manual acceptance |
| Remote instructor clone / access | Instructor can access exact submitted revision | Local clean-copy installation verified; remote access not assessed | PENDING |
| Live AI reliability | Supported configured model responds | Provider tests mocked; no live credentials exercised | NOT RUN, optional |

Browser checks used real Chromium and UI form submissions against the fresh-copy Django server. Automated browser checks are not a substitute for the student's required manual acceptance demonstration. Do not claim all manual acceptance scenarios have been completed. The browser run changed only its isolated sample database, not the main development data.

## Manual acceptance checklist for submission

Record actual results, not anticipated passes:

| Scenario | Expected result | Actual result | Status |
|---|---|---|---|
| Sign up → journal → accept → mark done → report | Data persists and counts match | To record | Pending |
| Empty title and invalid duration | Helpful validation, no unwanted save | To record | Pending |
| Search/filter matching and nonmatching records | Correct results/empty feedback | To record | Pending |
| Edit and delete entry with suggestions | Explained dismissal/cascade; accepted task remains | To record | Pending |
| Login as second account | Cannot view or change first account records | To record | Pending |
| Desktop and real mobile, keyboard navigation | Controls readable and usable; focus accessible | To record | Pending |
| Follow README from the submitted checkout | Install, migrate, seed and start succeed | To record | Pending |

## Known limitations

- Live AI calls are optional and not verified; demo is clearly labeled simulation.
- Concurrent suggestion acceptance can produce duplicate tasks; sequential repeat acceptance is covered.
- Business value/demand remains an assumption pending user feedback.
- SQLite/development DEBUG configuration is not a production deployment.
- Duration rules are enforced on task forms; direct database writes may bypass them.
- Journal edits are saved as written; AI is not rerun on edit.
