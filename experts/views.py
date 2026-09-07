from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from experts.models import DietPlan, FitnessVideo, WellnessTip, ExpertProfile


@login_required
def dashboard(request):
    expert = ExpertProfile.objects.filter(user=request.user).first()
    diet_plans = DietPlan.objects.filter(created_by_expert=expert).count() if expert else 0
    videos = FitnessVideo.objects.filter(uploaded_by_expert=expert).count() if expert else 0
    return render(request, 'experts/dashboard.html', {'expert': expert, 'diet_plans': diet_plans, 'videos': videos})


@login_required
def diet_plans(request):
    expert = ExpertProfile.objects.filter(user=request.user).first()
    plans = DietPlan.objects.filter(created_by_expert=expert) if expert else []
    return render(request, 'experts/diet_plans.html', {'plans': plans})


@login_required
def videos(request):
    expert = ExpertProfile.objects.filter(user=request.user).first()
    items = FitnessVideo.objects.filter(uploaded_by_expert=expert) if expert else []
    return render(request, 'experts/videos.html', {'items': items})


@login_required
def wellness_tips(request):
    tips = WellnessTip.objects.filter(is_published=True).order_by('-created_at')
    return render(request, 'experts/tips.html', {'tips': tips})
