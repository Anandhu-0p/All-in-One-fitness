from datetime import date, datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.forms import TrainerProfileForm
from events.models import Event
from fitness.models import UserWorkoutAssignment, WorkoutPlan
from notifications.utils import log_activity, notify
from trainers.models import Attendance, Batch, BatchMembership, TrainerAssignment, TrainerProfile
from users.models import HealthRecord, ProgressRecord

from .forms import (
    ExerciseFormSet,
    HealthRecordForm,
    ProgressRecordForm,
    WorkoutAssignmentForm,
    WorkoutPlanForm,
)

trainer_required = user_passes_test(
    lambda u: u.is_authenticated and (u.is_superuser or u.groups.filter(name='Trainer').exists()),
    login_url='login',
)


def _trainer(request):
    return TrainerProfile.objects.filter(user=request.user).first()


def _assigned_batches(trainer):
    return Batch.objects.filter(
        trainer_assignments__trainer=trainer, trainer_assignments__status='Active'
    ).distinct()


def _assigned_members(trainer):
    batches = _assigned_batches(trainer)
    return BatchMembership.objects.filter(batch__in=batches, status='Active').select_related('user', 'batch')


def _paginate(request, qs, per_page=15):
    paginator = Paginator(qs, per_page)
    return paginator.get_page(request.GET.get('page'))


@login_required
@trainer_required
def dashboard(request):
    trainer = _trainer(request)
    batches = _assigned_batches(trainer) if trainer else Batch.objects.none()
    members = _assigned_members(trainer) if trainer else BatchMembership.objects.none()
    attendance_count = Attendance.objects.filter(trainer=trainer).count() if trainer else 0
    pending_tasks = [b for b in batches if not Attendance.objects.filter(batch=b, date=date.today()).exists()]
    context = {
        'trainer': trainer,
        'stats': {
            'assigned_batches': batches.count(),
            'assigned_users': members.count(),
            'attendance_records': attendance_count,
            'workout_plans': WorkoutPlan.objects.filter(created_by_trainer=trainer).count() if trainer else 0,
        },
        'batches': batches,
        'recent_attendance': Attendance.objects.filter(trainer=trainer).order_by('-date')[:6] if trainer else [],
        'upcoming_events': Event.objects.filter(status='Open', event_date__gte=date.today()).order_by('event_date')[:5],
        'pending_tasks': pending_tasks,
    }
    return render(request, 'trainers/dashboard.html', context)


@login_required
@trainer_required
def profile(request):
    trainer = _trainer(request)
    if not trainer:
        messages.error(request, 'Trainer profile not found.')
        return redirect('trainer_dashboard')
    if request.method == 'POST':
        form = TrainerProfileForm(request.POST, request.FILES, instance=trainer)
        if form.is_valid():
            form.save()
            log_activity(request.user, 'Profile updated', 'Trainer updated their profile', request)
            messages.success(request, 'Profile updated.')
            return redirect('trainer_profile')
    else:
        form = TrainerProfileForm(instance=trainer)
    return render(request, 'trainers/profile.html', {'form': form, 'trainer': trainer})


@login_required
@trainer_required
def batches(request):
    trainer = _trainer(request)
    assignments = TrainerAssignment.objects.filter(trainer=trainer, status='Active').select_related('batch')
    return render(request, 'trainers/batches.html', {'assignments': assignments})


@login_required
@trainer_required
def batch_members(request, batch_id):
    trainer = _trainer(request)
    batch = get_object_or_404(Batch, id=batch_id, trainer_assignments__trainer=trainer)
    members = batch.memberships.filter(status='Active').select_related('user', 'user__profile')
    return render(request, 'trainers/batch_members.html', {'batch': batch, 'members': members})


# ---------------------------------------------------------------------------
# Workout plans
# ---------------------------------------------------------------------------
@login_required
@trainer_required
def workout_plans(request):
    trainer = _trainer(request)
    plans = WorkoutPlan.objects.filter(created_by_trainer=trainer).annotate(
        exercise_count=Count('exercises'), assignment_count=Count('user_assignments')
    ).order_by('-created_at')
    page_obj = _paginate(request, plans)
    return render(request, 'trainers/workout_plans.html', {'page_obj': page_obj})


@login_required
@trainer_required
def workout_create(request):
    trainer = _trainer(request)
    if request.method == 'POST':
        form = WorkoutPlanForm(request.POST)
        formset = ExerciseFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            plan = form.save(commit=False)
            plan.created_by_trainer = trainer
            plan.save()
            formset.instance = plan
            formset.save()
            log_activity(request.user, 'Workout plan created', f'Created "{plan.title}"', request)
            messages.success(request, 'Workout plan created.')
            return redirect('trainer_workout_plans')
    else:
        form = WorkoutPlanForm()
        formset = ExerciseFormSet()
    return render(request, 'trainers/workout_form.html', {'form': form, 'formset': formset, 'mode': 'Create Workout Plan'})


