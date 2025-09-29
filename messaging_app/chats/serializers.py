# messaging_app/chats/serializers.py
# COMPLETE UPDATED VERSION WITH JWT TOKEN SERIALIZERS

from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Conversation, Message

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer that includes additional user information
    """
    username_field = 'email'  # Use email instead of username
    
    @classmethod
    def get_token(cls, user):
        """
        Add custom claims to JWT token
        """
        token = super().get_token(user)
        
        # Add custom claims
        token['email'] = user.email
        token['role'] = user.role
        token['full_name'] = user.full_name
        token['user_id'] = str(user.user_id)
        
        return token
    
    def validate(self, attrs):
        """
        Override to use email instead of username
        """
        # The username field actually contains the email
        email = attrs.get(self.username_field)
        password = attrs.get('password')
        
        if email and password:
            try:
                # Find user by email
                user = User.objects.get(email=email)
                
                # Check password
                if user.check_password(password):
                    if not user.is_active:
                        raise serializers.ValidationError('User account is disabled.')
                    
                    # Set the username to email for parent validation
                    attrs[self.username_field] = user.email
                    
                    # Call parent validation
                    data = super().validate(attrs)
                    
                    # Add user information to response
                    data['user'] = {
                        'user_id': str(user.user_id),
                        'email': user.email,
                        'full_name': user.full_name,
                        'role': user.role,
                    }
                    
                    return data
                else:
                    raise serializers.ValidationError('Invalid credentials.')
                    
            except User.DoesNotExist:
                raise serializers.ValidationError('Invalid credentials.')
        
        raise serializers.ValidationError('Email and password required.')


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with JWT token generation
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    tokens = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'user_id', 'first_name', 'last_name', 'email', 
            'phone_number', 'role', 'password', 'password_confirm', 
            'tokens', 'created_at'
        ]
        read_only_fields = ['user_id', 'created_at', 'tokens']
    
    def validate(self, attrs):
        """
        Validate password confirmation
        """
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        
        # Remove password_confirm from attrs
        attrs.pop('password_confirm')
        return attrs
    
    def validate_email(self, value):
        """
        Check email uniqueness
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return value
    
    def create(self, validated_data):
        """
        Create user and return with JWT tokens
        """
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
    def get_tokens(self, user):
        """
        Generate JWT tokens for the new user
        """
        refresh = RefreshToken.for_user(user)
        refresh['email'] = user.email
        refresh['role'] = user.role
        refresh['full_name'] = user.full_name
        
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class UserSerializer(serializers.ModelSerializer):
    """
    Full User serializer with password handling and encryption
    Supports full CRUD operations with custom validation
    """
    full_name = serializers.ReadOnlyField()
    password = serializers.CharField(write_only=True, min_length=8, required=False)
    
    class Meta:
        model = User
        fields = [
            'user_id', 'first_name', 'last_name', 'email', 
            'phone_number', 'role', 'created_at', 'full_name', 'password',
            'is_active', 'last_login'
        ]
        read_only_fields = ['user_id', 'created_at', 'full_name', 'last_login']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def create(self, validated_data):
        """
        Create a new user with encrypted password
        """
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):
        """
        Update user instance, handle password separately
        """
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        
        if password:
            user.set_password(password)
            user.save()
        
        return user
    
    def validate_email(self, value):
        """
        Custom email validation
        """
        if User.objects.filter(email=value).exclude(user_id=getattr(self.instance, 'user_id', None)).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value


class UserSummarySerializer(serializers.ModelSerializer):
    """
    Lightweight User serializer for nested relationships
    Used in conversations and messages to avoid heavy payloads
    """
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = ['user_id', 'first_name', 'last_name', 'email', 'full_name', 'role']
        read_only_fields = ['user_id', 'full_name']


class MessageSerializer(serializers.ModelSerializer):
    """
    Full Message serializer with nested sender information
    Handles proper foreign key relationships and read/write field separation
    """
    sender = UserSummarySerializer(read_only=True)
    sender_id = serializers.UUIDField(write_only=True, required=False)
    can_edit = serializers.SerializerMethodField(read_only=True)
    can_delete = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'message_id', 'sender', 'sender_id', 'conversation', 
            'message_body', 'sent_at', 'can_edit', 'can_delete'
        ]
        read_only_fields = ['message_id', 'sent_at', 'sender']
    
    def get_can_edit(self, obj):
        """
        Check if current user can edit this message
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.sender == request.user or request.user.role == 'admin'
        return False
    
    def get_can_delete(self, obj):
        """
        Check if current user can delete this message
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.sender == request.user or request.user.role == 'admin'
        return False
    
    def validate_message_body(self, value):
        """
        Validate message content
        """
        if not value.strip():
            raise serializers.ValidationError("Message body cannot be empty.")
        if len(value) > 5000:
            raise serializers.ValidationError("Message is too long. Maximum 5000 characters allowed.")
        return value.strip()
    
    def create(self, validated_data):
        """
        Create a new message and associate with sender from context
        """
        # Remove sender_id if provided (we use request.user instead)
        validated_data.pop('sender_id', None)
        
        # Get sender from request context
        request = self.context.get('request')
        if request and request.user:
            validated_data['sender'] = request.user
        
        return super().create(validated_data)


