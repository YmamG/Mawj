"""Opaque, owner-filtered experimental storage. Cryptography lives in the browser."""
import base64
import hashlib
import json
import uuid
from functools import wraps

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import IntegrityError, transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.crypto import salted_hmac

from ai.provider import CLOUD_PROVIDERS, AIProviderError, process_journal
from config.api import endpoint, payload, paginated, entry_data
from .models import EncryptedJournalEntry, JournalEntry, JournalVault, VaultTaskAcceptance


def preview(methods=("GET",)):
    def decorate(function):
        @endpoint(methods)
        @wraps(function)
        def wrapped(request, *args, **kwargs):
            if not settings.E2EE_JOURNAL_PREVIEW:
                raise Http404
            return function(request, *args, **kwargs)
        return wrapped
    return decorate


def only(data, names):
    if not isinstance(data, dict) or set(data) != set(names):
        raise ValueError("Invalid envelope fields")


def b64(value, minimum, maximum=None):
    if not isinstance(value, str) or len(value) > ((maximum or minimum) + 2) // 3 * 4:
        raise ValueError()
    raw = base64.b64decode(value, validate=True)
    if not minimum <= len(raw) <= (maximum or minimum) or base64.b64encode(raw).decode() != value:
        raise ValueError()


def identifier(value):
    if not isinstance(value, str):
        raise ValueError()
    return uuid.UUID(value)


def encrypted(data):
    only(data, ("version", "iv", "ciphertext"))
    if type(data["version"]) is not int or data["version"] != 1:
        raise ValueError()
    b64(data["iv"], 12)
    b64(data["ciphertext"], 17, 262144)
    return data


def envelopes(data):
    only(data, ("passphrase", "recovery"))
    for name, method, salt_size in (("passphrase", "PBKDF2-SHA256", 16), ("recovery", "HKDF-SHA256", 32)):
        item = data[name]
        fields = ("kdf", "salt", "iv", "ciphertext", "iterations") if name == "passphrase" else ("kdf", "salt", "iv", "ciphertext")
        only(item, fields)
        if item["kdf"] != method or (name == "passphrase" and (type(item["iterations"]) is not int or item["iterations"] != 600000)):
            raise ValueError()
        b64(item["salt"], salt_size)
        b64(item["iv"], 12)
        b64(item["ciphertext"], 48)
    return data


def vault_data(vault):
    return {"id": str(vault.pk), "envelopes": vault.envelopes, "revision": vault.revision}


def note_data(note):
    return {"id": str(note.pk), "payload": note.payload, "revision": note.revision, "created_at": note.created_at}


def conflict():
    return JsonResponse({"error": "This record changed. Reload and unlock again; your draft has not been saved."}, status=409)


@preview(("GET", "POST"))
def vault(request):
    existing = JournalVault.objects.filter(user=request.user).first()
    if request.method == "GET":
        # An opaque cache binding, not a credential and never the session cookie.
        binding = salted_hmac("mawj.vault.browser-session", request.session.session_key or "", algorithm="sha256").hexdigest()
        return JsonResponse({"vault": vault_data(existing) if existing else None, "legacy_count": JournalEntry.objects.filter(user=request.user).count(), "device_session": binding})
    data = payload(request)
    only(data, ("id", "envelopes"))
    key_id = identifier(data["id"])
    wrapped = envelopes(data["envelopes"])
    if existing:
        return conflict()
    try:
        with transaction.atomic():
            created = JournalVault.objects.create(id=key_id, user=request.user, envelopes=wrapped)
    except IntegrityError:
        return conflict()
    return JsonResponse(vault_data(created), status=201)


@preview(("POST",))
def rewrap(request):
    current = get_object_or_404(JournalVault, user=request.user)
    data = payload(request)
    only(data, ("revision", "envelopes"))
    wrapped = envelopes(data["envelopes"])
    if type(data["revision"]) is not int:
        raise ValueError()
    # Recovery rewraps the same master key; no destructive reset or new empty vault.
    updated = JournalVault.objects.filter(pk=current.pk, revision=data["revision"]).update(envelopes=wrapped, revision=data["revision"] + 1)
    if not updated:
        return conflict()
    current.refresh_from_db()
    return JsonResponse(vault_data(current))


@preview(("GET", "POST"))
def notes(request):
    current = get_object_or_404(JournalVault, user=request.user)
    if request.method == "GET":
        return paginated(current.entries.all(), request, note_data)
    data = payload(request)
    only(data, ("id", "payload"))
    key_id = identifier(data["id"])
    cipher = encrypted(data["payload"])
    try:
        with transaction.atomic():
            note = current.entries.create(id=key_id, payload=cipher)
    except IntegrityError:
        return conflict()
    return JsonResponse(note_data(note), status=201)


