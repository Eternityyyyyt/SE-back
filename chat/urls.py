from django.urls import path, include
import chat.views as views

urlpatterns = [
    path('message',views.message),
    path('createPrivate', views.create_private),
    path('chat',views.chat_info),
    path('readMessage',views.read_message),
    path('messageReadStatus',views.message_read_status),
    path('createGroup',views.create_group),
    path('setAdmin',views.set_admin),
    path('changeOwner',views.change_owner),
]