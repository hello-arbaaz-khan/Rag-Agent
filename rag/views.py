from rag.services.document_service import DocumentService
from rag.services.qa_service import QAService
from rest_framework.parsers import MultiPartParser,FormParser
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rag.serializers import DocumentChunksSerializer,UploadedDocumentSerializer,DocumentListSerializer,DocumentDetailSerializer,QuestionSerializer,AnswerSerializer
from rag.models import UploadedDocument, DocumemtsChunks
from rag.utils.pdf_processor import process_document
from rag.utils.vector_store import delete_document_collection
# Create your views here. 


class DocumentListCreateView(APIView):
    def get(self, request):
        documents = DocumentService.list_all()
        serializer = UploadedDocumentSerializer(documents, many=True)
        return Response({"success": True, "data": serializer.data})

    def post(self, request):
        serializer = UploadedDocumentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            document = DocumentService.create_and_process(
                file=request.FILES["file"],
                name=serializer.validated_data["name"],
                file_type=serializer.validated_data["file_type"],
            )
            return Response(
                {"success": True, "data": UploadedDocumentSerializer(document).data},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {"success": False, "message": f"Processing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
class DocumentDetailView(APIView):
    def delete(self, request, document_id):
        try:
            DocumentService.delete(document_id)
            return Response(
                {"success": True, "message": "Document deleted"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except UploadedDocument.DoesNotExist:
            return Response(
                {"success": False, "message": "Document not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

class DocumentStatusView(APIView):
    def get(self, request, document_id):
        try:
            status_data = DocumentService.get_status(document_id)
            return Response({"success": True, "data": status_data})
        except UploadedDocument.DoesNotExist:
            return Response(
                {"success": False, "message": "Document not found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class QuestionAnswer(APIView):
    def post(self, request):
        serializer = QuestionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = QAService.answer_question(
                question=serializer.validated_data["question"],
                document_id=serializer.validated_data["document_id"],
            )
            return Response({"success": True, "data": result})

        except UploadedDocument.DoesNotExist:
            return Response(
                {"success": False, "message": "Document not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValueError as e:
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )