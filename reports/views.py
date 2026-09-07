from datetime import date, timedelta

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import get_object_or_404, render

from events.models import Event
from experts.models import UserDietAssignment
from fitness.models import UserWorkoutAssignment
from notifications.models import Feedback
from payments.models import MembershipPlan, Payment
from trainers.models import Attendance, Batch, BatchMembership, TrainerAssignment, TrainerProfile
from users.models import HealthRecord, ProgressRecord

admin_required = user_passes_test(lambda u: u.is_authenticated and u.is_superuser, login_url='login')
trainer_required = user_passes_test(
    lambda u: u.is_authenticated and (u.is_superuser or u.groups.filter(name='Trainer').exists()),
    login_url='login',
)
user_required = user_passes_test(
    lambda u: u.is_authenticated and (u.groups.filter(name='User').exists() or not (u.is_superuser or u.groups.filter(name='Trainer').exists() or u.groups.filter(name='Expert').exists())),
    login_url='login',
)


def _last_months(n=6):
    labels, totals = [], []
    today = date.today()
    for i in range(n - 1, -1, -1):
        first = today.replace(day=1) - timedelta(days=30 * i)
        labels.append(first.strftime('%b %Y'))
        totals.append(float(Payment.objects.filter(
            status='Paid',
            payment_year=str(first.year),
            payment_month=first.strftime('%B'),
        ).aggregate(t=Sum('amount'))['t'] or 0))
    return labels, totals


@login_required
@admin_required
def admin_report(request):
    # Users by batch
    batch_labels = [b.name for b in Batch.objects.all()[:8]]
    batch_counts = [b.memberships.filter(status='Active').count() for b in Batch.objects.all()[:8]]

    month_labels, month_revenue = _last_months()

    attendance = Attendance.objects.values('status').annotate(total=Count('status'))
    attendance_labels = [a['status'] for a in attendance]
    attendance_counts = [a['total'] for a in attendance]

    event_labels, event_counts = [], []
    for event in Event.objects.annotate(reg=Count('registrations')).order_by('-reg')[:8]:
        event_labels.append(event.title[:24])
        event_counts.append(event.reg)

    rating_labels = ['1', '2', '3', '4', '5']
    rating_counts = [Feedback.objects.filter(rating=r).count() for r in range(1, 6)]

    payment_status = Payment.objects.values('status').annotate(total=Count('id'), amount=Sum('amount'))
    plans = MembershipPlan.objects.annotate(subscribers=Count('payment')).order_by('-subscribers')

    context = {
        'total_users': User.objects.filter(is_superuser=False).count(),
        'active_users': User.objects.filter(is_superuser=False, is_active=True).count(),
        'total_trainers': TrainerProfile.objects.count(),
        'total_experts': User.objects.filter(groups__name='Expert').count(),
        'total_revenue': Payment.objects.filter(status='Paid').aggregate(t=Sum('amount'))['t'] or 0,
        'pending_payments': Payment.objects.filter(status='Pending').count(),
        'batch_labels': batch_labels, 'batch_counts': batch_counts,
        'month_labels': month_labels, 'month_revenue': month_revenue,
        'attendance_labels': attendance_labels, 'attendance_counts': attendance_counts,
        'event_labels': event_labels, 'event_counts': event_counts,
        'rating_labels': rating_labels, 'rating_counts': rating_counts,
        'feedback_avg': Feedback.objects.aggregate(a=Avg('rating'))['a'] or 0,
        'payment_status': payment_status,
        'plans': plans,
    }
    return render(request, 'reports/admin.html', context)


@login_required
@trainer_required
def trainer_report(request):
    trainer = TrainerProfile.objects.filter(user=request.user).first()
    batches = Batch.objects.filter(
        trainer_assignments__trainer=trainer, trainer_assignments__status='Active'
    ) if trainer else Batch.objects.none()

    batch_attendance = []
    for batch in batches:
        total = Attendance.objects.filter(batch=batch).count()
        present = Attendance.objects.filter(batch=batch, status='Present').count()
        batch_attendance.append({
            'batch': batch.name,
            'total': total,
            'present': present,
            'percentage': round((present / total) * 100) if total else 0,
            'members': batch.memberships.filter(status='Active').count(),
        })

    members = User.objects.filter(
        batch_memberships__batch__in=batches, batch_memberships__status='Active'
    ).distinct().order_by('username')

    selected_member = None
    weight_labels, weight_values = [], []
    member_id = request.GET.get('member', '')
    if member_id:
        selected_member = members.filter(id=member_id).first()
        if selected_member:
            for r in ProgressRecord.objects.filter(user=selected_member, weight__gt=0).order_by('recorded_at'):
                weight_labels.append(r.recorded_at.strftime('%d %b'))
                weight_values.append(r.weight)

    plan_counts = []
    for plan in (trainer.workout_plans.annotate(n=Count('user_assignments')) if trainer else []):
        plan_counts.append({'title': plan.title, 'assigned': plan.n, 'exercises': plan.exercises.count()})

    context = {
        'trainer': trainer,
        'batch_attendance': batch_attendance,
        'members': members,
        'selected_member': selected_member,
        'weight_labels': weight_labels, 'weight_values': weight_values,
        'plan_counts': plan_counts,
        'member_id': member_id,
    }
    return render(request, 'reports/trainer.html', context)


@login_required
@user_required
def user_report(request):
    user = request.user
    progress = ProgressRecord.objects.filter(user=user).order_by('recorded_at')
    weight_labels = [r.recorded_at.strftime('%d %b') for r in progress if r.weight]
    weight_values = [r.weight for r in progress if r.weight]
    body_fat_labels = [r.recorded_at.strftime('%d %b') for r in progress if r.body_fat_percentage]
    body_fat_values = [r.body_fat_percentage for r in progress if r.body_fat_percentage]

    attendance = Attendance.objects.filter(user=user)
    total_att = attendance.count()
    present_att = attendance.filter(status='Present').count()
    attendance_pct = round((present_att / total_att) * 100) if total_att else 0

    payments = Payment.objects.filter(user=user).order_by('payment_date')
    payment_labels = [p.payment_date.strftime('%d %b %Y') for p in payments]
    payment_values = [float(p.amount) for p in payments]

    workouts = UserWorkoutAssignment.objects.filter(user=user).select_related('workout_plan')
    diets = UserDietAssignment.objects.filter(user=user).select_related('diet_plan')

    context = {
        'weight_labels': weight_labels, 'weight_values': weight_values,
        'body_fat_labels': body_fat_labels, 'body_fat_values': body_fat_values,
        'attendance_pct': attendance_pct,
        'attendance_total': total_att, 'attendance_present': present_att,
        'payment_labels': payment_labels, 'payment_values': payment_values,
        'workouts': workouts, 'diets': diets,
        'health_records': HealthRecord.objects.filter(user=user).order_by('-recorded_at')[:10],
    }
    return render(request, 'reports/user.html', context)