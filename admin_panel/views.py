import calendar
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import PlatformContent, UserProfile
from accounts.utils import ROLE_EXPERT, ROLE_TRAINER, assign_role, user_role
from events.models import Event, EventRegistration
from experts.models import ExpertProfile
from fitness.models import WorkoutPlan
from notifications.models import ActivityLog, ContactMessage, Feedback
from notifications.utils import log_activity, notify
from payments.models import MembershipPlan, Payment, PaymentAlert
from trainers.models import Batch, BatchMembership, TrainerAssignment, TrainerProfile

from .forms import (
    AdminUserEditForm,
    AdminProfileForm,
    BatchForm,
    BatchUsersForm,
    CreateExpertForm,
    CreateTrainerForm,
    EventForm,
    FeedbackResponseForm,
    MembershipPlanForm,
    PaymentStatusForm,
    PlatformContentForm,
)

admin_required = user_passes_test(lambda u: u.is_authenticated and u.is_superuser, login_url='login')


def _paginate(request, queryset, per_page=15):
    paginator = Paginator(queryset, per_page)
    page = request.GET.get('page')
    return paginator.get_page(page)


def _user_filter(request, qs):
    q = request.GET.get('q', '').strip()
    role = request.GET.get('role', '').strip()
    status = request.GET.get('status', '').strip()
    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(email__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q))
    if role:
        qs = qs.filter(groups__name=role)
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)
    return qs, {'q': q, 'role': role, 'status': status}


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@login_required
@admin_required
def dashboard(request):
    users = User.objects.filter(is_superuser=False)
    trainers = User.objects.filter(groups__name=ROLE_TRAINER)
    experts = User.objects.filter(groups__name=ROLE_EXPERT)
    active_memberships = BatchMembership.objects.filter(status='Active').count()
    pending_payments = Payment.objects.filter(status='Pending').count()
    upcoming_events = Event.objects.filter(status='Open', event_date__gte=date.today()).count()
    total_collected = Payment.objects.filter(status='Paid').aggregate(t=Sum('amount'))['t'] or 0

    # Chart data: users by batch
    batch_labels = []
    batch_counts = []
    for batch in Batch.objects.all()[:8]:
        batch_labels.append(batch.name)
        batch_counts.append(batch.memberships.filter(status='Active').count())

    # Monthly revenue for the last 6 months
    month_labels = []
    month_revenue = []
    today = date.today()
    for i in range(5, -1, -1):
        first = today.replace(day=1) - timedelta(days=30 * i)
        month_labels.append(first.strftime('%b %Y'))
        total = Payment.objects.filter(
            status='Paid',
            payment_year=str(first.year),
            payment_month=first.strftime('%B'),
        ).aggregate(t=Sum('amount'))['t'] or 0
        month_revenue.append(float(total))

    # Attendance summary
    from trainers.models import Attendance
    attendance = Attendance.objects.values('status').annotate(total=Count('status'))
    attendance_labels = [a['status'] for a in attendance]
    attendance_counts = [a['total'] for a in attendance]

    # Feedback ratings
    feedback = Feedback.objects.aggregate(avg=Avg('rating'), total=Count('id'))
    rating_labels = ['1', '2', '3', '4', '5']
    rating_counts = []
    for r in range(1, 6):
        rating_counts.append(Feedback.objects.filter(rating=r).count())

    context = {
        'total_users': users.count(),
        'active_users': users.filter(is_active=True).count(),
        'total_trainers': trainers.count(),
        'total_experts': experts.count(),
        'active_memberships': active_memberships,
        'pending_payments': pending_payments,
        'upcoming_events': upcoming_events,
        'total_collected': total_collected,
        'open_feedback': Feedback.objects.filter(status='Open').count(),
        'batch_labels': batch_labels,
        'batch_counts': batch_counts,
        'month_labels': month_labels,
        'month_revenue': month_revenue,
        'attendance_labels': attendance_labels,
        'attendance_counts': attendance_counts,
        'rating_labels': rating_labels,
        'rating_counts': rating_counts,
        'feedback_avg': feedback['avg'] or 0,
        'feedback_total': feedback['total'] or 0,
        'recent_logs': ActivityLog.objects.all()[:6],
    }
    return render(request, 'admin_panel/dashboard.html', context)


