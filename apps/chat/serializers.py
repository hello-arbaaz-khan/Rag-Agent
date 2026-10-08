from rest_framework import serializers

from apps.chat.models import ChatMessage
from apps.documents.models import UploadedDocument
from apps.documents.serializers import DocumentChunksSerializer


class QuestionSerializer(serializers.Serializer):
    question = serializers.CharField(required=True, max_length=1000, min_length=2)
    conversation_id = serializers.IntegerField()

    def validate_question(self, value):
        if not value.strip():
            raise serializers.ValidationError("Question can't be empty")
        return value

    def validate_conversation_id(self, value):
        if not value or value < 1:
            raise serializers.ValidationError("Invalid conversation id")
        return value


class AnswerSerializer(serializers.Serializer):
    question = serializers.CharField()
    answer = serializers.CharField()
    source_chunk = DocumentChunksSerializer()
    document_name = serializers.CharField()


class ChatHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "conversation", "role", "content", "created_at"]
        read_only_fields = fields