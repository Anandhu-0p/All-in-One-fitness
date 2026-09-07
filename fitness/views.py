from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from experts.models import FitnessVideo
from fitness.models import UserWorkoutAssignment


@login_required
def workout_plans(request):
    assignments = UserWorkoutAssignment.objects.filter(user=request.user).select_related('workout_plan')
    return render(request, 'fitness/workout_plans.html', {'assignments': assignments})


@login_required
def videos(request):
    videos = FitnessVideo.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'fitness/videos.html', {'videos': videos})
