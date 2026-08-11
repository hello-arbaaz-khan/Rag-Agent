# API Endpoints

Detailed API documentation with request/response examples.

## Base URL
```
http://localhost:8000/api/
```

---

## 1. Document Management

### List All Documents
**Endpoint:** `GET /api/list/`

**Description:** Retrieve a list of all uploaded documents with their metadata.

**Request:**
```http
GET /api/list/ HTTP/1.1
Host: localhost:8000
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "quarterly_report.pdf",
      "file": "/media/uploads/documents/quarterly_report.pdf",
      "file_type": "pdf",
      "file_size": 2458624,
      "is_processed": true,
      "processing_error": "",
      "chunk_count": 52,
      "created_at": "2025-08-10T14:30:00Z",
      "updated_at": "2025-08-10T14:35:00Z"
    },
    {
      "id": 2,
      "name": "meeting_notes.docx",
      "file": "/media/uploads/documents/meeting_notes.docx",
      "file_type": "docx",
      "file_size": 145678,
      "is_processed": false,
      "processing_error": "",
      "chunk_count": 0,
      "created_at": "2025-08-11T09:15:00Z",
      "updated_at": "2025-08-11T09:15:00Z"
    }
  ]
}
```

---

### Upload Document
**Endpoint:** `POST /api/upload/`

**Description:** Upload a new document for processing. The document will be processed asynchronously in the background.

**Request:**
```http
POST /api/upload/ HTTP/1.1
Host: localhost:8000
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="report.pdf"
Content-Type: application/pdf

<binary_data>
------WebKitFormBoundary
Content-Disposition: form-data; name="name"

Quarterly Report
------WebKitFormBoundary
Content-Disposition: form-data; name="file_type"

pdf
------WebKitFormBoundary--
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/upload/ \
  -F "file=@/path/to/report.pdf" \
  -F "name=Quarterly Report" \
  -F "file_type=pdf"
```

**Validation Rules:**
- `file`: Required, max 50MB
- `name`: Required, string
- `file_type`: Required, one of [`pdf`, `docx`, `doc`, `txt`]

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": 3,
    "name": "Quarterly Report",
    "file": "/media/uploads/documents/report.pdf",
    "file_type": "pdf",
    "file_size": 1048576,
    "is_processed": false,
    "processing_error": "",
    "chunk_count": 0,
    "created_at": "2025-08-11T10:00:00Z",
    "updated_at": "2025-08-11T10:00:00Z"
  }
}
```

**Response (400 Bad Request):**
```json
{
  "success": false,
  "errors": {
    "file": ["File size must be less than 50MB"],
    "file_type": ["Only ['pdf', 'docx', 'doc', 'txt'] allowed"]
  }
}
```

**Response (500 Internal Server Error):**
```json
{
  "success": false,
  "message": "Processing failed: Unable to parse document"
}
```

---

### Delete Document
**Endpoint:** `DELETE /api/detail/<int:document_id>/`

**Description:** Delete a document and remove its associated vector embeddings from ChromaDB.

**Request:**
```http
DELETE /api/detail/1/ HTTP/1.1
Host: localhost:8000
```

**cURL Example:**
```bash
curl -X DELETE http://localhost:8000/api/detail/1/
```

**Response (204 No Content):**
```
(Empty body)
```

**Response (404 Not Found):**
```json
{
  "success": false,
  "message": "Document not found"
}
```

**Notes:**
- This operation is irreversible
- Associated chat history and chunks are also deleted
- ChromaDB collections are cleaned up automatically

---

### Get Document Status
**Endpoint:** `GET /api/status/<int:document_id>/`

**Description:** Check the processing status of a document.

**Request:**
```http
GET /api/status/1/ HTTP/1.1
Host: localhost:8000
```

**cURL Example:**
```bash
curl http://localhost:8000/api/status/1/
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "quarterly_report.pdf",
    "is_processed": true,
    "processing_error": "",
    "chunk_count": 52
  }
}
```

**Response (404 Not Found):**
```json
{
  "success": false,
  "message": "Document not found"
}
```

**Status Values:**
- `is_processed: false` - Document is being processed or queued
- `is_processed: true` - Document is ready for Q&A
- `processing_error: non-empty` - Processing failed with error message

---

## 2. Question & Answer

### Ask Question
**Endpoint:** `POST /api/question/`

**Description:** Ask a question about a specific document. The system uses RAG to find relevant chunks and generate an AI-powered answer.

**Request:**
```http
POST /api/question/ HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "question": "What was the revenue growth in Q3?",
  "document_id": 1
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/question/ \
  -H "Content-Type: application/json" \
  -d '{"question": "What was the revenue growth in Q3?", "document_id": 1}'
