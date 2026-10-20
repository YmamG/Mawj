"""Session-authenticated API for the Next.js client. Forms remain the source of validation."""
import json
import calendar
from datetime import date, timedelta
from functools import wraps

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse, Http404
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import override as locale_override
from django.views.csrf import csrf_failure as django_csrf_failure
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.cache import never_cache

from accounts.forms import ProfileEditForm, ThemeSelectionForm
from accounts.models import UserPreferences
from accounts.views import avatar
from ai.provider import CLOUD_PROVIDERS, AIProviderError, process_journal, manual_provider, suggest_task_details
from dashboard.reports import achievement_data
from journal.forms import JournalEntryForm
from journal.models import JournalEntry, TaskSuggestion
from tasks.forms import TaskForm
from tasks.models import Task
from tasks.views import task_toggle, reminder_dismiss


def csrf_failure(request, reason=""):
    if request.path.startswith("/api/"):
        return JsonResponse({"error": "Your session needs refreshing. Reload the page and try again."}, status=403)
    return django_csrf_failure(request, reason=reason)


def endpoint(methods=("GET",), public=False):
    def decorate(function):
        @wraps(function)
        def wrapped(request, *args, **kwargs):
            if request.method not in methods:
                response = JsonResponse({"error": "Method not allowed."}, status=405)
                response["Allow"] = ", ".join(methods)
                return response
            if not public and not request.user.is_authenticated:
                return JsonResponse({"error": "Please sign in."}, status=401)
            try:
                with locale_override("ar" if request.headers.get("X-Mawj-Language") == "ar" else "en"):
                    return function(request, *args, **kwargs)
            except (json.JSONDecodeError, UnicodeDecodeError, TypeError, ValueError):
                return JsonResponse({"error": "Invalid request."}, status=400)
            except Http404:
                return JsonResponse({"error": "This record could not be found."}, status=404)
        return never_cache(wrapped)
    return decorate


def payload(request):
    if request.content_type == "application/json":
        data = json.loads(request.body or b"{}")
        if not isinstance(data, dict):
            raise ValueError()
        return data
    return request.POST


def invalid(form):
    return JsonResponse({"error": "Check the highlighted fields.", "fields": dict(form.errors)}, status=400)


def task_data(task):
    return {field: getattr(task, field) for field in (
        "id", "title", "description", "date", "start_time", "deadline", "estimated_duration", "priority", "status", "completed_at", "created_at", "category", "repeat", "reminder_at", "reminder_dismissed",
    )}


def entry_data(entry, detail=False):
    data = {"id": entry.pk, "raw_text": entry.raw_text, "clean_text": entry.clean_text, "created_at": entry.created_at, "pending_count": entry.pending_count if hasattr(entry, "pending_count") else entry.suggestions.filter(status="pending").count()}
    if detail:
        data["suggestions"] = list(entry.suggestions.values("id", "title", "date", "start_time", "priority", "estimated_duration", "status"))
    return data


def account_data(user):
    preferences, _ = UserPreferences.objects.get_or_create(user=user)
    theme = {"tide": "grove", "forest": "grove", "orchid": "petal", "sunrise": "dusk"}.get(preferences.theme, preferences.theme)
    journal_count = user.journal_entries.count()
    if settings.E2EE_JOURNAL_PREVIEW:
        from journal.models import EncryptedJournalEntry
        journal_count += EncryptedJournalEntry.objects.filter(vault__user=user).count()
    return {"id": user.pk, "username": user.username, "first_name": user.first_name, "last_name": user.last_name, "email": user.email, "display_name": preferences.display_name, "theme": theme, "has_avatar": bool(preferences.avatar), "date_joined": user.date_joined,
        "stats": {"tasks": user.tasks.count(), "completed": user.tasks.filter(status="done").count(), "journals": journal_count}}


def paginated(queryset, request, serialize):
    from django.core.paginator import Paginator
    page = Paginator(queryset, 12).get_page(request.GET.get("page"))
    return JsonResponse({"results": [serialize(item) for item in page], "page": page.number, "pages": page.paginator.num_pages, "total": page.paginator.count})


