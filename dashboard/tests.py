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

class AchievementTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("progress")
        self.other = get_user_model().objects.create_user("other")
        self.client.force_login(self.user)

    def test_periods_boundaries_and_privacy(self):
        from datetime import date
        from unittest.mock import patch

        for scheduled, status in [
            (date(2026, 10, 11), "done"),
            (date(2026, 10, 17), "todo"),
            (date(2026, 10, 18), "done"),
            (date(2026, 10, 1), "todo"),
            (date(2026, 1, 1), "done"),
            (date(2025, 12, 31), "done"),
            (date(2027, 1, 1), "done"),
        ]:
            Task.objects.create(user=self.user, title="Task", date=scheduled, status=status)
        Task.objects.create(user=self.other, title="Private", date=date(2026, 10, 11), status="done")
        with patch("dashboard.views.timezone.localdate", return_value=date(2026, 10, 12)):
            for period, total, completed, percentage in [
                ("week", 2, 1, 50), ("month", 4, 2, 50), ("year", 5, 3, 60),
            ]:
                with self.subTest(period=period):
                    response = self.client.get(reverse("achievements"), {"period": period})
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.context["total"], total)
                    self.assertEqual(response.context["completed"], completed)
                    self.assertEqual(response.context["percentage"], percentage)
                    self.assertContains(response, f"{percentage}%")

    def test_undated_tasks_use_local_creation_date(self):
        from datetime import date, datetime, timezone as datetime_timezone
        from unittest.mock import patch

        task = Task.objects.create(user=self.user, title="Undated", status="done")
        # Sunday in Riyadh, still Saturday in UTC.
        Task.objects.filter(pk=task.pk).update(created_at=datetime(2026, 10, 10, 22, tzinfo=datetime_timezone.utc))
        with patch("dashboard.views.timezone.localdate", return_value=date(2026, 10, 12)):
            response = self.client.get(reverse("achievements"))
        self.assertEqual(response.context["completed"], 1)
        self.assertEqual(response.context["percentage"], 100)

    def test_empty_invalid_period_and_login(self):
        response = self.client.get(reverse("achievements"), {"period": "invalid"})
        self.assertEqual(response.context["period"], "week")
        self.assertEqual(response.context["percentage"], 0)
        self.assertContains(response, "No tasks in this period yet")
        self.client.logout()
        self.assertEqual(self.client.get(reverse("achievements")).status_code, 302)