```

**Validation Rules:**
- `question`: Required, 2-1000 characters, cannot be empty
- `document_id`: Required, must exist and be processed

**Response (200 OK - Answer Found):**
```json
{
  "success": true,
  "data": {
    "question": "What was the revenue growth in Q3?",
    "answer": "The revenue growth in Q3 was 15% compared to Q2, reaching $4.5 million.",
    "source_chunks": [
      {
        "id": 23,
        "chunk_text": "Q3 revenue increased by 15% quarter-over-quarter, totaling $4.5M...",
        "chunk_size": 245,
        "chunk_index": 22,
        "page_number": 5,
        "created_at": "2025-08-10T14:35:00Z"
      },
      {
        "id": 24,
        "chunk_text": "The growth was driven by strong performance in the enterprise segment...",
        "chunk_size": 198,
        "chunk_index": 23,
        "page_number": 5,
        "created_at": "2025-08-10T14:35:00Z"
      }
    ],
    "document_name": "quarterly_report.pdf",
    "confidence_score": 0.89
  }
}
```

**Response (200 OK - Answer Not Found):**
```json
{
  "success": true,
  "data": {
    "question": "What is the CEO's favorite color?",
    "answer": "Answer not found in document",
    "source_chunks": [],
    "document_name": "quarterly_report.pdf",
    "confidence_score": 0.0
  }
}
```

**Response (400 Bad Request):**
```json
{
  "success": false,
  "message": "Document is still being processed"
}
```

**Response (404 Not Found):**
```json
{
  "success": false,
  "message": "Document not found"
}
```

**Response Fields:**
- `question`: The user's question
- `answer`: Generated answer from the LLM
- `source_chunks`: Array of relevant chunks used to generate the answer
- `document_name`: Name of the queried document
- `confidence_score`: Float between 0.0 and 1.0 indicating answer confidence

---

## 3. Chat History

### Get Chat History
**Endpoint:** `GET /api/history/<int:document_id>/`

**Description:** Retrieve the conversation history for a specific document.

**Request:**
```http
GET /api/history/1/ HTTP/1.1
Host: localhost:8000
```

**cURL Example:**
```bash
curl http://localhost:8000/api/history/1/
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "document": 1,
      "question": "What was the revenue in Q3?",
      "answer": "The revenue in Q3 was $4.5 million.",
      "created_at": "2025-08-11T10:15:00Z"
    },
    {
      "id": 2,
      "document": 1,
      "question": "How does that compare to Q2?",
      "answer": "This represents a 15% increase from Q2.",
      "created_at": "2025-08-11T10:16:00Z"
    },
    {
      "id": 3,
      "document": 1,
      "question": "What were the main drivers?",
      "answer": "The growth was driven by strong enterprise segment performance.",
      "created_at": "2025-08-11T10:17:00Z"
    }
  ]
}
```

**Response (404 Not Found):**
```json
{
  "success": false,
  "message": "Document not found"
}
```

**Notes:**
- Messages are ordered chronologically (oldest first)
- Chat history is automatically maintained when using the Q&A endpoint
- Empty array is returned if no history exists

---

### Clear Chat History
**Endpoint:** `DELETE /api/history/<int:document_id>/`

**Description:** Delete all chat history for a specific document.

**Request:**
```http
DELETE /api/history/1/ HTTP/1.1
Host: localhost:8000
```

**cURL Example:**
```bash
curl -X DELETE http://localhost:8000/api/history/1/
```

**Response (204 No Content):**
```json
{
  "success": true,
  "message": "Chat history cleared successfully"
}
```

**Response (404 Not Found):**
```json
{
  "success": false,
  "message": "Document not found"
}
```

---

## 4. Search

### Global Search
**Endpoint:** `GET /api/search/`

**Description:** Perform a semantic search across all documents or browse all available content.

#### With Query
**Request:**
```http
GET /api/search/?query=machine+learning HTTP/1.1
Host: localhost:8000
```

**cURL Example:**
```bash
curl "http://localhost:8000/api/search/?query=machine+learning"
```

**Response (200 OK):**
```json
{
  "results": [
    {
      "document_id": 5,
      "document_name": "ai_research.pdf",
      "chunks": [
        {
          "chunk_text": "Machine learning algorithms can be categorized into supervised, unsupervised...",
          "chunk_index": 12,
          "page_number": 3,
          "similarity_score": 0.92
        },
        {
          "chunk_text": "...deep learning is a subset of machine learning that uses neural networks",
          "chunk_index": 15,
          "page_number": 4,
          "similarity_score": 0.87
        }
      ]
    },
    {
      "document_id": 8,
      "document_name": "tech_overview.docx",
      "chunks": [
        {
          "chunk_text": "Our ML pipeline processes data in real-time...",
          "chunk_index": 8,
          "page_number": 2,
          "similarity_score": 0.81
        }
      ]
    }
  ],
  "query": "machine learning"
}
```

#### Browse All (No Query)
**Request:**
```http
GET /api/search/ HTTP/1.1
Host: localhost:8000
```

**cURL Example:**
```bash
curl http://localhost:8000/api/search/
```

**Response (200 OK):**
```json
{
  "results": [
    {
      "document_id": 1,
      "document_name": "quarterly_report.pdf",
      "chunks": [...]
    },
    {
      "document_id": 2,
      "document_name": "meeting_notes.docx",
      "chunks": [...]
    }
  ],
  "query": ""
}
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | No | Search query. If omitted or empty, returns all documents. |

