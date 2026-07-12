# DocuMind Drive Service

FastAPI microservice for listing and downloading documents from Google Drive.

## Structure

```
drive_service/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/v1/
│   │   ├── router.py
│   │   └── endpoints/
│   │       ├── health.py
│   │       └── drive.py
│   ├── core/exceptions.py
│   ├── services/drive_client.py
│   └── schemas/drive.py
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

1. Create a virtual environment and install dependencies:

```bash
cd drive_service
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Copy environment file and add Google credentials:

```bash
cp .env.example .env
# Place your service account JSON at credentials.json (or update GOOGLE_CREDENTIALS_FILE)
```

3. Share the target Google Drive folder with the service account email.

## Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

## API Routes

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/drive/files` | List supported Drive files |
| GET | `/api/v1/drive/files/{file_id}` | Get file metadata |
| GET | `/api/v1/drive/files/{file_id}/download` | Download file (base64) |

Interactive docs: `http://localhost:8001/docs`
