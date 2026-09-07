from django.urls import path

from . import views

urlpatterns = [
    path('admin/', views.admin_report, name='reports_admin'),
    path('trainer/', views.trainer_report, name='reports_trainer'),
    path('user/', views.user_report, name='reports_user'),
]