from django.urls import path

from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='trainer_dashboard'),
    path('profile/', views.profile, name='trainer_profile'),
    path('batches/', views.batches, name='trainer_batches'),
    path('batches/<int:batch_id>/members/', views.batch_members, name='trainer_batch_members'),

    # Workout plans
    path('workout-plans/', views.workout_plans, name='trainer_workout_plans'),
    path('workout-plans/create/', views.workout_create, name='trainer_workout_create'),
    path('workout-plans/<int:plan_id>/edit/', views.workout_edit, name='trainer_workout_edit'),
    path('workout-plans/<int:plan_id>/delete/', views.workout_delete, name='trainer_workout_delete'),
    path('workout-plans/<int:plan_id>/assign/', views.workout_assign, name='trainer_workout_assign'),

    # Attendance
    path('attendance/', views.attendance, name='trainer_attendance'),
    path('attendance/mark/', views.attendance_mark, name='trainer_attendance_mark'),

    # Health & progress
    path('user-health/', views.user_health, name='trainer_user_health'),
    path('user-health/<int:user_id>/', views.member_health, name='member_health'),
    path('user-health/<int:user_id>/add/', views.member_health_add, name='member_health_add'),
    path('progress/', views.progress, name='trainer_progress'),
    path('progress/<int:user_id>/add/', views.member_progress_add, name='member_progress_add'),
]