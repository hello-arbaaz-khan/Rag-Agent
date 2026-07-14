from django.db import migrations


GLOBAL_COLLECTION_NAME = "global_documents"


def forwards(apps, schema_editor):
    import chromadb
    from sentence_transformers import SentenceTransformer

    from django.conf import settings

    UploadedDocument = apps.get_model('rag', 'UploadedDocument')
    DocumemtsChunks = apps.get_model('rag', 'DocumemtsChunks')

    chroma_path = settings.BASE_DIR / "chroma_db"
    client = chromadb.PersistentClient(path=str(chroma_path))
    collection = client.get_or_create_collection(
        name=GLOBAL_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    model = SentenceTransformer('all-MiniLM-L6-v2')
    batch = []
    batch_size = 500

    chunks = (
        DocumemtsChunks.objects
        .select_related('document')
        .order_by('id')
        .iterator(chunk_size=batch_size)
    )

    def flush(items):
        if not items:
            return

        ids = [str(item['chunk'].id) for item in items]
        documents = [item['chunk'].chunk_text for item in items]
        metadatas = [
            {
                'document_id': item['chunk'].document_id,
                'document_name': item['chunk'].document.name,
                'file_type': item['chunk'].document.file_type,
                'chunk_id': item['chunk'].id,
                'chunk_index': item['chunk'].chunk_index,
                'page_number': item['chunk'].page_number,
                'chunk_size': item['chunk'].chunk_size,
            }
            for item in items
        ]
        embeddings = []
        missing = [item for item in items if not item['chunk'].embedding]
        if missing:
            missing_texts = [item['chunk'].chunk_text for item in missing]
            missing_embeddings = model.encode(missing_texts, batch_size=32, show_progress_bar=False).tolist()
            missing_map = {item['chunk'].id: emb for item, emb in zip(missing, missing_embeddings)}
            for item in items:
                emb = item['chunk'].embedding
                if not emb:
                    emb = missing_map[item['chunk'].id]
                embeddings.append(emb)
        else:
            embeddings = [list(item['chunk'].embedding) for item in items]

        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    for chunk in chunks:
        batch.append({'chunk': chunk})
        if len(batch) >= batch_size:
            flush(batch)
            batch = []

    flush(batch)


def backwards(apps, schema_editor):
    import chromadb
    from django.conf import settings

    chroma_path = settings.BASE_DIR / "chroma_db"
    client = chromadb.PersistentClient(path=str(chroma_path))
    try:
        client.delete_collection(name=GLOBAL_COLLECTION_NAME)
    except Exception:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('rag', '0009_add_processing_sync_status'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
