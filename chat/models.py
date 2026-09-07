from django.contrib.auth.models import User
from django.db import models


class ChatConversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_conversations')
    trainer = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='trainer_conversations')
    expert = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='expert_conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user} conversation'


class ChatMessage(models.Model):
    conversation = models.ForeignKey(ChatConversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    message = models.TextField()
    attachment = models.FileField(upload_to='chat/', blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.sender} @ {self.sent_at}'
