# Quick Start Guide

Get DocuMind backend up and running in minutes.

## Prerequisites

Before you begin, ensure you have:

- ✅ Python 3.10 or higher
- ✅ Redis server installed and running
- ✅ pip (Python package manager)
- ✅ Git (for cloning)

### Check Prerequisites

```bash
# Check Python version
python --version  # Should be 3.10+

# Check if Redis is running
redis-cli ping    # Should return: PONG

# If Redis is not running, start it:
redis-server &    # On macOS/Linux
# or
brew services start redis  # On macOS with Homebrew
```

---

## Step 1: Clone and Setup

```bash
# Navigate to workspace
cd /workspace

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

---

## Step 2: Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed Django-6.0.6 djangorestframework-3.17.1 celery-5.4.0 ...
```

---

## Step 3: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

### Required Environment Variables

```bash
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True

# Celery & Redis (usually no change needed)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Groq API Key (Required for Q&A feature)
GROQ_API_KEY=gsk_your_groq_api_key_here

# Optional: Google Drive Integration
# GOOGLE_CLIENT_ID=your_client_id
# GOOGLE_CLIENT_SECRET=your_client_secret
```

### Get Groq API Key

1. Visit [Groq Console](https://console.groq.com/)
2. Sign up or log in
3. Create an API key
4. Copy and paste into `.env`

---

## Step 4: Database Setup

```bash
# Run database migrations
python manage.py migrate
```

**Expected output:**
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, rag, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  ...
```

### Create Superuser (Optional - for Django Admin)

```bash
python manage.py createsuperuser
```

Follow the prompts to set username, email, and password.

---

## Step 5: Start Services

You'll need **multiple terminal windows** to run all services.

### Terminal 1: Redis (if not already running)

```bash
redis-server
```

Or as a background service:
```bash
redis-server --daemonize yes
```

---

### Terminal 2: Celery Worker

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Start Celery worker
celery -A documind worker --loglevel=info
```

**Expected output:**
```
 -------------- celery@hostname v5.4.0 (immunity)
--- ***** ----- 
-- ******* ---- Linux-5.15.0-x86_64-with-glibc2.31 2025-08-11 10:00:00
- *** --- * --- 
- ** ---------- [config]
- ** ---------- .> app:         documind
- ** ---------- .> broker:      redis://localhost:6379/0
- ** ---------- .> loader:      celery.loaders.app.AppLoader
- ** ---------- .> concurrency: 8 (prefork)

[queues]
.> celery           exchange=celery(direct) key=celery

[tasks]
.> rag.tasks.process_document_task

[2025-08-11 10:00:00,000: INFO/MainProcess] Connected to redis://localhost:6379/0
[2025-08-11 10:00:00,000: INFO/MainProcess] celery@hostname ready.
```

---

### Terminal 3: Django Development Server

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Start Django server
python manage.py runserver
```

**Expected output:**
```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
August 11, 2025 - 10:00:00
Django version 6.0.6, using settings 'documind.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-BREAK.
```

---

### Terminal 4: Drive Service (Optional)

Only needed if you're using Google Drive integration.

```bash
cd drive_service
source venv/bin/activate  # or create separate venv
uvicorn main:app --port 8001 --reload
```

---

## Step 6: Verify Installation

### Test API Health

```bash
# List documents (should return empty list)
curl http://localhost:8000/api/list/

# Expected response:
# {"success":true,"data":[]}
```

### Test Document Upload

```bash
# Upload a test document
curl -X POST http://localhost:8000/api/upload/ \
  -F "file=@/path/to/your/test.pdf" \
  -F "name=Test Document" \
  -F "file_type=pdf"
```

**Expected response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Test Document",
    "file_type": "pdf",
    "is_processed": false,
    ...
  }
}
```

### Check Processing Status

```bash
# Check document status
curl http://localhost:8000/api/status/1/
```

**Wait for processing:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "is_processed": true,
    "chunk_count": 25,
    ...
  }
}
```

### Test Q&A

```bash
# Ask a question
curl -X POST http://localhost:8000/api/question/ \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is this document about?",
    "document_id": 1
  }'
