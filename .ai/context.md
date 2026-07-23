# System Context & Architecture Reference

## Project Overview

Documind is a Retrieval-Augmented Generation (RAG) platform that allows users to upload documents (PDF, DOCX, TXT) or sync them directly from Google Drive, and interact with their content through AI-powered QA and semantic search. It extracts text, chunks documents, generates vector embeddings, and uses Groq (LLM) to deliver context-aware answers with similarity scores and source citations.

- **Tech Stack**:
  - **Backend**: Python 3.12+, Django 6.0, Django REST Framework, Celery 5.4 + Redis 5.0 (async background task processing), FastAPI (for standalone Drive microservice).
  - **RAG & ML**: ChromaDB 1.5 (vector DB), SentenceTransformers (`all-MiniLM-L6-v2`), PyMuPDF / `python-docx` (text extraction), Groq API (`llama-3.1-8b-instant`).
  - **Frontend**: JavaScript (ES Modules), React 18, Vite 6, Tailwind CSS 3.4, Axios, Lucide React icons.

---

## Architecture

- **High-level Structure**: Service-oriented architecture with a React single-page application (SPA) frontend, a primary Django REST API backend with Celery/Redis for asynchronous task processing, and a standalone FastAPI microservice (`drive_service`) for Google Drive integration.

- **Folder Structure**:
  - `architecture/`: System documentation and reference guides.
  - `documind/`: Django project root containing configuration settings, URL routing, ASGI/WSGI, and Celery setup.
  - `drive_service/`: Standalone FastAPI microservice wrapping Google Drive API v3 for file listing and OAuth downloads.
  - `frontend/`: React + Vite single-page application interface.
  - `rag/`: Core Django application managing document ingestion, text extraction, chunking, vector storage, RAG Q&A, search services, and background tasks.
  - `chroma_db/`: Local persistent directory for ChromaDB vector collections.
  - `media/` / `uploads/`: Media storage directory for uploaded raw document files.

- **Key Entry Points**:
  - Backend API (Django): `manage.py` & `documind/wsgi.py` (starts Django server on port 8000).
  - Background Worker (Celery): `documind/celery.py` (`celery -A documind worker -l info`).
  - Google Drive Service (FastAPI): `drive_service/main.py` (runs via `uvicorn main:app --port 8001`).
  - Frontend SPA (Vite): `frontend/src/main.jsx` & `frontend/src/App.jsx` (dev server on port 3000).

---

## Core Modules/Components

- **API Views & Routing**: `rag/views.py` & `rag/urls.py`
  - *What it does*: Exposes REST endpoints for document upload, listing, deletion, status checking, Q&A, chat history, drive sync, and semantic search.
  - *Dependencies*: RAG services (`DocumentService`, `QAService`, `SearchService`, `drive_service`) & DRF serializers (`rag/serializers.py`).

- **Document Service**: `rag/services/document_service.py`
  - *What it does*: Manages CRUD operations for uploaded documents and triggers async Celery processing tasks.
  - *Dependencies*: `UploadedDocument` (models.py:L4), `process_document_task` (tasks.py:L9), and `vector_store`.

- **Q&A Service**: `rag/services/qa_service.py`
  - *What it does*: Orchestrates the RAG Q&A workflow by retrieving conversation history, querying vector store for context, invoking Groq LLM, and recording chat turns.
  - *Dependencies*: `rag_engine.py`, `vector_store.py`, `ChatHistory` (models.py:L63).

- **Search Service**: `rag/services/search_service.py`
  - *What it does*: Provides hybrid search across documents by combining tokenized filename matching with vector similarity across all indexed chunks.
  - *Dependencies*: `vector_store.py` and `DriveDocument` (models.py:L80).

- **Drive Sync Service**: `rag/services/drive_service.py`
  - *What it does*: Interacts with the external FastAPI microservice to fetch Google Drive file listings, create/update local `DriveDocument` records, download contents, and pass them for document indexing.
  - *Dependencies*: FastAPI `drive_service` HTTP endpoints and `DocumentService`.

