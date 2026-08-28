# DocuMind

DocuMind is a document-based AI assistant that lets you upload documents, search through them, and ask questions about their content.

The main idea behind the project is simple: instead of sending an entire document to an LLM, DocuMind first finds the relevant parts of the document and then uses those parts to generate the answer.

I built this project to work with RAG, vector search, document processing, background tasks, authentication, and a real frontend/backend setup rather than just a simple chatbot demo.

## What it can do

* Upload documents and process them in the background
* Chat with a document using natural language
* Search across uploaded documents
* Find relevant document chunks using semantic search
* Show the source chunks used for an answer
* Keep chat history for documents
* Search documents using the Advanced Search page
* Filter search results by file type, sync status, and date
* View document information and matched text
* Export search results as JSON
* Connect Google Drive and sync documents
* Automatically check Google Drive for changes
* Track document processing status
* Handle user signup and login
* Verify accounts using OTP
* Refresh expired JWT access tokens
* Reset and change passwords

---

## How it works

The basic flow is:

```text
Document
   ↓
Text extraction
   ↓
Chunking
   ↓
Embeddings
   ↓
PostgreSQL + pgvector
   ↓
Similarity search
   ↓
Relevant chunks
   ↓
Groq
   ↓
Answer
```

When a document is uploaded, it is processed in the background using Celery.

The text is split into smaller chunks and an embedding is generated for each chunk using `all-MiniLM-L6-v2`.

The embeddings are stored in PostgreSQL using pgvector.

When a user asks a question, the question is converted into an embedding as well. DocuMind then uses cosine similarity to find the most relevant chunks.

Those chunks are passed to the LLM as context, and the final answer is generated from that context.

---

## RAG

The project currently uses:

* Sentence Transformers for embeddings
* `all-MiniLM-L6-v2` as the embedding model
* PostgreSQL for application data
* pgvector for vector search
* Groq for LLM responses

I decided to keep the embeddings in PostgreSQL instead of using a separate vector database. This keeps the document data, chunks, metadata, and embeddings in one place.

The vector search code is mainly handled in:

```text
apps/rag/utils/vector_store.py
```

It supports both document-specific search and searching across all indexed documents.

---

## Document processing

Documents are processed asynchronously so that uploading a file does not make the API wait for the whole processing operation.

The general process is:

```text
Upload
  ↓
Save document
  ↓
Celery task
  ↓
Extract text
  ↓
Create chunks
  ↓
Generate embeddings
  ↓
Store chunks + embeddings
  ↓
Document ready
```

The application also keeps track of the processing state and errors.

If a document gets stuck during processing, there is a management command for putting it back into the queue:

```bash
python manage.py requeue_stuck_documents
```

---

## Document chat

After a document has been processed, the user can open it and start asking questions.

For example:

```text
What are the main points discussed in this document?
```

The system searches the document first and retrieves the closest chunks before generating the response.

The response can also include information about the chunks that were used, such as the page number and chunk index.

Chat history is saved so that previous questions and answers can be viewed later.

---

## Advanced Search

There is a separate Advanced Search page in the frontend.

It is useful when you have a lot of documents and want to find a particular file or piece of information.

The search page currently supports:

* Semantic search
* Search history
* Document type filtering
* Google Drive sync-status filtering
* Date filtering
* Pagination
* Relevance scores
* Matched snippets
* File details
* Opening a result directly in chat
* Exporting results as JSON

The search results contain information such as:

```text
Document ID
Document name
File type
Relevance score
Matched text
Drive file ID
Drive modified time
Sync status
```

---

## Google Drive

DocuMind can also sync documents from Google Drive.

The Drive integration is used to bring files from Google Drive into the same document processing pipeline.

The sync keeps information such as:

* Drive file ID
* File name
* MIME type
* Drive modified time
* Sync status

The frontend also has automatic Drive synchronization. It performs an initial sync and then checks periodically for changes.

---

## Authentication

The backend has its own authentication system using JWT.

Current authentication features include:

* Signup
* Login
* Email OTP verification
* Resend OTP
* Forgot password
* Password reset
* Change password
* Access tokens
* Refresh tokens
* Logout

The frontend also handles expired access tokens and can request a new access token using the refresh token.

---

## Frontend

The frontend is built with React and Vite.

Main technologies:

