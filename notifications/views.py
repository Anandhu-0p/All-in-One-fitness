from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from notifications.utils import log_activity
from .forms import FeedbackForm
from .models import Feedback, Notification


@login_required
def notifications_list(request):
    items = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    kind = request.GET.get('kind', '').strip()
    if kind:
        items = items.filter(notification_type=kind)
    kinds = Notification.objects.filter(recipient=request.user).values_list(
        'notification_type', flat=True
    ).distinct()
    notification_types = [
        (value, value.replace('_', ' ').title())
        for value in kinds
    ]
    return render(request, 'notifications/list.html', {
        'items': items,
        'kind': kind,
        'notification_types': notification_types,
    })


@login_required
def notification_mark_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notifications_list')


@login_required
def notification_mark_all(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    messages.success(request, 'All notifications marked as read.')
    return redirect('notifications_list')


@login_required
def feedback_form(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.save()
            log_activity(request.user, 'Feedback submitted', f'Feedback #{feedback.id}: {feedback.subject}', request)
            messages.success(request, 'Thank you for your feedback! Our team will review it.')
            return redirect('feedback_my')
    else:
        form = FeedbackForm()
    return render(request, 'notifications/feedback.html', {'form': form})


@login_required
def feedback_my(request):
    items = Feedback.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'notifications/feedback_my.html', {'items': items})