@ensure_csrf_cookie
@endpoint(public=True)
def session(request):
    return JsonResponse({"user": account_data(request.user) if request.user.is_authenticated else None, "csrf": get_token(request), "provider": settings.AI_PROVIDER, "sends_to_cloud": settings.AI_PROVIDER in CLOUD_PROVIDERS})


@endpoint(("POST",), public=True)
def signin(request):
    data = payload(request)
    user = authenticate(request, username=str(data.get("username") or "").strip(), password=data.get("password", ""))
    if user is None:
        return JsonResponse({"error": "The username or password is incorrect."}, status=400)
    if data.get("theme") in ("petal", "grove", "dusk", "ember", "midnight"):
        preferences, _ = UserPreferences.objects.get_or_create(user=user)
        preferences.theme = data["theme"]
        preferences.save(update_fields=["theme"])
    login(request, user)
    return JsonResponse({"user": account_data(user), "csrf": get_token(request)})


@endpoint(("POST",), public=True)
def signup(request):
    data = payload(request)
    form = UserCreationForm(data)
    if not form.is_valid():
        return invalid(form)
    user = form.save()
    if data.get("theme") in ("petal", "grove", "dusk", "ember", "midnight"):
        UserPreferences.objects.create(user=user, theme=data["theme"])
    login(request, user)
    return JsonResponse({"user": account_data(user), "csrf": get_token(request)}, status=201)


@endpoint(("POST",))
def signout(request):
    logout(request)
    return JsonResponse({"ok": True})


@endpoint(("GET", "POST"))
def profile(request):
    if request.method == "POST":
        prefs, _ = UserPreferences.objects.get_or_create(user=request.user)
        form = ProfileEditForm(payload(request), request.FILES, user=request.user, preferences=prefs)
        if not form.is_valid():
            return invalid(form)
        form.save()
    return JsonResponse(account_data(request.user))


@endpoint(("POST",))
def theme(request):
    form = ThemeSelectionForm(payload(request))
    if not form.is_valid():
        return invalid(form)
    prefs, _ = UserPreferences.objects.get_or_create(user=request.user)
    prefs.theme = form.cleaned_data["theme"]
    prefs.save(update_fields=["theme"])
    return JsonResponse({"ok": True})


@endpoint(("GET", "POST"))
def tasks(request):
    if request.method == "POST":
        form = TaskForm(payload(request))
        if not form.is_valid():
            return invalid(form)
        task = form.save(commit=False)
        task.user = request.user
        task.save()
        return JsonResponse(task_data(task), status=201)
    queryset = Task.objects.filter(user=request.user)
    query = request.GET.get("q", "").strip()
    if query:
        queryset = queryset.filter(Q(title__icontains=query) | Q(description__icontains=query))
    for field, choices in [("status", Task.STATUS_CHOICES), ("priority", Task.PRIORITY_CHOICES), ("category", Task.CATEGORY_CHOICES)]:
        value = request.GET.get(field, "")
        if field == "category" and value == "uncategorized":
            queryset = queryset.filter(category="")
        elif value and value in dict(choices):
            queryset = queryset.filter(**{field: value})
    return paginated(queryset.order_by("status", "date", "start_time", "-created_at", "pk"), request, task_data)


@endpoint(("GET", "POST"))
def task(request, pk):
    instance = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == "POST":
        data = payload(request)
        action = data.get("action")
        if action == "delete":
            instance.delete()
            return JsonResponse({"ok": True})
        if action == "toggle":
            task_toggle(request, pk)
            instance.refresh_from_db()
            result = task_data(instance)
            result["next_date"] = Task.objects.filter(previous_occurrence=instance).values_list("date", flat=True).first()
            return JsonResponse(result)
        if action == "dismiss":
            reminder_dismiss(request, pk)
            return JsonResponse({"ok": True})
        old_reminder = instance.reminder_at.replace(second=0, microsecond=0) if instance.reminder_at else None
        form = TaskForm(data, instance=instance)
        if not form.is_valid():
            return invalid(form)
        if form.cleaned_data.get("reminder_at") != old_reminder:
            form.instance.reminder_dismissed = False
        instance = form.save()
    return JsonResponse(task_data(instance))