@login_required
@admin_required
def admin_profile(request):
    if request.method == 'POST':
        form = AdminProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            log_activity(request.user, 'Admin profile updated', 'Administrator updated their profile', request)
            messages.success(request, 'Administrator profile updated.')
            return redirect('admin_profile')
    else:
        form = AdminProfileForm(instance=request.user)
    return render(request, 'admin_panel/profile.html', {'form': form})


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
@login_required
@admin_required
def manage_users(request):
    qs = User.objects.filter(is_superuser=False).select_related('profile').order_by('username')
    qs, filters = _user_filter(request, qs)
    page_obj = _paginate(request, qs)
    return render(request, 'admin_panel/users.html', {'page_obj': page_obj, 'filters': filters, 'batches': Batch.objects.all()})


@login_required
@admin_required
def user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = UserProfile.objects.filter(user=user).first()
    memberships = BatchMembership.objects.filter(user=user).select_related('batch')
    payments = Payment.objects.filter(user=user).order_by('-payment_date')[:8]
    return render(request, 'admin_panel/user_detail.html', {
        'target': user, 'profile': profile, 'memberships': memberships, 'payments': payments,
    })


@login_required
@admin_required
def user_edit(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = AdminUserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            log_activity(request.user, 'User updated', f'Edited account of {user.username}', request)
            messages.success(request, 'User updated successfully.')
            return redirect('user_detail', user_id=user.id)
    else:
        form = AdminUserEditForm(instance=user)
    return render(request, 'admin_panel/user_edit.html', {'form': form, 'target': user})


@login_required
@admin_required
def user_toggle(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    UserProfile.objects.filter(user=user).update(is_active=user.is_active)
    action = 'activated' if user.is_active else 'deactivated'
    log_activity(request.user, 'User toggled', f'{action} {user.username}', request)
    messages.success(request, f'Account {action}.')
    return redirect('user_detail', user_id=user.id)


@login_required
@admin_required
def user_delete(request, user_id):
    """Soft-delete: deactivate the account and end batch memberships, keeping history intact."""
    user = get_object_or_404(User, id=user_id)
    user.is_active = False
    user.save()
    UserProfile.objects.filter(user=user).update(is_active=False)
    BatchMembership.objects.filter(user=user, status='Active').update(status='Removed')
    log_activity(request.user, 'User removed', f'Soft-deleted account {user.username}', request)
    messages.success(request, f'{user.username} has been removed (deactivated). Historical records are kept.')
    return redirect('manage_users')


@login_required
@admin_required
def user_batch(request, user_id):
    user = get_object_or_404(User, id=user_id)
    memberships = BatchMembership.objects.filter(user=user).select_related('batch')
    if request.method == 'POST':
        batch_id = request.POST.get('batch')
        status = request.POST.get('status', 'Active')
        if batch_id:
            batch = get_object_or_404(Batch, id=batch_id)
            membership, created = BatchMembership.objects.get_or_create(
                batch=batch, user=user, defaults={'status': status}
            )
            if not created:
                membership.status = status
                membership.save()
            notify(user, 'Batch allocation', f'You have been assigned to batch "{batch.name}".')
            log_activity(request.user, 'Batch allocated', f'{user.username} -> {batch.name}', request)
            messages.success(request, f'{user.username} allocated to {batch.name}.')
        return redirect('user_batch', user_id=user.id)
    return render(request, 'admin_panel/user_batch.html', {
        'target': user, 'memberships': memberships,
        'batches': Batch.objects.filter(status__in=['Active', 'Upcoming']),
    })


# ---------------------------------------------------------------------------
# Trainers
# ---------------------------------------------------------------------------
@login_required
@admin_required
def manage_trainers(request):
    trainers = TrainerProfile.objects.select_related('user').order_by('full_name')
    q = request.GET.get('q', '').strip()
    if q:
        trainers = trainers.filter(Q(full_name__icontains=q) | Q(specialization__icontains=q) | Q(user__email__icontains=q))
    page_obj = _paginate(request, trainers)
    return render(request, 'admin_panel/trainers.html', {'page_obj': page_obj, 'q': q})


@login_required
@admin_required
def trainer_add(request):
    if request.method == 'POST':
        form = CreateTrainerForm(request.POST, request.FILES)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                is_active=True,
            )
            assign_role(user, ROLE_TRAINER)
            TrainerProfile.objects.create(
                user=user,
                full_name=form.cleaned_data['full_name'],
                email=form.cleaned_data['email'],
                mobile_number=form.cleaned_data['mobile_number'],
                specialization=form.cleaned_data['specialization'],
                qualification=form.cleaned_data['qualification'],
                experience=form.cleaned_data['experience'],
                bio=form.cleaned_data['bio'],
            )
            notify(user, 'Welcome aboard', 'Your trainer account has been created. Please log in and complete your profile.')
            log_activity(request.user, 'Trainer added', f'Created trainer account {user.username}', request)
            messages.success(request, 'Trainer account created.')
            return redirect('manage_trainers')
    else:
        form = CreateTrainerForm()
    return render(request, 'admin_panel/trainer_form.html', {'form': form, 'mode': 'Add Trainer'})


@login_required
@admin_required
def trainer_edit(request, trainer_id):
    trainer = get_object_or_404(TrainerProfile, id=trainer_id)
    from accounts.forms import TrainerProfileForm
    if request.method == 'POST':
        form = TrainerProfileForm(request.POST, request.FILES, instance=trainer)
        if form.is_valid():
            form.save()
            log_activity(request.user, 'Trainer updated', f'Edited {trainer.full_name}', request)
            messages.success(request, 'Trainer profile updated.')
            return redirect('manage_trainers')
    else:
        form = TrainerProfileForm(instance=trainer)
    return render(request, 'admin_panel/trainer_form.html', {'form': form, 'mode': f'Edit {trainer.full_name}'})


@login_required
@admin_required
def trainer_toggle(request, trainer_id):
    trainer = get_object_or_404(TrainerProfile, id=trainer_id)
    trainer.is_active = not trainer.is_active
    trainer.save()
    trainer.user.is_active = trainer.is_active
    trainer.user.save()
    action = 'activated' if trainer.is_active else 'deactivated'
    log_activity(request.user, 'Trainer toggled', f'{action} {trainer.full_name}', request)
    messages.success(request, f'{trainer.full_name} {action}.')
    return redirect('manage_trainers')


@login_required
@admin_required
def trainer_delete(request, trainer_id):
    trainer = get_object_or_404(TrainerProfile, id=trainer_id)
    has_history = (
        trainer.workout_plans.exists()
        or trainer.assigned_batches.exists()
        or trainer.attendance_records.exists()
    )
    if has_history:
        trainer.is_active = False
        trainer.save()
        trainer.user.is_active = False
        trainer.user.save()
        messages.warning(request, f'{trainer.full_name} has history, so the account was deactivated instead of deleted.')
    else:
        username = trainer.user.username
        trainer.user.delete()
        messages.success(request, f'Trainer {username} deleted.')
    log_activity(request.user, 'Trainer removed', f'Removed {trainer.full_name}', request)
    return redirect('manage_trainers')


@login_required
@admin_required
def trainer_assign_batch(request, trainer_id):
    trainer = get_object_or_404(TrainerProfile, id=trainer_id)
    assignments = TrainerAssignment.objects.filter(trainer=trainer).select_related('batch')
    if request.method == 'POST':
        batch_id = request.POST.get('batch')
        if batch_id:
            batch = get_object_or_404(Batch, id=batch_id)
            assignment, created = TrainerAssignment.objects.get_or_create(
                batch=batch, trainer=trainer, defaults={'status': 'Active'}
            )
            if not created:
                assignment.status = 'Active'
                assignment.save()
            notify(trainer.user, 'Batch assigned', f'You have been assigned to batch "{batch.name}".')
            log_activity(request.user, 'Trainer assigned', f'{trainer.full_name} -> {batch.name}', request)
            messages.success(request, f'{trainer.full_name} assigned to {batch.name}.')
        return redirect('trainer_assign_batch', trainer_id=trainer.id)
    return render(request, 'admin_panel/trainer_assign_batch.html', {
        'trainer': trainer, 'assignments': assignments,
        'batches': Batch.objects.filter(status__in=['Active', 'Upcoming']),
    })


# ---------------------------------------------------------------------------
# Experts
# ---------------------------------------------------------------------------
@login_required
@admin_required
def manage_experts(request):
    experts = ExpertProfile.objects.select_related('user').order_by('full_name')
    q = request.GET.get('q', '').strip()
    if q:
        experts = experts.filter(Q(full_name__icontains=q) | Q(specialization__icontains=q) | Q(user__email__icontains=q))
    page_obj = _paginate(request, experts)
    return render(request, 'admin_panel/experts.html', {'page_obj': page_obj, 'q': q})


@login_required
@admin_required
def expert_add(request):
    if request.method == 'POST':
        form = CreateExpertForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                is_active=True,
            )
            assign_role(user, ROLE_EXPERT)
            ExpertProfile.objects.create(
                user=user,
                full_name=form.cleaned_data['full_name'],
                email=form.cleaned_data['email'],
                mobile_number=form.cleaned_data['mobile_number'],
                specialization=form.cleaned_data['specialization'],
                qualification=form.cleaned_data['qualification'],
                bio=form.cleaned_data['bio'],
            )
            notify(user, 'Welcome aboard', 'Your expert account has been created. Please log in and complete your profile.')
            log_activity(request.user, 'Expert added', f'Created expert account {user.username}', request)
            messages.success(request, 'Expert account created.')
            return redirect('manage_experts')
    else:
        form = CreateExpertForm()
    return render(request, 'admin_panel/expert_form.html', {'form': form, 'mode': 'Add Expert'})


