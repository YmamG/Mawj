# Verification record

Executed 2026-10-12. Local demo mode; fictional records only. No live AI calls were made.

| Scenario | Expected | Actual | Status / method |
|---|---|---|---|
| Existing + new regression suite | All tests complete successfully | Final complete suite: 77 tests passed, including avatars, categories, recurrence, reminders, Today and chart checks | PASS, Django tests |
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

## Extra-feature verification (2026-10-12)

| Scenario | Expected | Actual | Status / method |
|---|---|---|---|
| Avatar default/upload/remove | Default avatar; resized private image; default restored | PNG/JPEG resized/re-encoded, delivery restricted, old files removed on commit | PASS, Django + Chromium |
| Invalid image/type/size | Reject invalid/non-PNG-JPEG files, >2 MB and >4096 dimensions | Form errors verified; no unwanted replacement | PASS, Django |
| Recurrence | One next daily/weekly occurrence, missed dates skipped; repeated undo/complete does not duplicate | Dates/details/reminders copied correctly; stop repetition supported | PASS, Django + Chromium daily workflow |
| Categories | Only matching owned category tasks displayed | Seeded Study filter and private isolation verified | PASS, Django + Chromium |
| Today sections | Correct today/undated, overdue, completed today; no cross-user records | Membership/counts verified; direct completion available | PASS, Django + Chromium |
| Reminder due/dismiss/reset | Only due incomplete tasks; owner-only POST dismissal; reschedule re-enables | Visibility, access and persistence verified | PASS, Django + Chromium; isolated fixture moved time into past |
| Chart | Bucket totals match summary for all periods | Week/month/year counts match known dataset; exact data table accessible | PASS, Django + Chromium |
| New migrations | Upgrade existing schema and create from empty database | Main DB migrated; clean-copy empty DB migrated successfully | PASS |
| Extra UI at mobile/desktop | No document overflow at 375/1280 px | Today, task form/list, profile/edit and month chart passed; screenshots reviewed | PASS, Chromium + manual screenshot review |

This second clean source copy reused the validated installed interpreter/dependencies and verified new migrations from an empty database. It was not a fresh remote Git clone. Browser-generated data and uploads stayed in the isolated copy. A first run-server command from `/tmp` failed due to the wrong working directory; running from the documented project directory succeeded. Actual phone/manual acceptance and live provider checks remain pending as noted above.

## Next.js redesign verification (2026-10-12)

- Full Django suite: **83 tests passed**, including API ownership, CSRF rejection and trusted-origin acceptance, auth/theme persistence, form validation, recurrence, journal acceptance, reports and calendar. After adding private no-cache headers, the six API tests passed again.
- Production Next.js build and TypeScript checking passed. `npm ci` installs the committed lockfile. Fonts are bundled locally, with no font-network dependency.
- Chromium exercised the actual two-service flow: login, all three themes, category search, demo AI suggestions, daily recurrence, task edit/delete, journal accept/edit/delete, private avatar upload/removal, theme persistence after reload, reminder dismissal, calendar month/day selection, and chart period/data controls. Actions used the real Django API on an isolated fictional database.
- The initial browser check diagnosed a trailing-slash redirect conflict between Next.js and Django; the tested rewrite preserves API URLs and appends the backend slash. A subsequent check found mobile decorative-orbit overflow; reducing the orbit dimensions fixed it. Test-script selector/navigation issues were corrected separately from application changes.
- Anonymous landing/auth/privacy/about pages and workspace layouts were checked at **390, 768, and 1440 px**. Expanded task details were checked on mobile. No document overflow or browser runtime errors remained in the layout run. Screenshots were reviewed manually.
- `next start` production startup, landing themes, mobile layout, API proxy and branded 404 passed. `node scripts/dev.mjs` starts the main Django checkout and Next.js together; landing and API readiness requests returned 200. Ports must be free; a launcher test with earlier validation servers still running correctly failed rather than silently selecting different ports.
- A clean backend source copy built its schema with the theme migration and fictional demo data; the main existing schema also migrated successfully. The clean copy reused installed Python dependencies, and was not a remote Git clone.

Saved visual previews: [Grove](previews/landing-grove.png), [Petal](previews/landing-petal.png), [Dusk](previews/landing-dusk.png), [mobile](previews/landing-mobile.png). These contain illustrative landing content only, not private user data.

Limitations remain: no production deployment or live AI provider test; reminders are in-app on visits; repetition advances on completion; real-device manual acceptance and instructor scope approval are still pending. The original Django screens remain available on port 8000.
