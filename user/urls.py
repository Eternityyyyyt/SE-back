from django.urls import path, include
import user.views as views

urlpatterns = [
    path('startup', views.startup),
    path('login', views.login),
    path('register', views.register),
]