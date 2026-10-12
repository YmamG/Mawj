from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from journal.models import JournalEntry
from tasks.models import Task


class CalendarViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.alice = user_model.objects.create_user("alice", password="pw12345!")
        self.bob = user_model.objects.create_user("bob", password="pw12345!")
        self.today = timezone.localdate()
        JournalEntry.objects.create(user=self.alice, raw_text="Alice's note")
        JournalEntry.objects.create(user=self.bob, raw_text="Bob's private note")
        Task.objects.create(user=self.alice, title="Finished task", date=self.today, status="done")
        Task.objects.create(user=self.alice, title="Pending task", date=self.today)
        Task.objects.create(user=self.bob, title="Bob's private task", date=self.today)
        self.client.force_login(self.alice)

    def test_month_shows_only_current_users_data_and_task_counts(self):
        response = self.client.get(reverse(
            "calendar_month",
            args=[self.today.year, self.today.month],
        ))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Journal entry")
        self.assertContains(response, "1 / 2 tasks completed")
        self.assertNotContains(response, "Bob's private note")
        self.assertNotContains(response, "Bob's private task")

    def test_day_shows_only_current_users_journal_and_tasks(self):
        response = self.client.get(reverse(
            "calendar_day",
            args=[self.today.year, self.today.month, self.today.day],
        ))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alice&#x27;s note")
        self.assertContains(response, "Finished task")
        self.assertContains(response, "Pending task")
        self.assertNotContains(response, "Bob's private")

    def test_invalid_calendar_date_returns_not_found(self):
        response = self.client.get(reverse("calendar_day", args=[2026, 2, 30]))
        self.assertEqual(response.status_code, 404)

    def test_invalid_month_returns_not_found(self):
        response = self.client.get(reverse("calendar_month", args=[2026, 13]))
        self.assertEqual(response.status_code, 404)

    def test_calendar_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("calendar"))
        self.assertEqual(response.status_code, 302)