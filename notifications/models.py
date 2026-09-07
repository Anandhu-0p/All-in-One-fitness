from django.contrib.auth.models import User
from django.db import models


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, default='info')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedback_entries')
    subject = models.CharField(max_length=200)
    message = models.TextField()
    rating = models.PositiveIntegerField(default=5)
    response = models.TextField(blank=True)
    status = models.CharField(max_length=30, default='Open')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user}: {self.subject}'
