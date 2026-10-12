from dashboard.views import achievements
from django.contrib import admin
from django.conf import settings
from django.shortcuts import redirect
from django.urls import include, path

urlpatterns = [
    path("api/", include("config.api_urls")),
    path("achievements/", achievements, name="achievements"),
    path("admin/", admin.site.urls),
    path("", lambda request: redirect(settings.FRONTEND_URL or "task_list")),
    path("accounts/", include("accounts.urls")),
    path("tasks/", include("tasks.urls")),
    path("journal/", include("journal.urls")),
    path("calendar/", include("dashboard.urls")),
]