- **Document Extraction & Processor**: `rag/utils/pdf_processor.py`
  - *What it does*: Extracts text from PDF, DOCX, and TXT files, cleans raw text, generates overlapping chunks, and creates database chunk entries.
  - *Dependencies*: `PyMuPDF` (`fitz`), `python-docx`, and `DocumemtsChunks` (models.py:L44).

- **Vector Store**: `rag/utils/vector_store.py`
  - *What it does*: Manages per-document and global ChromaDB collections, handles batch embeddings via SentenceTransformers (`all-MiniLM-L6-v2`), and executes vector search queries.
  - *Dependencies*: `chromadb`, `sentence_transformers`.

- **RAG LLM Engine**: `rag/utils/rag_engine.py`
  - *What it does*: Constructs context-aware prompts, interacts with Groq API (`llama-3.1-8b-instant`), and calculates confidence scores.
  - *Dependencies*: `groq` client library.

- **Background Tasks**: `rag/tasks.py`
  - *What it does*: Defers document extraction and vector indexing to Celery background tasks with retry policies and recovery methods for stuck documents.
  - *Dependencies*: `celery`, `pdf_processor.py`.

- **Drive Microservice**: `drive_service/main.py` & `drive_service/drive_client.py`
  - *What it does*: Standalone FastAPI service interfacing directly with Google Drive API v3 (OAuth2 authentication, file pagination, base64 file downloads).
  - *Dependencies*: `google-api-python-client`, `google-auth-oauthlib`, `fastapi`.

- **Frontend State & UI Components**: `frontend/src/App.jsx` & `frontend/src/context/AppContext.jsx`
  - *What it does*: Renders the React UI (chat interface, upload modal, advanced search page) and provides global state for active document selection, chat history, toast notifications, and status polling (`frontend/src/hooks/usePolling.js`).
  - *Dependencies*: React Context & `useReducer`, Axios service (`frontend/src/services/api.js`).

---

## Data Flow

### 1. Document Upload & Ingestion Flow
`User / Drive Sync Request` -> `DocumentListCreateView` / `SyncDrive` endpoint -> `DocumentService.create_and_process()` creates `UploadedDocument` record (`is_processed=False`) -> triggers `process_document_task.delay(id)` to Celery worker -> `pdf_processor.py` extracts and cleans text -> creates `DocumemtsChunks` rows in SQLite -> `vector_store.py` batch-embeds chunks via `SentenceTransformer` -> populates ChromaDB collections (`document{id}` & `global_documents`) -> updates document status to `is_processed=True`.

### 2. Question-Answering (RAG) Flow
`User submits question` -> `QuestionAnswer` API endpoint -> `QAService.answer_question()` retrieves document history -> `search_similar_chunks()` embeds query and fetches top matching chunks from `document{id}` ChromaDB collection -> `build_prompt()` formats context and transcript -> `generate_answer()` queries Groq API (`llama-3.1-8b-instant`) -> answer and confidence score saved to `ChatHistory` database table and returned to client.

### 3. Global Search Flow
`User types query` -> `SearchView` API endpoint -> `SearchService.search()` performs vector similarity query on `global_documents` ChromaDB collection and token match scoring on `DriveDocument` filenames -> aggregates & ranks results with relevance scores and matched snippets for display.

### Key Data Models
- `UploadedDocument` (models.py:L4): Uploaded file metadata (`name`, `file`, `file_type`, `file_size`, `is_processed`, `processing_error`).
- `DocumemtsChunks` (models.py:L44): Text chunk linked to a document with index, page number, and stored embedding.
- `ChatHistory` (models.py:L63): Q&A conversation history linked to a document.
- `DriveDocument` (models.py:L80): Google Drive file record with sync status (`pending`, `processing`, `indexed`, `failed`), drive file ID, and foreign key to `UploadedDocument`.

---

## Conventions & Patterns