@login_required
@trainer_required
def workout_edit(request, plan_id):
    trainer = _trainer(request)
    plan = get_object_or_404(WorkoutPlan, id=plan_id, created_by_trainer=trainer)
    if request.method == 'POST':
        form = WorkoutPlanForm(request.POST, instance=plan)
        formset = ExerciseFormSet(request.POST, instance=plan)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            log_activity(request.user, 'Workout plan updated', f'Edited "{plan.title}"', request)
            messages.success(request, 'Workout plan updated.')
            return redirect('trainer_workout_plans')
    else:
        form = WorkoutPlanForm(instance=plan)
        formset = ExerciseFormSet(instance=plan)
    return render(request, 'trainers/workout_form.html', {'form': form, 'formset': formset, 'mode': f'Edit {plan.title}'})


@login_required
@trainer_required
def workout_delete(request, plan_id):
    trainer = _trainer(request)
    plan = get_object_or_404(WorkoutPlan, id=plan_id, created_by_trainer=trainer)
    if plan.user_assignments.exists():
        plan.is_active = False
        plan.save()
        messages.warning(request, 'This plan is assigned to users, so it was deactivated instead of deleted.')
    else:
        plan.delete()
        messages.success(request, 'Workout plan deleted.')
    log_activity(request.user, 'Workout plan removed', f'Removed "{plan.title}"', request)
    return redirect('trainer_workout_plans')


@login_required
@trainer_required
def workout_assign(request, plan_id):
    trainer = _trainer(request)
    plan = get_object_or_404(WorkoutPlan, id=plan_id, created_by_trainer=trainer)
    batches = _assigned_batches(trainer)
    member_users = User.objects.filter(
        batch_memberships__batch__in=batches, batch_memberships__status='Active'
    ).distinct().order_by('username')

    if request.method == 'POST':
        form = WorkoutAssignmentForm(request.POST, user_qs=member_users, batch_qs=batches)
        if form.is_valid():
            target_type = form.cleaned_data['target_type']
            targets = []
            if target_type == 'user':
                targets = [form.cleaned_data['user']]
            else:
                batch = form.cleaned_data['batch']
                targets = list(User.objects.filter(
                    batch_memberships__batch=batch, batch_memberships__status='Active'
                ).distinct())
            assigned = 0
            for user in targets:
                assignment, created = UserWorkoutAssignment.objects.get_or_create(
                    workout_plan=plan, user=user,
                    defaults={'assigned_by': request.user, 'status': 'Active'},
                )
                if created:
                    assigned += 1
                else:
                    assignment.status = 'Active'
                    assignment.save()
                notify(user, 'Workout plan assigned', f'Your trainer assigned you the plan "{plan.title}".')
            log_activity(request.user, 'Workout assigned', f'Assigned "{plan.title}" to {assigned} user(s)', request)
            messages.success(request, f'Plan assigned to {assigned} user(s).')
            return redirect('trainer_workout_plans')
    else:
        form = WorkoutAssignmentForm(user_qs=member_users, batch_qs=batches)
    assigned_users = plan.user_assignments.select_related('user')
    return render(request, 'trainers/workout_assign.html', {'plan': plan, 'form': form, 'assigned_users': assigned_users})


# ---------------------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------------------
@login_required
@trainer_required
def attendance(request):
    trainer = _trainer(request)
    entries = Attendance.objects.filter(trainer=trainer).select_related('user', 'batch').order_by('-date', 'batch__name')
    status = request.GET.get('status', '').strip()
    batch_id = request.GET.get('batch', '').strip()
    if status:
        entries = entries.filter(status=status)
    if batch_id:
        entries = entries.filter(batch_id=batch_id)
    page_obj = _paginate(request, entries)
    batches = _assigned_batches(trainer)
    return render(request, 'trainers/attendance.html', {
        'page_obj': page_obj, 'batches': batches, 'status': status, 'batch_id': batch_id,
    })


