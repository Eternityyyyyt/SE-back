from django.urls import path, include
import chat.views as views

urlpatterns = [
    path('message',views.message),
]