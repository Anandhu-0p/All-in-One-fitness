from django.urls import path

from . import views

urlpatterns = [
    path('', views.notifications_list, name='notifications_list'),
    path('read/<int:notification_id>/', views.notification_mark_read, name='notification_mark_read'),
    path('read-all/', views.notification_mark_all, name='notification_mark_all'),
    path('feedback/', views.feedback_form, name='feedback_form'),
    path('feedback/my/', views.feedback_my, name='feedback_my'),
]