import logging
import os
import threading

import chromadb
from django.conf import settings as django_settings
from sentence_transformers import SentenceTransformer

from rag.models import DocumemtsChunks


logger = logging.getLogger(__name__)

GLOBAL_COLLECTION_NAME = "global_documents"

print("Embedding model is loading...")
EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
print("Embedding model ready")

# Lock to serialize concurrent .encode() calls.
# sentence-transformers is NOT thread-safe; two threads calling .encode()
# simultaneously with show_progress_bar=True cause a tqdm deadlock.
_EMBEDDING_LOCK = threading.Lock()

def get_chroma_client():
    """Create and return ChromaDB client"""
    chroma_path = os.path.join(django_settings.BASE_DIR, "chroma_db")
    client = chromadb.PersistentClient(
        path=chroma_path
    )
    return client


def get_collection(document_id):
    """ Every document will have its own collection """
    client = get_chroma_client()

    collection = client.get_or_create_collection(
        name = f"document{document_id}",
        metadata={"hnsw:space": "cosine"}
    )

    return collection


def get_global_collection():
    """Shared collection across all indexed document chunks."""
    client = get_chroma_client()

    collection = client.get_or_create_collection(
        name=GLOBAL_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    return collection


def create_embeddings(text):
    """ Text to number (vectors) """
    embedding = EMBEDDING_MODEL.encode(text)

    return embedding.tolist()


def create_embedding_batch(texts):
    """ create multiple vectors """
    with _EMBEDDING_LOCK:
        embedding = EMBEDDING_MODEL.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,  # tqdm causes GIL contention across threads
        )
    return embedding.tolist()


def _chunk_metadata(chunk):
    return {
        "document_id": chunk.document_id,
        "document_name": chunk.document.name,
        "file_type": chunk.document.file_type,
        "chunk_id": chunk.id,
        "chunk_index": chunk.chunk_index,
        "page_number": chunk.page_number,
        "chunk_size": chunk.chunk_size,
    }


def store_document_chunks(document_id):
    """ Save all chunks in chromadb and django db """
    chunks = list(
        DocumemtsChunks.objects.select_related("document")
        .filter(document_id=document_id)
        .order_by("chunk_index", "id")
    )

    if not chunks:
        raise ValueError("chunks not found")

    missing_embedding_indexes = [
        index for index, chunk in enumerate(chunks)
        if not chunk.embedding
    ]

    embeddings = [list(chunk.embedding) if chunk.embedding else None for chunk in chunks]
    if missing_embedding_indexes:
        texts_to_embed = [chunks[index].chunk_text for index in missing_embedding_indexes]
        logger.info("Creating %s missing embeddings for document %s", len(texts_to_embed), document_id)
        new_embeddings = create_embedding_batch(texts_to_embed)
        for index, embedding in zip(missing_embedding_indexes, new_embeddings):
            embeddings[index] = embedding
            chunks[index].embedding = embedding
        logger.info("Embeddings created for document %s", document_id)

    collection = get_collection(document_id)
    global_collection = get_global_collection()

    ids = [str(c.id) for c in chunks]
    texts = [c.chunk_text for c in chunks]
    metadatas = [_chunk_metadata(c) for c in chunks]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )
    global_collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    DocumemtsChunks.objects.bulk_update(chunks, ['embedding'])

    return len(texts)


def search_similar_chunks(question, document_id, top_k=3):
    """ Finding similar chunk of question """

    question_embedding = create_embeddings(question)
    collection = get_collection(document_id)
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k,
        include=['documents', 'metadatas', 'distances']
    )

    similar_chunks = []

    if not results or not results.get('documents') or not results['documents'][0]:
        return similar_chunks

    documents = results['documents'][0]
    metadatas = results['metadatas'][0]
    distances = results['distances'][0]

    for text, meta, dist in zip(documents, metadatas, distances):
        similarity = round(1 - dist, 2)

        similar_chunks.append({
            "text": text,
            "page_number": meta.get('page_number', 0),
            "chunk_index": meta.get('chunk_index', 0),
            "similarity": similarity
        })

    return similar_chunks

def delete_document_collection(document_id):
    """ Delete document from chromadb also """
    client = get_chroma_client()
    try:
        client.delete_collection(name=f"document{document_id}")
        logger.info("Document %s deleted from chromadb", document_id)
    except Exception as e:
        raise ValueError(f"Failed to delete document {document_id} from chromadb: {str(e)}")


def delete_global_document_chunks(document_id):
    """Remove a document's chunks from the global collection."""
    collection = get_global_collection()
    try:
        collection.delete(where={"document_id": document_id})
        logger.info("Document %s deleted from global chroma collection", document_id)
    except Exception as e:
        raise ValueError(f"Failed to delete document {document_id} from global chromadb: {str(e)}")
