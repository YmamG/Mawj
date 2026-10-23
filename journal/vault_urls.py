from django.urls import path
from . import vault_api as views

urlpatterns = [
    path("", views.vault),
    path("key/", views.managed_key),
    path("reset/", views.reset_legacy),
    path("entries/", views.notes),
    path("entries/<uuid:pk>/", views.note),
    path("entries/<uuid:pk>/tasks/", views.accept_task),
    path("legacy/", views.legacy),
    path("legacy/<int:pk>/", views.import_legacy),
    path("analyze/", views.analyze),
]
