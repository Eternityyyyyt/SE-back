from django.urls import path, include
import chat.views as views

urlpatterns = [
    path('message',views.message),
    path('createPrivate', views.create_private),
    path('',views.chat_info)
]