FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY drive_service/requirements.txt /tmp/drive-requirements.txt

RUN pip install --no-cache-dir \
    -r /tmp/drive-requirements.txt

COPY core ./core
COPY apps ./apps
COPY Workflow ./Workflow
COPY RagCore ./RagCore
COPY manage.py .
COPY drive_service/ .

EXPOSE 8001

HEALTHCHECK \
    --interval=30s \
    --timeout=10s \
    --start-period=40s \
    --retries=3 \
    CMD python -c \
    "import requests; requests.get('http://localhost:8001', timeout=5)" \
    || exit 1

CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8001"]