- **Naming Conventions**: Python components use standard `snake_case` for variables/functions and `PascalCase` for classes. React components use `PascalCase` and custom hooks use `camelCase` (`usePolling`).
- **State Management**: Frontend uses React Context + `useReducer` pattern in `AppContext.jsx`. Chat history is synchronized with `localStorage` for offline persistence across page reloads.
- **Error Handling**: API endpoints return standard JSON response objects: `{"success": true|false, "data"|"errors"|"message": ...}`. Background processing errors are caught, saved to the document's `processing_error` field, and retried up to 3 times by Celery.
- **Service Layer Pattern**: Business logic is separated into dedicated service classes under `rag/services/` keeping Django views lightweight.
- **Microservice Adapter Pattern**: Google Drive API interactions are isolated in a standalone FastAPI service (`drive_service`), called via HTTP client by the Django backend.

---

## Recent Changes / Current Work

- **Last Changed** (commit `677d9e4`, branch `upgrade/advance-search`):
  - **AI Query Intent Parsing**: Added `rag/utils/query_intent.py` (`parse_query_intent`) using Groq LLM (`llama-3.1-8b-instant`) to extract structured `topic` and `date_filter` (type: `on`/`before`/`after`/`between`, ISO dates) from natural language search queries.
  - **Advanced Search Upgrade**: Updated `SearchService.search()` in `rag/services/search_service.py` to filter results by `date_filter` against `drive_modified_at`, apply a relevance cutoff threshold (`MIN_RELEVANCE = 0.35`), and return a custom message when no matching files are found.
  - **Search History Feature**: Added client-side localStorage persistence for recent search queries (`frontend/src/components/Search/Searchhistory.js`), rendering searchable chips and recent history dropdown actions in `AdvancedSearch.jsx`.
- **Previous Change** (commit `ee0d302`, branch `fix/auto-sync-drive`): Replaced the manual "Sync Drive" button in `AdvancedSearch.jsx` with an automatic background sync. Extracted sync logic into a new `useDriveAutoSync` hook (`frontend/src/hooks/useDriveAutoSync.js`) that fires `/api/sync-drive/` immediately on mount and then every 60 seconds.
- Added API Reference Map and Full Codebase Map sections to context.md for faster agent lookup — reduces need for full-repo search on future changes.

---

## Do Not Touch / Gotchas

- **Embedding Thread Lock**: Do not remove `_EMBEDDING_LOCK` in `rag/utils/vector_store.py` (L18). Calling `SentenceTransformer.encode()` concurrently without a lock causes a deadlock in `tqdm` progress bars.
- **Dual Vector Store Collections**: Every indexed document chunk is added to **both** its per-document collection (`document{id}`) and the global collection (`global_documents`). When deleting a document, both collections must be updated to prevent orphaned vector chunks (`document_service.py:L35-L43`).
- **Model Name Typo**: The Django model `DocumemtsChunks` (models.py:L44) has a typo (`Documemts` with an 'm'). Do not rename the class without creating appropriate Django migrations to avoid breaking existing DB schemas.
- **FastAPI Port Dependency**: `DRIVE_SERVICE_BASE_URL` defaults to `http://127.0.0.1:8001`. Ensure the `drive_service` FastAPI app is running on port 8001 when syncing Drive documents.

---

## API Reference Map

### Django REST API (Base: `/api/` -- served by Django on port 8000)

Defined in `rag/urls.py` and `documind/urls.py`.

