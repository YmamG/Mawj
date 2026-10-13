from django.urls import path
from . import views
urlpatterns=[path('',views.public,name='web_home'),path('login/',views.public,{'page':'login'},name='web_login'),path('signup/',views.public,{'page':'signup'},name='web_signup'),path('about/',views.public,{'page':'about'},name='web_about'),path('privacy/',views.public,{'page':'privacy'},name='web_privacy'),path('app/<str:section>/',views.workspace,name='web_workspace')]
