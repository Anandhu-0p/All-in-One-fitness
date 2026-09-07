from django.urls import path

from . import views

urlpatterns = [
    path('notifications/', views.NotificationsAPI.as_view(), name='api_notifications'),
    path('events/', views.EventsAPI.as_view(), name='api_events'),
    path('progress/', views.ProgressAPI.as_view(), name='api_progress'),
    path('payments/', views.PaymentsAPI.as_view(), name='api_payments'),
    path('workouts/', views.WorkoutsAPI.as_view(), name='api_workouts'),
    path('diets/', views.DietsAPI.as_view(), name='api_diets'),
    path('attendance/', views.AttendanceAPI.as_view(), name='api_attendance'),
    path('chat/<int:conversation_id>/messages/', views.ChatMessagesAPI.as_view(), name='api_chat_messages'),
    path('tips/', views.TipsAPI.as_view(), name='api_tips'),
    path('videos/', views.VideosAPI.as_view(), name='api_videos'),
    path('summary/', views.DashboardSummaryAPI.as_view(), name='api_summary'),
]