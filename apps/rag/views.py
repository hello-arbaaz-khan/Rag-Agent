import requests
from apps.rag.services.search_service import SearchService
from django.conf import settings
from apps.rag.services.drive_service import sync_drive_documents
from apps.rag.services.document_service import DocumentService
from apps.rag.services.qa_service import QAService
from rest_framework.views import APIView
from rest_framework import status
from apps.rag.serializers import (UploadedDocumentSerializer,
QuestionSerializer,ChatHistorySerializer,
SearchQuerySerializer)

from apps.rag.models import UploadedDocument,ChatHistory,GoogleDriveAccount

from apps.auth_manager.permission import IsAuthenticatedAndVerified
from apps.shared.json_response import response_json
# Create your views here.


class DocumentListCreateView(APIView):
    permission_classes = [IsAuthenticatedAndVerified]
    def get(self, request):
        documents = DocumentService.list_for_user(request.user)
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
                user=request.user,
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
            DocumentService.delete(document_id, user=request.user)
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
            status_data = DocumentService.get_status(document_id, user=request.user)
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
            UploadedDocument.objects.get(id=document_id, user=request.user)
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
            UploadedDocument.objects.get(id=document_id, user=request.user)
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
                user=request.user,
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
    permission_classes = [IsAuthenticatedAndVerified]
    def post(self, request):
        """
        Sync Google Drive files with local database.
        This will fetch files from Google Drive and store them in the local database.
        """
        try:
            auth_header = request.META.get("HTTP_AUTHORIZATION")
            result = sync_drive_documents(user=request.user, auth_header=auth_header)
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
            auth_header = request.META.get("HTTP_AUTHORIZATION")
            result = SearchService.browse(request.user, auth_header)
        else:
            result = SearchService.search(query, request.user)
        return response_json(success=True, data=result, status=status.HTTP_200_OK)

class ConnectDriveView(APIView):
    permission_classes = [IsAuthenticatedAndVerified]

    def get(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION")
        if not auth_header:
            return response_json(success=False, message="Missing authorization header", status=401)

        try:
            resp = requests.get(
                f"{settings.DRIVE_SERVICE_BASE_URL}/connect",
                headers={"Authorization": auth_header},
                timeout=10,
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            return response_json(
                success=False,
                message=f"Failed to reach drive service: {e}",
                status=502,
            )

        return response_json(success=True, data={"auth_url": resp.json()["auth_url"]})

    
class DriveConnectionStatusView(APIView):
    permission_classes = [IsAuthenticatedAndVerified]

    def get(self, request):
        account = GoogleDriveAccount.objects.filter(user=request.user).first()

        if not account:
            return response_json(success=True, data={"connected": False})

        return response_json(
            success=True,
            data={
                "connected": True,
                "google_email": account.google_email,
                "connected_at": account.created_at,
            },
        )

class DisconnectDriveView(APIView):
    permission_classes = [IsAuthenticatedAndVerified]

    def delete(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION")
        if not auth_header:
            return response_json(success=False, message="Missing authorization header", status=401)

        try:
            resp = requests.delete(
                f"{settings.DRIVE_SERVICE_BASE_URL}/disconnect",
                headers={"Authorization": auth_header},
                timeout=10,
            )
            resp.raise_for_status()
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return response_json(success=False, message="Google Drive not connected.", status=404)
            return response_json(success=False, message=f"Failed to disconnect: {e}", status=502)
        except requests.RequestException as e:
            return response_json(success=False, message=f"Failed to reach drive service: {e}", status=502)

        return response_json(success=True, data={"disconnected": True})