@preview(("GET", "POST"))
def note(request, pk):
    current = get_object_or_404(EncryptedJournalEntry, pk=pk, vault__user=request.user)
    if request.method == "GET":
        return JsonResponse(note_data(current))
    data = payload(request)
    action = data.get("action")
    only(data, ("revision", "action") if action == "delete" else ("revision", "payload"))
    if type(data["revision"]) is not int:
        raise ValueError()
    matched = EncryptedJournalEntry.objects.filter(pk=current.pk, revision=data["revision"])
    if action == "delete":
        deleted, _ = matched.delete()
        return JsonResponse({"ok": True}) if deleted else conflict()
    cipher = encrypted(data["payload"])
    updated = matched.update(payload=cipher, revision=data["revision"] + 1, updated_at=timezone.now())
    if not updated:
        return conflict()
    current.refresh_from_db()
    return JsonResponse(note_data(current))


def legacy_snapshot(entry):
    data = entry_data(entry, detail=True)
    canonical = json.dumps(data, cls=DjangoJSONEncoder, sort_keys=True, separators=(",", ":"))
    return {"id": entry.pk, "document": data, "fingerprint": hashlib.sha256(canonical.encode()).hexdigest()}


@preview()
def legacy(request):
    return paginated(JournalEntry.objects.filter(user=request.user), request, legacy_snapshot)


@preview(("POST",))
def import_legacy(request, pk):
    current = get_object_or_404(JournalVault, user=request.user)
    data = payload(request)
    only(data, ("id", "payload", "fingerprint", "consent"))
    if data["consent"] is not True:
        raise ValueError()
    key_id, cipher = identifier(data["id"]), encrypted(data["payload"])
    try:
        with transaction.atomic():
            entry = get_object_or_404(JournalEntry.objects.select_for_update(), pk=pk, user=request.user)
            if legacy_snapshot(entry)["fingerprint"] != data["fingerprint"]:
                return conflict()
            note = current.entries.create(id=key_id, payload=cipher)
            # Preserve its calendar day; accepted tasks remain outside encryption.
            current.entries.filter(pk=note.pk).update(created_at=entry.created_at)
            entry.delete()
    except IntegrityError:
        return conflict()
    note.refresh_from_db()
    return JsonResponse(note_data(note), status=201)


@preview(("POST",))
def analyze(request):
    get_object_or_404(JournalVault, user=request.user)
    data = payload(request)
    only(data, ("text", "provider", "consent"))
    if data["consent"] is not True or data["provider"] != settings.AI_PROVIDER or settings.AI_PROVIDER not in CLOUD_PROVIDERS:
        return JsonResponse({"error": "Explicit consent for the currently selected cloud provider is required."}, status=400)
    if not isinstance(data["text"], str) or not 1 <= len(data["text"].strip()) <= 32000:
        raise ValueError()
    try:
        result = process_journal(data["text"])
    except AIProviderError:
        # Do not expose provider responses that might repeat a private prompt.
        return JsonResponse({"error": "Analysis failed. Your encrypted entry is unchanged."}, status=422)
    # No database write: result returns to the browser for encryption there.
    return JsonResponse(result)


@preview(("POST",))
def accept_task(request, pk):
    from tasks.forms import TaskForm
    entry = get_object_or_404(EncryptedJournalEntry, pk=pk, vault__user=request.user)
    data = payload(request)
    only(data, ("token", "task", "consent"))
    if data["consent"] is not True or not isinstance(data["task"], dict):
        raise ValueError()
    token = identifier(data["token"])
    with transaction.atomic():
        link, created = VaultTaskAcceptance.objects.get_or_create(entry=entry, token=token)
        if link.task_id is None and not created:
            return JsonResponse({"task_id": None, "already_accepted": True})
        if not created:
            return JsonResponse({"task_id": link.task_id, "already_accepted": True})
        form = TaskForm(data["task"])
        if not form.is_valid():
            # Roll back the claim so validation can be corrected and retried.
            transaction.set_rollback(True)
            return JsonResponse({"error": "Check the task schedule and details.", "fields": dict(form.errors)}, status=400)
        task = form.save(commit=False)
        task.user = request.user
        task.save()
        link.task = task
        link.save(update_fields=["task"])
    return JsonResponse({"task_id": task.pk}, status=201)
