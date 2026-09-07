from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from notifications.utils import log_activity
from .models import Event, EventRegistration


@login_required
def event_list(request):
    events = Event.objects.filter(status='Open').annotate(
        registered=Count('registrations')
    ).order_by('event_date')
    q = request.GET.get('q', '').strip()
    month = request.GET.get('month', '').strip()
    if q:
        events = events.filter(title__icontains=q)
    if month:
        events = events.filter(event_date__month=month)
    my_ids = EventRegistration.objects.filter(user=request.user).values_list('event_id', flat=True)
    for event in events:
        event.registered_by_me = event.id in my_ids
        event.spots_left = max(0, event.capacity - event.registered)
    return render(request, 'events/list.html', {'events': events, 'q': q, 'month': month})


@login_required
def register_event(request, event_id):
    event = get_object_or_404(Event, id=event_id, status='Open')
    if EventRegistration.objects.filter(event=event, user=request.user).exists():
        messages.error(request, 'You are already registered for this event.')
        return redirect('event_list')
    if event.registrations.count() >= event.capacity:
        messages.error(request, 'Sorry, this event is already full.')
        return redirect('event_list')
    EventRegistration.objects.create(event=event, user=request.user)
    log_activity(request.user, 'Event registered', f'Registered for "{event.title}"', request)
    messages.success(request, f'You are registered for "{event.title}". See you there!')
    return redirect('event_list')


@login_required
def cancel_event(request, event_id):
    registration = get_object_or_404(EventRegistration, id=event_id, user=request.user)
    title = registration.event.title
    registration.delete()
    messages.success(request, f'Your registration for "{title}" has been cancelled.')
    return redirect('user_events')