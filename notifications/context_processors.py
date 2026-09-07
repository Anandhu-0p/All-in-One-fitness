from accounts.utils import dashboard_url_for, user_role
from .models import Notification


def unread_notifications(request):
    if not request.user.is_authenticated:
        return {
            'unread_count': 0,
            'recent_notifications': [],
            'current_role': None,
            'dashboard_url': None,
        }
    items = Notification.objects.filter(recipient=request.user)[:5]
    unread = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return {
        'unread_count': unread,
        'recent_notifications': items,
        'current_role': user_role(request.user),
        'dashboard_url': dashboard_url_for(request.user),
    }