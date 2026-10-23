from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="goals_home"),
    path("<int:pk>/", views.detail, name="goal_detail"),
    path("<int:pk>/image/", views.image, name="goal_image"),
    path("<int:pk>/delete/", views.delete, name="goal_delete"),
    path("<int:pk>/steps/", views.add_step, name="goal_add_step"),
    path("<int:pk>/ai-plan/", views.ai_plan, name="goal_ai_plan"),
    path("<int:pk>/steps/<int:step_pk>/", views.step_action, name="goal_step_action"),
]
