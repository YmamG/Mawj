import json
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.utils import timezone
from tasks.models import Task
from journal.models import JournalEntry, TaskSuggestion
from accounts.models import UserPreferences


class ApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("api-user", password="12345678")
        self.other = get_user_model().objects.create_user("other-api")
        self.client.force_login(self.user)

    def post(self, path, data):
        return self.client.post("/api/" + path, data=json.dumps(data), content_type="application/json")

    def test_session_signup_login_logout_and_theme(self):
        self.client.logout()
        response = self.client.get("/api/session/")
        self.assertIsNone(response.json()["user"])
        self.assertIn("csrftoken", response.cookies)
        self.assertEqual(self.client.get("/api/tasks/").status_code, 401)
        response = self.post("auth/signup/", {"username": "new-api", "password1": "12345678", "password2": "12345678", "theme": "petal"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["user"]["theme"], "petal")
        self.assertEqual(self.post("auth/logout/", {}).status_code, 200)
        self.assertEqual(self.post("auth/login/", {"username": "new-api", "password": "wrong"}).status_code, 400)
        self.assertEqual(self.post("auth/login/", {"username": "new-api", "password": "12345678"}).status_code, 200)
        self.assertEqual(self.post("theme/", {"theme": "dusk"}).status_code, 200)
        self.assertEqual(self.client.get("/api/session/").json()["user"]["theme"], "dusk")
        self.assertEqual(self.post("theme/", {"theme": "invalid"}).status_code, 400)

    def test_csrf_blocks_missing_token_and_untrusted_origin(self):
        client = Client(enforce_csrf_checks=True)
        session = client.get("/api/session/").json()
        credentials = json.dumps({"username": "api-user", "password": "12345678"})
        self.assertEqual(client.post("/api/auth/login/", credentials, content_type="application/json").status_code, 403)
        self.assertEqual(client.post("/api/auth/login/", credentials, content_type="application/json", HTTP_X_CSRFTOKEN=session["csrf"], HTTP_ORIGIN="https://evil.example").status_code, 403)
        self.assertEqual(client.post("/api/auth/login/", credentials, content_type="application/json", HTTP_X_CSRFTOKEN=session["csrf"], HTTP_ORIGIN="http://localhost:3000").status_code, 200)

    def test_superuser_has_no_private_record_or_account_bypass_in_app(self):
        self.user.is_staff = self.user.is_superuser = True
        self.user.save(update_fields=["is_staff", "is_superuser"])
        task = Task.objects.create(user=self.other, title="Private task")
        entry = JournalEntry.objects.create(user=self.other, raw_text="Private journal")
        suggestion = TaskSuggestion.objects.create(user=self.other, entry=entry, title="Private suggestion")
        self.assertEqual(self.client.get("/api/tasks/").json()["total"], 0)
        self.assertEqual(self.client.get("/api/journal/").json()["total"], 0)
        for path in (f"tasks/{task.pk}/", f"journal/{entry.pk}/"):
            self.assertEqual(self.client.get("/api/" + path).status_code, 404)
            self.assertEqual(self.post(path, {"action": "delete"}).status_code, 404)
        self.assertEqual(self.post(f"suggestions/{suggestion.pk}/", {"action": "accept"}).status_code, 404)
        self.post("profile/", {"user_id": self.other.pk, "username": self.other.username, "display_name": "Own profile"})
        self.assertEqual(self.client.get("/api/session/").json()["user"]["id"], self.user.pk)
        self.other.refresh_from_db()
        self.assertEqual(self.other.username, "other-api")
        self.assertFalse(UserPreferences.objects.filter(user=self.other, display_name="Own profile").exists())
        self.assertTrue(Task.objects.filter(pk=task.pk).exists())
        self.assertTrue(JournalEntry.objects.filter(pk=entry.pk).exists())

    def test_tasks_validation_filters_recurrence_and_isolation(self):
        self.assertEqual(self.post("tasks/", {"title": "Invalid", "estimated_duration": 0}).status_code, 400)
        self.assertEqual(self.post("tasks/", {"title": "Missing date", "repeat": "daily"}).status_code, 400)
        response = self.post("tasks/", {"title": "Read", "category": "study", "date": timezone.localdate().isoformat(), "repeat": "daily"})
        self.assertEqual(response.status_code, 201)
        pk = response.json()["id"]
        response = self.post(f"tasks/{pk}/", {"action": "toggle"})
        self.assertEqual(response.json()["status"], "done")
        self.assertIsNotNone(response.json()["next_date"])
        self.assertEqual(Task.objects.filter(previous_occurrence_id=pk).count(), 1)
        response = self.client.get("/api/tasks/?category=study&status=todo&q=Read")
        self.assertEqual(response.json()["total"], 1)
        private = Task.objects.create(user=self.other, title="Private")
        self.assertEqual(self.post(f"tasks/{private.pk}/", {"action": "delete"}).status_code, 404)
        self.assertEqual(self.client.get(f"/api/tasks/{private.pk}/").status_code, 404)
        self.assertEqual(self.post(f"tasks/{pk}/", {"title": "Edited", "category": "personal"}).status_code, 200)
        self.assertEqual(self.post(f"tasks/{pk}/", {"action": "delete"}).status_code, 200)

    def test_journal_complete_journey_and_private_records(self):
        response = self.post("journal/", {"raw_text": "Today\n- Read a chapter"})
        self.assertEqual(response.status_code, 201)
        entry = response.json()
        suggestion = entry["suggestions"][0]["id"]
        self.assertEqual(self.client.get("/api/journal/").json()["results"][0]["pending_count"], 1)
        self.post(f"suggestions/{suggestion}/", {"action": "accept"})
        self.post(f"suggestions/{suggestion}/", {"action": "accept"})
        self.assertEqual(Task.objects.filter(user=self.user, title="Read a chapter").count(), 1)
        self.assertEqual(self.post(f"journal/{entry['id']}/", {"raw_text": "Revised"}).json()["clean_text"], "Revised")
        self.assertEqual(self.post(f"journal/{entry['id']}/", {"action": "delete"}).status_code, 200)
        self.assertEqual(Task.objects.filter(user=self.user).count(), 1)
        private = JournalEntry.objects.create(user=self.other, raw_text="Private")
        self.assertEqual(self.client.get(f"/api/journal/{private.pk}/").status_code, 404)

    def test_today_reminders_reports_calendar_and_profile(self):
        task = Task.objects.create(user=self.user, title="Task", date=timezone.localdate(), reminder_at=timezone.now()-timedelta(minutes=1))
        response = self.client.get("/api/today/").json()
        self.assertEqual(response["counts"]["today"], 1)
        self.assertEqual(response["reminder_count"], 1)
        self.post(f"tasks/{task.pk}/", {"action": "dismiss"})
        self.assertEqual(self.client.get("/api/today/").json()["reminder_count"], 0)
        for period in ("week", "month", "year"):
            response = self.client.get(f"/api/achievements/?period={period}").json()
            self.assertEqual(response["total"], 1)
            self.assertEqual(sum(row["total"] for row in response["chart"]), 1)
        self.assertEqual(self.client.get("/api/calendar/").json()["tasks"][0]["id"], task.pk)
        self.assertEqual(self.client.get("/api/calendar/?month=13").status_code, 400)
        response = self.post("profile/", {"display_name": "Amina"})
        self.assertEqual(response.json()["display_name"], "Amina")
        self.assertEqual(self.client.get("/api/profile/avatar/").status_code, 404)

    def test_invalid_body_and_methods(self):
        self.assertEqual(self.client.post("/api/tasks/", "bad-json", content_type="application/json").status_code, 400)
        self.assertEqual(self.post("tasks/", []).status_code, 400)
        self.assertEqual(self.client.get("/api/auth/login/").status_code, 405)

    def test_login_trims_username_but_preserves_password_spaces(self):
        self.client.logout()
        self.assertEqual(self.post("auth/login/", {"username": " api-user ", "password": "12345678"}).status_code, 200)
        self.client.logout()
        get_user_model().objects.create_user("space-password", password=" spaced password ")
        self.assertEqual(self.post("auth/login/", {"username": "space-password", "password": " spaced password "}).status_code, 200)
        self.client.logout()
        self.assertEqual(self.post("auth/login/", {"username": "space-password", "password": "spaced password"}).status_code, 400)

    def test_django_home_does_not_depend_on_an_old_next_frontend_setting(self):
        from django.test import override_settings
        with override_settings(FRONTEND_URL="http://127.0.0.1:3000"):
            response = self.client.get("/")
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'static/web/app.js')
            self.assertNotIn('Location', response.headers)

    def test_new_themes_and_natural_journal_reanalysis(self):
        for theme in ("ember", "midnight"):
            self.assertEqual(self.post("theme/", {"theme": theme}).status_code, 200)
            self.assertEqual(self.client.get("/api/session/").json()["user"]["theme"], theme)
        response = self.post("journal/", {"raw_text": "Today I need to review my notes. أبغى أجهز العرض"})
        self.assertEqual(response.status_code, 201)
        entry = response.json()
        self.assertEqual(entry["pending_count"], 2)
        self.post(f"suggestions/{entry['suggestions'][0]['id']}/", {"action": "accept"})
        updated = self.post(f"journal/{entry['id']}/", {"action": "analyze"}).json()
        self.assertEqual(updated["pending_count"], 1)
        self.assertEqual(len(updated["suggestions"]), 2)
        self.assertEqual(Task.objects.filter(user=self.user).count(), 1)

    def test_past_dates_cannot_bypass_api_or_suggestion_acceptance(self):
        past = timezone.localdate() - timedelta(days=1)
        response = self.post("tasks/", {"title": "Past", "date": past.isoformat()})
        self.assertEqual(response.status_code, 400)
        entry = JournalEntry.objects.create(user=self.user, raw_text="Older note")
        suggestion = TaskSuggestion.objects.create(user=self.user, entry=entry, title="Old suggestion", date=past)
        self.assertEqual(self.post(f"suggestions/{suggestion.pk}/", {"action": "accept"}).status_code, 400)
        suggestion.refresh_from_db()
        self.assertEqual(suggestion.status, "pending")
        self.assertEqual(Task.objects.filter(user=self.user).count(), 0)

    def test_login_keeps_the_theme_selected_on_the_login_screen(self):
        UserPreferences.objects.create(user=self.user, theme="grove")
        self.client.logout()
        response = self.post("auth/login/", {"username": "api-user", "password": "12345678", "theme": "ember"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["theme"], "ember")
        self.assertEqual(UserPreferences.objects.get(user=self.user).theme, "ember")

    def test_calendar_includes_undated_tasks_and_full_journals_on_their_local_day(self):
        local_day = timezone.localdate()
        task = Task.objects.create(user=self.user, title="Unscheduled")
        long_text = "A long personal note " * 40
        entry = JournalEntry.objects.create(user=self.user, raw_text=long_text, clean_text=long_text)
        private = Task.objects.create(user=self.other, title="Private unscheduled")
        response = self.client.get(f"/api/calendar/?year={local_day.year}&month={local_day.month}").json()
        tasks = {item["id"]: item for item in response["tasks"]}
        self.assertIn(task.pk, tasks)
        self.assertNotIn(private.pk, tasks)
        self.assertEqual(tasks[task.pk]["calendar_date"], local_day.isoformat())
        self.assertEqual(response["entries"][0]["clean_text"], long_text)
        day = next(item for item in response["days"] if item["date"] == local_day.isoformat())
        self.assertEqual(day["total"], 1)
        self.assertTrue(day["has_journal"])

    def test_arabic_validation_is_scoped_to_the_request(self):
        response = self.client.post("/api/tasks/", data="{}", content_type="application/json", HTTP_X_MAWJ_LANGUAGE="ar")
        self.assertEqual(response.status_code, 400)
        self.assertNotEqual(response.json()["fields"]["title"][0], "This field is required.")
        response = self.post("tasks/", {})
        self.assertEqual(response.json()["fields"]["title"][0], "This field is required.")
