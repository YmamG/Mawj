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

## Startup/account troubleshooting checks (2026-10-12)

- 19 targeted API/account/signup tests passed after username normalization and frontend bookmark redirects. Password spaces remain significant; username-edge spaces are trimmed.
- In an isolated file-backed database, API signup followed by login from two separate Python processes succeeded, including after logout. Original Django signup followed by original Django login from another process also succeeded. This verifies restart persistence in the tested checkout, not the user's Windows database.
- Updated launcher started both services, printed the active database path/account count and reached both readiness endpoints. Old `/accounts/signup/` and `/accounts/login/` URLs returned 302 to the new port-3000 routes; the API returned 200.
- Automatic browser opening is implemented for Windows via Python's standard webbrowser module; execution was not exercised on the Linux validation host. No user database was moved, replaced, or deleted.

## Chart, task scheduling, journal and theme fixes (2026-10-12)

- Final full Django suite: **88 tests passed**. A previous journal fixture used a historical date; it was updated to a future date while retaining time/detail assertions to match the new past-date rule.
- Next.js production build and TypeScript checking passed.
- Chromium verified that the empty-state Add task button scrolls/focuses the form, the date picker rejects past dates, first/middle/last monthly chart tips are fully inside the scroll region, natural Arabic/English demo notes yield suggestions, and reanalysis preserves accepted suggestions.
- Ember/Midnight settings persisted after reload; footer attribution and GitHub links appeared in both interfaces. Desktop (1280) and mobile (390) layouts passed without document overflow. An intermediate check found long usernames overflowing the mobile profile; wrapping them fixed the issue.
- Both client and server reject new past schedules; existing unchanged overdue records can still be edited. API acceptance cannot bypass these rules.
- Browser checks used generated fictional validation accounts in the local development database. These temporary accounts were removed after the run. No real credentials were used. Live AI remains untested; simulation and provider modes are now visible in the journal UI.

## Calendar, modal confirmations, login appearance and Arabic (2026-10-13)

- Final complete Django suite: **91 tests passed**, including login-theme retention, owner-only undated calendar tasks with complete journal text, and request-scoped Arabic form validation. Next.js production build and TypeScript checks passed.
- Real Chromium exercised signup/logout/login with Ember selected, creation of an undated task and a long journal, and calendar-day opening with the task and full journal text. Task deletion opened a visible modal; cancellation closed it without removing the task.
- Arabic RTL persisted across hard navigation and reload. Landing, Today, tasks, journal, profile, calendar and achievements had no document overflow at desktop 1280px and mobile 390px. User-written task and journal text remained unchanged. An additional login check verified switching English → Arabic → reload → English → reload without browser runtime errors.
- An intermediate SSR locale mismatch was fixed by reading a non-secret language cookie in the root layout and passing the initial locale into the client context. Translation rendering uses context-local locale rather than mutable server state.
- The uploaded old ZIP was reviewed without executing its contents. Its cloud-provider prompts and HTTP request functions match the current provider; the current local demo additionally supports intent phrases. `.env` loading now preserves provider settings between launches. No live provider was exercised because no live credential was configured; simulated and mocked provider checks do not establish cloud reliability.
- The three fictional `review_checks_` accounts created during browser review were removed afterward. These checks do not access the user's Windows database. No schema migration is required by this update.

## Saudi headings and formal Arabic copy (2026-10-13)

- Added the owner's supplied Saudi Web regular/bold WOFF2 assets through `next/font/local`. Browser font loading and computed heading styles confirmed Saudi was used; body copy retained Noto Sans Arabic.
- Reviewed Arabic interface wording and replaced colloquial phrases with Modern Standard Arabic, including empty states, marketing examples, account prompts, notices and privacy text. Reworked two segmented landing headings to produce grammatical Arabic. User-authored records were not modified.
- Next.js production build and TypeScript checks passed. Chromium checked landing, login, signup, about and privacy at 1280px and 390px: fonts loaded locally, no document overflow, and no browser runtime errors. Mobile landing screenshot was visually reviewed.
- An initial browser run timed out against the development process after a production build; restarting the existing launcher resolved it. No backend behavior changed in this update, so the Django suite was not rerun.

## Submission audit and fresh remote checkout (2026-10-13)

