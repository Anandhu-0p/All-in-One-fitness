from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.forms import ExpertProfileForm
from accounts.models import UserProfile
from notifications.utils import log_activity, notify
from users.models import HealthRecord
from .models import DietPlan, ExpertProfile, FitnessVideo, UserDietAssignment, WellnessTip

from .forms import DietMealFormSet, DietPlanForm, FitnessVideoForm, WellnessTipForm

expert_required = user_passes_test(
    lambda u: u.is_authenticated and (u.is_superuser or u.groups.filter(name='Expert').exists()),
    login_url='login',
)


def _expert(request):
    return ExpertProfile.objects.filter(user=request.user).first()


def _paginate(request, qs, per_page=12):
    paginator = Paginator(qs, per_page)
    return paginator.get_page(request.GET.get('page'))


@login_required
@expert_required
def dashboard(request):
    expert = _expert(request)
    context = {
        'expert': expert,
        'stats': {
            'diet_plans': DietPlan.objects.filter(created_by_expert=expert).count() if expert else 0,
            'videos': FitnessVideo.objects.filter(uploaded_by_expert=expert).count() if expert else 0,
            'tips': WellnessTip.objects.filter(author=request.user).count(),
            'assigned_diets': UserDietAssignment.objects.filter(diet_plan__created_by_expert=expert).count() if expert else 0,
        },
        'recent_plans': DietPlan.objects.filter(created_by_expert=expert).order_by('-created_at')[:4] if expert else [],
        'recent_videos': FitnessVideo.objects.filter(uploaded_by_expert=expert).order_by('-created_at')[:4] if expert else [],
    }
    return render(request, 'experts/dashboard.html', context)


@login_required
@expert_required
def profile(request):
    expert = _expert(request)
    if not expert:
        messages.error(request, 'Expert profile not found.')
        return redirect('expert_dashboard')
    if request.method == 'POST':
        form = ExpertProfileForm(request.POST, request.FILES, instance=expert)
        if form.is_valid():
            form.save()
            log_activity(request.user, 'Profile updated', 'Expert updated their profile', request)
            messages.success(request, 'Profile updated.')
            return redirect('expert_profile')
    else:
        form = ExpertProfileForm(instance=expert)
    return render(request, 'experts/profile.html', {'form': form, 'expert': expert})


# ---------------------------------------------------------------------------
# Diet plans
# ---------------------------------------------------------------------------
@login_required
@expert_required
def diet_plans(request):
    expert = _expert(request)
    plans = DietPlan.objects.filter(created_by_expert=expert).annotate(
        meal_count=Count('meals'), assignment_count=Count('assigned_users')
    ).order_by('-created_at')
    page_obj = _paginate(request, plans)
    return render(request, 'experts/diet_plans.html', {'page_obj': page_obj})


@login_required
@expert_required
def diet_create(request):
    expert = _expert(request)
    if request.method == 'POST':
        form = DietPlanForm(request.POST)
        formset = DietMealFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            plan = form.save(commit=False)
            plan.created_by_expert = expert
            plan.save()
            formset.instance = plan
            formset.save()
            log_activity(request.user, 'Diet plan created', f'Created "{plan.title}"', request)
            messages.success(request, 'Diet plan created.')
            return redirect('expert_diet_plans')
    else:
        form = DietPlanForm()
        formset = DietMealFormSet()
    return render(request, 'experts/diet_form.html', {'form': form, 'formset': formset, 'mode': 'Create Diet Plan'})


@login_required
@expert_required
def diet_edit(request, plan_id):
    expert = _expert(request)
    plan = get_object_or_404(DietPlan, id=plan_id, created_by_expert=expert)
    if request.method == 'POST':
        form = DietPlanForm(request.POST, instance=plan)
        formset = DietMealFormSet(request.POST, instance=plan)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            log_activity(request.user, 'Diet plan updated', f'Edited "{plan.title}"', request)
            messages.success(request, 'Diet plan updated.')
            return redirect('expert_diet_plans')
    else:
        form = DietPlanForm(instance=plan)
        formset = DietMealFormSet(instance=plan)
    return render(request, 'experts/diet_form.html', {'form': form, 'formset': formset, 'mode': f'Edit {plan.title}'})


@login_required
@expert_required
def diet_delete(request, plan_id):
    expert = _expert(request)
    plan = get_object_or_404(DietPlan, id=plan_id, created_by_expert=expert)
    if plan.assigned_users.exists():
        plan.is_active = False
        plan.save()
        messages.warning(request, 'This plan is assigned to users, so it was deactivated instead of deleted.')
    else:
        plan.delete()
        messages.success(request, 'Diet plan deleted.')
    log_activity(request.user, 'Diet plan removed', f'Removed "{plan.title}"', request)
    return redirect('expert_diet_plans')


