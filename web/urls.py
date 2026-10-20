from django.urls import path
from . import views

urlpatterns = [
    path('app/encrypted-journal/', views.encrypted_journal, name='encrypted_journal'),
    path('operator/accounts/', views.account_directory, name='account_directory'),
    path('', views.public, name='web_home'),
    path('login/', views.public, {'page': 'login'}, name='web_login'),
    path('signup/', views.public, {'page': 'signup'}, name='web_signup'),
    path('about/', views.public, {'page': 'about'}, name='web_about'),
    path('privacy/', views.public, {'page': 'privacy'}, name='web_privacy'),
    path('app/', views.workspace, name='web_workspace_home'),
    path('app/<str:section>/', views.workspace, name='web_workspace'),
]
