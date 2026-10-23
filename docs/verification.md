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

## Django public navigation/slash regression fix (2026-10-13)

- Public templates exported from Next had slashless links (`/signup`, `/login`, `/about`, `/privacy`). The branded catch-all resolved them before Django's APPEND_SLASH middleware could redirect, so clicking those links returned the branded 404 even though explicit slash-terminated routes worked. Corrected template links and added safe GET/HEAD normalization for known routes; unknown paths stay 404 and POST bodies are not redirected.
- Added a default `/app/` route and preserved safe local workspace `next` destinations after authentication. Six template tests passed (including two new regression checks). Chromium clicked all four public navigation links in both Arabic and English and verified slashless bookmarks redirect correctly. The previous full suite's 95-test result remains historical; a full 97-test run was not performed for this fix.

## Existing ZIP to Git conversion helper (2026-10-13)

- Added `scripts/connect_git.py` and one-time PowerShell instructions. The helper requires the actual project root, creates a local sibling backup, clones the explicit Django branch into a temporary folder and copies tracked source before installing Git metadata. Existing DB, `.env`, uploads and virtual environment paths are protected; existing different Git branch/origin is refused.
- Tested the helper against a fictional local Git remote and ZIP-like folder: old-code/data backup, new code installation, intact DB/config/uploads/venv, clean Git status, repeated connection, and a later fast-forward pull all passed. No application behavior changed, so the Django suite was not rerun. This validates Python/Git behavior on Linux; the Windows PowerShell download command and user's filesystem were not exercised here.

## Separate production configuration (2026-10-19)

- Prepared the Django-only `django-templates` edition in a separate checkout. Local settings and the original Next.js edition were preserved. Added explicit production settings/WSGI entry, private environment reference and Arabic PythonAnywhere instructions; no hosting account was accessed and no public deployment was performed.
- Full Django suite: **102 tests passed** on Python 3.12 / Django 6.1.2. The five new isolated production tests verify invalid key/host/origin rejection, unchanged local defaults, HTTPS redirects, rejection of spoofed forwarding/unknown hosts, secure CSRF cookie and valid/invalid CSRF requests. After the final mail configuration adjustment, these **five tests passed again**, including production WSGI startup.
- The initial deployment check rejected the inherited console email backend. Production now selects SMTP using Django's MAILERS setting without conflicting deprecated EMAIL_BACKEND. This does not configure or test email delivery; the app's reminders remain in-app.
- Final production `check --deploy` completed without errors and with **one warning, security.W004**: HSTS remains deferred until real hosting HTTPS is verified. `collectstatic` collected 160 files; checked application CSS, JavaScript, font stylesheet, Saudi bold font and admin CSS in the collection output. Generated assets and secrets are excluded from Git.
- Hosting WSGI integration, actual TLS/proxy behavior, provider outbound access, backups and physical phone acceptance remain untested. No real provider key or private user database was used. The guide is based on official PythonAnywhere help sources and Django's deployment checklist, rather than a claim of a verified public deployment.

## Public administration and privacy boundaries (2026-10-20)

- Disabled the Django admin URL tree in production, including user password changes and private task/journal browsing. Development administration remains available; the application's normal account/session behavior is unchanged. Existing accounts/data are preserved and no migration is required.
- Production checks verify that admin login/model routes resolve to the missing-page handler and return 404. An authenticated staff/superuser API regression verifies owner-only task/journal lists, rejection of reads/deletes/suggestion acceptance for another user, and rejection of profile target switching.
- **103 tests passed** in the full suite on Python 3.12 / Django 6.1.2; system checks and migration consistency passed. Earlier targeted API/production run: 19 tests passed. These are local checks; the operator must pull and reload the hosted application, then verify `/admin/` returns 404.
- Updated Arabic/English privacy statements to disclose that direct server/database/backup access remains possible and that journal/task content is not end-to-end encrypted. Disabling a URL does not prevent a hosting operator from reading SQLite or changing code/credentials through the server. No private user data, passwords or live hosting credentials were accessed.
- Corrected the hosting guide to use the user-selected `YmamG/Mawj:django-templates` repository and documented that a superuser is not required for deployment.

## Read-only registered account directory (2026-10-21)

