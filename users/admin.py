from django.contrib import admin

from .models import HealthRecord, ProgressRecord


@admin.register(HealthRecord)
class HealthRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'height', 'weight', 'bmi', 'recorded_at']
    search_fields = ['user__username', 'user__email']
    list_filter = ['recorded_at']


@admin.register(ProgressRecord)
class ProgressRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'weight', 'waist_measurement', 'recorded_at']
    search_fields = ['user__username', 'user__email']
    list_filter = ['recorded_at']