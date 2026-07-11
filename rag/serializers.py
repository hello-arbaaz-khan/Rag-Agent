from rest_framework import serializers
from rag.models import UploadedDocument, DocumemtsChunks,ChatHistory

class DocumentChunksSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumemtsChunks
        fields = '__all__'


class UploadedDocumentSerializer(serializers.ModelSerializer):
    chunk_count = serializers.SerializerMethodField()
    
    class Meta:
        model = UploadedDocument
        fields = ['id', 'name', 'file', 'file_type', 'file_size', 'is_processed', 'processing_error', 'chunk_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'file_size', 'is_processed', 'processing_error', 'chunk_count', 'created_at', 'updated_at']

    def get_chunk_count(self, obj):
        return obj.chunk_count

    def validate_file(self, value):
        max_size = 50 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("File size must be less than 50MB")
        
        allow_extention = ['pdf', 'docx', 'doc', 'txt']
        extention = value.name.split('.')[-1].lower()
        if extention not in allow_extention:
            raise serializers.ValidationError(f"Only {allow_extention} allowed")
        return value
    
    def validate_file_type(self, value):
        allowed_types = ['pdf', 'docx', 'doc', 'txt']
        if value not in allowed_types:
            raise serializers.ValidationError(f"File type must be one of {allowed_types}")
        return value

class DocumentListSerializer(serializers.ModelSerializer):
    """
    This serializers is used to get list of all the documents
    """
    
    file_size = serializers.ReadOnlyField()
    chunk_count = serializers.ReadOnlyField()
    class Meta:
        model = UploadedDocument
        fields = [
            'id',
            'name',
            'file_type',
            'file_size',
            'chunk_count',
            'is_processed',
            'processing_error',
            'created_at',
            'updated_at'
        ]

class DocumentDetailSerializer(serializers.ModelSerializer):
    """
    This serializers is used to get detail of a specific document.
    """
    chunks = DocumentChunksSerializer(read_only=True, many=True)
    file_size = serializers.ReadOnlyField()
    chunk_count = serializers.ReadOnlyField()

    class Meta:
        model = UploadedDocument
        fields = [
            'id',
            'name',
            'file_type',
            'file',
            'file_size',
            'chunk_count',
            'is_processed',
            'processing_error',
            'chunks',
            'created_at',
            'updated_at'
        ]     


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
    
class AnswerSerializer(serializers.ModelSerializer):
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