- Added `/operator/accounts/` as a separate server-rendered directory for authenticated, active staff/superusers. It queries only usernames and registration dates, paginates 50 rows per page and sends no-store headers. There are no per-account links, editing, deletion, password changes, impersonation or export endpoints. Production Django administration remains disabled.
- Linked the directory from the operator's own profile only. Added Arabic/English copy and updated privacy disclosures to distinguish registration metadata from private task/journal/email/photo content. Direct hosting/database access remains outside this UI restriction; no end-to-end encryption is claimed.
- Five new directory tests verify anonymous/nonoperator denial, exact selected fields and absence of private content, method/detail-route restrictions, pagination, Arabic/XSS escaping and profile-link visibility. Production configuration checks confirm anonymous access redirects to login while admin routes stay missing.
- **108 tests passed** in the full suite on Python 3.12 / Django 6.1.2; system check, migration consistency and diff whitespace checks passed. No schema migration or real user-data inspection was needed. Initial targeted directory/production run: 10 tests passed. The hosted instance still requires pull, static collection and Web Reload before the directory is available; hosted browser verification was not performed here.

## Opt-in encrypted journal preview (2026-10-21)

- Created the separate `e2ee-journal-preview` branch from `django-templates`; the deployed branch and hosting instance were not changed. Preview is disabled by default and requires `MAWJ_E2EE_JOURNAL_PREVIEW=1`. Added separate vault/ciphertext tables and optional per-entry legacy migration, without an automatic data conversion or deletion migration.
- Browser Web Crypto uses random 256-bit journal keys, AES-GCM with fresh 96-bit IVs/128-bit tags and user/vault/entry context binding. A 600,000-iteration PBKDF2-SHA256 passphrase envelope and an independent random recovery-key/HKDF-SHA256 envelope wrap the master key. Keys/passphrases/recovery codes are not uploaded in readable form by the normal storage flow, and the UI does not persist them or decrypted drafts in browser storage. This is an experimental protocol implementation, not an independent security audit.
- **122 Django tests passed** on Python 3.12 / Django 6.1.2 after the final backend changes, including 14 new vault checks for opt-in/auth/CSRF, envelope validation, owner isolation, stale revision rejection, consent gates, atomic migration and task acceptance idempotency. Initial full run before two additional checks: 120 passed. An early test used a nonexistent legacy URL; correcting the fixture to `/journal/add/` verified the actual guard rather than weakening the assertion.
- Node/Web Crypto checks passed for Arabic content round trip, fresh ciphertext/IVs, wrong passphrase, changed account/entry context, ciphertext tampering, recovery and rewrapping with a new passphrase. A second browser flow verified the old vault passphrase stops opening the current envelope while recovery retains access to existing content. These checks do not establish resistance to malicious code delivery or forensic memory recovery.
- Chromium browser checks passed twice against Django using fictional accounts: setup/recovery acknowledgement, encrypted network payloads, local-only Demo analysis, explicit unencrypted task acceptance, lock/wrong/correct unlock, legacy migration preserving raw/organized text, recovery, no secret/draft persistence in local/session storage, calendar links, Arabic RTL and 1280/390px layouts without document overflow. Mobile screenshot was visually reviewed. A separate browser test used a mocked cloud response: cancel sent no analysis request; approval sent the selected note with consent; result returned to encrypted storage; signing out in another tab immediately locked/cleared the vault. No live AI provider was called.
- The bundled Playwright browser download was blocked with `403 Domain forbidden`. Used the already-installed `/usr/bin/chromium` through Playwright instead; did not disable TLS verification or use an unverified download. All browser accounts were fictional and removed after the checks. No private hosting/user database or real provider secret was used.
- System check, migration consistency, JS syntax and diff whitespace checks passed. Production-mode preview deployment check had no errors and the existing HSTS warning `security.W004`; collectstatic collected 162 files and included both ES modules with a JavaScript MIME type in the local runtime. Actual hosting TLS/proxy/MIME behavior, Safari/Firefox and physical devices were not tested.
- The Arabic guide documents a separate checkout/database trial, key loss, metadata and unencrypted tasks, per-analysis cloud disclosure, partial migration/retry, old SQLite/WAL/backup remnants, fixed master/recovery-key limitations, server-code control and required independent review before sensitive/public use. No end-to-end encryption claim applies to the existing published site or old entries that have not been explicitly migrated.

## Calmer journal UX and session-bound device access (2026-10-22)

