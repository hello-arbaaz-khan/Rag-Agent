from rag.models import UploadedDocument
from rag.utils.rag_engine import (
    build_context, build_prompt, generate_answer, calculate_confidence
)
from rag.utils.vector_store import search_similar_chunks


class QAService:
    """Business logic for answering questions against a document."""

    @staticmethod
    def answer_question(question, document_id):
        document = UploadedDocument.objects.get(id=document_id)

        if not document.is_processed:
            raise ValueError("Document is still being processed")

        similar_chunks = search_similar_chunks(question, document_id, top_k=3)

        if not similar_chunks:
            return {
                "question": question,
                "answer": "Answer not found in document",
                "source_chunks": [],
                "document_name": document.name,
                "confidence_score": 0.0,
            }

        context = build_context(similar_chunks)
        prompt = build_prompt(question, context)
        answer = generate_answer(prompt)
        confidence = calculate_confidence(similar_chunks)

        return {
            "question": question,
            "answer": answer,
            "source_chunks": similar_chunks,
            "document_name": document.name,
            "confidence_score": confidence,
        }