# Work list

Completed: task/journal CRUD, ownership enforcement, task search/status/priority filters, journal search, deterministic pagination, pending-suggestion annotation, achievement counts and period boundaries, simple task form, duration validation, journal edit/deletion rules, responsive controls and calendar overflow, ERD, safe demo-data command, README and demo guide; private profile photo upload/removal; daily/weekly recurrence; Today sections; fixed categories/filtering; in-app reminder settings/dismissal; achievement chart with accessible data.

Submission priorities:
- Review and approve the scope with the instructor.
- Review the verification record and manually rehearse the demo on an actual phone and desktop.
- Confirm instructor repository access and submitted revision; commit reviewed changes with meaningful messages.
- Validate the student audience/value assumptions with actual feedback; record evidence separately from assumptions.
- Review significant AI assistance and explain the implementation in the technical discussion.

Optional future work: email/push notifications, custom categories, validated live AI models, secure deployment. These are not universal guide requirements.

Known limitations: live provider tests are mocked; no deployed production configuration; no evidence of demand yet; the legacy Django HTML suggestion-accept route can create duplicate tasks under concurrent requests (the Next.js API uses an atomic conditional claim); direct database writes can bypass form-level business rules. Edited journals save as written rather than reprocessing AI.

Extra-feature limitations: recurrence advances on completion; reminders only appear on site visits; charts report scheduled work rather than completion-event history; avatar files require backup with the database.

Next.js redesign completed: real Django API integration, public landing page, five palette themes, Arabic/English switching and the supplied Saudi heading font, complete workspace, locally hosted fonts, accessible state handling, private photo delivery and a cross-platform two-service launcher. Production deployment remains separate.

Submission audit and Arabic architecture/AI walkthrough: [submission-ar.md](submission-ar.md). Manual acceptance results and instructor access remain student-owned submission steps.
