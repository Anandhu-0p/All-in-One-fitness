from django.urls import path

from . import views

urlpatterns = [
    path('admin/', views.admin_report, name='admin_dashboard'),
    path('trainer/', views.trainer_report, name='trainer_report'),
    path('user/', views.user_report, name='user_report'),
]
