from datetime import timedelta

from django.contrib.auth import get_user_model
from unittest.mock import patch

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from tasks.models import Task
from .forms import GoalForm, StepForm
from .models import Goal, GoalStep
from .services import goal_data, owned_goals


class GoalTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="goal-owner", password="Fictional123!")
        self.other = get_user_model().objects.create_user(username="goal-other", password="Fictional123!")
        self.client.force_login(self.user)
        self.goal = Goal.objects.create(user=self.user, title="Learn a new skill")
        self.today = timezone.localdate()

    def url(self, name="goal_detail", **kwargs):
        return reverse(name, kwargs={"pk": self.goal.pk, **kwargs})

    def progress(self):
        return goal_data(owned_goals(self.user).get(pk=self.goal.pk))

    def test_authentication_and_csrf(self):
        self.client.logout()
        self.assertRedirects(self.client.get(reverse("goals_home")), "/login/?next=/app/goals/", fetch_redirect_response=False)
        secure = Client(enforce_csrf_checks=True)
        secure.force_login(self.user)
        self.assertEqual(secure.post(reverse("goals_home"), {"title": "Forbidden"}).status_code, 403)

    def test_title_only_create_and_forged_owner_ignored(self):
        response = self.client.post(reverse("goals_home"), {"title": "My future", "user": self.other.pk}, HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 201)
        created = Goal.objects.get(title="My future")
        self.assertEqual(created.user, self.user)
        self.assertEqual(created.category, "personal")
        self.assertEqual(response.json()["redirect"], reverse("goal_detail", args=[created.pk]))

    def test_other_owner_and_staff_cannot_access_content_or_mutate(self):
        step = GoalStep.objects.create(goal=self.goal, title="Private step")
        self.other.is_staff = self.other.is_superuser = True
        self.other.save()
        self.client.force_login(self.other)
        for name, kwargs in [("goal_detail", {}), ("goal_delete", {}), ("goal_add_step", {}), ("goal_ai_plan", {}), ("goal_step_action", {"step_pk": step.pk})]:
            url = self.url(name, **kwargs)
            self.assertEqual(self.client.post(url, {"action": "toggle", "title": "Intrusion", "confirm": "yes"}).status_code, 404)
        self.assertEqual(self.client.get(self.url()).status_code, 404)
        response = self.client.get(reverse("goals_home"))
        self.assertNotContains(response, self.goal.title)
        self.assertEqual(response.context["summary"]["total"], 0)
        self.assertTrue(Goal.objects.filter(pk=self.goal.pk).exists())

    def test_date_validation_and_unchanged_overdue_edit(self):
        past, future = self.today - timedelta(days=1), self.today + timedelta(days=5)
        self.assertFalse(GoalForm({"title": "Past", "target_date": past}).is_valid())
        self.goal.target_date = past
        self.goal.save()
        self.assertTrue(GoalForm({"title": "Renamed", "target_date": past}, instance=self.goal).is_valid())
        self.assertFalse(StepForm({"title": "Past", "target_date": past}, goal=self.goal).is_valid())
        self.goal.target_date = future
        self.goal.save()
        self.assertFalse(StepForm({"title": "Too late", "target_date": future + timedelta(days=1)}, goal=self.goal).is_valid())
        GoalStep.objects.create(goal=self.goal, title="Plan", target_date=future)
        self.assertFalse(GoalForm({"title": "Earlier", "target_date": self.today}, instance=self.goal).is_valid())

    def test_progress_follows_steps_and_filters(self):
        first = GoalStep.objects.create(goal=self.goal, title="Start")
        second = GoalStep.objects.create(goal=self.goal, title="Finish")
        self.assertEqual(self.progress()["progress"], 0)
        for step, expected in [(first, 50), (second, 100)]:
            response = self.client.post(self.url("goal_step_action", step_pk=step.pk), {"action": "toggle"}, HTTP_ACCEPT="application/json")
            self.assertEqual(response.status_code, 200)
            self.assertIn("html", response.json())
            self.assertEqual(self.progress()["progress"], expected)
        self.assertEqual(self.progress()["state"], "achieved")
        self.assertEqual(self.client.get(reverse("goals_home") + "?state=achieved").context["summary"]["achieved"], 1)
        self.assertEqual(len(self.client.get(reverse("goals_home") + "?state=active").context["cards"]), 0)
        self.client.post(self.url("goal_step_action", step_pk=first.pk), {"action": "toggle"})
        self.assertEqual(self.progress()["state"], "active")

    def test_manual_completion_pause_and_new_step(self):
        self.client.post(self.url(), {"action": "pause"})
        self.assertEqual(self.progress()["state"], "paused")
        self.client.post(self.url(), {"action": "pause"})
        self.client.post(self.url(), {"action": "complete"})
        self.assertEqual(self.progress()["progress"], 100)
        self.client.post(self.url("goal_add_step"), {"title": "Another step"})
        self.assertEqual(self.progress()["progress"], 0)
        self.assertEqual(self.client.post(self.url(), {"action": "complete"}).status_code, 400)

    def test_task_link_idempotent_and_bidirectional_completion(self):
        step = GoalStep.objects.create(goal=self.goal, title="Practice")
        url = self.url("goal_step_action", step_pk=step.pk)
        for _ in range(2):
            self.assertEqual(self.client.post(url, {"action": "task"}).status_code, 302)
        self.assertEqual(Task.objects.filter(user=self.user).count(), 1)
        step.refresh_from_db()
        self.client.post(url, {"action": "toggle"})
        step.task.refresh_from_db()
        self.assertEqual(step.task.status, "done")
        self.assertIsNotNone(step.task.completed_at)
        self.assertEqual(self.progress()["progress"], 100)
        self.client.post(reverse("task_toggle", args=[step.task_id]))
        self.assertEqual(self.progress()["progress"], 0)

    def test_completed_step_and_past_date_link_to_task(self):
        step = GoalStep.objects.create(goal=self.goal, title="Old plan", target_date=self.today - timedelta(days=2), is_done=True)
        self.client.post(self.url("goal_step_action", step_pk=step.pk), {"action": "task"})
        step.refresh_from_db()
        self.assertEqual(step.task.date, self.today)
        self.assertEqual(step.task.status, "done")
        self.assertEqual(self.progress()["progress"], 100)

    def test_task_deletion_preserves_step_completion(self):
        task = Task.objects.create(user=self.user, title="Done", status="done")
        step = GoalStep.objects.create(goal=self.goal, title="Done", task=task)
        task.delete()
        step.refresh_from_db()
        self.assertIsNone(step.task_id)
        self.assertTrue(step.is_done)
        self.assertEqual(self.progress()["progress"], 100)

    def test_goal_and_step_deletion_keep_task_and_require_confirmation(self):
        task = Task.objects.create(user=self.user, title="Independent task")
        step = GoalStep.objects.create(goal=self.goal, title="Step", task=task)
        self.client.post(self.url("goal_step_action", step_pk=step.pk), {"action": "delete"})
        self.assertTrue(Task.objects.filter(pk=task.pk).exists())
        GoalStep.objects.create(goal=self.goal, title="Step again", task=task)
        self.client.get(self.url("goal_delete"))
        self.client.post(self.url("goal_delete"))
        self.assertTrue(Goal.objects.filter(pk=self.goal.pk).exists())
        self.client.post(self.url("goal_delete"), {"confirm": "yes"})
        self.assertFalse(Goal.objects.filter(pk=self.goal.pk).exists())
        self.assertTrue(Task.objects.filter(pk=task.pk).exists())

    def test_invalid_ajax_form_and_escaped_content(self):
        response = self.client.post(reverse("goals_home"), {"title": ""}, HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("field-error", response.json()["html"])
        self.goal.title = '<script>alert("x")</script>'
        self.goal.why = '<img src=x onerror=alert(1)>'
        self.goal.save()
        response = self.client.get(self.url(), HTTP_ACCEPT="application/json")
        self.assertNotIn(self.goal.title, response.json()["html"])
        self.assertIn("&lt;script&gt;", response.json()["html"])

    def test_arabic_navigation_and_horizon_and_pagination(self):
        self.client.cookies["mawj-language"] = "ar"
        self.goal.target_date = self.today + timedelta(days=7)
        self.goal.save()
        for i in range(10):
            Goal.objects.create(user=self.user, title=f"Goal {i}")
        response = self.client.get(reverse("goals_home"))
        self.assertContains(response, "الأهداف")
        self.assertContains(response, "ما الهدف الذي تريد الوصول إليه؟")
        self.assertContains(response, 'class="goal-quick-stats"')
        self.assertNotContains(response, 'class="goal-horizon"')
        self.assertEqual(len(response.context["cards"]), 9)
        self.assertEqual(len(response.context["horizon"]), 1)
        self.assertEqual(response.context["summary"]["total"], 11)

    @override_settings(AI_PROVIDER="demo")
    def test_ai_demo_suggests_without_saving_then_accepts_selected_steps(self):
        url = self.url("goal_ai_plan")
        detail = self.client.get(self.url())
        self.assertContains(detail, "Demo mode")
        self.assertContains(detail, "generated locally")
        suggested = self.client.post(url, {"action": "suggest"})
        self.assertEqual(suggested.status_code, 200)
        self.assertEqual(suggested.json()["provider"], "demo")
        self.assertEqual(len(suggested.json()["suggestions"]), 4)
        self.assertEqual(self.goal.steps.count(), 0)

        accepted = self.client.post(
            url,
            {"action": "accept", "steps": '["Define success", "Take the first action"]'},
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(accepted.status_code, 200)
        self.assertEqual(set(self.goal.steps.values_list("title", flat=True)), {"Define success", "Take the first action"})
        self.assertIn("Suggested steps added.", accepted.json()["notice"])

    @override_settings(AI_PROVIDER="demo")
    def test_ai_accept_is_validated_deduplicated_and_reopens_goal(self):
        url = self.url("goal_ai_plan")
        GoalStep.objects.create(goal=self.goal, title="Existing")
        self.goal.marked_complete = True
        self.goal.save(update_fields=["marked_complete"])
        response = self.client.post(url, {"action": "accept", "steps": '["existing", "New", "new"]'}, HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.goal.steps.count(), 2)
        self.goal.refresh_from_db()
        self.assertFalse(self.goal.marked_complete)
        for invalid in ("not-json", "[]", '["' + "x" * 201 + '"]', "[1]"):
            self.assertEqual(self.client.post(url, {"action": "accept", "steps": invalid}).status_code, 400)

    @override_settings(AI_PROVIDER="manual")
    def test_ai_manual_mode_reports_that_suggestions_are_off(self):
        response = self.client.post(self.url("goal_ai_plan"), {"action": "suggest"})
        self.assertEqual(response.status_code, 422)
        self.assertIn("off", response.json()["error"])

    @override_settings(AI_PROVIDER="gemini")
    def test_cloud_goal_plan_requires_explicit_send_action(self):
        detail = self.client.get(self.url())
        self.assertContains(detail, "Step suggestions from")
        self.assertContains(detail, "Gemini")
        with patch("goals.views.suggest_goal_steps", return_value={"steps": [{"title": "One"}]}) as suggest:
            denied = self.client.post(self.url("goal_ai_plan"), {"action": "suggest"})
            allowed = self.client.post(self.url("goal_ai_plan"), {"action": "suggest", "consent": "yes"})
        self.assertEqual(denied.status_code, 400)
        self.assertEqual(allowed.status_code, 200)
        suggest.assert_called_once()

    @override_settings(AI_PROVIDER="demo")
    def test_ai_endpoint_requires_csrf(self):
        secure = Client(enforce_csrf_checks=True)
        secure.force_login(self.user)
        self.assertEqual(secure.post(self.url("goal_ai_plan"), {"action": "suggest"}).status_code, 403)
