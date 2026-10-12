from django.urls import path
from . import api
urlpatterns = [
    path("session/", api.session), path("auth/login/", api.signin), path("auth/signup/", api.signup), path("auth/logout/", api.signout),
    path("profile/", api.profile), path("profile/avatar/", api.endpoint()(api.avatar)), path("theme/", api.theme),
    path("tasks/", api.tasks), path("tasks/suggest/", api.task_suggest), path("tasks/<int:pk>/", api.task), path("today/", api.today),
    path("journal/", api.journals), path("journal/<int:pk>/", api.journal), path("suggestions/<int:pk>/", api.suggestion),
    path("achievements/", api.achievements), path("calendar/", api.month),
]