@endpoint(("POST",))
def task_suggest(request):
    data = payload(request)
    title = str(data.get("title", "")).strip()
    if not title:
        return JsonResponse({"error": "Write a title first."}, status=400)
    try:
        return JsonResponse(suggest_task_details(title, data.get("description", "")))
    except AIProviderError as error:
        return JsonResponse({"error": str(error)}, status=422)


@endpoint()
def today(request):
    current_date = timezone.localdate()
    owned = Task.objects.filter(user=request.user)
    pending = owned.filter(status="todo")
    overdue_q = Q(date__lt=current_date) | Q(deadline__lt=timezone.now())
    due_today = Q(date=current_date) | Q(deadline__date=current_date) | Q(date__isnull=True, deadline__isnull=True)
    overdue = pending.filter(overdue_q).order_by("date", "deadline", "pk")
    todays = pending.filter(due_today).exclude(overdue_q).order_by("start_time", "deadline", "pk")
    completed = owned.filter(status="done", completed_at__date=current_date).order_by("-completed_at", "pk")
    reminders = pending.filter(reminder_at__lte=timezone.now(), reminder_dismissed=False).order_by("reminder_at", "pk")
    section = request.GET.get("section", "today")
    queryset = {"today": todays, "overdue": overdue, "completed": completed}.get(section, todays)
    response = json.loads(paginated(queryset, request, task_data).content)
    response.update(date=current_date, counts={"today": todays.count(), "overdue": overdue.count(), "completed": completed.count()}, reminders=[task_data(item) for item in reminders[:20]], reminder_count=reminders.count())
    return JsonResponse(response)


@endpoint(("GET", "POST"))
def journals(request):
    if request.method == "POST":
        if settings.E2EE_JOURNAL_PREVIEW:
            return JsonResponse({"error": "Use the encrypted journal preview. Plaintext saving is disabled."}, status=409)
        form = JournalEntryForm(payload(request))
        if not form.is_valid():
            return invalid(form)
        entry = form.save(commit=False)
        entry.user = request.user
        warning = ""
        try:
            result = process_journal(entry.raw_text)
        except AIProviderError as error:
            result = manual_provider(entry.raw_text)
            warning = f"{error} Your entry was saved as written."
        with transaction.atomic():
            entry.clean_text = result["clean_text"]
            entry.save()
            for item in result["suggestions"]:
                TaskSuggestion.objects.create(user=request.user, entry=entry, **item)
        data = entry_data(entry, detail=True)
        data["warning"] = warning or result.get("warning", "")
        return JsonResponse(data, status=201)
    queryset = JournalEntry.objects.filter(user=request.user).annotate(pending_count=Count("suggestions", filter=Q(suggestions__status="pending")))
    query = request.GET.get("q", "").strip()
    if query:
        queryset = queryset.filter(Q(raw_text__icontains=query) | Q(clean_text__icontains=query))
    return paginated(queryset.order_by("-created_at", "-pk"), request, entry_data)


@endpoint(("GET", "POST"))
def journal(request, pk):
    entry = get_object_or_404(JournalEntry, pk=pk, user=request.user)
    if request.method == "POST":
        if settings.E2EE_JOURNAL_PREVIEW:
            return JsonResponse({"error": "Use the encrypted journal preview to migrate this entry."}, status=409)
        data = payload(request)
        if data.get("action") == "delete":
            entry.delete()
            return JsonResponse({"ok": True})
        if data.get("action") == "analyze":
            try:
                result = process_journal(entry.raw_text)
            except AIProviderError as error:
                return JsonResponse({"error": str(error)}, status=422)
            with transaction.atomic():
                decided = {item.title.casefold() for item in entry.suggestions.exclude(status="pending")}
                entry.clean_text = result["clean_text"]
                entry.save(update_fields=["clean_text"])
                entry.suggestions.filter(status="pending").delete()
                for item in result["suggestions"]:
                    if item["title"].casefold() not in decided:
                        TaskSuggestion.objects.create(user=request.user, entry=entry, **item)
            response = entry_data(entry, detail=True)
            response["warning"] = result.get("warning", "")
            return JsonResponse(response)
        form = JournalEntryForm(data, instance=entry)
        if not form.is_valid():
            return invalid(form)
        with transaction.atomic():
            entry = form.save(commit=False)
            entry.clean_text = entry.raw_text
            entry.save()
            entry.suggestions.filter(status="pending").update(status="dismissed")
    return JsonResponse(entry_data(entry, detail=True))


