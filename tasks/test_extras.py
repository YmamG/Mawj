from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Task


class ExtraTaskFeaturesTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("extras")
        self.other = get_user_model().objects.create_user("other-extras")
        self.client.force_login(self.user)
        self.today = timezone.localdate()

    def test_categories_filter_and_invalid_values(self):
        Task.objects.create(user=self.user, title="Study", category="study")
        Task.objects.create(user=self.user, title="Inbox")
        Task.objects.create(user=self.other, title="Private", category="study")
        response = self.client.get(reverse("task_list"), {"category": "study"})
        self.assertEqual([task.title for task in response.context["tasks"]], ["Study"])
        response = self.client.get(reverse("task_list"), {"category": "uncategorized"})
        self.assertEqual([task.title for task in response.context["tasks"]], ["Inbox"])
        response = self.client.post(reverse("task_create"), {"title": "Wrong", "category": "unknown"})
        self.assertIn("category", response.context["form"].errors)

    def test_custom_category_requires_a_name_and_is_preserved(self):
        response = self.client.post(reverse("task_create"), {"title": "Appointment", "category": "custom"})
        self.assertIn("custom_category", response.context["form"].errors)
        self.assertEqual(self.client.post(reverse("task_create"), {"title": "Appointment", "category": "custom", "custom_category": "Health"}).status_code, 302)
        task = Task.objects.get(title="Appointment")
        self.assertEqual((task.category, task.custom_category), ("custom", "Health"))
        self.client.post(reverse("task_update", args=[task.pk]), {"title": task.title, "category": "work", "custom_category": "Should clear"})
        task.refresh_from_db()
        self.assertEqual((task.category, task.custom_category), ("work", ""))

    def test_completed_tasks_leave_active_list_but_remain_in_archive(self):
        active = Task.objects.create(user=self.user, title="Active")
        done = Task.objects.create(user=self.user, title="Archived", status="done", completed_at=timezone.now())
        default = self.client.get(reverse("task_list"))
        self.assertEqual([task.pk for task in default.context["tasks"]], [active.pk])
        archive = self.client.get(reverse("task_list"), {"status": "done"})
        self.assertEqual([task.pk for task in archive.context["tasks"]], [done.pk])
        self.client.post(reverse("task_toggle", args=[done.pk]))
        self.assertTrue(Task.objects.filter(pk=done.pk, status="todo").exists())

    def test_daily_repeat_copies_details_and_creates_one_successor(self):
        now = timezone.now()
        task = Task.objects.create(user=self.user, title="Daily", date=self.today, repeat="daily", category="custom", custom_category="Routine", reminder_at=now, deadline=now, estimated_duration=20)
        url = reverse("task_toggle", args=[task.pk])
        self.client.post(url)
        next_task = Task.objects.get(previous_occurrence=task)
        self.assertEqual(next_task.date, self.today + timedelta(days=1))
        self.assertEqual(next_task.reminder_at, now + timedelta(days=1))
        self.assertEqual(next_task.deadline, now + timedelta(days=1))
        self.assertEqual((next_task.category, next_task.custom_category), ("custom", "Routine"))
        self.assertEqual(next_task.status, "todo")
        self.client.post(url)  # Undo does not delete a successor the user might have edited.
        self.client.post(url)
        self.assertEqual(Task.objects.filter(previous_occurrence=task).count(), 1)

    def test_weekly_repeat_skips_missed_dates_and_can_stop(self):
        task = Task.objects.create(user=self.user, title="Weekly", date=self.today - timedelta(days=21), repeat="weekly")
        self.client.post(reverse("task_toggle", args=[task.pk]))
        successor = Task.objects.get(previous_occurrence=task)
        self.assertEqual(successor.date, self.today + timedelta(days=7))
        successor.repeat = ""
        successor.save()
        self.client.post(reverse("task_toggle", args=[successor.pk]))
        self.assertFalse(Task.objects.filter(previous_occurrence=successor).exists())

    def test_repeat_needs_date_and_reminder_needs_future_time(self):
        response = self.client.post(reverse("task_create"), {"title": "Repeat", "repeat": "daily"})
        self.assertIn("date", response.context["form"].errors)
        response = self.client.post(reverse("task_create"), {"title": "Reminder", "reminder_at": "2000-01-01T09:00"})
        self.assertIn("reminder_at", response.context["form"].errors)
        future = timezone.localtime(timezone.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
        self.assertEqual(self.client.post(reverse("task_create"), {"title": "Future", "reminder_at": future}).status_code, 302)

    def test_today_sections_and_privacy(self):
        Task.objects.create(user=self.user, title="Today", date=self.today)
        Task.objects.create(user=self.user, title="Inbox")
        Task.objects.create(user=self.user, title="Overdue", date=self.today - timedelta(days=1))
        Task.objects.create(user=self.user, title="Future", date=self.today + timedelta(days=1))
        Task.objects.create(user=self.user, title="Completed", status="done", completed_at=timezone.now())
        Task.objects.create(user=self.other, title="Private", date=self.today)
        response = self.client.get(reverse("today"))
        self.assertEqual({task.title for task in response.context["tasks"]}, {"Today", "Inbox"})
        self.assertEqual(response.context["overdue_count"], 1)
        self.assertEqual(response.context["completed_count"], 1)
        response = self.client.get(reverse("today"), {"section": "overdue"})
        self.assertEqual([task.title for task in response.context["tasks"]], ["Overdue"])
        response = self.client.get(reverse("today"), {"section": "completed"})
        self.assertEqual([task.title for task in response.context["tasks"]], ["Completed"])

    def test_reminders_visibility_dismissal_and_permissions(self):
        past = timezone.now() - timedelta(minutes=1)
        due = Task.objects.create(user=self.user, title="Due", reminder_at=past)
        Task.objects.create(user=self.user, title="Not due", reminder_at=timezone.now() + timedelta(days=1))
        Task.objects.create(user=self.user, title="Done", status="done", reminder_at=past)
        private = Task.objects.create(user=self.other, title="Private", reminder_at=past)
        response = self.client.get(reverse("today"))
        self.assertEqual(response.context["due_reminder_count"], 1)
        self.assertEqual([task.title for task in response.context["reminders"]], ["Due"])
        url = reverse("reminder_dismiss", args=[due.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url)
        self.assertEqual(self.client.get(reverse("today")).context["due_reminder_count"], 0)
        self.assertEqual(self.client.post(reverse("reminder_dismiss", args=[private.pk])).status_code, 404)

    def test_editing_existing_due_reminder_is_allowed_and_rescheduling_resets_dismissal(self):
        task = Task.objects.create(user=self.user, title="Due", reminder_at=timezone.now() - timedelta(days=1), reminder_dismissed=True)
        url = reverse("task_update", args=[task.pk])
        original = timezone.localtime(task.reminder_at).strftime("%Y-%m-%dT%H:%M")
        self.assertEqual(self.client.post(url, {"title": "Edited", "reminder_at": original}).status_code, 302)
        task.refresh_from_db()
        self.assertTrue(task.reminder_dismissed)
        future = timezone.localtime(timezone.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")
        self.assertEqual(self.client.post(url, {"title": "Edited", "reminder_at": future}).status_code, 302)
        task.refresh_from_db()
        self.assertFalse(task.reminder_dismissed)

    def test_toggle_return_url_is_safe(self):
        task = Task.objects.create(user=self.user, title="Task")
        url = reverse("task_toggle", args=[task.pk])
        self.assertRedirects(self.client.post(url, {"next": reverse("today")}), reverse("today"))
        self.assertRedirects(self.client.post(url, {"next": "https://example.com"}), reverse("task_list"))

    def test_chart_totals_match_summary_for_each_period(self):
        Task.objects.create(user=self.user, title="Done", date=self.today, status="done")
        Task.objects.create(user=self.user, title="Todo", date=self.today)
        Task.objects.create(user=self.user, title="Undated", status="done")
        Task.objects.create(user=self.other, title="Private", date=self.today)
        for period, bucket_count in [("week", 7), ("month", __import__('calendar').monthrange(self.today.year, self.today.month)[1]), ("year", 12)]:
            with self.subTest(period=period):
                response = self.client.get(reverse("achievements"), {"period": period})
                self.assertEqual(response.status_code, 200)
                chart = response.context["chart"]
                self.assertEqual(len(chart), bucket_count)
                self.assertEqual(sum(row["total"] for row in chart), 3)
                self.assertEqual(sum(row["completed"] for row in chart), 2)
                self.assertEqual(response.context["percentage"], 67)

    def test_past_schedules_rejected_but_existing_overdue_tasks_can_be_edited(self):
        yesterday = (self.today - timedelta(days=1)).isoformat()
        for data in [{"date": yesterday}, {"deadline": "2000-01-01T12:00"}]:
            response = self.client.post(reverse("task_create"), {"title": "Past", **data})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context["form"].errors)
        old = Task.objects.create(user=self.user, title="Old", date=self.today-timedelta(days=2))
        response = self.client.post(reverse("task_update", args=[old.pk]), {"title": "Renamed", "date": old.date.isoformat()})
        self.assertEqual(response.status_code, 302)
        response = self.client.post(reverse("task_update", args=[old.pk]), {"title": "Renamed", "date": yesterday})
        self.assertEqual(response.status_code, 200)
        self.assertIn("date", response.context["form"].errors)
