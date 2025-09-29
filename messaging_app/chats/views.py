# messaging_app/chats/views.py
# UPDATED VERSION WITH JWT AUTHENTICATION AND CUSTOM PERMISSIONS

from django.contrib.auth import get_user_model
from django.db.models import Q, Prefetch
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
import logging

from .models import Conversation, Message
from .serializers import (
    ConversationSerializer,
    ConversationSummarySerializer,
    MessageSerializer,
    MessageCreateSerializer,
    UserSerializer,
    UserSummarySerializer,
    UserRegistrationSerializer,
    LogoutSerializer
)
from .permissions import (
    IsConversationParticipant,
    IsMessageOwner,
    MessagePermission,
    ConversationPermission,
    CanSendMessagePermission,
    get_user_accessible_conversations,
    get_user_accessible_messages
)
from .filters import MessageFilter, ConversationFilter
from .pagination import CustomPageNumberPagination

User = get_user_model()
logger = logging.getLogger('chats.auth')

class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling Conversation operations with JWT authentication
    
    Provides:
    - List conversations for authenticated user only
    - Retrieve specific conversation with messages (if participant)
    - Create new conversations
    - Update conversation participants (if participant)
    - Delete conversations (if participant)
    - Custom actions for adding/removing participants
    """
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated, ConversationPermission]
    serializer_class = ConversationSerializer
    pagination_class = CustomPageNumberPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ConversationFilter
    search_fields = ['participants__email', 'participants__first_name']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Filter conversations to only include those where the user is a participant
        Optimize queries with prefetch_related for better performance
        """
        user = self.request.user
        return get_user_accessible_conversations(user).prefetch_related(
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
        logger.info(f"User {request.user.email} creating new conversation")
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create conversation with current user as participant
        conversation = serializer.save()
        
        logger.info(f"Conversation {conversation.conversation_id} created by {request.user.email}")
        
        # Return serialized conversation
        response_serializer = self.get_serializer(conversation)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a specific conversation with all messages
        """
        conversation = self.get_object()
        
        logger.info(f"User {request.user.email} accessing conversation {conversation.conversation_id}")
        
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
            
            # Check if user is already a participant
            if conversation.participants.filter(user_id=user_id).exists():
                return Response(
                    {'message': f'User {user_to_add.full_name} is already a participant'},
                    status=status.HTTP_200_OK
                )
            
            conversation.participants.add(user_to_add)
            
            logger.info(
                f"User {request.user.email} added {user_to_add.email} "
                f"to conversation {conversation.conversation_id}"
            )
            
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
            
            # Check if user is actually a participant
            if not conversation.participants.filter(user_id=user_id).exists():
                return Response(
                    {'message': f'User {user_to_remove.full_name} is not a participant'},
                    status=status.HTTP_200_OK
                )
            
            conversation.participants.remove(user_to_remove)
            
            logger.info(
                f"User {request.user.email} removed {user_to_remove.email} "
                f"from conversation {conversation.conversation_id}"
            )
            
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
        
        logger.info(f"User {request.user.email} searched conversations with query: {query}")
        
        serializer = ConversationSummarySerializer(conversations, many=True, context={'request': request})
        return Response(serializer.data)


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling Message operations with JWT authentication
    
    Provides:
    - List messages in conversations user participates in
    - Retrieve specific message (if in accessible conversation)
    - Create new messages (if participant in conversation)
    - Update messages (if message owner)
    - Delete messages (if message owner or admin)
    - Filter messages by conversation
    """
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated, MessagePermission]
    serializer_class = MessageSerializer
    pagination_class = CustomPageNumberPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = MessageFilter
    search_fields = ['message_body']
    ordering_fields = ['sent_at']
    ordering = ['-sent_at']

    def get_queryset(self):
        """
        Filter messages to only include those in conversations where user is participant
        """
        user = self.request.user
        return get_user_accessible_messages(user).select_related(
            'sender', 'conversation'
        ).order_by('-sent_at')
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action
        """
        if self.action == 'create':
            return MessageCreateSerializer
        return MessageSerializer
    
    def perform_create(self, serializer):
        """
        Set the sender of the message to the requesting user
        """
        serializer.save(sender=self.request.user)
    
    @action(detail=False, methods=['get'])
    def by_conversation(self, request):
        """
        Get all messages for a specific conversation
        """
        conversation_id = request.query_params.get('conversation_id')
        if not conversation_id:
            return Response(
                {'error': 'conversation_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        messages = self.get_queryset().filter(conversation__conversation_id=conversation_id)
        page = self.paginate_queryset(messages)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)
    
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
        
        logger.info(f"User {request.user.email} searched messages with query: {query}")
        
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User operations with JWT authentication
    
    Provides:
    - List users (for finding conversation participants)
    - Retrieve user details
    - Create new users (registration)
    - Update user profile
    - Search users by name or email
    """
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Return users based on user role
        - Admins can see all users
        - Regular users can see limited user info for search purposes
        """
        user = self.request.user
        if user.role == 'admin':
            return User.objects.all()
        else:
            # Regular users can only see basic info of other users for messaging
            return User.objects.filter(is_active=True).only(
                'user_id', 'first_name', 'last_name', 'email', 'role'
            )
    
    def get_permissions(self):
        """
        Set permissions based on action
        """
        if self.action == 'create':
            permission_classes = [AllowAny]  # Allow registration without auth
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action
        """
        if self.action == 'create':
            return UserRegistrationSerializer
        elif self.action in ['list', 'search']:
            return UserSummarySerializer
        return UserSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Create a new user (registration)
        """
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save()
        
        logger.info(f"New user registered: {user.email}")
        
        return Response(
            {
                'message': 'User registered successfully',
                'user': UserSummarySerializer(user).data,
                'tokens': serializer.get_tokens(user)
            },
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """
        Update user profile - users can only update their own profile
        """
        user_to_update = self.get_object()
        
        # Check if user is updating their own profile or if admin
        if user_to_update.user_id != request.user.user_id and request.user.role != 'admin':
            return Response(
                {'error': 'You can only update your own profile'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        logger.info(f"User {request.user.email} updating profile for {user_to_update.email}")
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete user - only admins or the user themselves
        """
        user_to_delete = self.get_object()
        
        # Check permissions
        if user_to_delete.user_id != request.user.user_id and request.user.role != 'admin':
            return Response(
                {'error': 'You can only delete your own account'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        logger.warning(f"User {request.user.email} deleting account for {user_to_delete.email}")
        
        return super().destroy(request, *args, **kwargs)
    
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
        
        users = self.get_queryset().filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        ).exclude(user_id=request.user.user_id)  # Exclude current user
        
        logger.info(f"User {request.user.email} searched for users with query: {query}")
        
        serializer = UserSummarySerializer(users, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Get current user's details
        """
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'])
    def change_password(self, request):
        """
        Change current user's password
        """
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not old_password or not new_password:
            return Response(
                {'error': 'Both old_password and new_password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        
        if not user.check_password(old_password):
            return Response(
                {'error': 'Invalid old password'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate new password
        try:
            from django.contrib.auth.password_validation import validate_password
            validate_password(new_password, user)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()
        
        logger.info(f"User {user.email} changed their password")
        
        return Response({'message': 'Password changed successfully'})


# Additional utility views for JWT authentication
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token obtain view with enhanced logging
    """
    
    def post(self, request, *args, **kwargs):
        logger.info(f"Login attempt from IP: {request.META.get('REMOTE_ADDR', 'unknown')}")
        
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Extract email from request data for logging
            email = request.data.get('username', 'unknown')  # username field contains email
            logger.info(f"Successful JWT login for user: {email}")
        else:
            logger.warning(f"Failed JWT login attempt from IP: {request.META.get('REMOTE_ADDR', 'unknown')}")
        
        return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def auth_test(request):
    """
    Simple endpoint to test JWT authentication
    """
    return Response({
        'message': 'JWT Authentication working!',
        'user': {
            'user_id': str(request.user.user_id),
            'email': request.user.email,
            'role': request.user.role,
            'full_name': request.user.full_name,
        },
        'auth_method': request.auth.__class__.__name__ if request.auth else 'Unknown'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Logout view that blacklists the refresh token
    """
    from .serializers import LogoutSerializer
    
    serializer = LogoutSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    
    logger.info(f"User {request.user.email} logged out")
    
    return Response({'message': 'Successfully logged out'})


# Health check endpoint
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for monitoring
    """
    return Response({
        'status': 'healthy',
        'message': 'Messaging API is running',
        'timestamp': '2024-01-01T00:00:00Z'  # You can use timezone.now() here
    })