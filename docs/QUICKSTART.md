# Quick Start: Fully Local or Fully Docker

The PostgreSQL error

```text
connection to server at "127.0.0.1", port 5433 failed: Connection refused
```

means nothing is listening at that host and port. The app could not reach
PostgreSQL, so this is a service/host/port issue, not a Django migration error.
In this repository, port `5433` is published by Compose for use from the host.
Native PostgreSQL normally listens on `5432`; inside Compose, Django connects
to the service name `db` on port `5432`.

Pick **one** setup below. Do not run Django/Celery locally with Docker-only
service addresses, or use one Redis/PostgreSQL locally and another in Docker.

## Option A: Everything runs on your machine (no Docker services)

### 1. Start local PostgreSQL with pgvector and Redis

Install PostgreSQL 16 with the pgvector extension and Redis 7 using your OS's
packages or the projects' official installation instructions. On Debian/Ubuntu,
the package names are commonly:

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib postgresql-16-pgvector redis-server
```

If your distribution does not provide `postgresql-16-pgvector`, install pgvector
for your installed PostgreSQL version using
[pgvector's installation instructions](https://github.com/pgvector/pgvector#installation).

Start the services and create the app database:

```bash
sudo systemctl enable --now postgresql redis-server
sudo -u postgres psql
```

At the `psql` prompt, enter:

```sql
CREATE USER raguser WITH PASSWORD 'ragpassword';
CREATE DATABASE ragdb OWNER raguser;
\connect ragdb
CREATE EXTENSION IF NOT EXISTS vector;
\q
```

Confirm PostgreSQL is listening on `5432` and Redis on `6379`:

```bash
pg_isready -h 127.0.0.1 -p 5432
redis-cli -h 127.0.0.1 -p 6379 ping
```

Expected results are `accepting connections` and `PONG`.

### 2. Configure and install the application

From the repository root:

```bash
cp .env.example .env
cp drive_service/.env.example drive_service/.env
```

The local templates use PostgreSQL `127.0.0.1:5432`, Redis `127.0.0.1:6379`,
and local service URLs. Replace the placeholder Django/Groq/Google credentials
as needed. Drive OAuth credentials are only needed for Google Drive features.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r drive_service/requirements.txt
python manage.py migrate
```

### 3. Run the local application services

Run each command in its own terminal from the repository root (activate `venv`
in each Python terminal):

```bash
python manage.py runserver
```

```bash
celery -A core worker -l info
```

```bash
cd drive_service
../venv/bin/uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

Optional frontend, in another terminal:

```bash
cd frontend
npm install
npm run dev
```

The API is at `http://127.0.0.1:8000`, Drive service at
`http://127.0.0.1:8001`, and frontend at `http://localhost:3000`.

## Option B: Everything runs in Docker Compose

No local PostgreSQL or Redis installation is needed. Copy the Docker-specific
environment files; do not use the local `.env.example` files for Compose:

```bash
cp .env.docker.example .env.docker
cp drive_service/.env.docker.example drive_service/.env.docker
```

Set the required keys in both files, then launch the complete stack:

```bash
docker compose up --build -d
docker compose exec django python manage.py migrate
docker compose exec django python manage.py createsuperuser
```

Compose starts PostgreSQL/pgvector, Redis, Django, the Celery worker, the Drive
service, and the frontend. App containers use Docker DNS names and internal
ports: PostgreSQL `db:5432`, Redis `redis:6379`, Django `django:8000`, and Drive
service `drive_service:8001`. From your host, the published PostgreSQL and
Redis ports are `127.0.0.1:5433` and `127.0.0.1:6380`; these host ports are not
the addresses the app containers should use.

Open the frontend at `http://localhost:3000` and Django at
`http://localhost:8000`. Check startup and health with:

```bash
docker compose ps
docker compose logs -f db redis django celery_worker drive_service
```

## Switching between modes

Stop the mode you are using before switching. Stop Compose containers with
`docker compose down` (this keeps the named database volume). For local mode,
stop the locally running Django, Celery, and Drive processes. Do not run two
app stacks against different databases and expect their data to be shared.

If Django reports connection refused, compare its configured host/port with
the selected mode:

| Mode | Django database | Django/Celery Redis | Drive-service database |
|---|---|---|---|
| Local | `127.0.0.1:5432` | `127.0.0.1:6379` | `127.0.0.1:5432` |
| Docker app containers | `db:5432` | `redis:6379` | `db:5432` |
| Docker host tools | `127.0.0.1:5433` | `127.0.0.1:6380` | `127.0.0.1:5433` |
