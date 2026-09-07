from django.contrib import admin

from .models import PlatformContent, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'mobile_number', 'fitness_goal', 'is_active']
    search_fields = ['full_name', 'email', 'mobile_number']
    list_filter = ['is_active', 'gender', 'activity_level']


@admin.register(PlatformContent)
class PlatformContentAdmin(admin.ModelAdmin):
    list_display = ['key', 'title', 'updated_at']
    search_fields = ['key', 'title']