| Endpoint | Method | View (file:line) | Service Called (file:line) | Model(s) Touched |
|----------|--------|------------------|---------------------------|------------------|
| `/api/list/` | GET | rag/views.py:14 `DocumentListCreateView.get` | document_service.py:47 `DocumentService.list_all` | `UploadedDocument` |
| `/api/upload/` | POST | rag/views.py:19 `DocumentListCreateView.post` | document_service.py:10 `DocumentService.create_and_process` | `UploadedDocument` |
| `/api/detail/<int:document_id>/` | DELETE | rag/views.py:45 `DocumentDetailView.delete` | document_service.py:24 `DocumentService.delete` | `UploadedDocument`, `DocumemtsChunks`, ChromaDB |
| `/api/status/<int:document_id>/` | GET | rag/views.py:59 `DocumentStatusView.get` | document_service.py:50 `DocumentService.get_status` | `UploadedDocument` |
| `/api/question/` | POST | rag/views.py:99 `QuestionAnswer.post` | qa_service.py:12 `QAService.answer_question` | `UploadedDocument`, `ChatHistory`, ChromaDB |
| `/api/history/<int:document_id>/` | GET | rag/views.py:70 `ChatHistoryView.get` | _(direct ORM query)_ | `UploadedDocument`, `ChatHistory` |
| `/api/history/<int:document_id>/` | DELETE | rag/views.py:83 `ChatHistoryView.delete` | _(direct ORM delete)_ | `UploadedDocument`, `ChatHistory` |
| `/api/sync-drive/` | POST | rag/views.py:126 `SyncDrive.post` | drive_service.py:78 `sync_drive_documents` | `DriveDocument`, `UploadedDocument` |
| `/api/search/` | GET | rag/views.py:139 `SearchView.get` | search_service.py:59 `SearchService.browse` (no query) or search_service.py:80 `SearchService.search` (with `?query=...`) | `DriveDocument`, ChromaDB |

> **Note**: `/api/detail/<id>/` is also used as the GET endpoint by `api.js:getDocument()` but the view does not implement a GET method -- that call goes unanswered at the backend. Only DELETE is implemented on `DocumentDetailView`.

---

### FastAPI Drive Microservice (port 8001)

Defined in `drive_service/main.py`.

| Endpoint | Method | View (file:line) | Service Called (file:line) | Notes |
|----------|--------|------------------|---------------------------|-------|
| `/files` | GET | drive_service/main.py:9 `get_files` | drive_client.py:61 `list_files` | Supports `page_size` & `page_token` query params |
| `/files/{file_id}/download` | GET | drive_service/main.py:33 `get_file_download` | drive_client.py:74 `download_file` | Returns base64-encoded file content |

---

## Full Codebase Map

> Excludes: `node_modules/`, `__pycache__/`, `migrations/`, `media/`, `chroma_db/`, `venv/`, build artifacts.

---

### `documind/` -- Django project configuration root

#### documind/__init__.py
- **Purpose**: Registers the Celery app at Django startup so `@shared_task` decorators are picked up automatically
- **Key exports**: `celery_app`
- **Depends on**: `documind/celery.py`