- Replaced the standalone security-heavy preview page with Mawj's shared navigation, theme/language controls, profile avatar, journal cards and a normal editor. Setup uses two brief steps and a recovery-file download action, without repeated acknowledgement questions. Detailed privacy/recovery explanations are available on demand; the preview label remains visible. No change was published to the hosted branch.
- Removed locking on tab visibility and a fixed idle timeout. A non-extractable AES-GCM CryptoKey is stored in IndexedDB, scoped by account/vault and an opaque HMAC binding to the current Django login session. Reloads, navigation and browser back reopen automatically. Passphrases, recovery codes and readable journal drafts are not persisted. Normal logout clears the device key even if the journal tab is closed; manual lock and cross-tab logout clear memory/cache. New session bindings reject and remove stale records. This supersedes the previous memory-only preview policy; the usability/security tradeoff and same-origin/device-access limits are documented in the current guide.
- Added debounced encrypted autosave and save-before-navigation/selection. Saves snapshot the document and track input versions so typing during an in-flight request does not overwrite newer text. A delayed-save browser check verified the latest typed version survives reload and creates no duplicate entry. Errors retain the draft on the current page; this is not an offline synchronization system.
- Removed the extra task-acceptance confirmation dialog, retaining explicit ordinary-task labels and inline disclosure of the encryption boundary. External AI still requires consent for the selected note, and deletion retains confirmation. The normal write/demo/task flow produced no confirmation dialogs in browser review.
- **123 Django tests passed**, including a new binding test for stability, change after logout/login, and rejection as an authentication credential. The 15 targeted vault tests, Node Web Crypto tests, JS syntax, migration consistency and diff whitespace checks passed. Cryptographic algorithms/envelopes and existing encrypted records remain compatible.
- Chromium checks passed for setup/download, automatic encrypted save, typing during a delayed save, non-extractable key storage/export rejection, reload/tab switching/back navigation without re-unlock, manual lock, logout with journal closed, recovery, Arabic and 1280/390px layouts. Separate checks verified no-dialog save before immediate navigation, stale-session cache rejection, unavailable IndexedDB fallback, and cancel/approve external AI with a mocked response. No real external AI call was made. Fictional review accounts were removed afterward.
- An intermediate rerun used a cached template in the no-reload development server with newer JS and failed on missing new DOM IDs. Confirmed the stale template, restarted that test server, then reran both browser flows successfully. No assertions were disabled. Screenshots were visually reviewed; real devices and independent security review remain outstanding.

## Future goals and supplied interface references (2026-10-22)

- Added the owner-scoped `goals` app and its additive initial migration on `e2ee-journal-preview`. Title-only creation, optional reason/date/category, milestone dates, pause/resume, manual completion for goals without steps, derived equal-step progress, upcoming timeline, filtering and pagination are working. The migration does not alter existing journal or account tables.
- Linked steps create a task once on repeated submissions and use its actual completion state. Tests cover toggling through the goal and the ordinary task view, deletion preserving the appropriate step/task state, past-date validation, ownership isolation including staff/superusers, CSRF, escaped user content and invalid AJAX forms. Ordinary goals remain outside the encrypted-journal boundary, with corresponding privacy copy and documentation.
- **135 Django tests passed** on Python 3.12 / Django 6.1.2. Migration consistency, system checks, JS syntax, diff whitespace and the existing Node/Web Crypto checks passed. No new runtime dependency is required.
- Chromium/Playwright checks passed for real login through the supplied Django form, title-only goal creation, adding steps, 50%/100% progress, task linking, editing optional details, upcoming dates, pause/resume, achieved filtering, cancel/approve goal deletion, preservation of the task, Arabic RTL, all five themes and 1280/390px layouts without document overflow. Native goal/step submissions also passed with JavaScript disabled, using keyboard submission. Screenshots were visually reviewed, including settled Midnight colors. Physical phones and other browser engines remain untested.
- The first browser run found the hidden `action` input shadowing the form's `action` property. Changed the enhanced submit handler to read the actual HTML attribute and reran the complete browser flow successfully. Later harness failures came from addressing a collapsed optional section and a nonexistent explicit submit `type`; corrected the harness to use the visible controls. A no-JavaScript click was unstable during scrolling; native Enter submission verified that workflow. No checks were removed to conceal application failures.
- Adapted the attached React examples as a native timeline, lightweight SVG flowing paths and a subtle sign-in card. No React/Next/GSAP/Framer dependency, fake login, external photo or Google sign-in was added. Existing auth, theme/language handling and encrypted journal behavior were preserved; reduced-motion handling was checked. No AI request or automatic AI access to goals/journals was introduced, and no public deployment was performed.

## Journal and goals clarity pass (2026-10-22)

