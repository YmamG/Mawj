"""Opaque, owner-filtered experimental storage. Cryptography lives in the browser."""
import base64
import hashlib
import hmac
import json
import uuid
from functools import wraps

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import IntegrityError, transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

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
        raise ValueError("Invalid request fields")


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


def vault_data(vault):
    return {"id": str(vault.pk), "key_mode": vault.key_mode, "revision": vault.revision}


def managed_key_bytes(vault):
    secret = settings.JOURNAL_ENCRYPTION_KEY.encode()
    context = f"mawj:managed-journal:v1:user:{vault.user_id}:vault:{vault.pk}".encode()
    return hmac.new(secret, context, hashlib.sha256).digest()


def note_data(note):
    return {"id": str(note.pk), "payload": note.payload, "revision": note.revision, "created_at": note.created_at}


def conflict():
    return JsonResponse({"error": "This record changed. Reload the page; your draft has not been saved."}, status=409)


@preview(("GET", "POST"))
def vault(request):
    existing = JournalVault.objects.filter(user=request.user).first()
    if request.method == "GET":
        return JsonResponse({"vault": vault_data(existing) if existing else None, "legacy_count": JournalEntry.objects.filter(user=request.user).count()})
    data = payload(request)
    if data == {"mode": "managed"}:
        if existing:
            return conflict()
        try:
            created = JournalVault.objects.create(user=request.user, envelopes={}, key_mode="managed")
        except IntegrityError:
            return conflict()
        return JsonResponse(vault_data(created), status=201)
    raise ValueError()


@preview(("POST",))
def managed_key(request):
    current = get_object_or_404(JournalVault, user=request.user, key_mode="managed")
    if payload(request):
        raise ValueError()
    response = JsonResponse({"key": base64.b64encode(managed_key_bytes(current)).decode()})
    response["Cache-Control"] = "no-store"
    return response


@preview(("POST",))
def reset_legacy(request):
    current = get_object_or_404(JournalVault, user=request.user, key_mode="legacy")
    data = payload(request)
    only(data, ("confirmation",))
    if data["confirmation"] != "delete-locked-journal":
        raise ValueError()
    with transaction.atomic():
        current.delete()
        created = JournalVault.objects.create(user=request.user, envelopes={}, key_mode="managed")
    return JsonResponse(vault_data(created), status=201)


@preview(("GET", "POST"))
def notes(request):
    current = get_object_or_404(JournalVault, user=request.user, key_mode="managed")
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
    current = get_object_or_404(EncryptedJournalEntry, pk=pk, vault__user=request.user, vault__key_mode="managed")
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
    current = get_object_or_404(JournalVault, user=request.user, key_mode="managed")
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
    get_object_or_404(JournalVault, user=request.user, key_mode="managed")
    data = payload(request)
    only(data, ("text", "provider", "consent"))
    if data["consent"] is not True or data["provider"] != settings.AI_PROVIDER or settings.AI_PROVIDER not in CLOUD_PROVIDERS:
        return JsonResponse({"error": "Explicit consent for the currently selected cloud provider is required."}, status=400)
    if not isinstance(data["text"], str) or not 1 <= len(data["text"].strip()) <= 32000:
        raise ValueError()
    try:
        result = process_journal(data["text"])
    except AIProviderError as error:
        # AIProviderError contains our fixed safe messages, never the private prompt or provider body.
        return JsonResponse({"error": f"{error} Your encrypted entry is unchanged."}, status=422)
    # No database write: result returns to the browser for encryption there.
    return JsonResponse(result)


@preview(("POST",))
def accept_task(request, pk):
    from tasks.forms import TaskForm
    entry = get_object_or_404(EncryptedJournalEntry, pk=pk, vault__user=request.user, vault__key_mode="managed")
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
