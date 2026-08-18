from apps.rag.services.search_service import SearchService
from apps.rag.services.drive_service import sync_drive_documents
from apps.rag.services.document_service import DocumentService
from apps.rag.services.qa_service import QAService
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from apps.rag.serializers import UploadedDocumentSerializer,QuestionSerializer,ChatHistorySerializer,SearchQuerySerializer
from apps.rag.models import UploadedDocument,ChatHistory
from apps.auth_manager.permission import IsAuthenticatedAndVerified
from apps.shared.json_response import response_json
# Create your views here.


class DocumentListCreateView(APIView):
    permission_classes = [IsAuthenticatedAndVerified]
    def get(self, request):
        documents = DocumentService.list_all()
        serializer = UploadedDocumentSerializer(documents, many=True)
        return response_json(success=True, data=serializer.data)

    def post(self, request):
        serializer = UploadedDocumentSerializer(data=request.data)
        if not serializer.is_valid():
            return response_json(
                success=False,
                errors=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            document = DocumentService.create_and_process(
                file=request.FILES["file"],
                name=serializer.validated_data["name"],
                file_type=serializer.validated_data["file_type"],
            )
            return response_json(
                success=True,
                data=UploadedDocumentSerializer(document).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return response_json(
                success=False,
                message=f"Processing failed: {str(e)}",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DocumentDetailView(APIView):
    permission_classes = [IsAuthenticatedAndVerified]
    def delete(self, request, document_id):
        try:
            DocumentService.delete(document_id)
            return response_json(
                success=True,
                message="Document deleted",
                status=status.HTTP_204_NO_CONTENT,
            )
        except UploadedDocument.DoesNotExist:
            return response_json(
                success=False,
                message="Document not found",
                status=status.HTTP_404_NOT_FOUND,
            )

class DocumentStatusView(APIView):
    permission_classes = [IsAuthenticatedAndVerified]
    def get(self, request, document_id):
        try:
            status_data = DocumentService.get_status(document_id)
            return response_json(success=True, data=status_data)
        except UploadedDocument.DoesNotExist:
            return response_json(
                success=False,
                message="Document not found",
                status=status.HTTP_404_NOT_FOUND,
            )

class ChatHistoryView(APIView):
    permission_classes = [IsAuthenticatedAndVerified]
    def get(self,request,document_id):
        try:
            UploadedDocument.objects.get(id=document_id)
        except UploadedDocument.DoesNotExist:
            return response_json(
                success=False,
                message="Document not found",
                status=status.HTTP_404_NOT_FOUND,
            )

        messages = ChatHistory.objects.filter(document_id=document_id,).order_by('created_at')
        serializer = ChatHistorySerializer(messages, many=True)
        return response_json(success=True, data=serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, document_id):
        try:
            UploadedDocument.objects.get(id=document_id)
        except UploadedDocument.DoesNotExist:
            return response_json(
                success=False,
                message="Document not found",
                status=status.HTTP_404_NOT_FOUND
            )

        ChatHistory.objects.filter(document_id=document_id).delete()
        return response_json(
            success=True,
            message="Chat history cleared successfully",
            status=status.HTTP_204_NO_CONTENT
        )


class QuestionAnswer(APIView):
    permission_classes = [IsAuthenticatedAndVerified]
    def post(self, request):
        serializer = QuestionSerializer(data=request.data)
        if not serializer.is_valid():
            return response_json(
                success=False,
                errors=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = QAService.answer_question(
                question=serializer.validated_data["question"],
                document_id=serializer.validated_data["document_id"],
            )
            return response_json(success=True, data=result)

        except UploadedDocument.DoesNotExist:
            return response_json(
                success=False,
                message="Document not found",
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValueError as e:
            return response_json(
                success=False,
                message=str(e),
                status=status.HTTP_400_BAD_REQUEST,
            )

class SyncDrive(APIView):
    # permission_classes = [IsAuthenticatedAndVerified]
    def post(self, request):
        """
        Sync Google Drive files with local database.
        This will fetch files from Google Drive and store them in the local database.
        """
        try:
            result = sync_drive_documents()
            return response_json(success=True, data=result)
        except Exception as e:
            return response_json(success=False, message=str(e), status=500)


class SearchView(APIView):
    permission_classes = [IsAuthenticatedAndVerified]
    def get(self, request):
        serializer = SearchQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        query = serializer.validated_data["query"].strip()

        if not query:
            result = SearchService.browse()
        else:
            result = SearchService.search(query)

        return response_json(success=True, data=result, status=status.HTTP_200_OK)