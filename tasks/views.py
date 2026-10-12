from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from django.conf import settings

from ai.provider import CLOUD_PROVIDERS, AIProviderError, suggest_task_details

from .forms import TaskForm
from .models import Task


def _form_context(form, page_title):
    return {
        "form": form,
        "page_title": page_title,
        "provider": settings.AI_PROVIDER,
        "sends_to_cloud": settings.AI_PROVIDER in CLOUD_PROVIDERS,
    }


def _suggest_for_form(request, page_title, task=None):
    """Ask the AI for priority and duration, then show the form again with
    those values filled in. NOTHING is saved: the user reviews and presses Save."""
    data = request.POST.copy()
    title = data.get("title", "").strip()
    if not title:
        messages.error(request, "Write a title first, then ask the AI.")
    else:
        try:
            result = suggest_task_details(title, data.get("description", ""))
            if result["priority"]:
                data["priority"] = result["priority"]
            if result["estimated_duration"]:
                data["estimated_duration"] = result["estimated_duration"]
            messages.info(request, "AI suggestion filled in below. Review it, change anything, then press Save.")
        except AIProviderError as error:
            messages.warning(request, f"AI could not help: {error}")
    form = TaskForm(initial=data.dict(), instance=task)
    return render(request, "tasks/task_form.html", _form_context(form, page_title))


@login_required
def task_list(request):
    """Show only the logged-in user's tasks."""
    tasks = Task.objects.filter(user=request.user)
    return render(request, "tasks/task_list.html", {"tasks": tasks})


@login_required
def task_create(request):
    if request.method == "POST" and "suggest" in request.POST:
        return _suggest_for_form(request, "Add Task")
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user  # the owner is always the logged-in user
            task.save()
            messages.success(request, "Task created.")
            return redirect("task_list")
    else:
        form = TaskForm()
    return render(request, "tasks/task_form.html", _form_context(form, "Add Task"))


@login_required
def task_update(request, pk):
    # Filtering by user means other users' tasks give a 404
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == "POST" and "suggest" in request.POST:
        return _suggest_for_form(request, "Edit Task", task=task)
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, "Task updated.")
            return redirect("task_list")
    else:
        form = TaskForm(instance=task)
    return render(request, "tasks/task_form.html", _form_context(form, "Edit Task"))


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == "POST":
        task.delete()
        messages.success(request, "Task deleted.")
        return redirect("task_list")
    return render(request, "tasks/task_confirm_delete.html", {"task": task})


@login_required
@require_POST
def task_toggle(request, pk):
    """Switch between todo and done, and keep completed_at in sync."""
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if task.status == "todo":
        task.status = "done"
        task.completed_at = timezone.now()
    else:
        task.status = "todo"
        task.completed_at = None
    task.save()
    return redirect("task_list")
