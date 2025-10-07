from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('token/', views.TokenView.as_view(), name='add_token'),
    path('channels/', views.ChannelsView.as_view(), name='get_channels'),
    path('post-message/', views.PostMessageView.as_view(), name='post_message'),
    path('post-thread-reply/', views.PostThreadReplyView.as_view(), name='post_thread_reply'),
]