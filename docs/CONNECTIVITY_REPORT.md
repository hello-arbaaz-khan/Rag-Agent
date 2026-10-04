# Connectivity Report

Checked branch: `develop`
Current checked-out branch: `feature/apis-implement`

## Short Result

The current working branch is ready for initial Postman API testing after migrations and environment variables are set.

Core wiring exists between FastAPI, Django models, RagCore, PostgreSQL/pgvector, Redis, and Celery.

## What Is Connected

- Docker Compose defines `django`, `drive_service` FastAPI, `celery_worker`, `db`, `redis`, and `frontend`.
- Django settings point Celery to Redis through `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND`.
- Celery app is configured in `core/celery.py` and autodiscovers tasks.
- `apps.documents.tasks.process_document_task` calls `Workflow.documents.DocumentProcessingWorkflow`.
- Document workflow calls RagCore ingestion, chunking, embeddings, and chunk persistence.
- FastAPI chat endpoint calls `Workflow.chat.ChatQueryWorkflow`.
- Chat workflow calls the RagCore Agent for retrieval, reranking, context, and generation.
- RagCore retrieval uses Django ORM + pgvector through `DjangoPgVectorRepository`.

## Fixes Applied

- FastAPI document upload now uses `user_id` consistently for Django foreign keys.
- Upload now queues `process_document_task` through Celery and returns `processing_task_id`.
- Search endpoint is connected to Django metadata filters and RagCore vector search for content queries.
- Docker Compose passes DB settings to Django, Celery, and FastAPI.
- FastAPI has a `/` health endpoint and Docker healthcheck validates the response.
- `python-multipart` is declared for local and Docker upload support.

## Quick Verification

- `python manage.py check` passed.
- `python -m compileall core apps Workflow RagCore drive_service` passed.

## Remaining Requirements

- Run migrations before testing.
- Ensure `.env` has valid DB values, `SECRET_KEY`, and `GROQ_API_KEY`.
- Run `db`, `redis`, `django`, `celery_worker`, and `drive_service`.

## Final Status

Ready for API testing, with external dependencies required for full RAG answers.
