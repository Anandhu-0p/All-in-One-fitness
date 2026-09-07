from django.urls import path

from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='expert_dashboard'),
    path('diet-plans/', views.diet_plans, name='expert_diet_plans'),
    path('videos/', views.videos, name='expert_videos'),
    path('tips/', views.wellness_tips, name='expert_tips'),
]
