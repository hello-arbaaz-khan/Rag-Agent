from sentence_transformers import SentenceTransformer
from rag.models import DocumemtsChunks
import chromadb
import os
import threading
from django.conf import settings as django_settings


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
    """Shared collection across all indexed document chunks — used for search across all files."""
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
            show_progress_bar=False,  
        )
    return embedding.tolist()


def store_document_chunks(document_id):
    """ Save all chunks in chromadb (per-document + global) and django db """
    chunks = DocumemtsChunks.objects.select_related("document").filter(document_id=document_id)

    if not chunks.exists():
        raise ValueError("chunks not found")

    chunks = list(chunks)
    texts = [c.chunk_text for c in chunks]
    print(f"{len(texts)} chunks are creating embeddings...")
    embeddings = create_embedding_batch(texts)
    print("Embeddings created")

    collection = get_collection(document_id)
    global_collection = get_global_collection()

    ids = [str(c.id) for c in chunks]
    metadatas = [
        {
            "document_id": c.document_id,
            "document_name": c.document.name,
            "file_type": c.document.file_type,
            "chunk_id": c.id,
            "chunk_index": c.chunk_index,
            "page_number": c.page_number,
            "chunk_size": c.chunk_size,
        }
        for c in chunks
    ]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )
    global_collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    for c, emb in zip(chunks, embeddings):
        c.embedding = emb
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
        print(f"Document {document_id} deleted from chromadb")
    except Exception as e:
        raise ValueError(f"Failed to delete document {document_id} from chromadb: {str(e)}")


def delete_global_document_chunks(document_id):
    """Remove a document's chunks from the global collection (call this on document delete too)."""
    global_collection = get_global_collection()
    try:
        global_collection.delete(where={"document_id": document_id})
        print(f"Document {document_id} deleted from global chromadb collection")
    except Exception as e:
        raise ValueError(f"Failed to delete document {document_id} from global chromadb: {str(e)}")


def search_all_documents(query, top_k=10, chunks_per_query=30):
    """
    Semantic search across ALL indexed documents (global collection).
    Groups matching chunks by document_id and returns a ranked list of FILES,
    each with its best relevance score and its top supporting chunks.
    """
    query_embedding = create_embeddings(query)
    global_collection = get_global_collection()

    results = global_collection.query(
        query_embeddings=[query_embedding],
        n_results=chunks_per_query,
        include=['documents', 'metadatas', 'distances']
    )

    if not results or not results.get('documents') or not results['documents'][0]:
        return []

    documents = results['documents'][0]
    metadatas = results['metadatas'][0]
    distances = results['distances'][0]

    grouped = {}
    for text, meta, dist in zip(documents, metadatas, distances):
        document_id = meta.get('document_id')
        if document_id is None:
            continue

        similarity = round(1 - dist, 4)
        entry = grouped.setdefault(document_id, {
            'document_id': document_id,
            'document_name': meta.get('document_name'),
            'file_type': meta.get('file_type'),
            'relevance_score': similarity,
            'matched_chunk_text': text,
        })

        if similarity > entry['relevance_score']:
            entry['relevance_score'] = similarity
            entry['matched_chunk_text'] = text

    ranked_files = sorted(grouped.values(), key=lambda item: item['relevance_score'], reverse=True)
    return ranked_files[:top_k]