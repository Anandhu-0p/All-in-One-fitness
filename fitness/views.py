from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render

from experts.models import DietPlan, FitnessVideo, UserDietAssignment, WellnessTip
from fitness.models import UserWorkoutAssignment

member_required = user_passes_test(
    lambda u: u.is_authenticated and (u.groups.filter(name='User').exists() or not (u.is_superuser or u.groups.filter(name='Trainer').exists() or u.groups.filter(name='Expert').exists())),
    login_url='login',
)


@login_required
@member_required
def workout_plans(request):
    assignments = UserWorkoutAssignment.objects.filter(user=request.user).select_related(
        'workout_plan'
    ).prefetch_related('workout_plan__exercises').order_by('-start_date')
    return render(request, 'fitness/workout_plans.html', {'assignments': assignments})


@login_required
@member_required
def diet_plans(request):
    assignments = UserDietAssignment.objects.filter(user=request.user).select_related(
        'diet_plan', 'diet_plan__created_by_expert__user'
    ).prefetch_related('diet_plan__meals').order_by('-start_date')
    return render(request, 'fitness/diet_plans.html', {'assignments': assignments})


@login_required
@member_required
def videos(request):
    videos = FitnessVideo.objects.filter(is_active=True).select_related(
        'uploaded_by_expert__user'
    ).order_by('-created_at')
    category = request.GET.get('category', '').strip()
    if category:
        videos = videos.filter(category__icontains=category)
    categories = FitnessVideo.objects.filter(is_active=True).values_list('category', flat=True).distinct()
    return render(request, 'fitness/videos.html', {'videos': videos, 'category': category, 'categories': categories})


@login_required
@member_required
def tips(request):
    tips = WellnessTip.objects.filter(is_published=True).order_by('-created_at')
    category = request.GET.get('category', '').strip()
    if category:
        tips = tips.filter(category__icontains=category)
    categories = WellnessTip.objects.filter(is_published=True).values_list('category', flat=True).distinct()
    return render(request, 'fitness/tips.html', {'tips': tips, 'category': category, 'categories': categories})