@login_required
@admin_required
def expert_edit(request, expert_id):
    expert = get_object_or_404(ExpertProfile, id=expert_id)
    from accounts.forms import ExpertProfileForm
    if request.method == 'POST':
        form = ExpertProfileForm(request.POST, request.FILES, instance=expert)
        if form.is_valid():
            form.save()
            log_activity(request.user, 'Expert updated', f'Edited {expert.full_name}', request)
            messages.success(request, 'Expert profile updated.')
            return redirect('manage_experts')
    else:
        form = ExpertProfileForm(instance=expert)
    return render(request, 'admin_panel/expert_form.html', {'form': form, 'mode': f'Edit {expert.full_name}'})


@login_required
@admin_required
def expert_toggle(request, expert_id):
    expert = get_object_or_404(ExpertProfile, id=expert_id)
    expert.is_active = not expert.is_active
    expert.save()
    expert.user.is_active = expert.is_active
    expert.user.save()
    action = 'activated' if expert.is_active else 'deactivated'
    log_activity(request.user, 'Expert toggled', f'{action} {expert.full_name}', request)
    messages.success(request, f'{expert.full_name} {action}.')
    return redirect('manage_experts')


@login_required
@admin_required
def expert_delete(request, expert_id):
    expert = get_object_or_404(ExpertProfile, id=expert_id)
    has_history = expert.diet_plans.exists() or expert.uploaded_videos.exists()
    if has_history:
        expert.is_active = False
        expert.save()
        expert.user.is_active = False
        expert.user.save()
        messages.warning(request, f'{expert.full_name} has content history, so the account was deactivated instead of deleted.')
    else:
        username = expert.user.username
        expert.user.delete()
        messages.success(request, f'Expert {username} deleted.')
    log_activity(request.user, 'Expert removed', f'Removed {expert.full_name}', request)
    return redirect('manage_experts')


