from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from django.conf import settings

from ai.provider import CLOUD_PROVIDERS, AIProviderError, suggest_task_details

from .forms import TaskForm
from .models import Task
from .services import create_next_occurrence


def _form_context(form, page_title):
    return {
        "form": form,
        "show_details": form.is_bound or bool(form.instance.pk),
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
    context = _form_context(form, page_title)
    context["show_details"] = True
    return render(request, "tasks/task_form.html", context)


@login_required
def task_list(request):
    """Show only the logged-in user's tasks."""
    tasks = Task.objects.filter(user=request.user)
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "todo")
    priority = request.GET.get("priority", "")
    category = request.GET.get("category", "")
    if query:
        tasks = tasks.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if status == "done":
        tasks = tasks.filter(status="done")
    elif status == "all":
        pass
    else:
        status = "todo"
        tasks = tasks.filter(status="todo")
    if priority in dict(Task.PRIORITY_CHOICES):
        tasks = tasks.filter(priority=priority)
    else:
        priority = ""
    if category in dict(Task.CATEGORY_CHOICES) and category:
        tasks = tasks.filter(category=category)
    elif category == "uncategorized":
        tasks = tasks.filter(category="")
    else:
        category = ""
    tasks = tasks.order_by("status", "date", "start_time", "-created_at", "pk")
    page = Paginator(tasks, 10).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "tasks/task_list.html", {
        "tasks": page, "page_obj": page, "query": query, "status": status,
        "priority": priority, "category": category, "pagination_query": params.urlencode(),
        "category_choices": [("uncategorized", "Uncategorized")] + Task.CATEGORY_CHOICES[1:],
        "status_choices": Task.STATUS_CHOICES, "priority_choices": Task.PRIORITY_CHOICES,
    })


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
        original_reminder = task.reminder_at
        if original_reminder:
            original_reminder = original_reminder.replace(second=0, microsecond=0)
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            if form.cleaned_data.get("reminder_at") != original_reminder:
                form.instance.reminder_dismissed = False
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


def _return_to_tasks(request):
    destination = request.POST.get("next", "")
    if destination and url_has_allowed_host_and_scheme(destination, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(destination)
    return redirect("task_list")


@login_required
@require_POST
def task_toggle(request, pk):
    with transaction.atomic():
        task = get_object_or_404(Task.objects.select_for_update(), pk=pk, user=request.user)
        if task.status == "todo":
            task.status = "done"
            task.completed_at = timezone.now()
            task.save(update_fields=["status", "completed_at"])
            successor = create_next_occurrence(task)
            if successor:
                messages.success(request, f"Completed. Next occurrence: {successor.date}.")
        else:
            task.status = "todo"
            task.completed_at = None
            task.save(update_fields=["status", "completed_at"])
    return _return_to_tasks(request)


@login_required
@require_POST
def reminder_dismiss(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    task.reminder_dismissed = True
    task.save(update_fields=["reminder_dismissed"])
    return redirect("today")


@login_required
def today(request):
    current_date = timezone.localdate()
    now = timezone.now()
    owned = Task.objects.filter(user=request.user)
    overdue_query = Q(date__lt=current_date) | Q(deadline__lt=now)
    pending = owned.filter(status="todo")
    todays_query = Q(date=current_date) | Q(deadline__date=current_date) | Q(date__isnull=True, deadline__isnull=True)
    overdue = pending.filter(overdue_query).order_by("date", "deadline", "pk")
    todays = pending.filter(todays_query).exclude(overdue_query).order_by("start_time", "deadline", "pk")
    completed = owned.filter(status="done", completed_at__date=current_date).order_by("-completed_at", "pk")
    due_reminders = pending.filter(reminder_at__lte=now, reminder_dismissed=False).order_by("reminder_at", "pk")
    section = request.GET.get("section", "today")
    sections = {"today": todays, "overdue": overdue, "completed": completed}
    if section not in sections:
        section = "today"
    page = Paginator(sections[section], 10).get_page(request.GET.get("page"))
    return render(request, "tasks/today.html", {
        "current_date": current_date, "section": section, "tasks": page, "page_obj": page,
        "today_count": todays.count(), "overdue_count": overdue.count(), "completed_count": completed.count(),
        "reminders": due_reminders[:20], "pagination_query": f"section={section}",
    })
