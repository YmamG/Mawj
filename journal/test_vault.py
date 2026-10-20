import base64
import json
import uuid
from copy import deepcopy
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from tasks.models import Task
from .models import EncryptedJournalEntry, JournalEntry, JournalVault, TaskSuggestion
from .vault_api import legacy_snapshot


def encoded(size):
    return base64.b64encode(bytes(range(size))).decode()


def wrapped_keys():
    return {"passphrase": {"kdf": "PBKDF2-SHA256", "iterations": 600000, "salt": encoded(16), "iv": encoded(12), "ciphertext": encoded(48)}, "recovery": {"kdf": "HKDF-SHA256", "salt": encoded(32), "iv": encoded(12), "ciphertext": encoded(48)}}


def opaque_payload():
    # Only a wire-format fixture; actual authenticated encryption is tested in JS.
    return {"version": 1, "iv": encoded(12), "ciphertext": encoded(48)}


@override_settings(E2EE_JOURNAL_PREVIEW=True, AI_PROVIDER="demo")
class VaultApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user("vault-user")
        cls.other = get_user_model().objects.create_user("other-vault-user")

    def setUp(self):
        self.client.force_login(self.user)

    def post(self, path, data):
        return self.client.post("/api/" + path, json.dumps(data), content_type="application/json")

    def create_vault(self):
        result = self.post("vault/", {"id": str(uuid.uuid4()), "envelopes": wrapped_keys()})
        self.assertEqual(result.status_code, 201)
        return result.json()

    def create_note(self):
        self.create_vault()
        result = self.post("vault/entries/", {"id": str(uuid.uuid4()), "payload": opaque_payload()})
        self.assertEqual(result.status_code, 201)
        return result.json()

    @override_settings(E2EE_JOURNAL_PREVIEW=False)
    def test_preview_is_opt_in_and_not_enabled_on_normal_site(self):
        self.assertEqual(self.client.get("/api/vault/").status_code, 404)
        self.assertEqual(self.client.get("/app/encrypted-journal/").status_code, 404)

    def test_authentication_and_csrf_required(self):
        self.client.logout()
        self.assertEqual(self.client.get("/api/vault/").status_code, 401)
        self.assertEqual(self.client.get("/app/encrypted-journal/").status_code, 302)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post("/api/vault/", "{}", content_type="application/json").status_code, 403)

    def test_vault_registration_never_overwrites_existing_keys(self):
        original = self.create_vault()
        self.assertEqual(self.post("vault/", {"id": str(uuid.uuid4()), "envelopes": wrapped_keys()}).status_code, 409)
        self.assertEqual(self.client.get("/api/vault/").json()["vault"], original)
        self.assertEqual(JournalVault.objects.count(), 1)

    def test_rejects_plaintext_extra_fields_and_malformed_envelopes(self):
        for replacement in (None, 1, {}, "invalid"):
            self.assertEqual(self.post("vault/", {"id": replacement, "envelopes": wrapped_keys()}).status_code, 400)
        for field, value in (("iterations", 1), ("salt", "invalid"), ("iv", encoded(8)), ("ciphertext", encoded(16))):
            keys = wrapped_keys()
            keys["passphrase"][field] = value
            self.assertEqual(self.post("vault/", {"id": str(uuid.uuid4()), "envelopes": keys}).status_code, 400)
        self.assertEqual(self.post("vault/", {"id": str(uuid.uuid4()), "envelopes": wrapped_keys(), "passphrase": "never-send-this"}).status_code, 400)
        self.create_vault()
        for invalid in ({"version": True, "iv": encoded(12), "ciphertext": encoded(48)}, {"version": 1, "iv": "!!!!!!!!!!!!", "ciphertext": encoded(48)}, {**opaque_payload(), "text": "private"}):
            self.assertEqual(self.post("vault/entries/", {"id": str(uuid.uuid4()), "payload": invalid}).status_code, 400)
        self.assertEqual(EncryptedJournalEntry.objects.count(), 0)

    def test_ciphertext_ownership_revision_and_deletion(self):
        note = self.create_note()
        path = f"vault/entries/{note['id']}/"
        self.client.force_login(self.other)
        self.assertIsNone(self.client.get("/api/vault/").json()["vault"])
        self.assertEqual(self.client.get("/api/" + path).status_code, 404)
        self.assertEqual(self.post(path, {"revision": 1, "action": "delete"}).status_code, 404)
        self.client.force_login(self.user)
        updated = self.post(path, {"revision": 1, "payload": opaque_payload()})
        self.assertEqual(updated.json()["revision"], 2)
        self.assertEqual(self.post(path, {"revision": 1, "payload": opaque_payload()}).status_code, 409)
        self.assertEqual(self.post(path, {"revision": 1, "action": "delete"}).status_code, 409)
        self.assertEqual(self.post(path, {"revision": 2, "action": "delete"}).status_code, 200)
        self.assertFalse(EncryptedJournalEntry.objects.exists())

    def test_rewrap_requires_matching_revision(self):
        self.create_vault()
        keys = wrapped_keys()
        keys["passphrase"]["iv"] = base64.b64encode(b"x" * 12).decode()
        response = self.post("vault/rewrap/", {"revision": 1, "envelopes": keys})
        self.assertEqual(response.json()["revision"], 2)
        self.assertEqual(self.post("vault/rewrap/", {"revision": 1, "envelopes": wrapped_keys()}).status_code, 409)
        self.assertEqual(JournalVault.objects.get(user=self.user).envelopes, keys)

    @patch("config.api.process_journal")
    @patch("journal.views.process_journal")
    def test_legacy_plaintext_writes_and_automatic_analysis_are_blocked(self, legacy_process, api_process):
        entry = JournalEntry.objects.create(user=self.user, raw_text="legacy plaintext")
        self.assertEqual(self.post("journal/", {"raw_text": "new plaintext"}).status_code, 409)
        self.assertEqual(self.post(f"journal/{entry.pk}/", {"action": "analyze"}).status_code, 409)
        self.assertEqual(self.post(f"journal/{entry.pk}/", {"raw_text": "updated plaintext"}).status_code, 409)
        self.assertRedirects(self.client.post("/journal/add/", {"raw_text": "legacy bypass"}), "/app/encrypted-journal/", fetch_redirect_response=False)
        api_process.assert_not_called()
        legacy_process.assert_not_called()
        self.assertEqual(JournalEntry.objects.count(), 1)

    @override_settings(AI_PROVIDER="openai")
    @patch("journal.vault_api.process_journal")
    def test_analysis_requires_per_request_provider_consent_and_does_not_persist_text(self, process):
        self.create_note()
        original = deepcopy(EncryptedJournalEntry.objects.get().payload)
        for data in ({"text": "private", "provider": "openai", "consent": False}, {"text": "private", "provider": "claude", "consent": True}):
            self.assertEqual(self.post("vault/analyze/", data).status_code, 400)
        process.assert_not_called()
        process.return_value = {"clean_text": "organized private text", "suggestions": []}
        self.assertEqual(self.post("vault/analyze/", {"text": "private", "provider": "openai", "consent": True}).status_code, 200)
        process.assert_called_once_with("private")
        self.assertFalse(JournalEntry.objects.exists())
        self.assertFalse(TaskSuggestion.objects.exists())
        self.assertEqual(EncryptedJournalEntry.objects.get().payload, original)

    def test_explicit_legacy_migration_is_atomic_and_keeps_tasks_and_date(self):
        self.create_vault()
        entry = JournalEntry.objects.create(user=self.user, raw_text="old private text", clean_text="clean private text")
        suggestion = TaskSuggestion.objects.create(user=self.user, entry=entry, title="old private suggestion")
        task = Task.objects.create(user=self.user, title="previously accepted")
        stamp = entry.created_at
        source = self.client.get("/api/vault/legacy/").json()["results"][0]
        data = {"id": str(uuid.uuid4()), "payload": opaque_payload(), "fingerprint": source["fingerprint"], "consent": False}
        self.assertEqual(self.post(f"vault/legacy/{entry.pk}/", data).status_code, 400)
        data["consent"] = True
        entry.raw_text = "concurrent edit"
        entry.save()
        self.assertEqual(self.post(f"vault/legacy/{entry.pk}/", data).status_code, 409)
        self.assertTrue(TaskSuggestion.objects.filter(pk=suggestion.pk).exists())
        data["fingerprint"] = legacy_snapshot(entry)["fingerprint"]
        result = self.post(f"vault/legacy/{entry.pk}/", data)
        self.assertEqual(result.status_code, 201)
        self.assertEqual(EncryptedJournalEntry.objects.get().created_at, stamp)
        self.assertFalse(JournalEntry.objects.exists())
        self.assertFalse(TaskSuggestion.objects.exists())
        self.assertTrue(Task.objects.filter(pk=task.pk).exists())

    def test_legacy_import_collision_rolls_back_and_owner_is_checked(self):
        note = self.create_note()
        entry = JournalEntry.objects.create(user=self.user, raw_text="keep this")
        data = {"id": note["id"], "payload": opaque_payload(), "fingerprint": legacy_snapshot(entry)["fingerprint"], "consent": True}
        self.assertEqual(self.post(f"vault/legacy/{entry.pk}/", data).status_code, 409)
        self.assertTrue(JournalEntry.objects.filter(pk=entry.pk).exists())
        self.client.force_login(self.other)
        self.create_vault()
        self.assertEqual(self.post(f"vault/legacy/{entry.pk}/", data).status_code, 404)

    def test_unencrypted_task_acceptance_requires_consent_and_is_idempotent(self):
        note = self.create_note()
        data = {"token": str(uuid.uuid4()), "task": {"title": "approved ordinary task"}, "consent": False}
        path = f"vault/entries/{note['id']}/tasks/"
        self.assertEqual(self.post(path, data).status_code, 400)
        data["consent"] = True
        first = self.post(path, data)
        self.assertEqual(first.status_code, 201)
        self.assertEqual(self.post(path, data).json()["task_id"], first.json()["task_id"])
        self.assertEqual(Task.objects.count(), 1)
        task = Task.objects.get()
        task.delete()
        self.assertIsNone(self.post(path, data).json()["task_id"])
        self.assertFalse(Task.objects.exists())
        self.client.force_login(self.other)
        self.assertEqual(self.post(path, data).status_code, 404)

    def test_calendar_and_profile_show_metadata_without_ciphertext_or_plaintext(self):
        note = self.create_note()
        result = self.client.get("/api/calendar/").json()
        self.assertEqual(result["entries"][0]["id"], note["id"])
        self.assertTrue(result["entries"][0]["encrypted"])
        self.assertEqual(result["entries"][0]["raw_text"], "")
        self.assertNotIn("payload", result["entries"][0])
        day = next(day for day in result["days"] if day["date"] == timezone.localdate().isoformat())
        self.assertTrue(day["has_journal"])
        self.assertEqual(self.client.get("/api/session/").json()["user"]["stats"]["journals"], 1)
        response = self.client.get("/app/encrypted-journal/")
        self.assertContains(response, "Experimental preview")
        self.assertNotContains(response, "<form")
        self.assertIn("no-store", response.headers["Cache-Control"])

    @override_settings(AI_PROVIDER="openai")
    def test_page_identifies_cloud_provider_before_analysis_consent(self):
        response = self.client.get("/app/encrypted-journal/")
        self.assertTrue(response.context["boot"]["sends_to_cloud"])
        self.assertEqual(response.context["boot"]["provider"], "openai")

    def test_rejected_task_validation_does_not_claim_idempotency_token(self):
        note = self.create_note()
        data = {"token": str(uuid.uuid4()), "task": {"title": "", "date": "2000-01-01"}, "consent": True}
        path = f"vault/entries/{note['id']}/tasks/"
        self.assertEqual(self.post(path, data).status_code, 400)
        data["task"] = {"title": "corrected task"}
        self.assertEqual(self.post(path, data).status_code, 201)
        self.assertEqual(Task.objects.count(), 1)
