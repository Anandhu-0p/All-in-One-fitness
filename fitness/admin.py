from django.contrib import admin

from .models import UserWorkoutAssignment, WorkoutExercise, WorkoutPlan


@admin.register(WorkoutPlan)
class WorkoutPlanAdmin(admin.ModelAdmin):
    list_display = ['title', 'goal', 'difficulty_level', 'duration_weeks', 'created_by_trainer', 'is_active']
    search_fields = ['title', 'goal']
    list_filter = ['difficulty_level', 'is_active']


@admin.register(WorkoutExercise)
class WorkoutExerciseAdmin(admin.ModelAdmin):
    list_display = ['workout_plan', 'exercise_name', 'sets', 'repetitions', 'order']


@admin.register(UserWorkoutAssignment)
class UserWorkoutAssignmentAdmin(admin.ModelAdmin):
    list_display = ['workout_plan', 'user', 'assigned_by', 'start_date', 'status']
    list_filter = ['status']