from django_filters import rest_framework as filters
from .models import Message, Conversation

class MessageFilter(filters.FilterSet):
    start_date = filters.DateTimeFilter(field_name='sent_at', lookup_expr='gte')
    end_date = filters.DateTimeFilter(field_name='sent_at', lookup_expr='lte')
    conversation = filters.UUIDFilter(field_name='conversation__conversation_id')
    sender = filters.UUIDFilter(field_name='sender__user_id')

    class Meta:
        model = Message
        fields = ['conversation', 'sender', 'start_date', 'end_date']

class ConversationFilter(filters.FilterSet):
    participant = filters.UUIDFilter(field_name='participants__user_id')
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Conversation
        fields = ['participant', 'created_after', 'created_before']