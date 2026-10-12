from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponseBadRequest, FileResponse, Http404
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import ProfileEditForm, ThemeSelectionForm
from .models import UserPreferences
from journal.models import JournalEntry
from tasks.models import Task


def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("task_list")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})


@login_required
def profile(request):
    user_tasks = Task.objects.filter(user=request.user)
    preferences, _ = UserPreferences.objects.get_or_create(user=request.user)
    context = {
        "profile_user": request.user,
        "preferences": preferences,
        "display_name": preferences.display_name,
        "journal_count": JournalEntry.objects.filter(user=request.user).count(),
        "total_tasks": user_tasks.count(),
        "completed_tasks": user_tasks.filter(status="done").count(),
        "pending_tasks": user_tasks.filter(status="todo").count(),
    }
    return render(request, "accounts/profile.html", context)


@login_required
def profile_edit(request):
    preferences, _ = UserPreferences.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = ProfileEditForm(request.POST, request.FILES, user=request.user, preferences=preferences)
        if form.is_valid():
            form.save()
            return redirect("profile")
    else:
        form = ProfileEditForm(user=request.user, preferences=preferences)
    return render(request, "accounts/profile_edit.html", {"form": form})


@login_required
@require_POST
def theme_update(request):
    form = ThemeSelectionForm(request.POST)
    if form.is_valid():
        preferences, _ = UserPreferences.objects.get_or_create(user=request.user)
        preferences.theme = form.cleaned_data["theme"]
        preferences.save(update_fields=["theme"])
    else:
        return HttpResponseBadRequest("Choose one of the available themes.")

    return_to = request.POST.get("next", "")
    if url_has_allowed_host_and_scheme(
        return_to,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(return_to)
    return redirect("task_list")


@login_required
def avatar(request):
    preferences = UserPreferences.objects.filter(user=request.user).first()
    if not preferences or not preferences.avatar:
        raise Http404("No profile photo.")
    try:
        response = FileResponse(preferences.avatar.open("rb"), content_type="image/png")
    except FileNotFoundError:
        raise Http404("No profile photo.")
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response
