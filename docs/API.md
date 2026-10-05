# API Reference

The FastAPI service is the document, chat, search, and Google Drive API:

```text
http://localhost:8001
```

Interactive OpenAPI documentation is available at `/docs`. Django serves
authentication separately at `http://localhost:8000`.

## Authentication

Create an account with `POST http://localhost:8000/api/auth/signup/`:

```json
{
  "email": "you@example.com",
  "password": "your-password",
  "display_name": "Your Name"
}
```

Verify the emailed four-digit OTP using
`POST /api/auth/signup/verify-otp/` with `email` and `otp`. The response
contains `data.tokens.access` and `data.tokens.refresh`. Alternatively, an
active account can sign in with `POST /api/auth/login/` and `email` /
`password`. Send the access token to protected FastAPI routes as:

```http
Authorization: Bearer <access-token>
```

Refresh an expired access token with `POST /api/auth/token/refresh/` and a
JSON `refresh` field. The API checks the token signature and expiry and
rejects deleted or inactive Django users.

## Documents

All document routes require a bearer access token.

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/v1/documents` | Upload and queue a document |
| `GET` | `/api/v1/documents` | List the authenticated user's documents |
| `GET` | `/api/v1/documents/{document_id}` | Retrieve document details and processing status |
| `DELETE` | `/api/v1/documents/{document_id}` | Delete an owned document |

Upload as `multipart/form-data` with a `file` field. Supported extensions are
PDF, DOC, DOCX, TXT, JPG, JPEG, PNG, WEBP, and TIFF; the maximum size is 50 MB.
A successful upload returns `202 Accepted` with a document record. Processing
runs in Celery; poll `GET /api/v1/documents/{document_id}` until
`is_processed` is true or `processing_error` is non-empty. The same endpoint
serves as the status endpoint; there is no separate `/status` route.

Uploads are deduplicated per user by file hash. A duplicate returns `409
Conflict` and includes the existing document ID.

## Chat

`POST /api/v1/chat` requires a bearer token and accepts:

```json
{
  "question": "What is this document about?",
  "document_id": 1
}
```

The document must belong to the authenticated user and be processed. The
response contains the answer and its `chat_history_id`. An inaccessible
document returns `404`; a document that is still processing returns `409`.
Chat retrieves from the user's document through the existing RagCore retrieval
and reranking pipeline, generates an answer, and persists it in Django
`ChatHistory`.

## Document search

`GET /api/v1/search` requires a bearer token. Supported query parameters:

| Parameter | Values / format | Default |
|---|---|---|
| `query` | Optional text query | — |
| `uploaded_after` | `YYYY-MM-DD`, inclusive | — |
| `uploaded_before` | `YYYY-MM-DD`, inclusive | — |
| `file_type` | `pdf`, `doc`, `docx`, `txt`, `image` | — |
| `order_by` | `uploaded_at` or `name` | `uploaded_at` |
| `order` | `asc` or `desc` | `desc` |
| `limit` | 1–100 | `20` |
| `offset` | 0 or greater | `0` |

Without `query`, this lists matching document metadata. With `query`, it searches
processed documents owned by the authenticated user using the existing
sentence-transformer embeddings and pgvector retrieval, combined with
PostgreSQL full-text search over document chunks. Exact filename queries (for
example, `find Pakistan War.pdf`) prioritize the matching filename. Manual
uploads and Google Drive documents are searched together from the same
`UploadedDocument` records. Results are unique documents and include a
`relevance_score` and, when available, a `matched_snippet`; search does not
generate an answer.

Examples:

```text
GET /api/v1/search?query=political%20information
GET /api/v1/search?query=find%20Pakistan%20War.pdf
```

The response contains `results`, `count`, `limit`, and `offset`.

## Google Drive

These endpoints require a bearer access token, except for the OAuth callback,
which is authorized by its signed, single-use OAuth state.

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/v1/drive/connect` | Return the Google authorization URL |
| `GET` | `/api/v1/drive/callback` | Google OAuth redirect callback |
| `DELETE` | `/api/v1/drive/disconnect` | Disconnect the current user's Google account |
| `POST` | `/api/v1/drive/sync` | Queue a sync for the connected user's Drive |
| `GET` | `/api/v1/drive/files` | List Drive files (`page_size`, optional `page_token`) |
| `GET` | `/api/v1/drive/files/{file_id}/download` | Download Drive content as base64; requires `name` and `mime_type` query parameters |

Google OAuth credentials, a connected account, PostgreSQL migrations, and
Redis are required to exercise Drive operations. OAuth callback redirects to
the configured frontend URL and queues an initial Drive sync. The explicit
sync endpoint returns `202 Accepted` with the Celery task ID. Supported Drive
files are stored as `UploadedDocument` records with `source=google_drive` and
processed through the existing document task, Workflow, and RagCore pipeline.
Google Docs, Sheets, and Slides are exported as DOCX, XLSX, and PDF; Google
Workspace exports larger than the Drive API's 10 MB export limit are skipped.

## Services and local setup

The end-to-end upload/chat flow requires PostgreSQL with pgvector, Redis,
Django, the Celery worker, and FastAPI. With Docker Compose, start the
services and apply Django migrations before API use:

```bash
docker compose up --build -d
docker compose exec django python manage.py migrate
```

The service URLs are `http://localhost:8000` for Django authentication and
`http://localhost:8001` for FastAPI. Compose exposes PostgreSQL on host port
`5433` and Redis on host port `6380`; containers use their internal service
addresses.
