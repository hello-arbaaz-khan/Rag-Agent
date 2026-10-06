# DocuMind — RAG-Based Document AI Assistant

DocuMind (Rag-Agent) is a retrieval-augmented generation (RAG) document AI assistant. It lets users upload documents (PDF, DOCX, DOC, TXT), extracts and chunks text, generates embeddings, stores embeddings in PostgreSQL + pgvector, and answers document-focused questions using an LLM (Groq). The project provides a Django REST backend, a React frontend (Vite + Tailwind), and a FastAPI microservice for Google Drive sync. Background processing uses Celery with Redis.

Current status
- Development stage: Active development / alpha.
- Core features implemented: document upload and processing, chunking, embedding generation (Sentence Transformers), pgvector storage, semantic search, chat endpoints with citations, Google Drive microservice, frontend UI.
- Not yet production hardened: CI, full test coverage, API docs, monitoring, secrets management, and complete deployment guides are pending.

Table of contents
- Key features
- How it works
- Tech stack
- Architecture & project layout
- Local and Docker setup
- Environment files (cleaned examples)
- Database setup and pgvector
- API examples (upload, chat, search)
- Testing
- Troubleshooting
- Production checklist
- Missing / recommended files
- Contributing & license
- Author

---

Key features
- Upload and process PDF, DOCX, DOC, TXT files
- Asynchronous processing with Celery + Redis
- Text extraction, overlapping chunking, and metadata preservation
- Embedding generation with Sentence Transformers (all-MiniLM-L6-v2)
- Vector storage and similarity search using PostgreSQL + pgvector
- Semantic search across documents with relevance scoring and snippets
- Context-aware chat with source citations (LLM: Groq)
- Google Drive integration via a separate FastAPI microservice
- JWT authentication with refresh tokens and optional OTP verification

How it works (high level)
1. User uploads a document.
2. Celery task extracts text (PyMuPDF / python-docx / plain text).
3. Text is chunked into overlapping segments.
4. Embeddings are generated per chunk using Sentence Transformers.
5. Chunks, metadata, and vectors are stored in PostgreSQL with pgvector.
6. User query is embedded and a cosine-similarity search retrieves top-K chunks.
7. Selected chunks are passed as context to the Groq LLM to generate an answer with citations.

Tech stack
- Backend: Python 3.12, Django 6, Django REST Framework
- Vector search: PostgreSQL 16 + pgvector
- Background jobs: Celery + Redis
- LLM: Groq API
- Embeddings: Sentence Transformers (all-MiniLM-L6-v2)
- Frontend: React (Vite), Tailwind CSS
- Drive sync service: FastAPI + Uvicorn
- Containers: Docker, Docker Compose

Repository layout (top-level)
- apps/
  - auth_manager/ (authentication, OTP)
  - rag/ (models, views, tasks, utils)
- core/ (Django project settings, celery)
- drive_service/ (FastAPI microservice for Google Drive)
- frontend/ (React app)
- db-init/ (pgvector setup)
- db-image/ (Postgres image with pgvector)
- docker-compose.yml
- requirements.txt
- Dockerfile
- .env.example
- drive_service/.env.example
- README.md

## Local and Docker setup

Choose one complete setup; do not point a local Django/Celery process at
container-only service names or mix a local Redis/PostgreSQL with Docker ones.
The setup guide has separate instructions and environment files for each mode:
[docs/QUICKSTART.md](docs/QUICKSTART.md).

For fully local services, `.env.example` and `drive_service/.env.example` use
PostgreSQL at `127.0.0.1:5432` and Redis at `127.0.0.1:6379`.
Set `FRONTEND_BASE_URL=http://localhost:3000` so Google Drive OAuth redirects
back to the frontend's `/drive/callback` page.

For a fully Docker setup, copy `.env.docker.example` to `.env.docker` and
`drive_service/.env.docker.example` to `drive_service/.env.docker`; Compose
containers connect to `db:5432` and `redis:6379` on the Compose network. The
ports published on the host are PostgreSQL `5433` and Redis `6380`.

