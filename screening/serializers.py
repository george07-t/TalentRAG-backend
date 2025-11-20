from rest_framework import serializers
from .models import Session, ChatMessage

class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ['id', 'match_score', 'strengths', 'gaps', 'insights', 'created_at']

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'question', 'answer', 'retrieved_chunks', 'created_at']

class ChatRequestSerializer(serializers.Serializer):
    question = serializers.CharField()
