# DocuMind - RAG-Based Document AI Assistant

DocuMind is a full-stack document-based AI assistant that enables you to upload documents, search through them semantically, and ask intelligent questions about their content using Retrieval-Augmented Generation (RAG).

The core idea is simple but powerful: instead of sending entire documents to an LLM, DocuMind first retrieves the most relevant document chunks and uses those as context to generate accurate, grounded answers. This approach improves accuracy, reduces token usage, and provides transparency through source citations.

---

## Table of Contents

- [Key Features](#key-features)
- [How It Works](#how-it-works)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Running Locally](#running-locally)
- [Running with Docker](#running-with-docker)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [Why I Built This](#why-i-built-this)
- [Author](#author)

---

## Key Features

### Document Management
- Upload and process multiple document formats (PDF, DOCX, DOC, TXT)
- Automatic document processing in the background (asynchronous)
- Track document processing status and errors
- View document information and chunk statistics
- Support for large files with progress tracking

### Smart Search and Retrieval
- Semantic search using embeddings (not keyword-based)
- Search across all indexed documents
- Advanced filtering by file type, sync status, and date range
- Relevance scoring with matched text snippets
- Export search results as JSON
- Search history persistence

### Intelligent Chat
- Ask natural language questions about documents
- Get context-aware answers with source citations
- View which document chunks were used to generate answers
- Maintain full chat history per document
- Support for multi-turn conversations

### Google Drive Integration
- Connect Google Drive accounts securely
- Auto-sync documents from Google Drive
- Automatic periodic sync checking for changes
- Track sync status (pending, processing, indexed, failed)
- Sync error reporting

### Authentication and Security
- User signup and login
- Email OTP verification for account security
- Secure password reset and change functionality
- JWT-based authentication with refresh tokens
- Encrypted Google Drive tokens
- User-scoped document access

---

## How It Works

### Core RAG Pipeline

The system follows a well-defined retrieval-augmented generation pipeline that ensures accurate, context-aware responses:

```
Document Upload
    |
    v
Text Extraction (PDF, DOCX, DOC, TXT)
    |
    v
Text Chunking (overlapping chunks)
    |
    v
Embedding Generation (all-MiniLM-L6-v2)
    |
    v
PostgreSQL + pgvector Storage
    |
    v
User Query
    |
    v
Query Embedding
    |
    v
Cosine Similarity Search
    |
    v
Retrieve Top-K Relevant Chunks
    |
    v
Pass to Groq LLM with Context
    |
    v
Generate Answer with Citations
```

### Processing Flow

When a document is uploaded to the system:

1. Upload: File is saved to the system
2. Queue: A Celery task is created for asynchronous processing
3. Extract: Text is extracted using PyMuPDF, python-docx, or plain text reading
4. Chunk: Text is split into overlapping chunks to preserve context
5. Embed: Each chunk is converted to a 384-dimensional vector using Sentence Transformers
6. Store: Chunks, metadata, and embeddings are stored in PostgreSQL with pgvector
7. Ready: Document is marked as processed and ready for queries

### Query Resolution

When a user asks a question about a document:

1. Embed Query: Question is converted to a vector
2. Search: pgvector finds most similar chunks using cosine distance
3. Retrieve: Top-K chunks are fetched with metadata (page, document, relevance)
4. Context: Chunks are formatted as context for the LLM
5. Generate: Groq LLM generates answer based on context
6. Return: Answer is returned with source references

---

## Tech Stack

### Backend
- Language: Python 3.12
- Framework: Django 6.0.6 with Django REST Framework 3.17.1
- Database: PostgreSQL 16 with pgvector extension
- Vector Search: pgvector with cosine similarity
- Background Jobs: Celery 5.4.0 with Redis 7 message broker
- LLM: Groq API for fast inference
- Embeddings: Sentence Transformers (all-MiniLM-L6-v2)
- Document Processing: PyMuPDF, python-docx, plain text
- Authentication: JWT with djangorestframework-simplejwt
- API: RESTful API with CORS support

### Frontend
- Language: JavaScript (ES6+)
- Framework: React 18.3.1
- Build Tool: Vite 6.0.5
- Styling: Tailwind CSS 3.4.17
- HTTP Client: Axios 1.7.9
- Icons: Lucide React
- Package Manager: npm

### Google Drive Integration
- Service: FastAPI microservice (drive_service)
- Framework: FastAPI with Uvicorn
- Google Libraries: google-auth, google-auth-oauthlib, google-api-python-client
- Security: JWT tokens, encrypted credentials

### Infrastructure
- Containerization: Docker
- Orchestration: Docker Compose
- Web Server: Gunicorn/uWSGI for production
- Reverse Proxy: Nginx for production

---

## Architecture

### System Components

The system is built as a set of interconnected services that work together to provide a complete document AI solution:

```
Frontend Layer (React)
    |
    |-- Port 3000 (Vite dev server)
    |
    v
API Gateway (Django REST)
    |
    |-- Port 8000
    |
    +-- Authentication Module
    |       User signup, login, JWT tokens, OTP verification
    |
    +-- Document Management
    |       Upload, storage, processing status tracking
    |
    +-- RAG Engine
    |       Vector search, chunk retrieval, similarity scoring
    |
    +-- Chat Management
    |       Conversation storage, response generation, citations
    |
    v
Data Layer
    |
    +-- PostgreSQL (Port 5432)
    |   Documents, chunks, embeddings, users, chat history
    |
    +-- Redis (Port 6379)
    |   Message queue, cache, session storage
    |
    v
Processing Layer
    |
    +-- Celery Workers
    |   Document processing, embedding generation
    |
    +-- Drive Service (FastAPI, Port 8001)
    |   Google OAuth, file syncing, token management

External Services
    |
    +-- Groq LLM API
    |   Language model inference
    |
    +-- Google Drive API
    |   File access, metadata, sync
```

### Backend Modules

The backend is organized into logical modules, each handling specific responsibilities:

#### apps/auth_manager - Authentication and User Management
Handles all user-related functionality including account creation, verification, and security:
- User signup with email verification
- Login with JWT token generation
- OTP-based email verification for account security
- Password reset and change flows
- JWT access token and refresh token handling
- User profile management and password validation

#### apps/rag - Document Processing and RAG
Core module responsible for document management and intelligent querying:
- models.py: Data models for documents, chunks, chat history, and Drive integration
- views.py: REST API endpoints for documents, chat, and search operations
- serializers.py: Request and response data serialization
- tasks.py: Celery background tasks for document processing and embedding generation
- utils/:
  - vector_store.py: Similarity search and chunk retrieval logic
  - rag_engine.py: Context formatting and LLM integration
  - pdf_processor.py: PDF text extraction
  - query_intent.py: Query analysis and potential rewriting

#### core - Django Project Configuration
Central configuration for the Django project:
- settings.py: Database, cache, authentication, and CORS configuration
- urls.py: URL routing to all applications
- celery.py: Celery configuration for background tasks
- wsgi.py and asgi.py: Application server entry points

#### drive_service - Google Drive Microservice
Separate FastAPI service handling Google Drive operations:
- OAuth 2.0 token management
- File sync scheduling and execution
- Encrypted credential storage
- Independent from main Django application for scalability

---

## Project Structure

```
Rag-Agent/
|
|-- apps/
|   |-- auth_manager/
|   |   |-- models.py              User model with OTP fields
|   |   |-- views.py               Authentication endpoints
|   |   |-- serializers.py         Request/response serialization
|   |   |-- utils.py               OTP and token handling utilities
|   |   |-- permission.py          Custom permission classes
|   |   |-- urls.py                URL routing
|   |   |-- tests.py               Test suite for authentication
|   |   `-- migrations/
|   |
|   |-- rag/
|   |   |-- models.py              Document, Chunk, ChatHistory models
|   |   |-- views.py               Document and chat API endpoints
|   |   |-- serializers.py         Data serialization
|   |   |-- tasks.py               Celery background tasks
|   |   |-- urls.py                URL routing
|   |   |-- tests.py               Test suite
|   |   |-- utils/
|   |   |   |-- vector_store.py    Similarity search logic
|   |   |   |-- rag_engine.py      LLM integration
|   |   |   |-- pdf_processor.py   PDF text extraction
|   |   |   `-- query_intent.py    Query analysis
|   |   |-- services/              Business logic services
|   |   |-- management/            Django management commands
|   |   `-- migrations/
|   |
|   `-- shared/
|
|-- core/
|   |-- settings.py                Django configuration
|   |-- urls.py                    Main URL routing
|   |-- wsgi.py                    WSGI entry point
|   |-- asgi.py                    ASGI entry point
|   `-- celery.py                  Celery configuration
|
|-- drive_service/
|   |-- main.py                    FastAPI application
|   |-- app/                       FastAPI routes and services
|   |-- Dockerfile
|   |-- requirements.txt
|   `-- .env.example
|
|-- frontend/
|   |-- src/
|   |   |-- components/            React components
|   |   |-- pages/                 Page components
|   |   |-- services/              API client layer
|   |   |-- store/                 State management
|   |   |-- App.jsx
|   |   `-- main.jsx
|   |-- public/
|   |-- package.json
|   |-- vite.config.js
|   |-- tailwind.config.js
|   |-- Dockerfile
|   `-- .dockerignore
|
|-- db-init/
|   `-- 01-pgvector.sql            pgvector extension setup
|
|-- db-image/
|   `-- Dockerfile                 PostgreSQL 16 with pgvector
|
|-- manage.py                      Django CLI
|-- requirements.txt               Python dependencies
|-- docker-compose.yml             Local development stack
|-- Dockerfile                     Django container
|-- pytest.ini                     Pytest configuration
|-- .env.example                   Environment template
|-- .gitignore
`-- README.md
```

---

## Prerequisites

### Required Software
- Python 3.11 or higher (3.12 recommended)
- Node.js 16.x or higher (18+ recommended)
- Docker and Docker Compose for containerized deployment
- PostgreSQL 12 or higher (if running locally without Docker)
- Redis 6 or higher (if running locally without Docker)

### Required API Keys and Credentials
- Groq API Key: Obtain from https://console.groq.com
- Google OAuth Credentials: Set up in Google Cloud Console for Drive integration

### System Requirements
- RAM: Minimum 4GB (8GB recommended for comfortable development)
- Disk Space: 5GB or more for models, database, and document storage
- Internet: Required for LLM API calls, Google Drive API, and model downloads

---

## Quick Start

### Option 1: Docker Compose (Recommended for Quick Setup)

Clone and configure the repository:

```bash
git clone https://github.com/hello-arbaaz-khan/Rag-Agent.git
cd Rag-Agent
cp .env.example .env
cp drive_service/.env.example drive_service/.env
```

Edit the `.env` file with your API keys and configuration:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
GROQ_API_KEY=your-groq-api-key
DB_NAME=ragdb
DB_USER=raguser
DB_PASSWORD=ragpassword
```

Start all services using Docker Compose:

```bash
docker-compose up -d
```

Access the application at these URLs:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- PostgreSQL Database: localhost:5433

### Option 2: Local Development Setup

Clone the repository:

```bash
git clone https://github.com/hello-arbaaz-khan/Rag-Agent.git
cd Rag-Agent
```

Create and activate Python virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Set up environment configuration:

```bash
cp .env.example .env
# Edit .env with your settings
```

Initialize the database:

```bash
python manage.py migrate
```

Start the Django development server:

```bash
python manage.py runserver
```

In a separate terminal, start the Celery worker for background tasks:

```bash
celery -A core worker -l info
```

In another terminal, start the React frontend:

```bash
cd frontend
npm install
npm run dev
```

Access the application at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

---

## Running Locally

### Backend Setup

#### 1. PostgreSQL Database Configuration

Install PostgreSQL and create a database with the necessary user:

```bash
psql -U postgres

CREATE DATABASE ragdb;
CREATE USER raguser WITH PASSWORD 'ragpassword';
ALTER ROLE raguser SET client_encoding TO 'utf8';
ALTER ROLE raguser SET default_transaction_isolation TO 'read committed';
ALTER ROLE raguser SET default_transaction_deferrable TO on;
ALTER ROLE raguser SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE ragdb TO raguser;
\q
```

Enable the pgvector extension for vector operations:

```bash
psql -U raguser -d ragdb

CREATE EXTENSION IF NOT EXISTS vector;
\q
```

#### 2. Redis Installation and Configuration

Install and start Redis for the message broker:

```bash
# macOS using Homebrew
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis-server

# Using Docker
docker run -d -p 6379:6379 redis:7-alpine
```

#### 3. Python Dependencies Installation

Create virtual environment and install requirements:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 4. Environment Configuration

Create environment file from template:

```bash
cp .env.example .env
```

Edit `.env` with your specific settings:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=mixtral-8x7b-32768

# Database Configuration
DB_NAME=ragdb
DB_USER=raguser
DB_PASSWORD=ragpassword
DB_HOST=localhost
DB_PORT=5432

# Redis and Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Email Configuration (console backend for local testing)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Drive Service URL
DRIVE_SERVICE_BASE_URL=http://localhost:8001
```

#### 5. Database Migrations

Run Django migrations to set up database schema:

```bash
python manage.py migrate
```

#### 6. Create Superuser (Optional)

Create an admin user for Django admin panel:

```bash
python manage.py createsuperuser
```

#### 7. Start Django Development Server

Start the Django development server:

```bash
python manage.py runserver
```

Backend will be available at http://127.0.0.1:8000

### Celery Worker Setup

Start Celery worker in a separate terminal (with virtual environment activated):

```bash
celery -A core worker -l info
```

This worker processes background tasks including document embedding, text extraction, and Google Drive synchronization.

### Frontend Setup

Install npm dependencies and start development server:

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at http://localhost:3000

Build production bundle:

```bash
npm run build
```

---

## Running with Docker

### Starting All Services

Start all services defined in docker-compose.yml:

```bash
docker-compose up -d
```

Services will start in the following order:
- PostgreSQL database (port 5433)
- Redis cache and queue (port 6380)
- Django backend (port 8000)
- Celery worker for background tasks
- Drive service for Google Drive operations (port 8001)
- React frontend development server (port 3000)

### Viewing Service Logs

View logs from all running services:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f django
docker-compose logs -f celery_worker
docker-compose logs -f frontend
```

### Stopping Services

Stop and remove all running containers:

```bash
docker-compose down
```

### Rebuilding Docker Images

Rebuild images if you've made changes to code or dependencies:

```bash
docker-compose build --no-cache
docker-compose up -d
```

### Database Persistence

PostgreSQL data is stored in a named Docker volume called postgres-data. This volume persists across container restarts and even when containers are removed with `docker-compose down`.

---

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Django Core Settings
SECRET_KEY=your-secret-key-here
DEBUG=True  # Set to False in production

# Database Configuration
DB_NAME=ragdb
DB_USER=raguser
DB_PASSWORD=ragpassword
DB_HOST=db                    # Use 'db' for Docker, 'localhost' for local development
DB_PORT=5432

# Redis and Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0      # Docker configuration
CELERY_RESULT_BACKEND=redis://redis:6379/0  # Docker configuration
# For local development, use:
# CELERY_BROKER_URL=redis://localhost:6379/0
# CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Groq LLM API Configuration
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=mixtral-8x7b-32768  # Alternative: other available Groq models

# Google Drive Integration
DRIVE_SERVICE_BASE_URL=http://drive_service:8001  # Docker configuration
# For local development, use:
# DRIVE_SERVICE_BASE_URL=http://localhost:8001

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend  # Development/Testing
# For production, configure SMTP:
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_HOST_USER=your-email@gmail.com
# EMAIL_HOST_PASSWORD=your-app-password
# DEFAULT_FROM_EMAIL=your-email@gmail.com

# OTP Settings
OTP_EXPIRY_SECONDS=120
```

Create `drive_service/.env` for Google Drive integration:

```env
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_TOKEN_FILE=token.json
DJANGO_BASE_URL=http://django:8000  # Docker configuration
# For local development, use:
# DJANGO_BASE_URL=http://localhost:8000
GOOGLE_API_TIMEOUT_SECONDS=60
GOOGLE_API_PREFER_IPV4=True
```

---

## Database Setup

### PostgreSQL Installation

Install PostgreSQL on your system:

macOS with Homebrew:
```bash
brew install postgresql@16
brew services start postgresql@16
```

Ubuntu/Debian:
```bash
sudo apt-get install postgresql postgresql-contrib postgresql-16-pgvector
```

Windows:
Download installer from https://www.postgresql.org/download/windows/

### Creating Database and User

Connect to PostgreSQL and set up database and user:

```bash
psql -U postgres

CREATE DATABASE ragdb;
CREATE USER raguser WITH PASSWORD 'ragpassword';
ALTER ROLE raguser SET client_encoding TO 'utf8';
ALTER ROLE raguser SET default_transaction_isolation TO 'read committed';
ALTER ROLE raguser SET default_transaction_deferrable TO on;
ALTER ROLE raguser SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE ragdb TO raguser;
\q
```

### Enabling pgvector Extension

Enable pgvector for vector storage and operations:

```bash
psql -U raguser -d ragdb

CREATE EXTENSION IF NOT EXISTS vector;
\q
```

### Running Migrations

Apply all database migrations:

```bash
python manage.py migrate
```

---

## API Endpoints

### Authentication Endpoints
- `POST /api/auth/signup/` - Register new user account
- `POST /api/auth/login/` - Authenticate user and receive access and refresh tokens
- `POST /api/auth/verify-otp/` - Verify email OTP code
- `POST /api/auth/resend-otp/` - Request new OTP code
- `POST /api/auth/forgot-password/` - Initiate password reset process
- `POST /api/auth/reset-password/` - Complete password reset with token
- `POST /api/auth/change-password/` - Change password for authenticated user
- `POST /api/auth/refresh/` - Refresh expired access token using refresh token

### Document Management Endpoints
- `GET /api/documents/` - List all user's documents
- `POST /api/documents/` - Upload new document
- `GET /api/documents/{id}/` - Retrieve specific document details
- `DELETE /api/documents/{id}/` - Delete document
- `GET /api/documents/{id}/status/` - Get document processing status

### Chat and Conversation Endpoints
- `POST /api/documents/{id}/chat/` - Send message and get AI response
- `GET /api/documents/{id}/chat-history/` - Retrieve conversation history
- `DELETE /api/documents/{id}/chat/{chat_id}/` - Remove specific message

### Search Endpoints
- `GET /api/search/` - Perform semantic search across documents
- `GET /api/search/history/` - Retrieve user's search history

### Google Drive Integration Endpoints
- `POST /api/drive/connect/` - Connect Google Drive account
- `GET /api/drive/status/` - Check synchronization status
- `POST /api/drive/sync/` - Manually trigger synchronization
- `GET /api/drive/documents/` - List documents synced from Google Drive

---

## Testing

### Running Complete Test Suite

Execute all tests in the project:

```bash
python manage.py test
```

### Running Tests for Specific Application

Run tests for individual Django apps:

```bash
# Authentication application tests
python manage.py test apps.auth_manager

# RAG application tests
python manage.py test apps.rag
```

### Using Pytest Framework

Run tests with pytest if installed:

```bash
pytest
```

### Running Tests with Coverage Report

Generate test coverage metrics:

```bash
pip install coverage
coverage run -m pytest
coverage report
coverage html  # Generate HTML report in htmlcov/
```

---

## Troubleshooting

### Database Connection Issues

Problem: "psycopg2 connection refused" error when starting Django

Solution:
- Verify PostgreSQL is running: `psql -U postgres -c "SELECT 1;"`
- Check database credentials in `.env` file
- Verify DB_HOST, DB_PORT, and DB_NAME are correct
- Confirm database exists: `psql -l`
- On Docker, ensure `db` service has started and passed health checks

### Vector Database Extension Missing

Problem: "pgvector extension not found" error during migrations

Solution:
```bash
psql -U raguser -d ragdb -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Redis Connection Failed

Problem: "Redis connection refused" or Celery not processing tasks

Solution:
- Verify Redis is running: `redis-cli ping`
- Check CELERY_BROKER_URL in `.env` file
- Start Redis if not running: `redis-server` or use Docker
- For Docker issues, verify redis service status: `docker-compose ps redis`

### Celery Tasks Not Processing

Problem: Background document processing tasks not running

Solution:
- Confirm Celery worker is running: `celery -A core worker -l info`
- Test Redis connection: `redis-cli ping`
- Monitor active tasks: `celery -A core events`
- Check Celery logs for error messages
- Restart Celery worker if needed

### Document Processing Stuck

Problem: Document remains in processing state indefinitely

Solution:
- Requeue stuck documents:
  ```bash
  python manage.py requeue_stuck_documents
  ```
- Check Celery logs for errors: `docker-compose logs celery_worker`
- Verify sufficient disk space available
- Ensure Celery worker has access to temporary files
- Restart Celery worker

### Groq API Rate Limit

Problem: Responses with "Rate limit exceeded" from Groq API

Solution:
- Implement request throttling in your application
- Upgrade Groq account tier for higher limits
- Add retry logic with exponential backoff
- Monitor API usage in Groq dashboard

### Google Drive Synchronization Failures

Problem: Drive sync fails or documents not syncing

Solution:
- Verify Google credentials file is valid and accessible
- Check GOOGLE_CREDENTIALS_FILE path in drive_service/.env
- Re-authenticate Google account: delete existing connection and reconnect
- Check drive_service logs: `docker-compose logs drive_service`
- Verify DJANGO_BASE_URL is correct in drive_service/.env
- Check Google API quota limits in Google Cloud Console

### Frontend Cannot Reach Backend

Problem: Network errors or CORS failures when accessing API

Solution:
- Verify CORS_ALLOWED_ORIGINS in core/settings.py includes frontend URL
- Confirm backend is running on correct port
- Check browser console for specific CORS error messages
- Verify API base URL is correct in frontend configuration
- Test direct backend URL accessibility: `curl http://localhost:8000/api/`

---

## Roadmap

### High Priority Improvements
- Implement better retrieval and reranking algorithms for improved accuracy
- Add streaming response support using Server-Sent Events
- Support additional document formats (XLSX, PPTX, HTML)
- Implement OCR for processing scanned documents
- Enable multi-document conversations within single chat
- Improve citation quality and attribution tracking

### Medium Priority Features
- Upgrade to more powerful embedding models
- Implement query refinement and clarification
- Add document versioning and change tracking
- Support user roles and team collaboration features
- Implement advanced analytics and usage tracking
- Enhance full-text search capabilities

### Production Readiness
- Achieve comprehensive test coverage across all modules
- Set up production monitoring with Sentry and DataDog
- Implement rate limiting and usage quotas
- Generate API documentation with Swagger and OpenAPI
- Perform load testing and performance optimization
- Develop deployment guides for AWS, GCP, and Azure
- Conduct security audit and penetration testing
- Implement backup and disaster recovery procedures

---

## Why I Built This

I created DocuMind as a comprehensive learning project to understand how a complete, production-grade RAG application works from start to finish.

My objective was not simply to create another chatbot that calls an LLM. Instead, I wanted to work through all the non-trivial parts that make a real system work:

### Learning Objectives

- Document Ingestion: Handling multiple file formats, text extraction, and metadata preservation
- Text Processing: Developing chunking strategies, managing overlap, and preserving context
- Embeddings: Generating and storing vector representations at scale
- Vector Search: Implementing similarity matching, ranking, and retrieval optimization
- RAG Architecture: Combining retrieval and generation for accurate responses
- Asynchronous Processing: Managing background jobs with Celery and task scheduling
- Authentication: Implementing secure user management, OTP verification, and JWT tokens
- API Design: Building RESTful APIs with proper serialization and error handling
- Frontend Development: Creating responsive React interfaces with real-time updates
- Google Drive Integration: Implementing OAuth 2.0 and file synchronization
- Database Design: Managing both relational and vector data together
- DevOps: Containerizing applications with Docker and orchestrating with Docker Compose
- Testing: Writing unit tests, integration tests, and tracking coverage

This project demonstrates how these components integrate into a real application rather than treating them as isolated tutorials.

---

## Author

Arbaz Khan

GitHub: https://github.com/hello-arbaaz-khan

Repository: https://github.com/hello-arbaaz-khan/Rag-Agent

---

## Contributing

Contributions are welcome and appreciated. To contribute:

1. Fork the repository
2. Create a feature branch (git checkout -b feature/AmazingFeature)
3. Commit your changes (git commit -m 'Add AmazingFeature')
4. Push to the branch (git push origin feature/AmazingFeature)
5. Open a Pull Request with a clear description of your changes

---

## Support

If you encounter issues or have questions:

1. Check the Troubleshooting section above
2. Search existing GitHub Issues for similar problems
3. Create a new issue with detailed information about the problem, steps to reproduce, and your environment