- Reworked ordinary and encrypted journal screens around a notebook metaphor: a single visible write action, lined entry cards, date tabs, bookmarks, a page-like editor and an optional compact writing-assistant disclosure. The provider and privacy facts remain available without occupying the primary reading path. The encrypted setup, key handling, autosave and provider consent behavior did not change.
- Reduced the goals list to one add action, three summary values, direct filters and progress cards. Removed the separate visible horizon timeline. Goal detail now leads with status/progress and steps; edit, pause/resume and delete are grouped under a collapsed options section. Dates, task links, server-side validation and delete behavior are unchanged.
- Added distinct book, target, flag and shield icons and short entrance/hover transitions. Reduced-motion preferences disable the new animations. All five themes continue to use their existing variables.
- **136 Django tests passed**, including a new rendered-journal structure check and updated goals hierarchy assertion. System checks, migration consistency, JavaScript syntax, diff whitespace and Node/Web Crypto checks passed.
- Chromium browser flows passed for ordinary journal create/read, encrypted vault setup/download/autosave/read, goal create/step/100% progress, Arabic RTL, 1280px and 390px layouts and document-width checks. Goal detail, journal list, encrypted journal list and mobile Arabic screenshots were visually reviewed. No external AI request was made and no hosted branch was changed during these checks.

## Reviewable AI goal plans (2026-10-22)

- Added goal-step planning through the existing provider layer. Demo returns a clearly labeled local sample plan; configured cloud providers receive only the selected goal details and current step titles after the user presses the disclosed action. The goal prompt treats those fields as data and requests same-language, concrete steps. No journal content is included.
- Suggestions remain unsaved until review. Each title is editable and individually selectable; acceptance validates length and type on the server, caps the request, removes case-insensitive duplicates and reopens a completed goal when a new step is added. Ownership and CSRF rules apply to suggestion and acceptance requests.
- **146 Django tests passed** on Python 3.12 / Django 6.1.2, including parser/provider, local Demo, cloud consent, ownership, CSRF, validation, deduplication and acceptance checks. System check, migration consistency, JavaScript syntax, JSON syntax and diff whitespace checks passed. No migration or runtime dependency was added.
- Chromium completed a real login and Demo flow at 1280px and 390px: open planning, generate four local suggestions, edit one, deselect one and accept only the selected steps. Desktop and mobile review screens were visually inspected. No live external provider was called; provider behavior is covered by mocks and still requires verification with the operator's own account/key.

## Concise AI disclosures (2026-10-23)

- Replaced the encrypted-journal cloud confirmation dialog with a short provider label beside the existing analysis button. Pressing that disclosed button is the explicit per-entry action; the backend still requires the current provider and consent flag and does not persist readable analysis text. Full retention and encryption-boundary details remain in the privacy and encrypted-journal documentation.
- Matched the same neutral pattern in journal, task and goal interfaces: each names the configured provider and the help it supplies in one sentence. Demo and manual labels remain distinct. No provider, storage, encryption or API behavior changed.

## Journal book and trusted-device return (2026-10-23)

- Adapted the supplied React page-flip idea to the Django edition as a native journal book with a cover, lined entry pages, page counts, previous/next controls and restrained page-turn motion. Arabic RTL reverses the visual binding and controls; reduced-motion preferences disable the turn animation. No React, Tailwind, shadcn, npm package, external image or runtime dependency was added.
- Replaced repeated passphrase entry on the same browser with an explicit «فتح يومياتي» button. The existing non-extractable Web Crypto key is retained in IndexedDB for that account and vault across sign-out/sign-in; readable content and the in-memory key are still cleared at sign-out. «نسيان هذا الجهاز» deletes the retained key and returns to passphrase entry. The privacy page and technical guide describe the shared-device tradeoff.
- **146 Django tests passed**, including the 15 vault tests and new rendered controls. System checks, migration consistency, JavaScript syntax, Node/Web Crypto tests and diff whitespace checks passed. No migration was added.
- Chromium completed setup/download, two encrypted autosaves, book navigation, sign-out/sign-in, one-button trusted-device opening, Arabic RTL at 390px without horizontal overflow, and forget-device fallback to the passphrase. Desktop and mobile screenshots were visually reviewed. The check used Demo mode and fictional data; no external AI request or physical-device test was performed.

## Gemini configuration repair (2026-10-23)

- Removed the invalid `gemini-3.6-flash` default. `GEMINI_MODEL=auto` now queries Google's model-list endpoint using the configured key, sends no journal content in that request and chooses an available text-capable Flash model. A specific supported model can still be pinned. Existing private keys remain outside source control.
- Added `python manage.py check_ai` to report the active provider, model setting and whether the expected key was loaded without printing it. `--models` safely lists the text models available to a Gemini key; `--live` sends only a fixed fictional connection-test phrase. Encrypted-journal provider failures now return Mawj's fixed safe error text and status code without returning the note or provider response body.
- **148 Django tests passed**, including fixed and automatic Gemini model selection and a regression check that a provider error is useful but does not echo the submitted private note. System checks, migration consistency, Python compilation and diff whitespace checks passed. Provider requests and discovery remain covered by mocked responses; a real provider key was neither available nor used in this workspace.
