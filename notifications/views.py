from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from notifications.models import Feedback, Notification


@login_required
def notifications_list(request):
    items = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    return render(request, 'notifications/list.html', {'items': items})


@login_required
def feedback_form(request):
    if request.method == 'POST':
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        rating = request.POST.get('rating')
        Feedback.objects.create(user=request.user, subject=subject, message=message, rating=int(rating or 5))
        return render(request, 'notifications/feedback_submitted.html')
    return render(request, 'notifications/feedback.html')
