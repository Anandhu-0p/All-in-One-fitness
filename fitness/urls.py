from django.urls import path

from . import views

urlpatterns = [
    path('plans/', views.workout_plans, name='fitness_plans'),
    path('diet-plans/', views.diet_plans, name='user_diet_plans'),
    path('videos/', views.videos, name='fitness_videos'),
    path('tips/', views.tips, name='user_tips'),
]