from math import exp
from rest_framework.parsers import MultiPartParser,FormParser
from django.shortcuts import render,HttpResponse
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rag.serializers import DocumentChunksSerializer,UploadedDocumentSerializer,DocumentListSerializer,DocumentDetailSerializer,QuestionSerializer,AnswerSerializer
from rag.models import UploadedDocument, DocumemtsChunks
from rag.utils.pdf_processor import process_document
from rag.utils.vector_store import delete_document_collection
# Create your views here. 
from rag.utils.rag_engine import get_answer


class DocumentListCreateView(APIView):
    parser_classess = [MultiPartParser, FormParser]

    def get(self,request):
        documents = UploadedDocument.objects.all()
        serializer = DocumentListSerializer(documents,many=True)

        return Response({
            "success":True,
            "count":documents.count(),
            "data":serializer.data
        },
        status=status.HTTP_200_OK
        )

        def post(self,request):
            serializer = UploadedDocumentSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    "success":False,
                    "message":"Uploading fail",
                    "errors":serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
                )
            
            document = serializer.save(file_size=request.FILE['file'].size)

            try:
                process_document(documents)
            except Exception as e:
                document.processing_error = str(e)
                document.save()
            
            return Response({
                "success":True,
                "message":"Document uploaded successfully",
                "data":serializer.data
            },
            status=status.HTTP_201_CREATED
            )

class DocumentDetailView(APIView):
    def get_object(self,pk):
        try:
            return UploadedDocument.objects.get(id=pk)
        except UploadedDocument.DoesNotExist:
            return None
        
    def get(self,request,pk):
        document = self.get_object(pk)
        if not document:
            return Response({
                "success":False,
                "message":"Document not found"
            },
            status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = DocumentDetailSerializer(document)

        return Response({
            "success":True,
            "data":serializer.data
        },
        status=status.HTTP_200_OK
        )

    def delete(self,request,pk):
        document = self.get_object(pk)
        if not document:

            return Response({
                "seccess":False,
                "message":"Document not found"
            },
            status=status.HTTP_404_NOT_FOUND
            )
        
        doc_name = document.name
        delete_document_collection(pk)

        document.delete()
        
        return Response({
            "seccess":True,
            "message":"Document deleted successfully"
        },
        status=status.HTTP_200_OK
        )


class DocumentStatusView(APIView):
    def get(self,request,pk):
        try:
            document = UploadedDocument.object.get(id=pk)
        except UploadedDocument.DoesNotExist:
            return Response({
                "success":False,
                "message":"Document not found"
            },
            status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(
            {
                "success": True,
                "data": {
                    "id": document.id,
                    "name": document.name,
                    "is_processed": document.is_processed,
                    "chunk_count": document.chunk_count,
                    "processing_error": document.processing_error
                }
            },
            status=status.HTTP_200_OK
        )


class QuestionAnswer(APIView):
    def post(self, request):
        """Question bhejo, answer lo"""

        # Step 1: Validate karo
        serializer = QuestionSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Invalid question!",
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        question = serializer.validated_data['question']
        document_id = serializer.validated_data['document_id']

        try:
            document = UploadedDocument.objects.get(id=document_id)
        except UploadedDocument.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Document nahi mila!"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if not document.is_processed:
            return Response(
                {
                    "success": False,
                    "message": "Document abhi process ho raha hai!"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if not document.is_processed:
            return Response(
                {
                    "success": False,
                    "message": "Document abhi process ho raha hai!"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = get_answer(
                question=question,
                document_id=document_id
            )

            return Response(
                {
                    "success": True,
                    "data": result
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": f"Error: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
