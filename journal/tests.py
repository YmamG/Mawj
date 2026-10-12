from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from tasks.models import Task

from .models import JournalEntry, TaskSuggestion

User = get_user_model()
TEXT = "Today was long.\n- Call the bank\n* Buy milk\nI felt tired."


@override_settings(AI_PROVIDER="demo")
class JournalTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice", password="pw12345!")
        self.bob = User.objects.create_user("bob", password="pw12345!")
        self.client.login(username="alice", password="pw12345!")

    def make_entry(self):
        self.client.post(reverse("journal_create"), {"raw_text": TEXT})
        return JournalEntry.objects.get(user=self.alice)

    def test_login_required(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("journal_list")).status_code, 302)

    def test_create_saves_entry_and_suggestions_without_creating_tasks(self):
        entry = self.make_entry()
        self.assertEqual(entry.raw_text, TEXT)
        self.assertEqual(sorted(s.title for s in entry.suggestions.all()), ["Buy milk", "Call the bank"])
        self.assertEqual(Task.objects.count(), 0)  # nothing added until approval

    def test_accept_creates_task_for_request_user_once(self):
        entry = self.make_entry()
        s = entry.suggestions.get(title="Buy milk")
        self.client.post(reverse("suggestion_accept", args=[s.pk]))
        self.client.post(reverse("suggestion_accept", args=[s.pk]))  # double click
        self.assertEqual(Task.objects.filter(user=self.alice, title="Buy milk").count(), 1)
        s.refresh_from_db()
        self.assertEqual(s.status, "accepted")

    def test_dismiss_creates_no_task(self):
        entry = self.make_entry()
        s = entry.suggestions.first()
        self.client.post(reverse("suggestion_dismiss", args=[s.pk]))
        s.refresh_from_db()
        self.assertEqual(s.status, "dismissed")
        self.assertEqual(Task.objects.count(), 0)

    def test_other_users_cannot_see_or_touch_entry(self):
        entry = self.make_entry()
        s = entry.suggestions.first()
        self.client.logout()
        self.client.login(username="bob", password="pw12345!")
        self.assertNotIn("Today was long", self.client.get(reverse("journal_list")).content.decode())
        self.assertEqual(self.client.get(reverse("journal_detail", args=[entry.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("suggestion_accept", args=[s.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("journal_delete", args=[entry.pk])).status_code, 404)
        self.assertEqual(Task.objects.count(), 0)

    def test_delete(self):
        entry = self.make_entry()
        self.client.post(reverse("journal_delete", args=[entry.pk]))
        self.assertFalse(JournalEntry.objects.filter(pk=entry.pk).exists())


class ManualProviderTests(TestCase):
    @override_settings(AI_PROVIDER="manual")
    def test_manual_saves_text_and_suggests_nothing(self):
        User.objects.create_user("alice", password="pw12345!")
        self.client.login(username="alice", password="pw12345!")
        self.client.post(reverse("journal_create"), {"raw_text": TEXT})
        self.assertEqual(TaskSuggestion.objects.count(), 0)
        self.assertEqual(JournalEntry.objects.get().clean_text, TEXT)
