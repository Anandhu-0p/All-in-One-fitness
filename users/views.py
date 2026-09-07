from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.forms import HealthDetailsForm
from accounts.models import UserProfile
from events.models import Event, EventRegistration
from experts.models import DietPlan, UserDietAssignment
from fitness.models import UserWorkoutAssignment
from notifications.utils import log_activity
from payments.models import MembershipPlan, Payment, PaymentAlert
from trainers.models import Attendance, BatchMembership, TrainerAssignment
from users.models import HealthRecord, ProgressRecord

from .forms import ProgressEntryForm

user_required = user_passes_test(
    lambda u: u.is_authenticated and (u.groups.filter(name='User').exists() or not (u.is_superuser or u.groups.filter(name='Trainer').exists() or u.groups.filter(name='Expert').exists())),
    login_url='login',
)


def _attendance_stats(user):
    total = Attendance.objects.filter(user=user).count()
    present = Attendance.objects.filter(user=user, status='Present').count()
    pct = round((present / total) * 100) if total else 0
    return {'total': total, 'present': present, 'percentage': pct}


def _payment_status(user):
    latest = Payment.objects.filter(user=user).order_by('-payment_date').first()
    due_alerts = PaymentAlert.objects.filter(user=user, is_read=False).count()
    return {'latest': latest, 'due_alerts': due_alerts}


@login_required
@user_required
def dashboard(request):
    user = request.user
    profile = UserProfile.objects.filter(user=user).first()
    membership = BatchMembership.objects.filter(user=user, status='Active').select_related('batch').first()
    workout = UserWorkoutAssignment.objects.filter(user=user, status='Active').select_related('workout_plan').order_by('-start_date').first()
    diet = UserDietAssignment.objects.filter(user=user, status='Active').select_related('diet_plan').order_by('-start_date').first()
    attendance = _attendance_stats(user)
    payment = _payment_status(user)
    events = Event.objects.filter(status='Open', event_date__gte=date.today()).order_by('event_date')[:5]
    my_events = EventRegistration.objects.filter(user=user).select_related('event').order_by('-registered_at')[:5]
    progress = ProgressRecord.objects.filter(user=user).order_by('-recorded_at')[:5]
    trainer = None
    if membership:
        assignment = TrainerAssignment.objects.filter(batch=membership.batch, status='Active').select_related('trainer').first()
        if assignment:
            trainer = assignment.trainer
    context = {
        'profile': profile,
        'membership': membership,
        'workout': workout,
        'diet': diet,
        'attendance': attendance,
        'payment': payment,
        'events': events,
        'my_events': my_events,
        'recent_progress': progress,
        'trainer': trainer,
    }
    return render(request, 'users/dashboard.html', context)


@login_required
@user_required
def profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    membership = BatchMembership.objects.filter(user=request.user, status='Active').select_related('batch').first()
    return render(request, 'users/profile.html', {'profile': profile, 'membership': membership})


@login_required
@user_required
def health_details(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    records = HealthRecord.objects.filter(user=request.user).order_by('-recorded_at')
    if request.method == 'POST':
        form = HealthDetailsForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            log_activity(request.user, 'Health updated', 'User updated their health details', request)
            messages.success(request, 'Health details saved.')
            return redirect('user_health')
    else:
        latest = records.first()
        form = HealthDetailsForm(instance=profile, initial={
            'height': latest.height if latest else None,
            'weight': latest.weight if latest else None,
        })
    return render(request, 'users/health.html', {'form': form, 'records': records, 'profile': profile})


@login_required
@user_required
def attendance(request):
    entries = Attendance.objects.filter(user=request.user).select_related('batch').order_by('-date')
    stats = _attendance_stats(request.user)
    status = request.GET.get('status', '').strip()
    if status:
        entries = entries.filter(status=status)
    return render(request, 'users/attendance.html', {'entries': entries, 'stats': stats, 'status': status})


@login_required
@user_required
def progress(request):
    records = ProgressRecord.objects.filter(user=request.user).order_by('recorded_at')
    if request.method == 'POST':
        form = ProgressEntryForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.user = request.user
            record.save()
            log_activity(request.user, 'Progress added', 'User recorded a progress measurement', request)
            messages.success(request, 'Progress measurement saved.')
            return redirect('user_progress')
    else:
        form = ProgressEntryForm()
    weights = [{'date': r.recorded_at.strftime('%Y-%m-%d'), 'weight': r.weight} for r in records if r.weight]
    body_fat = [{'date': r.recorded_at.strftime('%Y-%m-%d'), 'value': r.body_fat_percentage} for r in records if r.body_fat_percentage]
    waist = [{'date': r.recorded_at.strftime('%Y-%m-%d'), 'value': r.waist_measurement} for r in records if r.waist_measurement]
    return render(request, 'users/progress.html', {
        'form': form, 'records': records,
        'weights': weights, 'body_fat': body_fat, 'waist': waist,
    })


@login_required
@user_required
def my_events(request):
    registrations = EventRegistration.objects.filter(user=request.user).select_related('event').order_by('-registered_at')
    return render(request, 'users/events.html', {'registrations': registrations})


@login_required
@user_required
def payments(request):
    items = Payment.objects.filter(user=request.user).select_related('membership_plan').order_by('-payment_date')
    alerts = PaymentAlert.objects.filter(user=request.user).order_by('-created_at')
    plans = MembershipPlan.objects.filter(is_active=True)
    payment = _payment_status(request.user)
    return render(request, 'users/payments.html', {
        'items': items, 'alerts': alerts, 'plans': plans, 'payment': payment,
    })


@login_required
@user_required
def pay_now(request, plan_id):
    plan = get_object_or_404(MembershipPlan, id=plan_id, is_active=True)
    if request.method == 'POST':
        today = date.today()
        transaction_id = f'TXN-{request.user.id}-{today.strftime("%Y%m%d%H%M%S")}'
        Payment.objects.create(
            user=request.user,
            membership_plan=plan,
            amount=plan.amount,
            payment_month=today.strftime('%B'),
            payment_year=str(today.year),
            payment_method='Demo Card (•••• 4242)',
            transaction_id=transaction_id,
            status='Paid',
        )
        PaymentAlert.objects.filter(user=request.user).update(is_read=True)
        log_activity(request.user, 'Payment made', f'Paid {plan.name} via demo gateway', request)
        messages.success(request, f'Payment of ₹{plan.amount} recorded successfully. Receipt: {transaction_id}')
        return redirect('user_payments')
    return render(request, 'users/pay_now.html', {'plan': plan})