#### documind/settings.py
- **Purpose**: Central Django configuration -- database, Celery broker/backend, CORS origins, media paths, installed apps
- **Key config**: `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, `DRIVE_SERVICE_BASE_URL`, `DATABASES` (SQLite with 30s timeout)
- **Depends on**: `python-decouple` for env vars

#### documind/urls.py
- **Purpose**: Root URL router -- mounts `/admin/` and includes all `rag/` API URLs under `/api/`
- **Key exports**: `urlpatterns`
- **Depends on**: `rag/urls.py`

#### documind/celery.py
- **Purpose**: Celery application factory -- sets Django settings module and enables task auto-discovery
- **Key exports**: `app` (Celery instance)
- **Depends on**: `documind/settings.py`

#### documind/wsgi.py
- **Purpose**: WSGI entry point for production deployment (e.g., gunicorn)
- **Depends on**: `documind/settings.py`

#### documind/asgi.py
- **Purpose**: ASGI entry point for async-compatible servers (unused in current stack, but present for future use)
- **Depends on**: `documind/settings.py`

---

### `rag/` -- Core Django application

#### rag/models.py
- **Purpose**: Defines all database models for the RAG system
- **Key classes**: `UploadedDocument` (L4), `DocumemtsChunks` (L44), `ChatHistory` (L63), `DriveDocument` (L80)
- **Depends on**: Django ORM only

#### rag/views.py
- **Purpose**: DRF API view classes -- thin controllers that delegate to service layer
- **Key classes**: `DocumentListCreateView` (L13), `DocumentDetailView` (L44), `DocumentStatusView` (L58), `ChatHistoryView` (L69), `QuestionAnswer` (L98), `SyncDrive` (L125), `SearchView` (L138)
- **Depends on**: `rag/services/document_service.py`, `rag/services/qa_service.py`, `rag/services/search_service.py`, `rag/services/drive_service.py`, `rag/serializers.py`, `rag/models.py`

#### rag/urls.py
- **Purpose**: URL routing for all `rag` app endpoints mounted at `/api/`
- **Key exports**: `urlpatterns`
- **Depends on**: `rag/views.py`

#### rag/serializers.py
- **Purpose**: DRF serializers for input validation and output formatting
- **Key classes**: `UploadedDocumentSerializer` (L10), `DocumentListSerializer` (L38), `DocumentDetailSerializer` (L59), `QuestionSerializer` (L84), `ChatHistorySerializer` (L121), `SearchQuerySerializer` (L127)
- **Depends on**: `rag/models.py`

#### rag/tasks.py
- **Purpose**: Celery task definitions for async document processing with retry and recovery logic
- **Key functions**: `process_document_task` (L9, Celery task, max 3 retries, 30s delay), `requeue_stuck_documents` (L26)
- **Depends on**: `rag/utils/pdf_processor.py`, `rag/models.py`

#### rag/admin.py
- **Purpose**: Django admin registration (currently empty -- no models are registered in admin)
- **Depends on**: nothing

#### rag/apps.py
- **Purpose**: Django AppConfig for the `rag` application
- **Key classes**: `RagConfig`
- **Depends on**: nothing

---

### `rag/services/` -- Business logic layer

#### rag/services/document_service.py
- **Purpose**: CRUD operations for documents -- create, list, delete, get status; dispatches Celery tasks
- **Key class/methods**: `DocumentService` -- `create_and_process` (L10), `delete` (L24), `list_all` (L47), `get_status` (L50)
- **Depends on**: `rag/models.py`, `rag/tasks.py`, `rag/utils/vector_store.py`

#### rag/services/qa_service.py
- **Purpose**: Orchestrates the RAG Q&A pipeline -- retrieves context chunks, builds prompt, calls Groq, saves chat turn
- **Key class/methods**: `QAService` -- `answer_question` (L12)
- **Depends on**: `rag/models.py`, `rag/utils/rag_engine.py`, `rag/utils/vector_store.py`

#### rag/services/search_service.py
- **Purpose**: Hybrid search over all Drive documents -- vector similarity via ChromaDB global collection + filename token matching
- **Key class/functions**: `SearchService` -- `browse` (L59), `search` (L80); `score_filename_match` (L16)
- **Depends on**: `rag/models.py` (`DriveDocument`), `rag/utils/vector_store.py`

#### rag/services/drive_service.py
- **Purpose**: Interfaces with the FastAPI Drive microservice to sync, download, and index Google Drive files
- **Key functions**: `sync_drive_documents` (L78), `process_pending_drive_file` (L25), `fetch_drive_files` (L19), `browse_files` (L143)
- **Depends on**: `rag/models.py` (`DriveDocument`), `rag/services/document_service.py`

---

### `rag/utils/` -- Utility / infrastructure layer

#### rag/utils/pdf_processor.py
- **Purpose**: Full document processing pipeline -- extract text by file type, clean, chunk with overlap, bulk-save to DB, trigger vector indexing
- **Key functions**: `process_document` (L114), `create_chunks` (L70), `clean_text` (L51), `extract_text_from_pdf` (L9), `extract_text_from_docx` (L37), `extract_text_from_txt` (L25), `get_extractor` (L103)
- **Depends on**: `rag/models.py` (`DocumemtsChunks`), `rag/utils/vector_store.py`

#### rag/utils/vector_store.py
- **Purpose**: ChromaDB wrapper -- manages per-document and global vector collections, batch embedding, similarity search, and cleanup on deletion
- **Key functions**: `get_chroma_client` (L20), `get_collection` (L29), `get_global_collection` (L41), `create_embeddings` (L53), `create_embedding_batch` (L60), `store_document_chunks` (L71), `search_similar_chunks` (L121), `delete_document_collection` (L153), `delete_global_document_chunks` (L163), `search_all_documents` (L173)
- **Key globals**: `EMBEDDING_MODEL` (loaded at import time, L12), `_EMBEDDING_LOCK` (threading lock, L18)
- **Depends on**: `rag/models.py` (`DocumemtsChunks`), `sentence_transformers`, `chromadb`

#### rag/utils/rag_engine.py
- **Purpose**: LLM interaction layer -- lazy Groq client init, prompt construction with conversation history, API call, confidence scoring
- **Key functions**: `get_client` (L5), `build_context` (L16), `build_history_block` (L30), `build_prompt` (L46), `generate_answer` (L66), `calculate_confidence` (L95)
- **Depends on**: `groq` library (lazy import), `python-decouple` for `GROQ_API_KEY`

#### rag/utils/query_intent.py
- **Purpose**: Query intent parsing via LLM -- extracts structured topic and date_filter (`on`/`before`/`after`/`between`, ISO dates) from natural language search queries
- **Key functions**: `parse_query_intent` (L56), `_strip_code_fences` (L50)
- **Depends on**: `rag/utils/rag_engine.py` (`get_client`)

---

### `rag/management/commands/`

#### rag/management/commands/requeue_stuck_documents.py
- **Purpose**: Django management command (`python manage.py requeue_stuck_documents`) to find and re-queue documents stuck in processing >10 minutes
- **Key classes**: `Command` (L4)
- **Depends on**: `rag/tasks.py` (`requeue_stuck_documents`)

---

### `drive_service/` -- Standalone FastAPI Google Drive microservice

#### drive_service/main.py
- **Purpose**: FastAPI app exposing two HTTP endpoints for listing and downloading Google Drive files
- **Key routes**: `GET /files` (L9), `GET /files/{file_id}/download` (L33)
- **Depends on**: `drive_service/drive_client.py`, `drive_service/schemas.py`

#### drive_service/drive_client.py
- **Purpose**: Google Drive API v3 client -- OAuth credential management, file listing (paginated), file download as raw bytes
- **Key functions**: `get_credentials` (L11), `get_drive_service` (L57), `list_files` (L61), `download_file` (L74)
- **Depends on**: `drive_service/config.py`

#### drive_service/auth.py
- **Purpose**: One-time interactive OAuth2 browser flow script to generate and save `token.json`; must be run manually from CLI, never called by the server
- **Key functions**: `main` (L31)
- **Depends on**: `drive_service/config.py`

#### drive_service/config.py
- **Purpose**: Pydantic settings model for Drive service configuration -- credential file paths and OAuth scopes
- **Key classes**: `Settings` (L3)
- **Depends on**: nothing (reads `.env` via pydantic-settings)

#### drive_service/schemas.py
- **Purpose**: Pydantic response models for FastAPI endpoints
- **Key classes**: `DriveFile` (L4), `DriveFileListResponse` (L11), `DriveFileDownloadResponse` (L17)
- **Depends on**: nothing

---

### `frontend/` -- Vite config and HTML shell

#### frontend/index.html
- **Purpose**: HTML entry point -- loads Inter font from Google Fonts and mounts Vite SPA at `#root`
- **Depends on**: `frontend/src/main.jsx`

