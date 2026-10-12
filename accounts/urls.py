from django.contrib.auth import views as auth_views
from django.urls import path
from django.conf import settings
from django.shortcuts import redirect

from . import views

def frontend_or_legacy(view, destination):
    def dispatch(request, *args, **kwargs):
        if settings.FRONTEND_URL:
            return redirect(settings.FRONTEND_URL + destination)
        return view(request, *args, **kwargs)
    return dispatch


urlpatterns = [
    path("login/", frontend_or_legacy(auth_views.LoginView.as_view(), "/login"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("signup/", frontend_or_legacy(views.signup, "/signup"), name="signup"),
    path("profile/avatar/", views.avatar, name="avatar"),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("theme/", views.theme_update, name="theme_update"),
]
