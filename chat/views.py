from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.utils import user_role
from experts.models import ExpertProfile
from notifications.utils import log_activity
from trainers.models import BatchMembership, TrainerAssignment, TrainerProfile
from .models import ChatConversation, ChatMessage


def _contacts_for(request):
    """People the current user can start a chat with."""
    role = user_role(request.user)
    if role == 'User':
        trainer_users = User.objects.filter(
            trainer_profile__assigned_batches__batch__memberships__user=request.user,
            trainer_profile__assigned_batches__status='Active',
            trainer_profile__is_active=True,
        ).distinct()
        expert_users = User.objects.filter(expert_profile__is_active=True)
        return {
            'trainer': trainer_users.first(),
            'experts': expert_users,
        }
    if role == 'Trainer':
        members = User.objects.filter(
            batch_memberships__batch__trainer_assignments__trainer__user=request.user,
            batch_memberships__status='Active',
            batch_memberships__batch__trainer_assignments__status='Active',
            is_active=True,
        ).distinct().order_by('username')
        return {'members': members}
    if role == 'Expert':
        members = User.objects.filter(groups__name='User', is_active=True).order_by('username')
        return {'members': members}
    return {}


def _conversations_for(request):
    role = user_role(request.user)
    if role == 'User':
        return ChatConversation.objects.filter(user=request.user)
    if role == 'Trainer':
        return ChatConversation.objects.filter(trainer=request.user)
    if role == 'Expert':
        return ChatConversation.objects.filter(expert=request.user)
    return ChatConversation.objects.none()


def _other_party(conversation, request):
    if conversation.user == request.user:
        return conversation.trainer or conversation.expert
    return conversation.user


@login_required
def chat_home(request):
    conversations = _conversations_for(request).order_by('-updated_at')
    for convo in conversations:
        convo.other = _other_party(convo, request)
        convo.last_message = convo.messages.order_by('-sent_at').first()
        convo.unread = convo.messages.filter(is_read=False).exclude(sender=request.user).count()
    contacts = _contacts_for(request)
    return render(request, 'chat/index.html', {'conversations': conversations, 'contacts': contacts})


@login_required
def chat_thread(request, conversation_id):
    conversation = get_object_or_404(ChatConversation, id=conversation_id)
    allowed = (
        conversation.user == request.user
        or conversation.trainer == request.user
        or conversation.expert == request.user
    )
    if not allowed:
        messages.error(request, 'You do not have access to this conversation.')
        return redirect('chat_home')
    conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    other = _other_party(conversation, request)

    if request.method == 'POST':
        text = request.POST.get('message', '').strip()
        attachment = request.FILES.get('attachment')
        if attachment:
            if attachment.size > 10 * 1024 * 1024:
                raise ValidationError('Attachment must be smaller than 10 MB.')
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif', 'webp', 'pdf', 'txt', 'doc', 'docx'])(attachment)
        if text or attachment:
            ChatMessage.objects.create(
                conversation=conversation, sender=request.user, message=text, attachment=attachment,
            )
            conversation.save()  # auto_now refreshes updated_at
            log_activity(request.user, 'Message sent', f'Message in conversation with {other.username}', request)
        else:
            messages.error(request, 'Write a message or attach a file.')
        return redirect('chat_thread', conversation_id=conversation.id)

    messages_qs = conversation.messages.select_related('sender').order_by('sent_at')
    return render(request, 'chat/thread.html', {'conversation': conversation, 'other': other, 'messages_qs': messages_qs})


@login_required
def chat_start(request, target_type, target_id):
    role = user_role(request.user)
    if role == 'User':
        if target_type == 'trainer':
            profile = get_object_or_404(TrainerProfile, id=target_id, is_active=True)
            target = profile.user
            conversation, _ = ChatConversation.objects.get_or_create(user=request.user, trainer=target)
        elif target_type == 'expert':
            profile = get_object_or_404(ExpertProfile, id=target_id, is_active=True)
            target = profile.user
            conversation, _ = ChatConversation.objects.get_or_create(user=request.user, expert=target)
        else:
            messages.error(request, 'Unknown chat target.')
            return redirect('chat_home')
    elif role in ('Trainer', 'Expert'):
        target = get_object_or_404(User, id=target_id, is_active=True)
        if role == 'Trainer':
            conversation, _ = ChatConversation.objects.get_or_create(user=target, trainer=request.user)
        else:
            conversation, _ = ChatConversation.objects.get_or_create(user=target, expert=request.user)
    else:
        messages.error(request, 'Chat is not available for this role.')
        return redirect('chat_home')
    return redirect('chat_thread', conversation_id=conversation.id)