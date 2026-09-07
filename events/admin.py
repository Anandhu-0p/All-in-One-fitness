from django.contrib import admin

from .models import Event, EventRegistration


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'venue', 'event_date', 'start_time', 'end_time', 'capacity', 'status']
    search_fields = ['title', 'venue']
    list_filter = ['status', 'event_date']


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ['event', 'user', 'registered_at', 'status']
    list_filter = ['status']