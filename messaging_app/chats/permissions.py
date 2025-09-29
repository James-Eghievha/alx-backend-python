from rest_framework import permissions
from django.shortcuts import get_object_or_404
from .models import Conversation, Message

class IsConversationParticipant(permissions.BasePermission):
    """Custom permission to only allow participants of a conversation to interact with it."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return request.user in obj.participants.all()

class IsMessageOwner(permissions.BasePermission):
    """Custom permission to only allow owners of a message to edit/delete it."""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return request.user in obj.conversation.participants.all()
        return obj.sender == request.user

class MessagePermission(permissions.BasePermission):
    """Custom permission for Message model."""
    
    def has_permission(self, request, view):
        if request.method == 'POST':
            conversation_id = request.data.get('conversation')
            if not conversation_id:
                return False
            conversation = get_object_or_404(Conversation, id=conversation_id)
            return request.user in conversation.participants.all()
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return request.user in obj.conversation.participants.all()
        return obj.sender == request.user

class ConversationPermission(permissions.BasePermission):
    """Custom permission for Conversation model."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return request.user in obj.participants.all()

class CanSendMessagePermission(permissions.BasePermission):
    """Custom permission to check if user can send messages in a conversation."""
    
    def has_permission(self, request, view):
        if request.method != 'POST':
            return True
            
        conversation_id = request.data.get('conversation')
        if not conversation_id:
            return False
            
        conversation = get_object_or_404(Conversation, id=conversation_id)
        return request.user in conversation.participants.all()

def get_user_accessible_conversations(user):
    """Helper function to get conversations accessible to a user."""
    from .models import Conversation
    return Conversation.objects.filter(participants=user)

def get_user_accessible_messages(user):
    """Helper function to get messages accessible to a user."""
    from .models import Message
    return Message.objects.filter(conversation__participants=user)