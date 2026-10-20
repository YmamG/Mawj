from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from django.conf import settings

from ai.provider import CLOUD_PROVIDERS, AIProviderError, manual_provider, process_journal
from tasks.models import Task

from .forms import JournalEntryForm
from .models import JournalEntry, TaskSuggestion


@login_required
def journal_list(request):
    if settings.E2EE_JOURNAL_PREVIEW:
        return redirect("/app/encrypted-journal/")
    entries = JournalEntry.objects.filter(user=request.user).annotate(
        pending_count=Count("suggestions", filter=Q(suggestions__status="pending")),
    ).order_by("-created_at", "-pk")
    query = request.GET.get("q", "").strip()
    if query:
        entries = entries.filter(Q(raw_text__icontains=query) | Q(clean_text__icontains=query))
    page = Paginator(entries, 10).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "journal/journal_list.html", {
        "entries": page, "page_obj": page, "query": query,
        "pagination_query": params.urlencode(),
    })


@login_required
def journal_create(request):
    if settings.E2EE_JOURNAL_PREVIEW:
        return redirect("/app/encrypted-journal/")
    if request.method == "POST":
        form = JournalEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user

            try:
                result = process_journal(entry.raw_text)   # AI (or manual) step
            except AIProviderError as error:
                # If the AI fails, never lose the user's text: save it as written.
                result = manual_provider(entry.raw_text)
                messages.warning(request, f"AI could not process this entry: {error} Saved as written.")
            entry.clean_text = result["clean_text"]
            entry.save()

            for item in result["suggestions"]:
                TaskSuggestion.objects.create(
                    user=request.user,
                    entry=entry,
                    title=item["title"],
                    date=item.get("date"),
                    start_time=item.get("start_time"),
                    priority=item.get("priority", "medium"),
                    estimated_duration=item.get("estimated_duration"),
                )
            messages.success(request, "Journal entry saved.")
            return redirect("journal_detail", pk=entry.pk)
    else:
        form = JournalEntryForm()
    context = {"form": form, "provider": settings.AI_PROVIDER,
               "sends_to_cloud": settings.AI_PROVIDER in CLOUD_PROVIDERS}
    return render(request, "journal/journal_form.html", context)


@login_required
def journal_detail(request, pk):
    if settings.E2EE_JOURNAL_PREVIEW:
        return redirect("/app/encrypted-journal/")
    entry = get_object_or_404(JournalEntry, pk=pk, user=request.user)
    pending = entry.suggestions.filter(status="pending")
    return render(request, "journal/journal_detail.html", {"entry": entry, "pending": pending})


@login_required
def journal_delete(request, pk):
    entry = get_object_or_404(JournalEntry, pk=pk, user=request.user)
    if request.method == "POST":
        entry.delete()
        messages.success(request, "Journal entry deleted.")
        return redirect("journal_list")
    return render(request, "journal/journal_confirm_delete.html", {"entry": entry})


@login_required
@require_POST
def suggestion_accept(request, pk):
    """The human approves: only now is a real Task created."""
    suggestion = get_object_or_404(TaskSuggestion, pk=pk, user=request.user)
    if suggestion.status == "pending":
        from tasks.forms import TaskForm
        form = TaskForm({"title": suggestion.title, "date": suggestion.date, "start_time": suggestion.start_time, "priority": suggestion.priority, "estimated_duration": suggestion.estimated_duration})
        if not form.is_valid():
            messages.error(request, "This suggestion has a past schedule. Add it manually with today or a future date.")
            return redirect("journal_detail", pk=suggestion.entry_id)
        Task.objects.create(
            user=request.user,
            title=suggestion.title,
            description="Added from journal.",
            date=suggestion.date,
            start_time=suggestion.start_time,
            priority=suggestion.priority,
            estimated_duration=suggestion.estimated_duration,
        )
        suggestion.status = "accepted"
        suggestion.save()
        messages.success(request, "Task added to your list.")
    return redirect("journal_detail", pk=suggestion.entry_id)


@login_required
@require_POST
def suggestion_dismiss(request, pk):
    suggestion = get_object_or_404(TaskSuggestion, pk=pk, user=request.user)
    if suggestion.status == "pending":
        suggestion.status = "dismissed"
        suggestion.save()
    return redirect("journal_detail", pk=suggestion.entry_id)


@login_required
def journal_update(request, pk):
    if settings.E2EE_JOURNAL_PREVIEW:
        return redirect("/app/encrypted-journal/")
    entry = get_object_or_404(JournalEntry, pk=pk, user=request.user)
    form = JournalEntryForm(request.POST if request.method == "POST" else None, instance=entry)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            updated = form.save(commit=False)
            updated.clean_text = updated.raw_text
            updated.save()
            updated.suggestions.filter(status="pending").update(status="dismissed")
        messages.success(request, "Journal entry updated. Old pending suggestions were dismissed; existing tasks are unchanged.")
        return redirect("journal_detail", pk=entry.pk)
    return render(request, "journal/journal_form.html", {
        "form": form, "editing": True, "entry": entry,
    })
