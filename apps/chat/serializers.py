from rest_framework import serializers
from apps.chat.models import ChatHistory
from apps.documents.models import UploadedDocument
from apps.documents.serializers import DocumentChunksSerializer


class QuestionSerializer(serializers.ModelSerializer):
    """
    Question validation serializer
    """
    question = serializers.CharField(required=True, max_length=1000, min_length=2)
    document_id = serializers.IntegerField()

    class Meta:
        model = UploadedDocument
        fields = [
            'id',
            'question',
            'document_id',
        ]

    def validate_question(self, value):
        """Question validation"""
        if not value.strip():
            raise serializers.ValidationError("Question can't be empty")
        return value

    def validate_document_id(self, value):
        """Check document exists"""
        if not UploadedDocument.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"Document id {value} not exist")
        return value

class AnswerSerializer(serializers.Serializer):
    """
    Rag response serializer
    """
    question = serializers.CharField()
    answer = serializers.CharField()
    source_chunk = DocumentChunksSerializer()
    document_name = serializers.CharField()


class ChatHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatHistory
        fields = ['id','document', 'question', 'answer', 'created_at']
        read_only_fields = fields