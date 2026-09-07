from .models import ActivityLog, Notification


def notify(recipient, title, message, notification_type='info'):
    """Create a notification for a single user."""
    if recipient is None:
        return None
    return Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notification_type,
    )


def notify_many(recipients, title, message, notification_type='info'):
    """Create a notification for a list/queryset of users."""
    created = 0
    for recipient in recipients:
        if recipient is not None and recipient.is_active:
            notify(recipient, title, message, notification_type)
            created += 1
    return created


def log_activity(user, action, description='', request=None):
    """Record an entry in the system activity log."""
    ip = None
    if request is not None:
        ip = request.META.get('REMOTE_ADDR')
    return ActivityLog.objects.create(
        user=user,
        action=action,
        description=description,
        ip_address=ip,
    )