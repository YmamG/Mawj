from django.urls import path

from . import views

urlpatterns = [
    path("", views.journal_list, name="journal_list"),
    path("add/", views.journal_create, name="journal_create"),
    path("<int:pk>/", views.journal_detail, name="journal_detail"),
    path("<int:pk>/delete/", views.journal_delete, name="journal_delete"),
    path("suggestions/<int:pk>/accept/", views.suggestion_accept, name="suggestion_accept"),
    path("suggestions/<int:pk>/dismiss/", views.suggestion_dismiss, name="suggestion_dismiss"),
]