- Re-read all six pages of the supplied Capstone Project Guide, mapped its eight assessment criteria in `submission-ar.md`, and corrected stale design/demo/work-list descriptions. No new application features were added.
- Cloned GitHub `main` into a separate empty directory at revision `4c2500b`. Created a new Python 3.12.14 virtual environment; installed Django 6.1.2 and all declared dependencies; `pip check`, system check and migration consistency passed. All migrations built a new SQLite schema.
- Created fictional sample data with a generated password kept out of logs. A second seed preserved the account/data. The fresh report returned 6/12 complete = 50%.
- Frozen-lockfile `npm ci` passed. Its first attempt could not create the sandbox's default home cache; specifying a writable temporary cache resolved installation without changing integrity checks or lockfiles.
- Fresh Next.js production build passed. Started the separate Django and Next servers and verified the landing response, authenticated session/API proxy, week report and per-journal pending-suggestion annotation over HTTP. An initial review harness used `items` instead of the API's `results` key; correcting that harness yielded a passing check without changing application code.
- This validates current Linux fresh setup, not installation on the student's actual Windows machine or instructor access. Last complete Django run remains 91 passing tests; it was not rerun for documentation-only changes. Manual acceptance, agreed scope, evidence of demand/assumptions and individual technical discussion remain submission responsibilities. Live provider calls were not made.

## LAN phone launcher and development origins (2026-10-13)

- Added `node scripts/dev.mjs --lan`, which prints adapter-specific phone URLs, binds Next to all interfaces, and merges exact local origins into Django's configured CSRF origins. Django remains on loopback and default startup retains loopback-only Next binding.
- Next `allowedDevOrigins` now includes localhost, loopback and actual local IPv4 addresses. TypeScript and Node syntax checks passed; the updated launcher started successfully.
- Chromium confirmed loopback HMR connects when Next binds to `0.0.0.0`. Direct LAN browser navigation in this cloud runner was rejected by its browsing proxy with `403 Domain forbidden`; this was not an application response. Node HTTP calls to the actual local IPv4 address successfully exchanged session/CSRF cookies, signed up a fictional account and created/retrieved a persisted task. A real HMR WebSocket handshake/message exchange from that LAN origin passed. The fictional account was then removed.
- No Windows phone or physical network was available here. Wi-Fi reachability, Windows firewall permission and router client isolation still require checking on the student's devices.

## Separate Django template edition (2026-10-13)

- Created `django-templates` as a separate branch/checkout; the original `main` Next.js edition remains unchanged. Added inherited server-rendered public/workspace templates, local CSS/fonts/SVGs, translation tags, and plain JavaScript interactions. Removed the Next/React source and Node launcher only from this branch. No new schema migration is required.
- Full Django suite: **95 tests passed**, including four new template-edition checks for server-rendered ownership/XSS protection, anonymous access, Arabic/local assets, and safe full calendar JSON. Updated the old home-to-Next test to assert the new local landing behavior rather than deleting coverage.
- Browser checks on actual Django verified signup, selected theme retention, task creation and demo suggestions, edit, journal generation/acceptance, modal cancellation, complete calendar details, Arabic RTL and 1280/390px layouts. Additional checks passed in-app reminder dismissal, daily successor creation, profile/avatar upload/removal, and monthly/yearly chart layout. Node syntax and Django system/migration consistency checks passed. All browser accounts were fictional and removed afterward.
- Visual review caught mismatched graph/filter classes and stale cached development templates; the classes were corrected and the checks rerun against a freshly started server. An initial avatar fixture was invalid and rejected; a valid generated PNG exercised upload/removal. A subsequent browser wait raced an already visible notice; waiting for navigation verified the actual removal without application changes.
- The Python-only LAN helper started, printed explicit network URLs and served both loopback/LAN landing requests. A branded missing-page response returned 404. Python dependencies were reused from the existing validated environment; migrations created a fresh separate local database, rather than copying personal data. No real AI credentials or physical Windows phone were exercised.
- Forms/sections now use full Django page navigation, and compact dates can be numeric. Core design and features are preserved; no pixel-perfect comparison is claimed. Historical Next.js setup records above refer to `main`, not this branch. Manual acceptance and instructor access remain user-owned submission steps.
