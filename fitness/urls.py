from django.urls import path

from . import views

urlpatterns = [
    path('plans/', views.workout_plans, name='fitness_plans'),
    path('videos/', views.videos, name='fitness_videos'),
]
