from django.urls import path

from . import views

urlpatterns = [
    path("", views.calendar_current_month, name="calendar"),
    path("<int:year>/<int:month>/", views.calendar_month, name="calendar_month"),
    path("day/<int:year>/<int:month>/<int:day>/", views.day_detail, name="calendar_day"),
]