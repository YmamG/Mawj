from dashboard.views import achievements
from web.views import missing
from django.contrib import admin
from django.conf import settings
from django.shortcuts import redirect
from django.urls import include, path

urlpatterns = [
    path("", include("web.urls")),
    path("api/", include("config.api_urls")),
    path("achievements/", achievements, name="achievements"),
    path("accounts/", include("accounts.urls")),
    path("tasks/", include("tasks.urls")),
    path("journal/", include("journal.urls")),
    path("calendar/", include("dashboard.urls")),
    path("<path:unmatched>", missing),
]

if getattr(settings, "ADMIN_ENABLED", True):
    # Keep development administration available, ahead of the branded catch-all.
    urlpatterns.insert(-1, path("admin/", admin.site.urls))