# ---------------------------------------------------------------------------
# Batches
# ---------------------------------------------------------------------------
@login_required
@admin_required
def manage_batches(request):
    batches = Batch.objects.annotate(member_count=Count('memberships', filter=Q(memberships__status='Active'))).order_by('-created_at')
    q = request.GET.get('q', '').strip()
    if q:
        batches = batches.filter(name__icontains=q)
    page_obj = _paginate(request, batches)
    return render(request, 'admin_panel/batches.html', {'page_obj': page_obj, 'q': q})


@login_required
@admin_required
def batch_create(request):
    if request.method == 'POST':
        form = BatchForm(request.POST)
        if form.is_valid():
            batch = form.save()
            log_activity(request.user, 'Batch created', f'Created batch {batch.name}', request)
            messages.success(request, 'Batch created.')
            return redirect('manage_batches')
    else:
        form = BatchForm()
    return render(request, 'admin_panel/batch_form.html', {'form': form, 'mode': 'Create Batch'})


@login_required
@admin_required
def batch_edit(request, batch_id):
    batch = get_object_or_404(Batch, id=batch_id)
    if request.method == 'POST':
        form = BatchForm(request.POST, instance=batch)
        if form.is_valid():
            form.save()
            log_activity(request.user, 'Batch updated', f'Edited batch {batch.name}', request)
            messages.success(request, 'Batch updated.')
            return redirect('manage_batches')
    else:
        form = BatchForm(instance=batch)
    return render(request, 'admin_panel/batch_form.html', {'form': form, 'mode': f'Edit {batch.name}'})