Database setup and pgvector
1. Create database and user (example with psql):
   psql -U postgres
   CREATE DATABASE ragdb;
   CREATE USER raguser WITH PASSWORD 'ragpassword';
   GRANT ALL PRIVILEGES ON DATABASE ragdb TO raguser;
   \q

2. Enable pgvector (must be enabled before migrations that depend on the extension):
   psql -U raguser -d ragdb -c "CREATE EXTENSION IF NOT EXISTS vector;"

3. Run Django migrations:
   python manage.py migrate

API examples
- Upload document (multipart/form-data):
  curl -X POST "http://localhost:8000/api/documents/" \
    -H "Authorization: Bearer <access_token>" \
    -F "file=@/path/to/file.pdf"

- Chat with document (get LLM response with citations):
  curl -X POST "http://localhost:8000/api/documents/{id}/chat/" \
    -H "Authorization: Bearer <access_token>" \
    -H "Content-Type: application/json" \
    -d '{"message":"Summarize the key points from the uploaded document."}'

  Sample response:
  {
    "answer": "The main points are ...",
    "sources": [
      {"document_id": 12, "page": 3, "chunk_id": 97, "text_snippet": "..." }
    ],
    "usage": { "model": "mixtral-8x7b-32768", "tokens": 123 }
  }

- Semantic search:
  GET /api/search/?q=your+query

Testing
- Run Django tests:
  python manage.py test

- Run a specific app:
  python manage.py test apps.rag

- Pytest (if configured):
  pytest

Troubleshooting (common issues)
- psycopg2 connection refused: verify DB service is running, check DB_HOST/DB_PORT and credentials.
- pgvector extension missing: run CREATE EXTENSION as shown above.
- Redis connection refused: verify Redis is running and CELERY_BROKER_URL is correct.
- Celery tasks not processing: ensure a Celery worker is running and connected to the Redis broker.
- Groq rate limits: implement retries with backoff; consider upgrading plan.

Production checklist (short)
- DEBUG=False and set ALLOWED_HOSTS
- Use a secrets manager for API keys and credentials
- Configure HTTPS and a reverse proxy (nginx)
- Run Gunicorn (or similar) behind nginx
- Add monitoring (Sentry/Prometheus) and structured logs
- Enable backups for PostgreSQL and retention for data volumes
- Add rate limiting and throttling for API endpoints
- Ensure pgvector extension exists on production DB

Missing / recommended files to add
- LICENSE (no license file included — choose MIT or other)
- CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md
- CHANGELOG.md or release notes
- GitHub Actions workflows for tests and linting
- API reference or OpenAPI/Swagger (drf-spectacular or drf-yasg suggested)
- Readme: short note about expected database port mapping (confirm docker-compose.yml)

Small improvements to consider
- Add a Makefile or helper scripts for common tasks (migrate, requeue, run tests)
- Add a wait-for-db or healthcheck script for container startup ordering
- Provide example curl commands for upload/chat in README (done above)
- Add a management command or compose entry to requeue stuck documents (README references one; provide usage)

Contributing
Contributions are welcome. Suggested workflow:
1. Fork the repository
2. Create a branch: git checkout -b feature/YourFeature
3. Commit changes with clear message
4. Push branch and open a Pull Request describing the change and motivation

Support
- Check Troubleshooting above
- Search existing Issues before opening a new one
- When creating an issue, include: environment, steps to reproduce, logs, expected vs actual behavior

License
- No license file is included in this repository. Add a LICENSE (for example, MIT) to clarify usage and contribution terms.

Author
Arbaz Khan
GitHub: https://github.com/hello-arbaaz-khan

---

If you want, I can:
- Commit this README.md directly to the repository (create a branch & PR) and include the cleaned .env.example and drive_service/.env.example updates.
- Draft a GitHub Actions workflow that runs tests and linters on PRs.
- Produce CONTRIBUTING.md and a minimal LICENSE file (MIT) and open a PR with those files.

Tell me which of these you'd like me to do next.  
