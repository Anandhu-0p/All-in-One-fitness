from django.urls import path

from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='expert_dashboard'),
    path('profile/', views.profile, name='expert_profile'),

    # Diet plans
    path('diet-plans/', views.diet_plans, name='expert_diet_plans'),
    path('diet-plans/create/', views.diet_create, name='expert_diet_create'),
    path('diet-plans/<int:plan_id>/edit/', views.diet_edit, name='expert_diet_edit'),
    path('diet-plans/<int:plan_id>/delete/', views.diet_delete, name='expert_diet_delete'),
    path('diet-plans/<int:plan_id>/assign/', views.diet_assign, name='expert_diet_assign'),

    # Videos
    path('videos/', views.videos, name='expert_videos'),
    path('videos/create/', views.video_create, name='expert_video_create'),
    path('videos/<int:video_id>/edit/', views.video_edit, name='expert_video_edit'),
    path('videos/<int:video_id>/delete/', views.video_delete, name='expert_video_delete'),

    # Tips
    path('tips/', views.wellness_tips, name='expert_tips'),
    path('tips/create/', views.tip_create, name='expert_tip_create'),
    path('tips/<int:tip_id>/edit/', views.tip_edit, name='expert_tip_edit'),
    path('tips/<int:tip_id>/delete/', views.tip_delete, name='expert_tip_delete'),

    # Users
    path('users/', views.users_list, name='expert_users'),
    path('users/<int:user_id>/', views.user_detail, name='expert_user_detail'),
]