from sentence_transformers import SentenceTransformer
from rag.models import DocumemtsChunks
import chromadb
import os
from django.conf import settings as django_settings


print("Embedding model is loading...")
EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
print("EMbedding model ready")

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


def create_embeddings(text):
    """ Text to number (vectors) """
    embedding = EMBEDDING_MODEL.encode(text)
    
    return embedding.tolist()


def create_embedding_batch(texts):
    """ create multiple vectors """

    embedding = EMBEDDING_MODEL.encode(
        texts,
        batch_size=32,
        show_progress_bar=True
        )
    return embedding.tolist()


def store_document_chunks(document_id):
    """ Save all chunks in chromadb and django db """
    chunks = DocumemtsChunks.objects.filter(document_id=document_id)

    if not chunks.exists():
        raise ValueError("chunks not found")
    
    texts = [c.chunk_text for c in chunks]
    print(f"{len(texts)} chunks are creating embeddings...")
    embeddings = create_embedding_batch(texts)
    print("Embeddings created")

    collection = get_collection(document_id)

    collection.add(
        ids=[str(c.id) for c in chunks],
        embeddings=embeddings,
        documents=texts,
        metadatas=[
            {
                "chunk_index": c.chunk_index,
                "page_number": c.page_number,
                "chunk_size": c.chunk_size,
            }
            for c in chunks
        ]
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