@login_required
@admin_required
def batch_delete(request, batch_id):
    batch = get_object_or_404(Batch, id=batch_id)
    if batch.memberships.exists() or batch.trainer_assignments.exists() or batch.attendance.exists():
        batch.status = 'Closed'
        batch.save()
        messages.warning(request, f'Batch "{batch.name}" has history, so it was closed instead of deleted.')
    else:
        batch.delete()
        messages.success(request, 'Batch deleted.')
    log_activity(request.user, 'Batch removed', f'Removed batch {batch.name}', request)
    return redirect('manage_batches')


@login_required
@admin_required
def batch_detail(request, batch_id):
    batch = get_object_or_404(Batch, id=batch_id)
    members = batch.memberships.select_related('user').order_by('joined_date')
    trainers = batch.trainer_assignments.select_related('trainer')
    return render(request, 'admin_panel/batch_detail.html', {
        'batch': batch, 'members': members, 'trainers': trainers,
    })


@login_required
@admin_required
def batch_users(request, batch_id):
    batch = get_object_or_404(Batch, id=batch_id)
    assigned_ids = batch.memberships.values_list('user_id', flat=True)
    available = User.objects.filter(is_active=True, is_superuser=False).exclude(id__in=assigned_ids).order_by('username')
    if request.method == 'POST':
        form = BatchUsersForm(request.POST, user_qs=available)
        if form.is_valid():
            added = 0
            for user in form.cleaned_data['users']:
                BatchMembership.objects.get_or_create(batch=batch, user=user, defaults={'status': 'Active'})
                notify(user, 'Batch allocation', f'You have been added to batch "{batch.name}".')
                added += 1
            remove_id = request.POST.get('remove_user')
            if remove_id:
                BatchMembership.objects.filter(batch=batch, user_id=remove_id, status='Active').update(status='Removed')
            log_activity(request.user, 'Batch updated', f'Updated members of {batch.name}', request)
            messages.success(request, f'Batch members updated ({added} added).')
        return redirect('batch_users', batch_id=batch.id)
    form = BatchUsersForm(user_qs=available)
    return render(request, 'admin_panel/batch_users.html', {
        'batch': batch,
        'members': batch.memberships.filter(status='Active').select_related('user'),
        'form': form,
    })