@login_required
@trainer_required
def attendance_mark(request):
    trainer = _trainer(request)
    batches = _assigned_batches(trainer)
    selected_batch = None
    members = []
    att_date = date.today()

    if request.method == 'POST':
        batch_id = request.POST.get('batch')
        att_date = _attendance_date(request.POST.get('date'))
        if batch_id:
            selected_batch = get_object_or_404(Batch, id=batch_id, trainer_assignments__trainer=trainer)
            members = selected_batch.memberships.filter(status='Active').select_related('user')
            present_ids = request.POST.getlist('present')
            saved = 0
            with transaction.atomic():
                for membership in members:
                    status_value = 'Present' if str(membership.user_id) in present_ids else 'Absent'
                    Attendance.objects.update_or_create(
                        user=membership.user, batch=selected_batch, date=att_date,
                        defaults={'trainer': trainer, 'status': status_value},
                    )
                    saved += 1
            log_activity(request.user, 'Attendance marked', f'Marked attendance for {selected_batch.name} on {att_date}', request)
            messages.success(request, f'Attendance saved for {saved} member(s).')
            return redirect('trainer_attendance')
    else:
        batch_id = request.GET.get('batch', '').strip()
        att_date = _attendance_date(request.GET.get('date'))
        if batch_id:
            selected_batch = get_object_or_404(Batch, id=batch_id, trainer_assignments__trainer=trainer)
            members = selected_batch.memberships.filter(status='Active').select_related('user')
            existing = Attendance.objects.filter(batch=selected_batch, date=att_date).values_list('user_id', 'status')
            existing_map = {uid: st for uid, st in existing}
            for m in members:
                m.present_today = existing_map.get(m.user_id) == 'Present'

    return render(request, 'trainers/attendance_mark.html', {
        'batches': batches, 'selected_batch': selected_batch, 'members': members, 'att_date': att_date,
    })


def _attendance_date(value):
    if not value:
        return date.today()
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return date.today()


# ---------------------------------------------------------------------------
# User health & progress
# ---------------------------------------------------------------------------
@login_required
@trainer_required
def user_health(request):
    trainer = _trainer(request)
    members = _assigned_members(trainer)
    q = request.GET.get('q', '').strip()
    if q:
        members = members.filter(Q(user__username__icontains=q) | Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q) | Q(user__email__icontains=q))
    page_obj = _paginate(request, members)
    return render(request, 'trainers/user_health.html', {'page_obj': page_obj, 'q': q})


@login_required
@trainer_required
def member_health(request, user_id):
    trainer = _trainer(request)
    member = get_object_or_404(User, id=user_id)
    if not _assigned_members(trainer).filter(user=member).exists():
        messages.error(request, 'You can only view members of your assigned batches.')
        return redirect('trainer_user_health')
    records = HealthRecord.objects.filter(user=member).order_by('-recorded_at')
    progress = ProgressRecord.objects.filter(user=member).order_by('-recorded_at')
    return render(request, 'trainers/member_health.html', {
        'member': member, 'records': records, 'progress': progress,
    })


@login_required
@trainer_required
def member_health_add(request, user_id):
    trainer = _trainer(request)
    member = get_object_or_404(User, id=user_id)
    if not _assigned_members(trainer).filter(user=member).exists():
        messages.error(request, 'You can only add records for members of your assigned batches.')
        return redirect('trainer_user_health')
    if request.method == 'POST':
        form = HealthRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.user = member
            record.recorded_by = request.user
            record.save()
            notify(member, 'Health record added', f'Your trainer recorded new health measurements.')
            log_activity(request.user, 'Health record added', f'Recorded health data for {member.username}', request)
            messages.success(request, 'Health record saved.')
            return redirect('member_health', user_id=member.id)
    else:
        latest = HealthRecord.objects.filter(user=member).order_by('-recorded_at').first()
        form = HealthRecordForm(initial={'height': latest.height if latest else None, 'weight': latest.weight if latest else None})
    return render(request, 'trainers/health_form.html', {'form': form, 'member': member, 'mode': 'Add Health Record'})


@login_required
@trainer_required
def member_progress_add(request, user_id):
    trainer = _trainer(request)
    member = get_object_or_404(User, id=user_id)
    if not _assigned_members(trainer).filter(user=member).exists():
        messages.error(request, 'You can only add records for members of your assigned batches.')
        return redirect('trainer_user_health')
    if request.method == 'POST':
        form = ProgressRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.user = member
            record.save()
            notify(member, 'Progress updated', 'Your trainer added a new progress measurement.')
            log_activity(request.user, 'Progress added', f'Recorded progress for {member.username}', request)
            messages.success(request, 'Progress record saved.')
            return redirect('member_health', user_id=member.id)
    else:
        form = ProgressRecordForm()
    return render(request, 'trainers/progress_form.html', {'form': form, 'member': member, 'mode': 'Add Progress Measurement'})


@login_required
@trainer_required
def progress(request):
    trainer = _trainer(request)
    members = _assigned_members(trainer).annotate(
        record_count=Count('user__progress_records')
    ).order_by('user__username')
    page_obj = _paginate(request, members)
    return render(request, 'trainers/progress.html', {'page_obj': page_obj})