from django.urls import path

from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='trainer_dashboard'),
    path('batches/', views.batches, name='trainer_batches'),
    path('attendance/', views.attendance, name='trainer_attendance'),
    path('user-health/', views.user_health, name='trainer_user_health'),
]
