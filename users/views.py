from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from accounts.models import UserProfile
from events.models import Event, EventRegistration
from fitness.models import UserWorkoutAssignment
from payments.models import Payment
from trainers.models import Attendance, BatchMembership


@login_required
def dashboard(request):
    user = request.user
    profile = UserProfile.objects.filter(user=user).first()
    assigned_batch = BatchMembership.objects.filter(user=user, status='Active').select_related('batch').first()
    workout = UserWorkoutAssignment.objects.filter(user=user, status='Active').select_related('workout_plan').order_by('-start_date').first()
    payment = Payment.objects.filter(user=user).order_by('-payment_date').first()
    events = Event.objects.filter(status='Open').order_by('event_date')[:5]
    attendance = Attendance.objects.filter(user=user).count()
    context = {
        'profile': profile,
        'assigned_batch': assigned_batch,
        'workout': workout,
        'payment': payment,
        'events': events,
        'attendance': attendance,
    }
    return render(request, 'users/dashboard.html', context)


@login_required
def profile(request):
    profile = UserProfile.objects.filter(user=request.user).first()
    return render(request, 'users/profile.html', {'profile': profile})


@login_required
def health_details(request):
    return render(request, 'users/health.html', {})


@login_required
def my_events(request):
    registrations = EventRegistration.objects.filter(user=request.user)
    return render(request, 'users/events.html', {'registrations': registrations})


@login_required
def payments(request):
    payments = Payment.objects.filter(user=request.user).order_by('-payment_date')
    return render(request, 'users/payments.html', {'payments': payments})


@login_required
def notifications(request):
    return render(request, 'users/notifications.html', {})
