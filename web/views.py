"""Server-rendered presentation over the same authenticated Django business endpoints."""
import calendar
import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.middleware.csrf import get_token
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache

from config import api
from .templatetags.mawj import MESSAGES

THEMES = [("grove", "Grove"), ("petal", "Petal"), ("dusk", "Dusk"), ("ember", "Ember"), ("midnight", "Midnight")]
NAV = [
    ("today", "Today", "Sun"), ("tasks", "My tasks", "CheckCircle"),
    ("journal", "Journal", "Notebook"), ("achievements", "Progress", "ChartBar"),
    ("calendar", "Calendar", "CalendarBlank"), ("profile", "My space", "UserCircle"),
]
COPY = {
    "today": ("A fresh little beginning", "Let’s find your flow.", "A little structure. A little breathing room."),
    "tasks": ("One thing at a time", "Make a little room.", "Keep what matters in sight. Let the rest wait."),
    "journal": ("A space for your thoughts", "Let it out.", "The messy thoughts, the small joys, the in-between."),
    "achievements": ("Small steps add up", "Look how far you’ve come.", "A little perspective on the plans you’re making."),
    "calendar": ("Your days, at a glance", "Find your rhythm.", "See what’s coming. Leave a little room for yourself."),
    "profile": ("Your space, your pace", "A few things about you.", "The little details that make this place yours."),
}


def context(request):
    account = api.account_data(request.user) if request.user.is_authenticated else None
    lang = "ar" if request.COOKIES.get("mawj-language") == "ar" else "en"
    theme = account["theme"] if account else request.COOKIES.get("mawj-theme", "grove")
    return {
        "lang": lang, "theme": theme if theme in dict(THEMES) else "grove",
        "account": account, "themes": THEMES, "navigation": NAV,
        "today": timezone.localdate().isoformat(), "provider": settings.AI_PROVIDER,
        "sends_to_cloud": settings.AI_PROVIDER in api.CLOUD_PROVIDERS,
        "boot": {"language": lang, "user": account, "csrf": get_token(request),
                 "provider": settings.AI_PROVIDER, "translations": MESSAGES},
    }


@never_cache
def public(request, page="landing"):
    if page not in ("landing", "login", "signup", "about", "privacy"):
        raise Http404
    if page in ("login", "signup") and request.user.is_authenticated:
        return redirect("/app/today/")
    ctx = context(request)
    return render(request, f'web/{page}-{ctx["lang"]}.html', ctx)


@login_required(login_url="/login/")
@never_cache
def workspace(request, section="today"):
    handlers = {
        "today": api.today, "tasks": api.tasks, "journal": api.journals,
        "achievements": api.achievements, "calendar": api.month, "profile": api.profile,
    }
    if section not in handlers:
        return missing(request)
    # Reuse owner-filtered query/report logic; no HTTP call to our own server.
    response = handlers[section](request)
    data = json.loads(response.content)
    ctx = context(request)
    params = request.GET.copy()
    params.pop("page", None)
    ctx.update(
        categories=[("uncategorized", "Uncategorized"), ("study", "Study"), ("personal", "Personal"), ("work", "Work")],
        priorities=[("low", "Low"), ("medium", "Medium"), ("high", "High")],
        periods=[("week", "This week"), ("month", "This month"), ("year", "This year")],
        section=section, heading=COPY[section], data=data,
        pagination_query=params.urlencode(), page_error=data.get("error", ""), initial_data=data,
    )
    if section == "calendar" and response.status_code == 200:
        year, month = data["year"], data["month"]
        ctx.update(
            calendar_offset=range((calendar.weekday(year, month, 1) + 1) % 7),
            month_heading=f"{month:02d} / {year}",
            weekdays=["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
        )
    return render(request, "web/workspace.html", ctx, status=response.status_code)


@never_cache
def missing(request, unmatched=None):
    return render(request, "web/missing.html", context(request), status=404)
