from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from events.models import Event, EventRegistration


@login_required
def event_list(request):
    events = Event.objects.filter(status='Open').order_by('event_date')
    return render(request, 'events/list.html', {'events': events})


@login_required
def register_event(request, event_id):
    event = Event.objects.get(id=event_id)
    if EventRegistration.objects.filter(event=event, user=request.user).exists():
        messages.error(request, 'You are already registered for this event.')
        return redirect('event_list')
    EventRegistration.objects.create(event=event, user=request.user)
    messages.success(request, 'You have successfully registered.')
    return redirect('event_list')