#### frontend/vite.config.js
- **Purpose**: Vite build and dev-server configuration (React plugin, proxy rules)
- **Depends on**: nothing project-internal

#### frontend/tailwind.config.js
- **Purpose**: Tailwind CSS v3 configuration -- content paths and any custom theme tokens
- **Depends on**: nothing project-internal

---

### `frontend/src/` -- React application source

#### frontend/src/main.jsx
- **Purpose**: React app bootstrap -- renders App inside AppProvider context to the DOM `#root`
- **Depends on**: `frontend/src/App.jsx`, `frontend/src/context/AppContext.jsx`, `frontend/src/styles.css`

#### frontend/src/App.jsx
- **Purpose**: Root layout -- manages view state (`chat` vs `search`), renders `Sidebar`, `ChatArea` / `AdvancedSearch`, `UploadModal`, and `Toast`; initiates status polling and automatic Drive sync
- **Key components**: `App`
- **Depends on**: `AppContext.jsx`, `usePolling.js`, `useDriveAutoSync.js`, all top-level UI components

#### frontend/src/styles.css
- **Purpose**: Global CSS -- Tailwind directives, scrollbar theming, `animate-fade-in` keyframe
- **Depends on**: nothing

#### frontend/src/context/AppContext.jsx
- **Purpose**: Global React state -- documents list, selected document, chat history (with `localStorage` persistence), toast queue; all via `useReducer`
- **Key exports**: `AppProvider`, `useAppContext`; reducer handles `SET_DOCUMENTS`, `UPSERT_DOCUMENT`, `REMOVE_DOCUMENT`, `ADD_MESSAGE`, `CLEAR_CHAT`, `SET_DOCUMENT_CHAT_HISTORY`, `ADD_TOAST`, `REMOVE_TOAST`
- **Depends on**: `frontend/src/services/api.js`

