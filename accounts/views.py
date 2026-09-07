from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from events.models import Event
from experts.models import ExpertProfile, FitnessVideo, WellnessTip
from fitness.models import WorkoutPlan
from notifications.models import ContactMessage
from notifications.utils import log_activity
from trainers.models import TrainerProfile

from .forms import (
    ContactForm,
    CustomUserRegistrationForm,
    EmailAuthenticationForm,
    PasswordChangeForm,
    UserProfileForm,
)
from .models import PlatformContent, UserProfile
from .utils import dashboard_url_for, user_role

DEFAULT_CONTENT = {
    'hero_title': 'Your Complete Fitness Journey Starts Here',
    'hero_subtitle': 'Train with certified coaches, follow personalised nutrition and workout plans, track your progress, and be part of a community that keeps you moving.',
    'benefits_title': 'Everything you need, in one place',
    'benefits_text': 'Personalised workout and diet plans, real trainer guidance, expert nutrition advice, attendance and payment tracking, events, and private messaging.',
    'features_title': 'Built for every step of your journey',
    'features_text': 'From first-timers to advanced athletes, our platform adapts to your goals.',
    'testimonials_title': 'What our members say',
    'testimonials_text': 'Real results from real members.',
    'faq_title': 'Frequently asked questions',
    'faq_text': 'Quick answers to common questions.',
}


def _content():
    """Return a dict of PlatformContent values with sensible defaults."""
    data = dict(DEFAULT_CONTENT)
    for item in PlatformContent.objects.all():
        data[item.key] = item.content or item.title
    return data


def landing(request):
    ctx = _content()
    ctx.update({
        'trainers': TrainerProfile.objects.filter(is_active=True)[:3],
        'experts': ExpertProfile.objects.filter(is_active=True)[:3],
        'tips': WellnessTip.objects.filter(is_published=True).order_by('-created_at')[:3],
        'videos': FitnessVideo.objects.filter(is_active=True).order_by('-created_at')[:3],
        'events': Event.objects.filter(status='Open').order_by('event_date')[:3],
        'member_count': UserProfile.objects.filter(is_active=True).count(),
        'trainer_count': TrainerProfile.objects.filter(is_active=True).count(),
        'expert_count': ExpertProfile.objects.filter(is_active=True).count(),
        'workout_plan_count': WorkoutPlan.objects.filter(is_active=True).count(),
    })
    return render(request, 'landing.html', ctx)


def about(request):
    ctx = _content()
    ctx.update({
        'trainers': TrainerProfile.objects.filter(is_active=True)[:3],
        'experts': ExpertProfile.objects.filter(is_active=True)[:3],
    })
    return render(request, 'public/about.html', ctx)


def features(request):
    return render(request, 'public/features.html', _content())


def public_trainers(request):
    trainers = TrainerProfile.objects.filter(is_active=True)
    return render(request, 'public/trainers.html', {'trainers': trainers})


def public_experts(request):
    experts = ExpertProfile.objects.filter(is_active=True)
    return render(request, 'public/experts.html', {'experts': experts})


def resources(request):
    videos = FitnessVideo.objects.filter(is_active=True).order_by('-created_at')
    tips = WellnessTip.objects.filter(is_published=True).order_by('-created_at')
    return render(request, 'public/resources.html', {'videos': videos, 'tips': tips})


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            ContactMessage.objects.create(**form.cleaned_data)
            messages.success(request, 'Thank you! Your message has been sent. We will get back to you soon.')
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'public/contact.html', {'form': form})


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')
    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            log_activity(user, 'Registered', f'New {user_role(user).lower()} account created', request)
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')
    else:
        form = CustomUserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')
    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None and user.is_active:
                login(request, user)
                log_activity(user, 'Login', 'User logged in', request)
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                return redirect(dashboard_url_for(user))
        form.add_error(None, 'Invalid credentials or deactivated account.')
    else:
        form = EmailAuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    if request.user.is_authenticated:
        log_activity(request.user, 'Logout', 'User logged out', request)
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('landing')


@login_required
def dashboard_redirect(request):
    return redirect(dashboard_url_for(request.user))


@login_required
def user_profile(request):
    profile, _ = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={'full_name': request.user.get_full_name() or request.user.username, 'email': request.user.email},
    )
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            log_activity(request.user, 'Profile updated', 'User updated their profile', request)
            messages.success(request, 'Profile updated successfully.')
            return redirect('user_profile')
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'accounts/profile.html', {'form': form, 'profile': profile})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            old_password = form.cleaned_data['old_password']
            if not request.user.check_password(old_password):
                form.add_error('old_password', 'Your current password is incorrect.')
            else:
                request.user.set_password(form.cleaned_data['new_password'])
                request.user.save()
                update_session_auth_hash(request, request.user)
                log_activity(request.user, 'Password changed', 'User changed their password', request)
                messages.success(request, 'Password updated successfully.')
                return redirect(dashboard_url_for(request.user))
    else:
        form = PasswordChangeForm()
    return render(request, 'accounts/change_password.html', {'form': form})