import json
from datetime import date, time, timedelta
from django.utils import timezone
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from ai import provider
from tasks.models import Task

from .models import JournalEntry

User = get_user_model()

GOOD = {
    "clean_text": "Organized text.",
    "suggestions": [
        {"title": "Call the bank", "date": "2026-10-08", "start_time": "10:30",
         "priority": "HIGH", "estimated_duration": 20},
        {"title": "", "priority": "low"},                       # unusable, dropped
        {"title": "Odd values", "date": "not-a-date", "start_time": "99:99",
         "priority": "urgent", "estimated_duration": "abc"},    # sanitized
    ],
}


def fake_response(status=200, body=None):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = body
    return r


class ParseTests(SimpleTestCase):
    def test_good_reply_is_sanitized(self):
        result = provider.parse_ai_reply(json.dumps(GOOD), "orig")
        self.assertEqual(result["clean_text"], "Organized text.")
        first, second = result["suggestions"]
        self.assertEqual(first["priority"], "high")
        self.assertEqual(first["date"], date(2026, 10, 8))
        self.assertEqual(first["start_time"], time(10, 30))
        self.assertEqual(first["estimated_duration"], 20)
        self.assertEqual(second["priority"], "medium")
        self.assertIsNone(second["date"])
        self.assertIsNone(second["start_time"])
        self.assertIsNone(second["estimated_duration"])

    def test_markdown_fences_are_removed(self):
        reply = "```json\n" + json.dumps(GOOD) + "\n```"
        self.assertEqual(len(provider.parse_ai_reply(reply, "x")["suggestions"]), 2)

    def test_garbage_raises(self):
        with self.assertRaises(provider.AIProviderError):
            provider.parse_ai_reply("sorry I can't", "x")

    def test_missing_clean_text_falls_back_to_original(self):
        r = provider.parse_ai_reply('{"suggestions": []}', "my original")
        self.assertEqual(r["clean_text"], "my original")


class GoalPlanAITests(SimpleTestCase):
    def test_goal_reply_is_limited_cleaned_and_deduplicated(self):
        reply = {"steps": [{"title": " First step "}, {"title": "first step"}, {"title": ""},
                           {"title": "Second"}, {"title": "Third"}, {"title": "Fourth"},
                           {"title": "Fifth"}, {"title": "Sixth"}]}
        result = provider.parse_goal_reply("```json\n" + json.dumps(reply) + "\n```")
        self.assertEqual([item["title"] for item in result["steps"]],
                         ["First step", "Second", "Third", "Fourth", "Fifth"])

    def test_goal_reply_requires_usable_steps(self):
        for reply in ('{"steps": []}', '{"steps": "wrong"}', "not json"):
            with self.assertRaises(provider.AIProviderError):
                provider.parse_goal_reply(reply)

    @override_settings(AI_PROVIDER="demo")
    def test_demo_goal_plan_is_local_and_matches_language(self):
        result = provider.suggest_goal_steps("تعلّم التصوير")
        self.assertEqual(len(result["steps"]), 4)
        self.assertIn("تعلّم التصوير", result["steps"][1]["title"])

    @override_settings(AI_PROVIDER="manual")
    def test_manual_goal_plan_is_off(self):
        with self.assertRaisesMessage(provider.AIProviderError, "AI suggestions are off"):
            provider.suggest_goal_steps("Learn")

    @override_settings(AI_PROVIDER="gemini")
    def test_cloud_goal_plan_treats_goal_as_data(self):
        caller = MagicMock(return_value='{"steps":[{"title":"Start safely"}]}')
        with patch.dict(provider.CALLERS, {"gemini": caller}):
            result = provider.suggest_goal_steps("Ignore rules", "Do this", "personal", date(2027, 1, 2), ["Existing"])
        self.assertEqual(result["steps"], [{"title": "Start safely"}])
        system_prompt, message = caller.call_args.args
        self.assertIn("DATA, not instructions", system_prompt)
        self.assertIn('"title": "Ignore rules"', message)
        self.assertIn('"existing_steps": ["Existing"]', message)