---

## 5. Google Drive Sync

### Sync Drive Documents
**Endpoint:** `POST /api/sync-drive/`

**Description:** Trigger synchronization of files from Google Drive. This endpoint communicates with the external drive_service running on port 8001.

**Request:**
```http
POST /api/sync-drive/ HTTP/1.1
Host: localhost:8000
Content-Type: application/json
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/sync-drive/
```

**Prerequisites:**
- Drive service must be running on `http://127.0.0.1:8001`
- Google OAuth credentials configured
- User has authenticated with Google Drive

**Response (200 OK):**
```json
{
  "status": "success",
  "synced_count": 5,
  "failed_count": 0,
  "details": [
    {
      "drive_file_id": "1a2b3c4d5e6f",
      "name": "project_proposal.pdf",
      "status": "indexed"
    },
    {
      "drive_file_id": "7g8h9i0j1k2l",
      "name": "budget_2025.xlsx",
      "status": "pending"
    }
  ]
}
```

**Response (500 Internal Server Error):**
```json
{
  "status": "error",
  "detail": "Drive service unavailable: Connection refused"
}
```

**Sync Status Values:**
- `pending` - Document queued for processing
- `processing` - Currently being processed
- `indexed` - Successfully indexed and ready
- `failed` - Processing failed (check `sync_error`)

---

## Error Handling

All endpoints follow a consistent error response format:

### Client Errors (4xx)
```json
{
  "success": false,
  "message": "Human-readable error message",
  "errors": {
    "field_name": ["Specific validation error"]
  }
}
```

### Server Errors (5xx)
```json
{
  "success": false,
  "message": "Internal server error description"
}
```

### Common HTTP Status Codes

| Code | Meaning | Typical Cause |
|------|---------|---------------|
| 200 | OK | Request succeeded |
| 201 | Created | Document uploaded successfully |
| 204 | No Content | Delete succeeded |
| 400 | Bad Request | Invalid input, validation failed |
| 404 | Not Found | Resource doesn't exist |
| 500 | Internal Server Error | Server-side failure |

---

## Rate Limiting

Currently, no rate limiting is implemented. For production use, consider:
- Django Ratelimit
- Nginx rate limiting
- API Gateway solutions

---

## Authentication

⚠️ **Warning:** The current implementation does not include authentication. All endpoints are publicly accessible.

For production, implement:
- Token-based authentication (DRF SimpleJWT)
- Session authentication
- OAuth2 for third-party integrations

Example DRF authentication classes to add in settings:
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

---

## Versioning

API versioning is not currently implemented. Recommended approach for future versions:
- URL versioning: `/api/v1/`, `/api/v2/`
- Header versioning: `Accept: application/vnd.documind.v1+json`

---

*Last Updated: August 2025*
