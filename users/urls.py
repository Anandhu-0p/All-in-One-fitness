from django.urls import path

from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='user_dashboard'),
    path('profile/', views.profile, name='user_profile_page'),
    path('health/', views.health_details, name='user_health'),
    path('attendance/', views.attendance, name='user_attendance'),
    path('progress/', views.progress, name='user_progress'),
    path('events/', views.my_events, name='user_events'),
    path('payments/', views.payments, name='user_payments'),
    path('payments/pay/<int:plan_id>/', views.pay_now, name='pay_now'),
]