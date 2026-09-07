from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from chat.models import ChatConversation


@login_required
def chat_home(request):
    conversations = ChatConversation.objects.filter(user=request.user).order_by('-updated_at')
    return render(request, 'chat/index.html', {'conversations': conversations})
