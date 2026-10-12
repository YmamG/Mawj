from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Task

User = get_user_model()


class TaskViewTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice", password="pw12345!")
        self.bob = User.objects.create_user("bob", password="pw12345!")
        self.bobs_task = Task.objects.create(user=self.bob, title="Bob secret")
        self.client.login(username="alice", password="pw12345!")

    def test_login_required(self):
        self.client.logout()
        r = self.client.get(reverse("task_list"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/accounts/login/", r.url)

    def test_create_assigns_request_user_and_list_is_private(self):
        r = self.client.post(reverse("task_create"), {
            "title": "Alice task", "description": "d", "date": "2026-10-05",
            "start_time": "09:00", "deadline": "2026-10-05T17:00",
            "estimated_duration": 45, "priority": "high"})
        self.assertEqual(r.status_code, 302)
        t = Task.objects.get(title="Alice task")
        self.assertEqual(t.user, self.alice)
        page = self.client.get(reverse("task_list")).content.decode()
        self.assertIn("Alice task", page)
        self.assertIn("45 min", page)
        self.assertNotIn("Bob secret", page)

    def test_cannot_touch_other_users_task(self):
        pk = self.bobs_task.pk
        for name in ("task_update", "task_delete"):
            self.assertEqual(self.client.get(reverse(name, args=[pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("task_toggle", args=[pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("task_delete", args=[pk])).status_code, 404)
        self.assertTrue(Task.objects.filter(pk=pk).exists())

    def test_edit(self):
        t = Task.objects.create(user=self.alice, title="Old")
        self.client.post(reverse("task_update", args=[t.pk]), {"title": "New", "priority": "low"})
        t.refresh_from_db()
        self.assertEqual((t.title, t.priority), ("New", "low"))

    def test_toggle_sets_and_clears_completed_at(self):
        t = Task.objects.create(user=self.alice, title="T")
        self.client.post(reverse("task_toggle", args=[t.pk]))
        t.refresh_from_db()
        self.assertEqual(t.status, "done")
        self.assertIsNotNone(t.completed_at)
        self.client.post(reverse("task_toggle", args=[t.pk]))
        t.refresh_from_db()
        self.assertEqual(t.status, "todo")
        self.assertIsNone(t.completed_at)

    def test_toggle_rejects_get(self):
        t = Task.objects.create(user=self.alice, title="T")
        self.assertEqual(self.client.get(reverse("task_toggle", args=[t.pk])).status_code, 405)

    def test_delete(self):
        t = Task.objects.create(user=self.alice, title="T")
        self.client.post(reverse("task_delete", args=[t.pk]))
        self.assertFalse(Task.objects.filter(pk=t.pk).exists())

    def test_edit_form_prefills_deadline(self):
        t = Task.objects.create(user=self.alice, title="T", deadline="2026-10-05T17:00:00+03:00")
        page = self.client.get(reverse("task_update", args=[t.pk])).content.decode()
        self.assertIn('value="2026-10-05T17:00"', page)


class SignupTests(TestCase):
    def test_signup_logs_in_and_redirects_to_tasks(self):
        r = self.client.post(reverse("signup"), {
            "username": "sara", "password1": "Str0ng-pass!9", "password2": "Str0ng-pass!9"})
        self.assertRedirects(r, reverse("task_list"))
        self.assertEqual(self.client.get(reverse("task_list")).status_code, 200)


class SimpleTaskFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("simple")
        self.client.force_login(self.user)

    def test_title_only_saves_with_default_priority(self):
        response = self.client.post(reverse("task_create"), {"title": "One thing"})
        self.assertEqual(response.status_code, 302)
        task = Task.objects.get(user=self.user)
        self.assertEqual(task.priority, "medium")
        self.assertIsNone(task.date)

    def test_details_collapsed_initially_and_open_for_errors(self):
        response = self.client.get(reverse("task_create"))
        self.assertNotContains(response, 'class="task-details" open')
        response = self.client.post(reverse("task_create"), {"title": "Task", "estimated_duration": "wrong"})
        self.assertContains(response, 'class="task-details" open')
        self.assertEqual(Task.objects.count(), 0)


class TaskFilteringTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("filters")
        self.other = User.objects.create_user("private")
        self.client.force_login(self.user)
        for index in range(12):
            Task.objects.create(user=self.user, title=f"Study {index}", status="done", priority="high")
        Task.objects.create(user=self.user, title="Shopping", priority="low")
        Task.objects.create(user=self.other, title="Study private", status="done", priority="high")

    def test_combined_filters_pagination_and_privacy(self):
        response = self.client.get(reverse("task_list"), {"q": "Study", "status": "done", "priority": "high"})
        self.assertEqual(response.context["page_obj"].paginator.count, 12)
        self.assertEqual(len(response.context["tasks"]), 10)
        self.assertNotContains(response, "Study private")
        self.assertContains(response, "q=Study")
        response = self.client.get(reverse("task_list"), {"q": "Study", "page": 2})
        self.assertEqual(len(response.context["tasks"]), 2)

    def test_no_results_and_invalid_query_parameters(self):
        response = self.client.get(reverse("task_list"), {"q": "unmatched"})
        self.assertContains(response, "No tasks match your filters")
        response = self.client.get(reverse("task_list"), {"status": "bad", "priority": "bad", "page": "bad"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].paginator.count, 13)

    def test_duration_limits(self):
        for value in ("0", "-1", "1441"):
            response = self.client.post(reverse("task_create"), {"title": "Invalid", "estimated_duration": value})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context["form"].errors)
        self.assertFalse(Task.objects.filter(title="Invalid").exists())
        self.assertEqual(self.client.post(reverse("task_create"), {"title": "Valid", "estimated_duration": "1440"}).status_code, 302)


class DemoDataTests(TestCase):
    def test_seed_is_repeatable_and_preserves_existing_data(self):
        from io import StringIO
        from unittest.mock import patch
        from django.core.management import call_command
        with patch.dict("os.environ", {"MAWJ_DEMO_PASSWORD": "Fictional-Only!93"}):
            call_command("seed_demo", stdout=StringIO())
            call_command("seed_demo", stdout=StringIO())
        user = User.objects.get(username="mawj_demo")
        self.assertTrue(user.check_password("Fictional-Only!93"))
        self.assertEqual(Task.objects.filter(user=user).count(), 13)
        self.assertEqual(user.journal_entries.count(), 2)
        self.assertEqual(user.task_suggestions.filter(status="pending").count(), 2)