* React
* Vite
* Axios
* Tailwind CSS
* Lucide React

The frontend currently contains:

* Login
* Signup
* OTP verification
* Forgot password
* Reset password
* Change password
* Document sidebar
* Document upload
* Document processing status
* Chat interface
* Chat history
* Advanced Search
* Search filters
* Search history
* File details
* Google Drive sync
* Toast notifications
* Loading and error states
* Responsive layouts

The frontend code is inside:

```text
frontend/
```

---

## Backend

The backend is built with Django and Django REST Framework.

Main technologies:

* Python
* Django
* Django REST Framework
* PostgreSQL
* pgvector
* Celery
* Redis
* Sentence Transformers
* Groq

The backend is responsible for authentication, document management, RAG, search, chat history, document processing, and Google Drive synchronization.

---

## Project structure

The project is roughly organized like this:

```text
Rag-Agent/
│
├── apps/
│   ├── auth_manager/
│   ├── rag/
│   └── shared/
│
├── core/
│
├── drive_service/
│
├── frontend/
│
├── docs/
│
├── manage.py
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

Some of the important backend code is under:

```text
apps/auth_manager/
apps/rag/
```

The RAG-related utilities are under:

```text
apps/rag/utils/
```

and the frontend is under:

```text
frontend/src/
```

---

## Running locally

### Backend

Clone the repository:

```bash
git clone https://github.com/hello-arbaaz-khan/Rag-Agent.git
cd Rag-Agent
```

Create a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Create your environment file:

```bash
cp .env.example .env
```

Add your database, Groq, JWT, Google Drive, and other required configuration to `.env`.

Run migrations:

```bash
python manage.py migrate
```

Start Django:

```bash
python manage.py runserver
```

The backend will normally be available at:

```text
http://127.0.0.1:8000
```

---

## Redis and Celery

Redis is used by Celery for background jobs.

Start Redis and then run the Celery worker:

```bash
celery -A core worker --loglevel=info
```

The worker handles the background document-processing tasks.

---

## Frontend

Go to the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The frontend is normally available at:

```text
http://localhost:3000
```

For a production build:

```bash
npm run build
```

---

## Environment variables

Create a `.env` file based on `.env.example`.

The exact variables depend on which parts of the application you want to use, but the main configuration includes:

```env
SECRET_KEY=
DEBUG=

DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=

GROQ_API_KEY=

CELERY_BROKER_URL=
CELERY_RESULT_BACKEND=

GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=
```

Do not commit your real `.env` file or API keys to the repository.

---

## Database

PostgreSQL is used as the main database.

pgvector is required because document embeddings are stored in PostgreSQL.

After creating the database, make sure the vector extension is available:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Then run:

```bash
python manage.py migrate
```

---

## Testing

Run the Django tests with:

```bash
python manage.py test
```

You can also run tests for a specific application, for example:

```bash
python manage.py test apps.auth_manager
```

---

## A few implementation details

### Embeddings

The project uses:

```text
all-MiniLM-L6-v2
```

from Sentence Transformers.

### Vector search

Vector similarity is calculated using pgvector's cosine distance support.

### Background jobs

Celery + Redis are used for asynchronous document processing.

### LLM

Groq is currently used for generating the final responses.

### Database

PostgreSQL stores the application data, document chunks, metadata, and embeddings.

---

## Current status

The main document RAG flow is working, along with document management, authentication, search, Google Drive synchronization, and the React frontend.

There are still areas that can be improved, especially around production deployment, testing, retrieval quality, and more advanced RAG techniques.

Some things I would like to add later include:

* Better retrieval/reranking
* Streaming responses
* More document formats
* OCR for scanned documents
* Better citations
* Multi-document conversations
* More detailed document previews
* Better test coverage
* Production monitoring

---

## Why I built this

I built DocuMind as a practical project to understand how a complete RAG application works.

The goal wasn't only to make a chatbot that calls an LLM. I wanted to work through the other parts as well:

* document ingestion
* text extraction
* chunking
* embeddings
* vector search
* RAG
* background processing
* authentication
* API design
* frontend development
* Google Drive integration
* database design

So the project is still evolving, but the main end-to-end flow is already in place.

---

## Author

**Arbaz Khan**

GitHub:
https://github.com/hello-arbaaz-khan/Rag-Agent