#### frontend/src/hooks/usePolling.js
- **Purpose**: Polls `/api/status/<id>/` every 5 seconds for each document with `is_processed=false`; dispatches `UPSERT_DOCUMENT` and fires a toast on completion
- **Key exports**: `usePolling`
- **Depends on**: `AppContext.jsx`, `frontend/src/services/api.js`

#### frontend/src/hooks/useDriveAutoSync.js
- **Purpose**: Automatically calls `/api/sync-drive/` once on mount and then every 60 seconds for the lifetime of the app; uses a `syncingRef` guard to prevent overlapping in-flight requests; shows an error toast on failure. Replaces the old manual "Sync Drive" button that previously lived in `AdvancedSearch.jsx`.
- **Key exports**: `useDriveAutoSync`
- **Depends on**: `AppContext.jsx`, `frontend/src/services/api.js`

#### frontend/src/services/api.js
- **Purpose**: Axios API client -- all backend HTTP calls with error normalization; base URL `/api/`
- **Key exports**: `documentApi` (object with `listDocuments`, `uploadDocument`, `getDocument`, `getDocumentStatus`, `deleteDocument`, `askQuestion`, `getChatHistory`, `clearChatHistory`, `search`, `syncDrive`)
- **Depends on**: nothing project-internal

---

### `frontend/src/components/Chat/`

#### frontend/src/components/Chat/ChatArea.jsx
- **Purpose**: Main chat UI -- displays messages for selected document, handles question submission, shows processing state and errors, offers clear-chat action
- **Key components**: `ChatArea`, `WelcomeScreen` (L10), `EmptyMessages` (L24)
- **Depends on**: `AppContext.jsx`, `api.js`, `ChatInput.jsx`, `ChatMessage.jsx`, `TypingIndicator.jsx`, `Badge.jsx`

#### frontend/src/components/Chat/ChatInput.jsx
- **Purpose**: Textarea + send button form; supports Enter-to-submit (Shift+Enter for newline), disables when processing
- **Key components**: `ChatInput`
- **Depends on**: nothing project-internal

#### frontend/src/components/Chat/ChatMessage.jsx
- **Purpose**: Renders a single user or assistant message bubble with optional confidence badge and page source summary
- **Key components**: `ChatMessage`; helper `pageSummary` (L4)
- **Depends on**: `Badge.jsx`

#### frontend/src/components/Chat/TypingIndicator.jsx
- **Purpose**: Animated three-dot typing indicator shown while the LLM response is being generated
- **Key components**: `TypingIndicator`
- **Depends on**: nothing

---

### `frontend/src/components/Sidebar/`

