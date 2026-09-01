from sentence_transformers import SentenceTransformer
from apps.rag.models import DocumemtsChunks
from pgvector.django import CosineDistance
import threading

_model = None

def get_embedding_model():
    global _model
    if _model is None:
        print("Embedding model is loading...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        print("Embedding model ready")
    return _model

_EMBEDDING_LOCK = threading.Lock()


def create_embeddings(text):
    """ Text to number (vectors) """
    embedding = get_embedding_model().encode(text)
    return embedding.tolist()


def create_embedding_batch(texts):
    """ create multiple vectors """
    with _EMBEDDING_LOCK:
        embedding = get_embedding_model().encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
        )
    return embedding.tolist()


def store_document_chunks(document_id):
    """ Save all chunks with embeddings directly in Postgres """
    chunks = DocumemtsChunks.objects.select_related("document").filter(document_id=document_id)

    if not chunks.exists():
        raise ValueError("chunks not found")

    chunks = list(chunks)
    texts = [c.chunk_text for c in chunks]
    print(f"{len(texts)} chunks are creating embeddings...")
    embeddings = create_embedding_batch(texts)
    print("Embeddings created")

    for c, emb in zip(chunks, embeddings):
        c.embedding = emb

    DocumemtsChunks.objects.bulk_update(chunks, ['embedding'])
    return len(texts)


def search_similar_chunks(question, document_id, user, top_k=3):
    """ Finding similar chunks of a question within one document """
    question_embedding = create_embeddings(question)

    results = DocumemtsChunks.objects.filter(
        document__user=user,
        document_id=document_id,
        embedding__isnull=False
    ).annotate(
        distance=CosineDistance('embedding', question_embedding)
    ).order_by('distance')[:top_k]

    similar_chunks = []
    for chunk in results:
        similarity = round(1 - chunk.distance, 2)
        similar_chunks.append({
            "text": chunk.chunk_text,
            "page_number": chunk.page_number,
            "chunk_index": chunk.chunk_index,
            "similarity": similarity
        })

    return similar_chunks


def search_all_documents(query, user, top_k=10):
    """ Semantic search across ALL indexed documents """
    query_embedding = create_embeddings(query)

    results = DocumemtsChunks.objects.select_related('document').filter(
        document__user=user,
        embedding__isnull=False
    ).annotate(
        distance=CosineDistance('embedding', query_embedding)
    ).order_by('distance')[:top_k * 3]

    grouped = {}
    for chunk in results:
        doc_id = chunk.document_id
        similarity = round(1 - chunk.distance, 4)

        if doc_id not in grouped or similarity > grouped[doc_id]['relevance_score']:
            grouped[doc_id] = {
                'document_id': doc_id,
                'document_name': chunk.document.name,
                'file_type': chunk.document.file_type,
                'relevance_score': similarity,
                'matched_chunk_text': chunk.chunk_text,
            }

    ranked_files = sorted(grouped.values(), key=lambda x: x['relevance_score'], reverse=True)
    return ranked_files[:top_k]


def delete_document_collection(document_id):
    """ Delete document's chunks (embeddings included, since they're in the same row) """
    DocumemtsChunks.objects.filter(document_id=document_id).delete()
    print(f"Document {document_id} chunks deleted")


def delete_global_document_chunks(document_id):
    """ Kept for compatibility — same as delete_document_collection now since there's no separate global collection """
    DocumemtsChunks.objects.filter(document_id=document_id).delete()
    print(f"Document {document_id} chunks removed")