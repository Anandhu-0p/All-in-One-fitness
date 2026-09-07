from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from trainers.models import Attendance, Batch, BatchMembership, TrainerAssignment, TrainerProfile


@login_required
def dashboard(request):
    trainer = TrainerProfile.objects.filter(user=request.user).first()
    batches = Batch.objects.filter(trainer_assignments__trainer=trainer).distinct() if trainer else []
    stats = {
        'assigned_batches': len(batches),
        'assigned_users': BatchMembership.objects.filter(batch__in=batches).count(),
        'attendance': Attendance.objects.filter(trainer=trainer).count() if trainer else 0,
    }
    return render(request, 'trainers/dashboard.html', {'trainer': trainer, 'batches': batches, 'stats': stats})


@login_required
def batches(request):
    trainer = TrainerProfile.objects.filter(user=request.user).first()
    assignments = TrainerAssignment.objects.filter(trainer=trainer).select_related('batch') if trainer else []
    return render(request, 'trainers/batches.html', {'assignments': assignments})


@login_required
def attendance(request):
    trainer = TrainerProfile.objects.filter(user=request.user).first()
    entries = Attendance.objects.filter(trainer=trainer).order_by('-date') if trainer else []
    return render(request, 'trainers/attendance.html', {'entries': entries})


@login_required
def user_health(request):
    trainer = TrainerProfile.objects.filter(user=request.user).first()
    batch_ids = [a.batch_id for a in TrainerAssignment.objects.filter(trainer=trainer)] if trainer else []
    members = BatchMembership.objects.filter(batch_id__in=batch_ids).select_related('user')
    return render(request, 'trainers/user_health.html', {'members': members})
