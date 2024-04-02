from django.urls import path, include
import user.views as views

urlpatterns = [
    path('startup', views.startup),
    path('login', views.login),
    path('register', views.register),
    path('user/<userName>',views.user_board),
    path('searchUser/<userName>',views.search_user),
    path('sendFriendRequest/<receiverName>',views.send_friend_request),
    path('friendRequest/<userName>',views.friend_request)
]