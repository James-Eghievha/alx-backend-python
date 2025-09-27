# messaging_app/chats/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import User, Conversation, Message

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Full User serializer with password handling and encryption
    Supports full CRUD operations with custom validation
    """
    full_name = serializers.ReadOnlyField()
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = [
            'user_id', 'first_name', 'last_name', 'email', 
            'phone_number', 'role', 'created_at', 'full_name', 'password'
        ]
        read_only_fields = ['user_id', 'created_at', 'full_name']
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
    
    class Meta:
        model = Message
        fields = [
            'message_id', 'sender', 'sender_id', 'conversation', 
            'message_body', 'sent_at'
        ]
        read_only_fields = ['message_id', 'sent_at', 'sender']
    
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
    messages = MessageSerializer(many=True, read_only=True)
    participant_count = serializers.ReadOnlyField()
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'conversation_id', 'participants', 'participant_ids',
            'messages', 'participant_count', 'last_message', 'created_at'
        ]
        read_only_fields = ['conversation_id', 'created_at', 'participant_count']
    
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
    
    class Meta:
        model = Conversation
        fields = [
            'conversation_id', 'participants', 'participant_count',
            'last_message', 'created_at'
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