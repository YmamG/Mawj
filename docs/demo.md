# Demonstration

1. Run the README setup, choose an invented password for `mawj_demo`, and sign in. No real personal information is needed.
2. Explain the intended student audience, the journal-to-task workflow, and that market demand remains a hypothesis. Demo AI is explicitly a simulation.
3. Open Journal: show one entry with 2 pending suggestions and one with 0. This is the per-entry ORM annotation.
4. Create a journal containing `- Review database notes`. Open it and accept the suggestion. Show the task in Tasks and mark it complete.
5. Add a task using only its title. Show optional details and AI suggestion review. Submit a zero duration to demonstrate validation, then fix it.
6. Search tasks and filter status/priority; show a search with no matches. Show pagination using the seeded 12 current tasks.
7. Open Achievements and change week/month/year. Explain scheduled-work completion and the 50% initial dataset (the earlier demo actions may change it).
8. Edit a journal with pending suggestions; explain their dismissal. Delete a journal and show that accepted tasks remain.
9. Explain USER→TASK and JOURNAL_ENTRY→TASK_SUGGESTION relationships, and trace a request through URLs, view, ORM and template.
10. Describe limitations and next improvements: validate demand with students, improve AI value based on feedback, and optionally add charts. No commercial traction or live AI verification is claimed.

Before submission: run checks, confirm instructor repository access, choose the exact submitted revision, and rehearse the same workflow. The instructor determines presentation length. Be ready to explain every assisted code change yourself.

## Extra-feature demonstration

- Edit Profile, upload a fictional PNG/JPEG, then remove it to restore the default avatar.
- Add a task dated today with Study category and Daily repeat. Complete it and show the next dated occurrence. Undo and re-complete: no second successor is created.
- Show the Today/Overdue/Completed today tabs and the category filter in Tasks.
- Choose a reminder a few minutes in the future. After its time passes, reload the site, open Today, and dismiss it. Explain that these are in-app reminders, not external notifications.
- Switch the achievement chart week/month/year; expand View chart data and compare the exact totals.
