from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Sum
from django.shortcuts import render

from events.models import Event
from payments.models import Payment
from trainers.models import Attendance, BatchMembership


@login_required
def admin_report(request):
    total_users = User.objects.count()
    trainers = User.objects.filter(groups__name='Trainer').count()
    experts = User.objects.filter(groups__name='Expert').count()
    active_memberships = BatchMembership.objects.filter(status='Active').count()
    pending_payments = Payment.objects.filter(status='Pending').count()
    upcoming_events = Event.objects.filter(status='Open').count()
    attendance_summary = Attendance.objects.values('status').annotate(total=Count('status'))
    revenue = Payment.objects.filter(status='Paid').aggregate(total=Sum('amount'))['total'] or 0
    context = {
        'total_users': total_users,
        'trainers': trainers,
        'experts': experts,
        'active_memberships': active_memberships,
        'pending_payments': pending_payments,
        'upcoming_events': upcoming_events,
        'attendance_summary': attendance_summary,
        'revenue': revenue,
    }
    return render(request, 'reports/admin.html', context)


@login_required
def trainer_report(request):
    return render(request, 'reports/trainer.html', {'attendance_summary': []})


@login_required
def user_report(request):
    return render(request, 'reports/user.html', {'entries': []})
