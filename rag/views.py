import manage
from rag.services.document_service import DocumentService
from rag.services.qa_service import QAService
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rag.serializers import UploadedDocumentSerializer,QuestionSerializer,ChatHistorySerializer
from rag.models import UploadedDocument,ChatHistory
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

class ChatHistoryView(APIView):
    def get(self,request,document_id):
        try:
            UploadedDocument.objects.get(id=document_id)
        except UploadedDocument.DoesNotExist:
            return Response(
                {"success":False, "message":"Document not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        messages = ChatHistory.objects.filter(document_id=document_id,).order_by('created_at')
        serializer = ChatHistorySerializer(messages, many=True)
        return Response({"success":True, "data": serializer.data}, status=status.HTTP_200_OK)

    def delete(self, request, document_id):
        try:
            ChatHistory.objects.filter(document_id=document_id)
        except ChatHistory.DoesNotExist:
            return Response(
                {"success":False, "message":"Documet not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        ChatHistory.objects.filter(document_id=document_id).delete()
        return Response({
            "success":True,"message":"Chat history cleared successfully"
        }, status=status.HTTP_204_NO_CONTENT)


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