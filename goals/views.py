import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, F, Sum
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST

from tasks.forms import TaskForm
from tasks.views import task_toggle
from web.views import context
from ai.provider import AIProviderError, CLOUD_PROVIDERS, suggest_goal_steps
from .forms import GoalForm, StepForm
from .models import Goal, GoalStep
from .services import achieved_query, goal_data, owned_goals


def _context(request, goal=None, **extra):
    ctx = context(request)
    all_goals = owned_goals(request.user)
    state = request.GET.get("state", "all")
    filtered = all_goals.order_by(F("target_date").asc(nulls_last=True), "created_at", "pk")
    if state == "achieved":
        filtered = filtered.filter(achieved_query())
    elif state in ("active", "paused"):
        filtered = filtered.exclude(achieved_query()).filter(paused=state == "paused")
    else:
        state = "all"
    page = Paginator(filtered, 9).get_page(request.GET.get("page"))
    totals = all_goals.aggregate(total=Count("pk"), steps=Sum("done_steps", default=0))
    ctx.update(section="goals", summary={"total": totals["total"], "achieved": all_goals.filter(achieved_query()).count(), "steps": totals["steps"]},
               cards=[goal_data(item) for item in page], page_obj=page, goal_state=state,
               horizon=[goal_data(item) for item in all_goals.exclude(achieved_query()).filter(paused=False, target_date__gte=timezone.localdate()).order_by("target_date", "pk")[:6]],
               goal_form=GoalForm(instance=goal), show_compose=bool(request.GET.get("new") or request.GET.get("edit")), goal=None)
    if goal:
        ctx.update(goal=goal_data(goal), steps=list(goal.steps.select_related("task")), step_form=StepForm(goal=goal))
    ctx.update(extra)
    return ctx


def _response(request, ctx, status=200, notice=""):
    if "application/json" in request.headers.get("Accept", ""):
        return JsonResponse({"html": render_to_string("web/goals-content.html", ctx, request=request), "notice": notice}, status=status)
    return render(request, "web/goals.html", ctx, status=status)


def _finish(request, pk, notice):
    if "application/json" in request.headers.get("Accept", ""):
        goal = get_object_or_404(owned_goals(request.user), pk=pk)
        return _response(request, _context(request, goal), notice=notice)
    return redirect("goal_detail", pk=pk)


@login_required(login_url="/login/")
@never_cache
@require_http_methods(["GET", "POST"])
def home(request):
    if request.method == "POST":
        form = GoalForm(request.POST, request.FILES)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            url = reverse("goal_detail", args=[goal.pk])
            if "application/json" in request.headers.get("Accept", ""):
                return JsonResponse({"redirect": url}, status=201)
            return redirect(url)
        return _response(request, _context(request, goal_form=form, show_compose=True), status=400)
    return _response(request, _context(request))


@login_required(login_url="/login/")
@never_cache
@require_http_methods(["GET", "POST"])
def detail(request, pk):
    goal = get_object_or_404(owned_goals(request.user), pk=pk)
    if request.method == "POST":
        action = request.POST.get("action", "edit")
        if action == "pause":
            goal.paused = not goal.paused
            goal.save(update_fields=["paused"])
        elif action == "complete" and goal.total_steps == 0:
            goal.marked_complete = not goal.marked_complete
            goal.save(update_fields=["marked_complete"])
        elif action == "edit":
            form = GoalForm(request.POST, request.FILES, instance=goal)
            if not form.is_valid():
                return _response(request, _context(request, goal, goal_form=form, show_compose=True), status=400)
            form.save()
        else:
            return JsonResponse({"error": "Invalid goal action."}, status=400)
        return _finish(request, pk, "Goal updated.")
    return _response(request, _context(request, goal))


@login_required(login_url="/login/")
@never_cache
@require_POST
def add_step(request, pk):
    goal = get_object_or_404(owned_goals(request.user), pk=pk)
    form = StepForm(request.POST, goal=goal)
    if not form.is_valid():
        return _response(request, _context(request, goal, step_form=form), status=400)
    with transaction.atomic():
        step = form.save(commit=False)
        step.goal = goal
        step.save()
        goal.marked_complete = False
        goal.save(update_fields=["marked_complete"])
    return _finish(request, pk, "Step added.")


@login_required(login_url="/login/")
@never_cache
@require_POST
def ai_plan(request, pk):
    goal = get_object_or_404(owned_goals(request.user), pk=pk)
    action = request.POST.get("action", "suggest")
    if action == "suggest":
        if settings.AI_PROVIDER in CLOUD_PROVIDERS and request.POST.get("consent") != "yes":
            return JsonResponse({"error": "Confirm before sending goal details to the AI provider."}, status=400)
        try:
            result = suggest_goal_steps(
                goal.title,
                goal.why,
                goal.category,
                goal.target_date,
                goal.steps.values_list("title", flat=True),
            )
        except AIProviderError as exc:
            return JsonResponse({"error": str(exc)}, status=422)
        return JsonResponse({"suggestions": result["steps"], "provider": settings.AI_PROVIDER})

    if action != "accept":
        return JsonResponse({"error": "Invalid AI plan action."}, status=400)
    try:
        submitted = json.loads(request.POST.get("steps", "[]"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Choose valid suggested steps."}, status=400)
    if not isinstance(submitted, list) or not submitted or len(submitted) > 8:
        return JsonResponse({"error": "Choose between one and eight suggested steps."}, status=400)

    titles = []
    for value in submitted:
        if not isinstance(value, str):
            return JsonResponse({"error": "Choose valid suggested steps."}, status=400)
        form = StepForm({"title": value.strip()}, goal=goal)
        if not form.is_valid():
            return JsonResponse({"error": "Check the suggested step titles."}, status=400)
        titles.append(form.cleaned_data["title"])

    with transaction.atomic():
        locked_goal = get_object_or_404(Goal.objects.select_for_update(), pk=goal.pk, user=request.user)
        existing = {value.casefold() for value in locked_goal.steps.values_list("title", flat=True)}
        created = 0
        for title in titles:
            key = title.casefold()
            if key in existing:
                continue
            GoalStep.objects.create(goal=locked_goal, title=title)
            existing.add(key)
            created += 1
        if created and locked_goal.marked_complete:
            locked_goal.marked_complete = False
            locked_goal.save(update_fields=["marked_complete"])
    return _finish(request, pk, "Suggested steps added." if created else "Those steps are already in your plan.")


@login_required(login_url="/login/")
@never_cache
@require_POST
def step_action(request, pk, step_pk):
    with transaction.atomic():
        step = get_object_or_404(GoalStep.objects.select_for_update().select_related("goal", "task"), pk=step_pk, goal_id=pk, goal__user=request.user)
        action = request.POST.get("action")
        if action == "toggle":
            if step.task_id:
                task_toggle(request, step.task_id)
            else:
                step.is_done = not step.is_done
                step.save(update_fields=["is_done"])
        elif action == "task":
            if not step.task_id:
                date = max(step.target_date, timezone.localdate()) if step.target_date else None
                form = TaskForm({"title": step.title, "date": date, "category": step.goal.category})
                if not form.is_valid():
                    return JsonResponse({"error": "Check the step date."}, status=400)
                task = form.save(commit=False)
                task.user = request.user
                if step.is_done:
                    task.status, task.completed_at = "done", timezone.now()
                task.save()
                step.task = task
                step.save(update_fields=["task"])
        elif action == "delete":
            step.delete()
        else:
            return JsonResponse({"error": "Invalid step action."}, status=400)
    return _finish(request, pk, "Step updated.")


@login_required(login_url="/login/")
@never_cache
@require_http_methods(["GET", "POST"])
def delete(request, pk):
    goal = get_object_or_404(owned_goals(request.user), pk=pk)
    if request.method == "POST" and request.POST.get("confirm") == "yes":
        goal.delete()
        if "application/json" in request.headers.get("Accept", ""):
            return JsonResponse({"redirect": reverse("goals_home")})
        return redirect("goals_home")
    return render(request, "web/goal-delete.html", {**context(request), "section": "goals", "goal": goal})


@login_required(login_url="/login/")
@never_cache
def image(request, pk):
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    if not goal.image:
        raise Http404
    try:
        response = FileResponse(goal.image.open("rb"), content_type="image/jpeg")
    except (FileNotFoundError, OSError):
        raise Http404
    response["Content-Disposition"] = 'inline; filename="goal.jpg"'
    response["Cache-Control"] = "private, no-store"
    return response
