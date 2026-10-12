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


class JournalReportingAndEditingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("editor")
        self.other = User.objects.create_user("other-editor")
        self.client.force_login(self.user)
        self.entry = JournalEntry.objects.create(user=self.user, raw_text="Original", clean_text="Original")
        for title, status in [("First", "pending"), ("Second", "pending"), ("Accepted", "accepted"), ("Dismissed", "dismissed")]:
            TaskSuggestion.objects.create(user=self.user, entry=self.entry, title=title, status=status)
        self.task = Task.objects.create(user=self.user, title="Accepted task")

    def test_annotation_search_and_zero_counts(self):
        JournalEntry.objects.create(user=self.user, raw_text="Empty", clean_text="Empty")
        JournalEntry.objects.create(user=self.other, raw_text="Private", clean_text="Private")
        response = self.client.get(reverse("journal_list"))
        self.assertEqual({entry.raw_text: entry.pending_count for entry in response.context["entries"]}, {"Original": 2, "Empty": 0})
        self.assertContains(response, "2 pending suggestions")
        response = self.client.get(reverse("journal_list"), {"q": "Original"})
        self.assertEqual(response.context["page_obj"].paginator.count, 1)
        self.assertContains(self.client.get(reverse("journal_list"), {"q": "missing"}), "No entries match")

    def test_edit_dismisses_stale_suggestions_and_preserves_tasks(self):
        response = self.client.post(reverse("journal_update", args=[self.entry.pk]), {"raw_text": "Revised"})
        self.assertRedirects(response, reverse("journal_detail", args=[self.entry.pk]))
        self.entry.refresh_from_db()
        self.assertEqual((self.entry.raw_text, self.entry.clean_text), ("Revised", "Revised"))
        self.assertEqual(self.entry.suggestions.filter(status="pending").count(), 0)
        self.assertEqual(self.entry.suggestions.filter(status="accepted").count(), 1)
        self.assertTrue(Task.objects.filter(pk=self.task.pk).exists())

    def test_invalid_edit_and_access(self):
        response = self.client.post(reverse("journal_update", args=[self.entry.pk]), {"raw_text": ""})
        self.assertEqual(response.status_code, 200)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.raw_text, "Original")
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse("journal_update", args=[self.entry.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("journal_update", args=[self.entry.pk]), {"raw_text": "Private edit"}).status_code, 404)

    def test_delete_cascades_suggestions_but_keeps_tasks(self):
        self.assertContains(self.client.get(reverse("journal_delete", args=[self.entry.pk])), "Tasks you already accepted will remain")
        self.client.post(reverse("journal_delete", args=[self.entry.pk]))
        self.assertFalse(TaskSuggestion.objects.filter(entry_id=self.entry.pk).exists())
        self.assertTrue(Task.objects.filter(pk=self.task.pk).exists())
