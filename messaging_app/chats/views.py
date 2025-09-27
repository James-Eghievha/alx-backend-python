# messaging_app/chats/views.py

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Prefetch
from django.contrib.auth import get_user_model

from .models import Conversation, Message
from .serializers import (
    ConversationSerializer,
    ConversationSummarySerializer,
    MessageSerializer,
    MessageCreateSerializer,
    UserSerializer,
    UserSummarySerializer  # Add this import
)

User = get_user_model()

from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

@login_required
def profile_redirect(request):
    """Redirect authenticated users to API root"""
    return redirect('/api/')


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling Conversation operations
    
    Provides:
    - List conversations for authenticated user
    - Retrieve specific conversation with messages
    - Create new conversations
    - Update conversation participants
    - Delete conversations
    - Custom actions for adding/removing participants
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filter conversations to only include those where the user is a participant
        Optimize queries with prefetch_related for better performance
        """
        user = self.request.user
        return Conversation.objects.filter(
            participants=user
        ).prefetch_related(
            'participants',
            Prefetch(
                'messages', 
                queryset=Message.objects.select_related('sender').order_by('-sent_at')
            )
        ).distinct().order_by('-created_at')
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action
        """
        if self.action == 'list':
            return ConversationSummarySerializer
        return ConversationSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Create a new conversation
        Automatically add the requesting user as a participant
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get participant IDs from request data
        participant_ids = request.data.get('participant_ids', [])
        
        # Add current user to participants if not already included
        current_user_id = str(request.user.user_id)
        if current_user_id not in participant_ids:
            participant_ids.append(current_user_id)
        
        # Create conversation
        conversation = Conversation.objects.create()
        
        # Add participants
        participants = User.objects.filter(user_id__in=participant_ids)
        conversation.participants.set(participants)
        
        # Return serialized conversation
        serializer = self.get_serializer(conversation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a specific conversation with all messages
        """
        conversation = self.get_object()
        
        # Ensure user is a participant in this conversation
        if not conversation.participants.filter(user_id=request.user.user_id).exists():
            return Response(
                {'error': 'You are not a participant in this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(conversation)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        """
        Add a participant to an existing conversation
        """
        conversation = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user_to_add = User.objects.get(user_id=user_id)
            conversation.participants.add(user_to_add)
            
            return Response(
                {'message': f'User {user_to_add.full_name} added to conversation'},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def remove_participant(self, request, pk=None):
        """
        Remove a participant from a conversation
        """
        conversation = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user_to_remove = User.objects.get(user_id=user_id)
            
            # Prevent removing the last participant
            if conversation.participants.count() <= 1:
                return Response(
                    {'error': 'Cannot remove the last participant from conversation'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            conversation.participants.remove(user_to_remove)
            
            return Response(
                {'message': f'User {user_to_remove.full_name} removed from conversation'},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search conversations by participant name or email
        """
        query = request.query_params.get('q', '')
        if not query:
            return Response(
                {'error': 'Search query parameter "q" is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        conversations = self.get_queryset().filter(
            Q(participants__first_name__icontains=query) |
            Q(participants__last_name__icontains=query) |
            Q(participants__email__icontains=query)
        ).distinct()
        
        serializer = ConversationSummarySerializer(conversations, many=True)
        return Response(serializer.data)


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling Message operations
    
    Provides:
    - List messages in a conversation
    - Retrieve specific message
    - Create new messages
    - Update messages (edit functionality)
    - Delete messages
    - Filter messages by conversation
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filter messages to only include those in conversations where user is participant
        """
        user = self.request.user
        return Message.objects.filter(
            conversation__participants=user
        ).select_related('sender', 'conversation').order_by('-sent_at')
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action
        """
        if self.action == 'create':
            return MessageCreateSerializer
        return MessageSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Create a new message in a conversation
        Automatically set the sender to the requesting user
        """
        serializer = MessageCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        # Verify user is participant in the conversation
        conversation = serializer.validated_data['conversation']
        if not conversation.participants.filter(user_id=request.user.user_id).exists():
            return Response(
                {'error': 'You are not a participant in this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create the message
        message = serializer.save()
        
        # Return full message details
        response_serializer = MessageSerializer(message)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """
        Update a message (only allow sender to edit their own messages)
        """
        message = self.get_object()
        
        # Only allow sender to edit their message
        if message.sender.user_id != request.user.user_id:
            return Response(
                {'error': 'You can only edit your own messages'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete a message (only allow sender to delete their own messages)
        """
        message = self.get_object()
        
        # Only allow sender to delete their message
        if message.sender.user_id != request.user.user_id:
            return Response(
                {'error': 'You can only delete your own messages'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def by_conversation(self, request):
        """
        Get all messages for a specific conversation
        """
        conversation_id = request.query_params.get('conversation_id')
        if not conversation_id:
            return Response(
                {'error': 'conversation_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            conversation = Conversation.objects.get(conversation_id=conversation_id)
            
            # Verify user is participant
            if not conversation.participants.filter(user_id=request.user.user_id).exists():
                return Response(
                    {'error': 'You are not a participant in this conversation'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            messages = self.get_queryset().filter(conversation=conversation)
            serializer = MessageSerializer(messages, many=True)
            return Response(serializer.data)
            
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search messages by content
        """
        query = request.query_params.get('q', '')
        conversation_id = request.query_params.get('conversation_id')
        
        if not query:
            return Response(
                {'error': 'Search query parameter "q" is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        messages = self.get_queryset().filter(message_body__icontains=query)
        
        # Filter by conversation if specified
        if conversation_id:
            messages = messages.filter(conversation__conversation_id=conversation_id)
        
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for User operations (read-only for messaging context)
    
    Provides:
    - List users (for finding conversation participants)
    - Retrieve user details
    - Search users by name or email
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search users by name or email for adding to conversations
        """
        query = request.query_params.get('q', '')
        if not query:
            return Response(
                {'error': 'Search query parameter "q" is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        users = User.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        ).exclude(user_id=request.user.user_id)  # Exclude current user
        
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Get current user's details
        """
        serializer = UserSerializer(request.user)
        return Response(serializer.data)