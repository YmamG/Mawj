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
    entries = JournalEntry.objects.filter(user=request.user)
    return render(request, "journal/journal_list.html", {"entries": entries})


@login_required
def journal_create(request):
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