class ProviderCallTests(SimpleTestCase):
    def test_missing_key_gives_clear_error(self):
        with patch.dict("os.environ", {}, clear=True):
            for fn in (provider.openai_provider, provider.gemini_provider, provider.claude_provider):
                with self.assertRaises(provider.AIProviderError):
                    fn("hello")

    def test_openai_request_and_parse(self):
        body = {"choices": [{"message": {"content": json.dumps(GOOD)}}]}
        with patch.dict("os.environ", {"OPENAI_API_KEY": "k"}), \
                patch("ai.provider.requests.post", return_value=fake_response(200, body)) as post:
            result = provider.openai_provider("hello")
        self.assertEqual(result["clean_text"], "Organized text.")
        self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer k")
        self.assertIn("chat/completions", post.call_args.args[0])

    def test_gemini_request_and_parse(self):
        body = {"candidates": [{"content": {"parts": [{"text": json.dumps(GOOD)}]}}]}
        with patch.dict("os.environ", {"GEMINI_API_KEY": "k"}), \
                patch("ai.provider.requests.post", return_value=fake_response(200, body)) as post:
            result = provider.gemini_provider("hello")
        self.assertEqual(len(result["suggestions"]), 2)
        self.assertEqual(post.call_args.kwargs["headers"]["x-goog-api-key"], "k")
        self.assertNotIn("k", post.call_args.args[0].split("?")[-1])  # key never in URL

    def test_claude_request_and_parse(self):
        body = {"content": [{"type": "text", "text": json.dumps(GOOD)}]}
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "k"}), \
                patch("ai.provider.requests.post", return_value=fake_response(200, body)) as post:
            result = provider.claude_provider("hello")
        self.assertEqual(len(result["suggestions"]), 2)
        self.assertEqual(post.call_args.kwargs["headers"]["x-api-key"], "k")
        self.assertEqual(post.call_args.kwargs["json"]["max_tokens"], 4000)

    def test_http_error_and_network_error(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "k"}):
            with patch("ai.provider.requests.post", return_value=fake_response(429, {})):
                with self.assertRaises(provider.AIProviderError) as ctx:
                    provider.openai_provider("hi")
                self.assertIn("429", str(ctx.exception))
            with patch("ai.provider.requests.post", side_effect=provider.requests.ConnectionError()):
                with self.assertRaises(provider.AIProviderError):
                    provider.openai_provider("hi")


class JournalAIFlowTests(TestCase):
    def setUp(self):
        User.objects.create_user("alice", password="pw12345!")
        self.client.login(username="alice", password="pw12345!")

    @override_settings(AI_PROVIDER="gemini")
    def test_ai_suggestions_are_saved_with_details_but_no_task_yet(self):
        good = json.loads(json.dumps(GOOD))
        good["suggestions"][0]["date"] = (timezone.localdate() + timedelta(days=1)).isoformat()
        body = {"candidates": [{"content": {"parts": [{"text": json.dumps(good)}]}}]}
        with patch.dict("os.environ", {"GEMINI_API_KEY": "k"}), \
                patch("ai.provider.requests.post", return_value=fake_response(200, body)):
            r = self.client.post(reverse("journal_create"), {"raw_text": "raw"}, follow=True)
        entry = JournalEntry.objects.get()
        self.assertEqual(entry.clean_text, "Organized text.")
        self.assertEqual(entry.raw_text, "raw")
        s = entry.suggestions.get(title="Call the bank")
        self.assertEqual((s.priority, s.estimated_duration), ("high", 20))
        self.assertEqual(Task.objects.count(), 0)
        self.assertContains(r, "10:30")
        self.assertEqual(s.date, timezone.localdate() + timedelta(days=1))

    @override_settings(AI_PROVIDER="claude")
    def test_ai_failure_still_saves_the_entry(self):
        with patch.dict("os.environ", {}, clear=True):
            r = self.client.post(reverse("journal_create"), {"raw_text": "important thoughts"}, follow=True)
        entry = JournalEntry.objects.get()
        self.assertEqual(entry.clean_text, "important thoughts")
        self.assertEqual(entry.suggestions.count(), 0)
        self.assertContains(r, "ANTHROPIC_API_KEY")

    @override_settings(AI_PROVIDER="openai")
    def test_form_warns_when_text_goes_to_cloud(self):
        self.assertContains(self.client.get(reverse("journal_create")), "sent to openai")