@login_required
@admin_required
def batch_trainers(request, batch_id):
    batch = get_object_or_404(Batch, id=batch_id)
    assigned_ids = batch.trainer_assignments.values_list('trainer_id', flat=True)
    available = TrainerProfile.objects.filter(is_active=True).exclude(id__in=assigned_ids)
    if request.method == 'POST':
        trainer_id = request.POST.get('trainer')
        if trainer_id:
            trainer = get_object_or_404(TrainerProfile, id=trainer_id)
            TrainerAssignment.objects.get_or_create(batch=batch, trainer=trainer, defaults={'status': 'Active'})
            notify(trainer.user, 'Batch assigned', f'You have been assigned to batch "{batch.name}".')
            messages.success(request, f'{trainer.full_name} assigned to {batch.name}.')
        remove_id = request.POST.get('remove_trainer')
        if remove_id:
            TrainerAssignment.objects.filter(batch=batch, trainer_id=remove_id, status='Active').update(status='Removed')
        log_activity(request.user, 'Batch updated', f'Updated trainers of {batch.name}', request)
        return redirect('batch_trainers', batch_id=batch.id)
    return render(request, 'admin_panel/batch_trainers.html', {
        'batch': batch,
        'assignments': batch.trainer_assignments.filter(status='Active').select_related('trainer'),
        'available': available,
    })


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------
@login_required
@admin_required
def manage_events(request):
    events = Event.objects.annotate(reg_count=Count('registrations')).order_by('-event_date')
    status = request.GET.get('status', '').strip()
    q = request.GET.get('q', '').strip()
    if status:
        events = events.filter(status=status)
    if q:
        events = events.filter(Q(title__icontains=q) | Q(venue__icontains=q))
    page_obj = _paginate(request, events)
    return render(request, 'admin_panel/events.html', {'page_obj': page_obj, 'q': q, 'status': status})


