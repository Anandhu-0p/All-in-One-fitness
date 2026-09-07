from django.contrib import admin

from .models import DietPlan, DietPlanMeal, ExpertProfile, FitnessVideo, UserDietAssignment, WellnessTip


@admin.register(ExpertProfile)
class ExpertProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'specialization', 'is_active']
    search_fields = ['full_name', 'email', 'specialization']
    list_filter = ['is_active']


@admin.register(DietPlan)
class DietPlanAdmin(admin.ModelAdmin):
    list_display = ['title', 'goal', 'calories', 'dietary_preference', 'created_by_expert', 'is_active']
    search_fields = ['title', 'goal']
    list_filter = ['is_active', 'dietary_preference']


@admin.register(DietPlanMeal)
class DietPlanMealAdmin(admin.ModelAdmin):
    list_display = ['diet_plan', 'meal_type', 'meal_name', 'calories', 'order']


@admin.register(UserDietAssignment)
class UserDietAssignmentAdmin(admin.ModelAdmin):
    list_display = ['diet_plan', 'user', 'assigned_by', 'start_date', 'status']


@admin.register(FitnessVideo)
class FitnessVideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'uploaded_by_expert', 'created_at', 'is_active']
    search_fields = ['title', 'category']
    list_filter = ['is_active', 'category']


@admin.register(WellnessTip)
class WellnessTipAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'author', 'created_at', 'is_published']
    search_fields = ['title', 'content']
    list_filter = ['is_published', 'category']