@endpoint(("POST",))
def suggestion(request, pk):
    action = payload(request).get("action")
    if action not in ("accept", "dismiss"):
        return JsonResponse({"error": "Choose accept or dismiss."}, status=400)
    with transaction.atomic():
        instance = get_object_or_404(TaskSuggestion, pk=pk, user=request.user)
        if instance.status == "pending" and action == "accept":
            form = TaskForm({"title": instance.title, "date": instance.date, "start_time": instance.start_time, "priority": instance.priority, "estimated_duration": instance.estimated_duration})
            if not form.is_valid():
                return invalid(form)
        # Claim the pending row before creating its task so repeat requests cannot duplicate it.
        updated = TaskSuggestion.objects.filter(pk=pk, user=request.user, status="pending").update(status="accepted" if action == "accept" else "dismissed")
        if updated and action == "accept":
            Task.objects.create(user=request.user, title=instance.title, description="Added from journal.", date=instance.date, start_time=instance.start_time, priority=instance.priority, estimated_duration=instance.estimated_duration)
    return JsonResponse({"ok": True})


@endpoint()
def achievements(request):
    return JsonResponse(achievement_data(request.user, request.GET.get("period", "week")))


@endpoint()
def month(request):
    today = timezone.localdate()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))
    if not (1900 <= year <= 9998 and 1 <= month <= 12):
        return JsonResponse({"error": "Choose a valid month."}, status=400)
    entries = JournalEntry.objects.filter(user=request.user, created_at__year=year, created_at__month=month)
    entry_dates = set(entries.values_list("created_at__date", flat=True))
    encrypted_entries = []
    if settings.E2EE_JOURNAL_PREVIEW:
        from journal.models import EncryptedJournalEntry
        encrypted_entries = list(EncryptedJournalEntry.objects.filter(vault__user=request.user, created_at__year=year, created_at__month=month))
        entry_dates.update(timezone.localtime(item.created_at).date() for item in encrypted_entries)
    from django.db.models.functions import Coalesce, TruncDate
    start = date(year, month, 1)
    end = (start + timedelta(days=32)).replace(day=1)
    queryset = Task.objects.filter(user=request.user).filter(Q(date__gte=start, date__lt=end) | Q(date__isnull=True, created_at__date__gte=start, created_at__date__lt=end))
    summaries = {row["calendar_date"]: row for row in queryset.order_by().annotate(calendar_date=Coalesce("date", TruncDate("created_at"))).values("calendar_date").annotate(total=Count("pk"), completed=Count("pk", filter=Q(status="done")))}
    days = []
    for day in range(1, calendar.monthrange(year, month)[1] + 1):
        current = date(year, month, day)
        counts = summaries.get(current, {})
        days.append({"date": current, "day": day, "total": counts.get("total", 0), "completed": counts.get("completed", 0), "has_journal": current in entry_dates})
    return JsonResponse({"year": year, "month": month, "days": days, "tasks": [{**task_data(task), "calendar_date": task.date or timezone.localtime(task.created_at).date()} for task in queryset], "entries": [entry_data(entry) for entry in entries] + [{"id": str(entry.pk), "created_at": entry.created_at, "encrypted": True, "raw_text": "", "clean_text": ""} for entry in encrypted_entries]})