@login_required
@admin_required
def event_create(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            log_activity(request.user, 'Event created', f'Created event {event.title}', request)
            messages.success(request, 'Event created.')
            return redirect('manage_events')
    else:
        form = EventForm()
    return render(request, 'admin_panel/event_form.html', {'form': form, 'mode': 'Create Event'})


@login_required
@admin_required
def event_edit(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            log_activity(request.user, 'Event updated', f'Edited event {event.title}', request)
            messages.success(request, 'Event updated.')
            return redirect('manage_events')
    else:
        form = EventForm(instance=event)
    return render(request, 'admin_panel/event_form.html', {'form': form, 'mode': f'Edit {event.title}'})


@login_required
@admin_required
def event_delete(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if event.registrations.exists():
        event.status = 'Cancelled'
        event.save()
        messages.warning(request, f'Event "{event.title}" has registrations, so it was cancelled instead of deleted.')
    else:
        event.delete()
        messages.success(request, 'Event deleted.')
    log_activity(request.user, 'Event removed', f'Removed event {event.title}', request)
    return redirect('manage_events')


@login_required
@admin_required
def event_participants(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    registrations = event.registrations.select_related('user').order_by('registered_at')
    page_obj = _paginate(request, registrations)
    return render(request, 'admin_panel/event_participants.html', {'event': event, 'page_obj': page_obj})


# ---------------------------------------------------------------------------
# Membership plans
# ---------------------------------------------------------------------------
@login_required
@admin_required
def manage_plans(request):
    plans = MembershipPlan.objects.order_by('amount')
    return render(request, 'admin_panel/plans.html', {'plans': plans})


@login_required
@admin_required
def plan_create(request):
    if request.method == 'POST':
        form = MembershipPlanForm(request.POST)
        if form.is_valid():
            form.save()
            log_activity(request.user, 'Plan created', f'Created membership plan', request)
            messages.success(request, 'Membership plan created.')
            return redirect('manage_plans')
    else:
        form = MembershipPlanForm()
    return render(request, 'admin_panel/plan_form.html', {'form': form, 'mode': 'Create Plan'})


@login_required
@admin_required
def plan_edit(request, plan_id):
    plan = get_object_or_404(MembershipPlan, id=plan_id)
    if request.method == 'POST':
        form = MembershipPlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            log_activity(request.user, 'Plan updated', f'Edited plan {plan.name}', request)
            messages.success(request, 'Membership plan updated.')
            return redirect('manage_plans')
    else:
        form = MembershipPlanForm(instance=plan)
    return render(request, 'admin_panel/plan_form.html', {'form': form, 'mode': f'Edit {plan.name}'})


@login_required
@admin_required
def plan_delete(request, plan_id):
    plan = get_object_or_404(MembershipPlan, id=plan_id)
    if plan.payment_set.exists():
        plan.is_active = False
        plan.save()
        messages.warning(request, f'Plan "{plan.name}" has payments, so it was deactivated instead of deleted.')
    else:
        plan.delete()
        messages.success(request, 'Membership plan deleted.')
    log_activity(request.user, 'Plan removed', f'Removed plan {plan.name}', request)
    return redirect('manage_plans')


# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------
def _month_choices():
    now = date.today()
    months = []
    for i in range(11, -1, -1):
        d = now.replace(day=1) - timedelta(days=30 * i)
        months.append((d.strftime('%B'), d.strftime('%Y')))
    return months


@login_required
@admin_required
def payment_reports(request):
    payments = Payment.objects.select_related('user', 'membership_plan').order_by('-payment_date')
    month = request.GET.get('month', '').strip()
    year = request.GET.get('year', '').strip()
    status = request.GET.get('status', '').strip()
    q = request.GET.get('q', '').strip()
    if month:
        payments = payments.filter(payment_month=month)
    if year:
        payments = payments.filter(payment_year=year)
    if status:
        payments = payments.filter(status=status)
    if q:
        payments = payments.filter(Q(user__username__icontains=q) | Q(user__email__icontains=q) | Q(transaction_id__icontains=q))

    total_collected = payments.filter(status='Paid').aggregate(t=Sum('amount'))['t'] or 0
    total_pending = payments.filter(status='Pending').aggregate(t=Sum('amount'))['t'] or 0

    years = sorted({y for y in Payment.objects.values_list('payment_year', flat=True) if y}, reverse=True)

    page_obj = _paginate(request, payments)
    return render(request, 'admin_panel/payment_reports.html', {
        'page_obj': page_obj,
        'month': month, 'year': year, 'status': status, 'q': q,
        'total_collected': total_collected,
        'total_pending': total_pending,
        'months': [m[0] for m in _month_choices()],
        'years': years or [str(date.today().year)],
    })


@login_required
@admin_required
def payment_status(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    if request.method == 'POST':
        form = PaymentStatusForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            log_activity(request.user, 'Payment updated', f'Payment {payment.id} marked {payment.status}', request)
            if payment.status == 'Paid':
                notify(payment.user, 'Payment confirmed', f'Your payment of ₹{payment.amount} has been confirmed. Thank you!', 'success')
            messages.success(request, 'Payment status updated.')
    return redirect(request.META.get('HTTP_REFERER') or 'payment_reports')


def _due_users():
    """Users with no Paid payment for the current month/year."""
    now = date.today()
    current_month = now.strftime('%B')
    current_year = str(now.year)
    paid_ids = Payment.objects.filter(
        status='Paid', payment_month=current_month, payment_year=current_year
    ).values_list('user_id', flat=True)
    return User.objects.filter(is_active=True, is_superuser=False).exclude(id__in=paid_ids).order_by('username')


@login_required
@admin_required
def due_payments(request):
    due = _due_users()
    q = request.GET.get('q', '').strip()
    if q:
        due = due.filter(Q(username__icontains=q) | Q(email__icontains=q) | Q(first_name__icontains=q))
    page_obj = _paginate(request, due)
    return render(request, 'admin_panel/due_payments.html', {'page_obj': page_obj, 'q': q})


@login_required
@admin_required
def due_remind(request):
    due = _due_users()
    now = date.today()
    last_day = calendar.monthrange(now.year, now.month)[1]
    due_date = date(now.year, now.month, last_day)
    sent = 0
    for user in due:
        PaymentAlert.objects.create(
            user=user,
            message=f'Your membership payment for {now.strftime("%B %Y")} is due by {due_date}. Please pay to keep your membership active.',
            due_date=due_date,
        )
        notify(user, 'Payment reminder', f'Your membership fee for {now.strftime("%B %Y")} is due by {due_date}.', 'warning')
        sent += 1
    log_activity(request.user, 'Reminders sent', f'Sent {sent} payment reminders', request)
    messages.success(request, f'Reminders sent to {sent} user(s).')
    return redirect('due_payments')


# ---------------------------------------------------------------------------
# Feedback, contact messages, logs, settings
# ---------------------------------------------------------------------------
@login_required
@admin_required
def feedback_list(request):
    items = Feedback.objects.select_related('user').order_by('-created_at')
    status = request.GET.get('status', '').strip()
    if status:
        items = items.filter(status=status)
    page_obj = _paginate(request, items)
    return render(request, 'admin_panel/feedback.html', {'page_obj': page_obj, 'status': status})


@login_required
@admin_required
def feedback_respond(request, feedback_id):
    feedback = get_object_or_404(Feedback, id=feedback_id)
    if request.method == 'POST':
        form = FeedbackResponseForm(request.POST, instance=feedback)
        if form.is_valid():
            form.save()
            if feedback.response:
                notify(feedback.user, 'Feedback response', f'Regarding "{feedback.subject}": {feedback.response}')
            log_activity(request.user, 'Feedback handled', f'Responded to feedback #{feedback.id}', request)
            messages.success(request, 'Feedback updated.')
            return redirect('feedback_list')
    else:
        form = FeedbackResponseForm(instance=feedback)
    return render(request, 'admin_panel/feedback_respond.html', {'form': form, 'feedback': feedback})


@login_required
@admin_required
def activity_logs(request):
    logs = ActivityLog.objects.select_related('user').order_by('-created_at')
    action = request.GET.get('action', '').strip()
    q = request.GET.get('q', '').strip()
    if action:
        logs = logs.filter(action=action)
    if q:
        logs = logs.filter(Q(user__username__icontains=q) | Q(description__icontains=q))
    page_obj = _paginate(request, logs)
    actions = ActivityLog.objects.values_list('action', flat=True).distinct().order_by('action')
    return render(request, 'admin_panel/activity_logs.html', {
        'page_obj': page_obj, 'actions': actions, 'action': action, 'q': q,
    })


@login_required
@admin_required
def admin_settings(request):
    keys = ['hero_title', 'hero_subtitle', 'benefits_title', 'benefits_text', 'features_title', 'features_text', 'testimonials_title', 'testimonials_text', 'faq_title', 'faq_text']
    for key in keys:
        PlatformContent.objects.get_or_create(key=key)
    items = PlatformContent.objects.filter(key__in=keys).order_by('key')

    if request.method == 'POST':
        for item in items:
            title = request.POST.get(f'title_{item.id}')
            content = request.POST.get(f'content_{item.id}')
            if title is not None and content is not None:
                item.title = title
                item.content = content
                item.save()
        log_activity(request.user, 'Settings updated', 'Updated platform content', request)
        messages.success(request, 'Platform content saved.')
        return redirect('admin_settings')

    return render(request, 'admin_panel/settings.html', {'items': items, 'messages_list': ContactMessage.objects.filter(is_read=False)[:5]})