```

**Expected response:**
```json
{
  "success": true,
  "data": {
    "question": "What is this document about?",
    "answer": "This document discusses...",
    "source_chunks": [...],
    "confidence_score": 0.85
  }
}
```

---

## Common Issues & Solutions

### Issue 1: Redis Connection Error

**Error:**
```
celery.exceptions.OperatorError: Error connecting to Redis: Connection refused
```

**Solution:**
```bash
# Check if Redis is running
redis-cli ping

# If not running, start Redis
redis-server

# Or on macOS with Homebrew
brew services start redis
```

---

### Issue 2: Database Locked

**Error:**
```
OperationalError: database is locked
```

**Solution:**
- Already configured with 30s timeout
- Avoid running multiple write operations simultaneously
- Consider migrating to PostgreSQL for production

---

### Issue 3: Missing Groq API Key

**Error:**
```
groq.AuthenticationError: No API key provided
```

**Solution:**
1. Get API key from https://console.groq.com/
2. Add to `.env`:
   ```bash
   GROQ_API_KEY=gsk_your_key_here
   ```
3. Restart Django server

---

### Issue 4: File Upload Size Error

**Error:**
```
{"file": ["File size must be less than 50MB"]}
```

**Solution:**
- Ensure file is under 50MB
- To increase limit, modify `rag/serializers.py`:
  ```python
  max_size = 100 * 1024 * 1024  # 100MB
  ```

---

### Issue 5: Celery Worker Not Processing Tasks

**Symptoms:**
- Document stuck in "is_processed: false"
- No activity in Celery logs

**Solution:**
```bash
# Check if Celery is running
ps aux | grep celery

# Restart Celery worker
celery -A documind worker --loglevel=debug

# Check Redis queue
redis-cli
> LLEN celery  # Should show pending tasks
```

---

## Next Steps

### Explore the API

See [API Documentation](./API.md) for complete endpoint reference.

### Django Admin Interface

Access the admin panel at: http://localhost:8000/admin/

Login with superuser credentials created earlier.

### Frontend Integration

Connect your frontend to the API:

```javascript
// Example: Upload document
const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('name', file.name);
  formData.append('file_type', file.name.split('.').pop());
  
  const response = await fetch('http://localhost:8000/api/upload/', {
    method: 'POST',
    body: formData,
  });
  
  return await response.json();
};
```

### Production Deployment

See [Architecture Overview](./ARCHITECTURE.md) for deployment guidelines.

Key considerations:
- Use PostgreSQL instead of SQLite
- Set `DEBUG=False`
- Configure proper secrets management
- Set up multiple Celery workers
- Enable monitoring and logging

---

## Development Tips

### Run Tests

```bash
python manage.py test rag
```

### Code Formatting

```bash
# Install black and flake8
pip install black flake8

# Format code
black .

# Check code style
flake8 .
```

### Watch Files for Changes

Django auto-reloads on code changes during development.

For Celery, use:
```bash
celery -A documind worker --loglevel=info --pool=solo
```

### Debug Mode

Enable detailed error pages:
```bash
# In .env
DEBUG=True
```

⚠️ **Never use DEBUG=True in production!**

---

## Useful Commands Reference

```bash
# Database operations
python manage.py migrate          # Apply migrations
python manage.py makemigrations   # Create new migrations
python manage.py dbshell          # Open database shell

# Django shell
python manage.py shell            # Interactive Python shell

# Celery operations
celery -A documind worker --loglevel=info        # Start worker
celery -A documind flower                        # Start Flower UI
celery -A documind inspect active                # Check active tasks
celery -A documend purge                          # Clear queue (careful!)

# Static files
python manage.py collectstatic   # Collect static files (production)

# Server
python manage.py runserver       # Start dev server
python manage.py runserver 0.0.0.0:8000  # Expose to network
```

---

## Getting Help

- Check [Main README](../README.md) for overview
- Review [API Docs](./API.md) for endpoint details
- Read [Architecture](./ARCHITECTURE.md) for system design
- Inspect logs in Celery and Django terminals
- Search issues in project repository

---

*Last Updated: August 2025*
