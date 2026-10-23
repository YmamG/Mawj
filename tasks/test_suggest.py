import json
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from ai import provider

from .models import Task

User = get_user_model()


def fake_response(body):
    r = MagicMock()
    r.status_code = 200
    r.json.return_value = body
    return r


class ParseTaskReplyTests(SimpleTestCase):
    def test_good_reply(self):
        r = provider.parse_task_reply('{"priority": "HIGH", "estimated_duration": 45}')
        self.assertEqual(r, {"priority": "high", "estimated_duration": 45})

    def test_partly_bad_reply_keeps_the_good_part(self):
        r = provider.parse_task_reply('{"priority": "urgent", "estimated_duration": "30"}')
        self.assertEqual(r, {"priority": None, "estimated_duration": 30})

    def test_unusable_replies_raise(self):
        for bad in ("nope", "[]", '{"priority": "x", "estimated_duration": 0}', '{"estimated_duration": 99999}'):
            with self.assertRaises(provider.AIProviderError):
                provider.parse_task_reply(bad)


class SuggestButtonTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice", password="pw12345!")
        self.bob = User.objects.create_user("bob", password="pw12345!")
        self.client.login(username="alice", password="pw12345!")

    def post_suggest(self, url, **extra):
        data = {"title": "Write report", "description": "Quarterly numbers", "suggest": "1"}
        data.update(extra)
        return self.client.post(url, data)

    @override_settings(AI_PROVIDER="demo")
    def test_create_form_gets_values_and_nothing_is_saved(self):
        r = self.post_suggest(reverse("task_create"), date="2026-10-20", deadline="2026-10-20T17:00")
        self.assertEqual(r.status_code, 200)
        html = r.content.decode()
        self.assertIn('value="30"', html)                       # duration filled in
        self.assertIn('<option value="medium" selected>', html)
        self.assertIn('value="Write report"', html)             # what the user typed is kept
        self.assertIn('value="2026-10-20"', html)
        self.assertIn('value="2026-10-20T17:00"', html)
        self.assertIn("Review it", html)
        self.assertEqual(Task.objects.count(), 0)

    @override_settings(AI_PROVIDER="gemini")
    def test_real_provider_reply_fills_the_form(self):
        body = {"candidates": [{"content": {"parts": [{"text": json.dumps(
            {"priority": "high", "estimated_duration": 90})}]}}]}
        with patch.dict("os.environ", {"GEMINI_API_KEY": "k", "GEMINI_MODEL": "gemini-2.5-flash"}), \
                patch("ai.provider.requests.post", return_value=fake_response(body)) as post:
            r = self.post_suggest(reverse("task_create"))
        html = r.content.decode()
        self.assertIn('value="90"', html)
        self.assertIn('<option value="high" selected>', html)
        self.assertIn("Write report", post.call_args.kwargs["json"]["contents"][0]["parts"][0]["text"])
        self.assertContains(r, "sends the title and description to gemini")
        self.assertEqual(Task.objects.count(), 0)

    @override_settings(AI_PROVIDER="manual")
    def test_ai_off_shows_message_and_keeps_input(self):
        r = self.post_suggest(reverse("task_create"))
        self.assertContains(r, "AI could not help")
        self.assertContains(r, 'value="Write report"')

    @override_settings(AI_PROVIDER="claude")
    def test_missing_key_shows_message(self):
        with patch.dict("os.environ", {}, clear=True):
            r = self.post_suggest(reverse("task_create"))
        self.assertContains(r, "ANTHROPIC_API_KEY")
        self.assertEqual(Task.objects.count(), 0)

    @override_settings(AI_PROVIDER="demo")
    def test_empty_title_asks_for_title(self):
        r = self.post_suggest(reverse("task_create"), title="")
        self.assertContains(r, "Write a title first")

    @override_settings(AI_PROVIDER="demo")
    def test_edit_form_suggest_does_not_change_the_saved_task(self):
        t = Task.objects.create(user=self.alice, title="Old", priority="low", estimated_duration=5)
        r = self.post_suggest(reverse("task_update", args=[t.pk]))
        self.assertContains(r, 'value="30"')
        t.refresh_from_db()
        self.assertEqual((t.title, t.priority, t.estimated_duration), ("Old", "low", 5))

    @override_settings(AI_PROVIDER="demo")
    def test_cannot_suggest_on_other_users_task(self):
        t = Task.objects.create(user=self.bob, title="Bob task")
        self.assertEqual(self.post_suggest(reverse("task_update", args=[t.pk])).status_code, 404)

    @override_settings(AI_PROVIDER="demo")
    def test_normal_save_still_works(self):
        r = self.client.post(reverse("task_create"), {"title": "Plain", "priority": "high", "estimated_duration": 20})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Task.objects.get().estimated_duration, 20)

    @override_settings(AI_PROVIDER="demo")
    def test_login_required(self):
        self.client.logout()
        r = self.post_suggest(reverse("task_create"))
        self.assertEqual(r.status_code, 302)
