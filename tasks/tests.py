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
