from django.urls import path

from . import views

urlpatterns = [
    path('', views.chat_home, name='chat_home'),
    path('thread/<int:conversation_id>/', views.chat_thread, name='chat_thread'),
    path('start/<str:target_type>/<int:target_id>/', views.chat_start, name='chat_start'),
]