class MessageCreateSerializer(serializers.ModelSerializer):
    """
    Streamlined serializer specifically for creating messages
    Simplified interface for message creation endpoints
    """
    class Meta:
        model = Message
        fields = ['conversation', 'message_body']
    
    def validate_message_body(self, value):
        """
        Validate message content
        """
        if not value.strip():
            raise serializers.ValidationError("Message body cannot be empty.")
        if len(value) > 5000:
            raise serializers.ValidationError("Message is too long. Maximum 5000 characters allowed.")
        return value.strip()
    
    def validate_conversation(self, value):
        """
        Validate that user is participant in conversation
        """
        request = self.context.get('request')
        if request and request.user:
            if not value.participants.filter(user_id=request.user.user_id).exists():
                raise serializers.ValidationError("You are not a participant in this conversation.")
        return value
    
    def create(self, validated_data):
        """
        Create message with sender from request context
        """
        request = self.context.get('request')
        if request and request.user:
            validated_data['sender'] = request.user
        return super().create(validated_data)


class ConversationSerializer(serializers.ModelSerializer):
    """
    Full Conversation serializer with nested relationships
    Handles participants and messages with many-to-many relationships
    Includes helper fields like participant_count and last_message
    """
    participants = UserSummarySerializer(many=True, read_only=True)
    participant_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        help_text="List of user IDs to add as participants"
    )
    messages = MessageSerializer(many=True, read_only=True, source='messages.all')
    participant_count = serializers.ReadOnlyField()
    last_message = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField(read_only=True)
    can_delete = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Conversation
        fields = [
            'conversation_id', 'participants', 'participant_ids',
            'messages', 'participant_count', 'last_message', 'created_at',
            'can_edit', 'can_delete'
        ]
        read_only_fields = ['conversation_id', 'created_at', 'participant_count']
    
    def get_can_edit(self, obj):
        """
        Check if current user can edit this conversation
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return (obj.participants.filter(user_id=request.user.user_id).exists() or 
                    request.user.role == 'admin')
        return False
    
    def get_can_delete(self, obj):
        """
        Check if current user can delete this conversation
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return (obj.participants.filter(user_id=request.user.user_id).exists() or 
                    request.user.role == 'admin')
        return False
    
    def get_last_message(self, obj):
        """
        Get the most recent message in the conversation
        """
        last_message = obj.get_last_message()
        if last_message:
            return {
                'message_id': last_message.message_id,
                'sender': UserSummarySerializer(last_message.sender).data,
                'message_body': last_message.message_body,
                'sent_at': last_message.sent_at
            }
        return None
    
    def validate_participant_ids(self, value):
        """
        Validate participant IDs
        """
        if not value:
            raise serializers.ValidationError("At least one participant is required.")
        
        # Check if users exist
        existing_users = User.objects.filter(user_id__in=value)
        if len(existing_users) != len(value):
            raise serializers.ValidationError("One or more user IDs are invalid.")
        
        return value
    
    def create(self, validated_data):
        """
        Create a new conversation with participants
        Automatically add current user as participant
        """
        participant_ids = validated_data.pop('participant_ids', [])
        
        # Add current user to participants if not already included
        request = self.context.get('request')
        if request and request.user:
            current_user_id = str(request.user.user_id)
            if current_user_id not in [str(pid) for pid in participant_ids]:
                participant_ids.append(request.user.user_id)
        
        # Create conversation
        conversation = Conversation.objects.create()
        
        # Add participants
        if participant_ids:
            participants = User.objects.filter(user_id__in=participant_ids)
            conversation.participants.set(participants)
        
        return conversation
    
    def update(self, instance, validated_data):
        """
        Update conversation participants
        """
        participant_ids = validated_data.pop('participant_ids', None)
        
        if participant_ids is not None:
            participants = User.objects.filter(user_id__in=participant_ids)
            instance.participants.set(participants)
        
        return super().update(instance, validated_data)


class ConversationSummarySerializer(serializers.ModelSerializer):
    """
    Lightweight Conversation serializer for listings
    Optimized for conversation list views with minimal data
    """
    participants = UserSummarySerializer(many=True, read_only=True)
    participant_count = serializers.ReadOnlyField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'conversation_id', 'participants', 'participant_count',
            'last_message', 'unread_count', 'created_at'
        ]
        read_only_fields = ['conversation_id', 'created_at', 'participant_count']
    
    def get_last_message(self, obj):
        """
        Get a summary of the most recent message
        """
        last_message = obj.get_last_message()
        if last_message:
            return {
                'message_id': last_message.message_id,
                'sender_name': last_message.sender.full_name,
                'message_body': last_message.message_body[:100] + ('...' if len(last_message.message_body) > 100 else ''),
                'sent_at': last_message.sent_at
            }
        return None
    
    def get_unread_count(self, obj):
        """
        Get unread message count for current user
        This is a placeholder - you'd need to implement read status tracking
        """
        # TODO: Implement read status tracking
        return 0


class TokenRefreshResponseSerializer(serializers.Serializer):
    """
    Serializer for token refresh response
    """
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = serializers.DictField(read_only=True)


class LogoutSerializer(serializers.Serializer):
    """
    Serializer for logout (token blacklisting)
    """
    refresh = serializers.CharField()
    
    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs
    
    def save(self, **kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except Exception as e:
            raise serializers.ValidationError(str(e))

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['user_id', 'email', 'first_name', 'last_name']
        read_only_fields = ['user_id']

class ConversationSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    
    class Meta:
        model = Conversation
        fields = ['conversation_id', 'participants', 'created_at']
        read_only_fields = ['conversation_id', 'created_at']

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = ['message_id', 'conversation', 'sender', 'message_body', 'sent_at']
        read_only_fields = ['message_id', 'sender', 'sent_at']