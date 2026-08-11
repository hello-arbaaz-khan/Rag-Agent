# Architecture Overview

This document describes the system architecture of DocuMind backend.

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Client Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │   Web App    │  │  Mobile App  │  │  API Clients │                  │
│  │  (React)     │  │   (Future)   │  │  (cURL, etc) │                  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                  │
└─────────┼──────────────────┼──────────────────┼─────────────────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │ HTTP/REST
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           API Gateway Layer                              │
│                         (Django + DRF)                                   │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                        URL Routing                                │   │
│  │                    /api/* endpoints                               │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │   Views     │ │ Serializers │ │ Middleware  │ │   Auth      │       │
│  │  (APIView)  │ │ (Validation)│ │   (CORS)    │ │  (Future)   │       │
│  └──────┬──────┘ └─────────────┘ └─────────────┘ └─────────────┘       │
└─────────┼───────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Service Layer                                   │
│                     (Business Logic)                                     │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐            │
│  │ DocumentService │ │   QAService     │ │ SearchService   │            │
│  │ - create        │ │ - answer_question│ │ - search       │            │
│  │ - delete        │ │ - build_context │ │ - browse       │            │
│  │ - list          │ │ - generate_answer││                │            │
│  │ - get_status    │ │ - store_history │ │                │            │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘            │
│  ┌─────────────────┐                                                    │
│  │  DriveService   │                                                    │
│  │ - sync_documents│                                                    │
│  └─────────────────┘                                                    │
└─────────┼───────────────────────────────────────────────────────────────┘
          │
          ├──────────────────────────────────────────┐
          │                                          │
          ▼                                          ▼
┌─────────────────────┐                 ┌─────────────────────────────────┐
│    Data Access      │                 │      Background Tasks           │
│       Layer         │                 │        (Celery Workers)         │
│  ┌───────────────┐  │                 │  ┌───────────────────────────┐  │
│  │ Django ORM    │  │                 │  │  process_document_task    │  │
│  │ - models.py   │  │                 │  │  - parse document         │  │
│  │ - migrations/ │  │                 │  │  - chunk text             │  │
│  └───────────────┘  │                 │  │  - generate embeddings    │  │
│  ┌───────────────┐  │                 │  │  - store in ChromaDB      │  │
│  │ Vector Store  │  │                 │  └───────────────────────────┘  │
│  │ (ChromaDB)    │  │                 └──────────────┬──────────────────┘  │
│  └───────────────┘  │                                │                      │
└─────────┬───────────┘                                │ Async                │
          │                                            ▼                      │
          │                            ┌─────────────────────────────────┐   │
          │                            │        Utility Layer            │   │
          │                            │  ┌───────────────────────────┐  │   │
          │                            │  │   rag_engine.py           │  │   │
          │                            │  │ - build_prompt            │  │   │
          │                            │  │ - generate_answer (Groq)  │  │   │
          │                            │  │ - calculate_confidence    │  │   │
          │                            │  └───────────────────────────┘  │   │
          │                            │  ┌───────────────────────────┐  │   │
          │                            │  │   pdf_processor.py        │  │   │
          │                            │  │ - extract_text            │  │   │
          │                            │  │ - split_chunks            │  │   │
          │                            │  └───────────────────────────┘  │   │
          │                            └─────────────────────────────────┘   │
          │                                                                  │
          ▼                                                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                              Data Stores                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐           │
│  │   SQLite3       │  │   ChromaDB      │  │     Redis       │           │
│  │  (Database)     │  │ (Vector Store)  │  │  (Message Broker)│          │
│  │ - documents     │  │ - embeddings    │  │ - task queue    │           │
│  │ - chunks        │  │ - collections   │  │ - result backend│           │
│  │ - chat_history  │  │                 │  │                 │           │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘           │
│  ┌─────────────────┐  ┌─────────────────┐                                │
│  │  File System    │  │  Google Drive   │                                │
│  │  /media/        │  │  (External)     │                                │
│  │ - uploads/      │  │  - source docs  │                                │
│  └─────────────────┘  └─────────────────┘                                │
└──────────────────────────────────────────────────────────────────────────┘

                              External Services
┌──────────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐           │
│  │  Groq API       │  │  Google OAuth   │  │  Drive Service  │           │
│  │  (LLM)          │  │                 │  │  (port 8001)    │           │
│  │ - LLM inference│  │ - Authentication│  │ - file listing  │           │
│  │ - text gen     │  │ - tokens        │  │ - file download │           │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘           │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. API Gateway Layer (Django + DRF)

**Technologies:** Django 6.0.6, Django REST Framework 3.17.1

**Responsibilities:**
- HTTP request routing
- Request/response serialization
- Input validation
- CORS handling
- Error handling

**Key Files:**
- `documind/urls.py` - Root URL configuration
- `rag/urls.py` - API endpoint routing
- `rag/views.py` - API view classes
- `rag/serializers.py` - Data validation and serialization

**Request Flow:**
```
Client → Django Middleware → URL Router → View → Serializer → Service Layer
```

---

### 2. Service Layer (Business Logic)

**Location:** `rag/services/`

**Design Pattern:** Service Layer Pattern

**Purpose:** 
- Encapsulate business logic
- Separate concerns from views
- Enable reusability
- Facilitate testing

**Services:**

#### DocumentService
```python
# rag/services/document_service.py
class DocumentService:
    @staticmethod
    def create_and_process(file, name, file_type)
    @staticmethod
    def delete(document_id)
    @staticmethod
    def list_all()
    @staticmethod
    def get_status(document_id)
```

#### QAService
```python
# rag/services/qa_service.py
class QAService:
    @staticmethod
    def answer_question(question, document_id)
    # Returns: question, answer, source_chunks, confidence_score
```

#### SearchService
```python
# rag/services/search_service.py
class SearchService:
    @staticmethod
    def search(query)
    @staticmethod
    def browse()
```

#### DriveService
```python
# rag/services/drive_service.py
def sync_drive_documents()
# Syncs files from Google Drive
```

---

### 3. Background Task Processing (Celery)

**Technologies:** Celery 5.4.0, Redis 5.0.8

**Architecture:**
```
Django App → Redis (Broker) → Celery Worker → Task Execution
                                      ↓
                                 Redis (Backend)
                                      ↓
                                 Task Results
```

**Configuration:**
- **Broker:** `redis://localhost:6379/0`
- **Backend:** `redis://localhost:6379/0`
- **Serializer:** JSON
- **Acknowledgment:** Late (for reliability)

**Main Task:**
```python
# rag/tasks.py
@app.task(bind=True, acks_late=True)
def process_document_task(self, document_id):
    """
    1. Fetch document
    2. Parse content (PDF/DOCX/TXT)
    3. Split into chunks
    4. Generate embeddings
    5. Store in ChromaDB
    6. Update status
    """
```

**Why Async?**
- Document processing is CPU-intensive
- Embedding generation takes time
- Prevents blocking HTTP requests
- Enables retry on failure

---

### 4. Data Access Layer

#### Django ORM (SQLite3)

**Models:** `rag/models.py`

**Tables:**
- `UploadedDocument` - Document metadata
- `DocumemtsChunks` - Text chunks with embeddings
- `ChatHistory` - Q&A conversation history
- `DriveDocument` - Google Drive sync tracking

**Features:**
- Automatic migrations
- Relationship management (ForeignKey, OneToOne)
- Query optimization
- Transaction support

**Example:**
```python
# Create document
document = UploadedDocument.objects.create(
    name="report.pdf",
    file=uploaded_file,
    file_type="pdf"
)

# Query with relationships
chunks = document.chunks.all().order_by('chunk_index')
```

#### ChromaDB (Vector Store)

**Location:** `rag/utils/vector_store.py`

**Strategy:**
- **Per-document collections:** `document{document_id}`
- **Global collection:** For cross-document search

**Operations:**
```python
# Add chunks with embeddings
add_chunks_to_collection(document_id, chunks, embeddings)

# Semantic search
similar_chunks = search_similar_chunks(query, document_id, top_k=3)

# Cleanup
delete_document_collection(document_id)
delete_global_document_chunks(document_id)
```

**Embedding Model:** Sentence Transformers (all-MiniLM-L6-v2 or similar)

---

### 5. Utility Layer

#### RAG Engine (`rag/utils/rag_engine.py`)

**Purpose:** LLM interaction and prompt engineering

**Functions:**
```python
build_context(chunks)           # Concatenate relevant chunks
build_prompt(question, context, history)  # Create LLM prompt
generate_answer(prompt)         # Call Groq API
calculate_confidence(chunks)    # Compute relevance score
```

**Prompt Structure:**
```
System: You are a helpful assistant answering questions based on provided context.

History:
User: Previous question 1
Assistant: Previous answer 1

Context:
[Chunk 1 text]
[Chunk 2 text]
...

Question: Current user question

Answer:
```

**LLM Provider:** Groq API (fast inference)

---

#### PDF Processor (`rag/utils/pdf_processor.py`)

**Purpose:** Document parsing and chunking

**Supported Formats:**
- PDF (via PyMuPDF)
- DOCX (via python-docx)
- DOC (legacy Word)
- TXT (plain text)

**Process:**
```
File → Extract Text → Clean → Split Chunks → Return List
```

**Chunking Strategy:**
- Configurable chunk size (e.g., 500 characters)
- Overlap between chunks for context
- Preserve page numbers

---

#### Vector Store (`rag/utils/vector_store.py`)

**Purpose:** ChromaDB operations

**Key Functions:**
```python
search_similar_chunks(query, document_id, top_k)
add_chunks_to_collection(document_id, chunks, embeddings)
delete_document_collection(document_id)
delete_global_document_chunks(document_id)
```

**Embedding Generation:**
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(chunks)
```

---

### 6. External Services

#### Groq API (LLM Inference)

**Purpose:** Generate answers using LLM

**Integration:**
```python
from groq import Groq
client = Groq(api_key=GROQ_API_KEY)
response = client.chat.completions.create(
    model="llama-3.1-70b-versatile",
    messages=[{"role": "user", "content": prompt}]
)
answer = response.choices[0].message.content
```

**Benefits:**
- Fast inference (sub-second)
- Cost-effective
- High-quality models

---

#### Google Drive Integration

**Architecture:**
```
Django App (port 8000) → Drive Service (port 8001) → Google Drive API
```

**Drive Service Components:**
- `drive_service/main.py` - FastAPI app
- `drive_service/auth.py` - OAuth handling
- `drive_service/drive_client.py` - Google Drive API client

**Flow:**
1. User authenticates with Google OAuth
2. Drive service fetches file list
3. Files downloaded and stored temporarily
4. Django imports files as UploadedDocument
5. Normal processing pipeline begins

---

## Data Flow Examples

### Example 1: Document Upload & Processing

```
1. Client uploads file via POST /api/upload/
2. Django validates file (size, type)
3. DocumentService creates UploadedDocument record
4. Celery task queued: process_document_task.delay(document_id)
5. Response returned immediately (201 Created)
6. [Async] Celery worker picks up task
7. [Async] Document parsed (PyMuPDF/python-docx)
8. [Async] Text split into chunks
9. [Async] Embeddings generated (Sentence Transformers)
10. [Async] Chunks stored in ChromaDB
11. [Async] UploadedDocument.is_processed = True
```

**Timeline:**
```
T0: Upload request (2s)
T1: Response to client
T1-T60: Background processing (varies by document size)
T60: Document ready for Q&A
```

---

### Example 2: Question & Answer

```
1. Client sends POST /api/question/ {question, document_id}
2. QAService validates document is processed
3. QAService retrieves chat history
4. VectorStore searches similar chunks (top 3)
5. RAG Engine builds context from chunks
6. RAG Engine builds prompt with history + context
7. Groq API generates answer
8. Confidence score calculated
9. ChatHistory record created
10. Response returned to client
```

**Response Time:** ~1-3 seconds (depending on LLM latency)

---

### Example 3: Document Deletion

```
1. Client sends DELETE /api/detail/<id>/
2. DocumentService starts database transaction
3. UploadedDocument deleted from DB
4. ChromaDB collection deleted
5. Global chunks deleted
6. Transaction committed
7. Response returned (204 No Content)
```

**Atomicity:** All-or-nothing via database transaction

---

## Security Considerations

### Current State
⚠️ **No authentication implemented** - All endpoints publicly accessible

### Recommended Improvements

1. **Authentication**
   ```python
   # Add to settings.py
   REST_FRAMEWORK = {
       'DEFAULT_AUTHENTICATION_CLASSES': [
           'rest_framework_simplejwt.authentication.JWTAuthentication',
       ],
       'DEFAULT_PERMISSION_CLASSES': [
           'rest_framework.permissions.IsAuthenticated',
       ],
   }
   ```

2. **Authorization**
   - Users should only access their own documents
   - Add `owner` field to models
   - Filter queries by user

3. **Input Validation**
   - Already implemented via serializers ✓
   - File type validation ✓
   - File size limits ✓

4. **Rate Limiting**
   ```python
   # Install django-ratelimit
   # Add to views
   from ratelimit.decorators import ratelimit
   
   @ratelimit(key='ip', rate='10/m')
   def post(self, request):
       ...
   ```

5. **CORS Configuration**
   - Currently configured for localhost ✓
   - Review for production

---

## Scalability Considerations

### Current Bottlenecks

1. **SQLite Database**
   - Write-lock contention
   - Limited concurrent connections
   - **Solution:** Migrate to PostgreSQL

2. **Single Celery Worker**
   - Sequential task processing
   - **Solution:** Multiple workers, worker autoscaling

3. **ChromaDB In-Memory**
   - Memory constraints
   - **Solution:** ChromaDB persistent mode or cloud vector DB

4. **Synchronous LLM Calls**
   - Blocking during Groq API calls
   - **Solution:** Async views, caching

### Scaling Strategies

#### Horizontal Scaling
```
Load Balancer
    ├── Django Instance 1
    ├── Django Instance 2
    └── Django Instance 3
    
Shared Resources:
- PostgreSQL (database)
- Redis (broker/backend)
- ChromaDB Server (vector store)
- Media Storage (S3/NFS)
```

#### Celery Scaling
```bash
# Auto-scale workers based on queue depth
celery -A documind worker --loglevel=info --autoscale=10,3
```

#### Caching Strategy
```python
# Cache frequently asked questions
from django.core.cache import cache

def answer_question(question, document_id):
    cache_key = f"qa:{document_id}:{hash(question)}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    answer = QAService.answer_question(...)
    cache.set(cache_key, answer, timeout=3600)
    return answer
```

---

## Monitoring & Observability

### Recommended Tools

1. **Application Monitoring**
   - Sentry (error tracking)
   - New Relic / Datadog (APM)

2. **Celery Monitoring**
   - Flower (real-time monitoring)
   ```bash
   celery -A documind flower
   ```

3. **Logging**
   ```python
   # Configure structured logging
   LOGGING = {
       'version': 1,
       'handlers': {
           'file': {
               'class': 'logging.FileHandler',
               'filename': 'debug.log',
           },
       },
       'loggers': {
           'rag': {
               'handlers': ['file'],
               'level': 'INFO',
           },
       },
   }
   ```

4. **Metrics to Track**
   - Document processing time
   - Q&A response latency
   - ChromaDB query performance
   - Celery task success/failure rates
   - API error rates

---

## Deployment Architecture

### Development
```
localhost:8000 - Django
localhost:6379 - Redis
localhost:8001 - Drive Service
FileSystem - ChromaDB + SQLite
```

### Production (Recommended)
```
                    ┌─────────────────┐
                    │  Load Balancer  │
                    │  (Nginx/ALB)    │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
    ┌─────────▼────┐ ┌──────▼─────┐ ┌──────▼────┐
    │   Django 1   │ │  Django 2  │ │  Django 3 │
    │   (Gunicorn) │ │  (Gunicorn)│ │  (Gunicorn)│
    └─────────┬────┘ └──────┬─────┘ └──────┬────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
    ┌─────────▼────┐ ┌──────▼─────┐ ┌──────▼────┐
    │  PostgreSQL  │ │   Redis    │ │  ChromaDB │
    │   (RDS)      │ │  (Elasti.) │ │  (Server) │
    └──────────────┘ └────────────┘ └───────────┘
    
    ┌─────────────────────────────────────────┐
    │         Celery Workers (Auto-scale)     │
    └─────────────────────────────────────────┘
    
    ┌─────────────────────────────────────────┐
    │         Media Storage (S3 Bucket)       │
    └─────────────────────────────────────────┘
```

---

*Last Updated: August 2025*
*Version: 1.0.0*