#### frontend/src/components/Sidebar/Sidebar.jsx
- **Purpose**: Left navigation panel -- app logo, upload button, chat/search nav tabs, document list with loading skeleton and error state
- **Key components**: `Sidebar`, `SidebarSkeleton` (L12)
- **Depends on**: `AppContext.jsx`, `api.js`, `DocumentItem.jsx`, `UploadButton.jsx`

#### frontend/src/components/Sidebar/DocumentItem.jsx
- **Purpose**: Single document card in the sidebar list -- shows name, file type badge, processing/ready/error status, and delete button
- **Key components**: `DocumentItem`
- **Depends on**: `Badge.jsx`, `Spinner.jsx`

#### frontend/src/components/Sidebar/UploadButton.jsx
- **Purpose**: Styled "Upload Document" button that triggers the upload modal; presentational only
- **Key components**: `UploadButton`
- **Depends on**: nothing

---

### `frontend/src/components/Upload/`

#### frontend/src/components/Upload/UploadModal.jsx
- **Purpose**: Modal dialog for file upload -- file selection, 50MB validation, upload progress bar, error display, dispatches new document to global state on success
- **Key components**: `UploadModal`
- **Depends on**: `AppContext.jsx`, `api.js`, `FileDropzone.jsx`, `Spinner.jsx`

#### frontend/src/components/Upload/FileDropzone.jsx
- **Purpose**: Drag-and-drop file input zone -- accepts PDF, TXT, DOC, DOCX; shows selected file name and size with remove option
- **Key components**: `FileDropzone`
- **Depends on**: nothing

---

### `frontend/src/components/Search/`

#### frontend/src/components/Search/AdvancedSearch.jsx
- **Purpose**: Full advanced search page -- search bar, type/status/date filters, paginated results grid, side panel for file details, "Open in Chat" action. The manual Drive sync button was removed; syncing is now fully automatic via `useDriveAutoSync` mounted at the `App` root.
- **Key components**: `AdvancedSearch`
- **Depends on**: `AppContext.jsx`, `api.js`, `FileDetailsPanel.jsx`, `SearchResultCard.jsx`, `searchUtils.js`

#### frontend/src/components/Search/SearchResultCard.jsx
- **Purpose**: Single search result card -- displays file name, MIME type label, relevance score badge, matched snippet, and relative modified date
- **Key components**: `SearchResultCard`
- **Depends on**: `searchUtils.js`

#### frontend/src/components/Search/FileDetailsPanel.jsx
- **Purpose**: Side panel showing selected search result details -- Drive file ID, MIME type, sync status, chunk count, matched snippet, copy-to-clipboard, and "Open in Chat" button
- **Key components**: `FileDetailsPanel`, `DetailRow` (L5)
- **Depends on**: `searchUtils.js`

#### frontend/src/components/Search/Searchhistory.js
- **Purpose**: LocalStorage search history persistence helper -- manages recent search query history array
- **Key exports**: `getSearchHistory` (L5), `saveSearchHistory` (L15), `removeSearchHistory` (L27), `clearSearchHistory` (L38)
- **Depends on**: nothing project-internal

#### frontend/src/components/Search/searchUtils.js
- **Purpose**: Pure utility functions and style constants for the search UI
- **Key exports**: `timeAgo` (L1), `mimeToLabel` (L24), `syncStatusStyles` (L34), `relevanceTone` (L41)
- **Depends on**: nothing

---

### `frontend/src/components/Common/`

#### frontend/src/components/Common/Badge.jsx
- **Purpose**: Reusable pill/badge component with tone variants (neutral, low, medium, high) used for file types, confidence levels, and status indicators
- **Key exports**: `Badge` (default), `getConfidenceLevel` (L8)
- **Depends on**: nothing

#### frontend/src/components/Common/Toast.jsx
- **Purpose**: Global toast notification container -- renders the `toasts` array from `AppContext` with success/error/info styles and auto-dismiss
- **Key components**: `Toast`
- **Depends on**: `AppContext.jsx`

#### frontend/src/components/Common/Spinner.jsx
- **Purpose**: Small inline loading spinner with configurable size via className prop
- **Key components**: `Spinner`
- **Depends on**: nothing