@login_required
@expert_required
def diet_assign(request, plan_id):
    expert = _expert(request)
    plan = get_object_or_404(DietPlan, id=plan_id, created_by_expert=expert)
    users = User.objects.filter(is_active=True, is_superuser=False).exclude(
        id__in=plan.assigned_users.values_list('user_id', flat=True)
    ).order_by('username')
    if request.method == 'POST':
        user_ids = request.POST.getlist('users')
        assigned = 0
        for uid in user_ids:
            user = User.objects.filter(id=uid, is_active=True).first()
            if user:
                UserDietAssignment.objects.get_or_create(
                    diet_plan=plan, user=user,
                    defaults={'assigned_by': request.user, 'status': 'Active'},
                )
                notify(user, 'Diet plan assigned', f'Your expert assigned you the diet plan "{plan.title}".')
                assigned += 1
        log_activity(request.user, 'Diet plan assigned', f'Assigned "{plan.title}" to {assigned} user(s)', request)
        messages.success(request, f'Diet plan assigned to {assigned} user(s).')
        return redirect('expert_diet_plans')
    return render(request, 'experts/diet_assign.html', {
        'plan': plan, 'users': users,
        'assigned_users': plan.assigned_users.select_related('user'),
    })


# ---------------------------------------------------------------------------
# Videos
# ---------------------------------------------------------------------------
@login_required
@expert_required
def videos(request):
    expert = _expert(request)
    items = FitnessVideo.objects.filter(uploaded_by_expert=expert).order_by('-created_at')
    page_obj = _paginate(request, items)
    return render(request, 'experts/videos.html', {'page_obj': page_obj})


@login_required
@expert_required
def video_create(request):
    expert = _expert(request)
    if request.method == 'POST':
        form = FitnessVideoForm(request.POST, request.FILES)
        if form.is_valid():
            video = form.save(commit=False)
            video.uploaded_by_expert = expert
            video.save()
            log_activity(request.user, 'Video added', f'Added "{video.title}"', request)
            messages.success(request, 'Video added.')
            return redirect('expert_videos')
    else:
        form = FitnessVideoForm()
    return render(request, 'experts/video_form.html', {'form': form, 'mode': 'Add Video'})


@login_required
@expert_required
def video_edit(request, video_id):
    expert = _expert(request)
    video = get_object_or_404(FitnessVideo, id=video_id, uploaded_by_expert=expert)
    if request.method == 'POST':
        form = FitnessVideoForm(request.POST, request.FILES, instance=video)
        if form.is_valid():
            form.save()
            log_activity(request.user, 'Video updated', f'Edited "{video.title}"', request)
            messages.success(request, 'Video updated.')
            return redirect('expert_videos')
    else:
        form = FitnessVideoForm(instance=video)
    return render(request, 'experts/video_form.html', {'form': form, 'mode': f'Edit {video.title}'})


@login_required
@expert_required
def video_delete(request, video_id):
    expert = _expert(request)
    video = get_object_or_404(FitnessVideo, id=video_id, uploaded_by_expert=expert)
    video.delete()
    log_activity(request.user, 'Video removed', f'Removed "{video.title}"', request)
    messages.success(request, 'Video deleted.')
    return redirect('expert_videos')


# ---------------------------------------------------------------------------
# Tips & articles
# ---------------------------------------------------------------------------
@login_required
@expert_required
def wellness_tips(request):
    tips = WellnessTip.objects.filter(author=request.user).order_by('-created_at')
    page_obj = _paginate(request, tips)
    return render(request, 'experts/tips.html', {'page_obj': page_obj})


@login_required
@expert_required
def tip_create(request):
    if request.method == 'POST':
        form = WellnessTipForm(request.POST)
        if form.is_valid():
            tip = form.save(commit=False)
            tip.author = request.user
            tip.save()
            log_activity(request.user, 'Tip created', f'Published "{tip.title}"', request)
            messages.success(request, 'Tip published.')
            return redirect('expert_tips')
    else:
        form = WellnessTipForm()
    return render(request, 'experts/tip_form.html', {'form': form, 'mode': 'Create Tip / Article'})


@login_required
@expert_required
def tip_edit(request, tip_id):
    tip = get_object_or_404(WellnessTip, id=tip_id, author=request.user)
    if request.method == 'POST':
        form = WellnessTipForm(request.POST, instance=tip)
        if form.is_valid():
            form.save()
            log_activity(request.user, 'Tip updated', f'Edited "{tip.title}"', request)
            messages.success(request, 'Tip updated.')
            return redirect('expert_tips')
    else:
        form = WellnessTipForm(instance=tip)
    return render(request, 'experts/tip_form.html', {'form': form, 'mode': f'Edit {tip.title}'})


@login_required
@expert_required
def tip_delete(request, tip_id):
    tip = get_object_or_404(WellnessTip, id=tip_id, author=request.user)
    tip.delete()
    log_activity(request.user, 'Tip removed', f'Removed "{tip.title}"', request)
    messages.success(request, 'Tip deleted.')
    return redirect('expert_tips')


# ---------------------------------------------------------------------------
# User profiles (nutrition-relevant info)
# ---------------------------------------------------------------------------
@login_required
@expert_required
def users_list(request):
    qs = User.objects.filter(is_active=True, is_superuser=False, groups__name='User').select_related('profile').order_by('username')
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(email__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q))
    page_obj = _paginate(request, qs)
    return render(request, 'experts/users.html', {'page_obj': page_obj, 'q': q})


@login_required
@expert_required
def user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id, is_active=True, is_superuser=False, groups__name='User')
    profile = UserProfile.objects.filter(user=user).first()
    latest_health = HealthRecord.objects.filter(user=user).order_by('-recorded_at').first()
    return render(request, 'experts/user_detail.html', {
        'target': user, 'profile': profile, 'latest_health': latest_health,
    })