from django.contrib import admin

from .models import Attendance, Batch, BatchMembership, TrainerAssignment, TrainerProfile


@admin.register(TrainerProfile)
class TrainerProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'specialization', 'experience', 'is_active']
    search_fields = ['full_name', 'email', 'specialization']
    list_filter = ['is_active', 'specialization']


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'capacity', 'status']
    search_fields = ['name']
    list_filter = ['status']


@admin.register(BatchMembership)
class BatchMembershipAdmin(admin.ModelAdmin):
    list_display = ['batch', 'user', 'joined_date', 'status']
    search_fields = ['batch__name', 'user__username']
    list_filter = ['status']


@admin.register(TrainerAssignment)
class TrainerAssignmentAdmin(admin.ModelAdmin):
    list_display = ['batch', 'trainer', 'assigned_date', 'status']
    list_filter = ['status']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['user', 'batch', 'trainer', 'date', 'status']
    search_fields = ['user__username', 'batch__name']
    list_filter = ['status', 'date']