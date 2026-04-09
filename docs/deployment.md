# ADMS Deployment Guide

Complete deployment and configuration guide for the Archival Document Management System.

---

## 1. Prerequisites

| Requirement | Minimum | Recommended |
|---|---|---|
| Docker Engine | 24.0+ | Latest stable |
| Docker Compose | 2.20+ | Latest stable |
| RAM | 4 GB | 8 GB+ |
| Disk | 20 GB (system) | Varies with collection size |
| OS | Any Linux with Docker | Ubuntu 22.04+, Unraid 6.12+ |

ADMS does not require root access inside containers. All services run as non-root users.

---

## 2. Quick Start (Single Instance)

```bash
# Clone the repository
git clone https://github.com/thegspiro/Document-Archival-Management-System.git
cd Document-Archival-Management-System

# Create environment file from template
cp .env.example .env

# Edit .env with your values (see Section 4 below)
nano .env

# Start all services
docker compose up -d

# Verify all services are running
docker compose ps

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/api/v1/health
# NoCoDB: http://localhost:8080
```

On first startup, navigate to `http://localhost:3000/setup` to run the setup wizard.

---

## 3. Deployment Tiers

### Tier 1 — Home Server / Unraid (Primary Target)

One machine. Docker Compose. A `.env` file. One command.

```bash
docker compose up -d
```

**Unraid-specific steps:**
1. Install the Docker Compose plugin from Community Applications
2. Clone the repo to `/mnt/user/appdata/adms/`
3. Set `STORAGE_ROOT` in `.env` to your desired share path (e.g., `/mnt/user/archives/`)
4. Map the storage volume in `docker-compose.yml`:
   ```yaml
   volumes:
     - /mnt/user/archives:/data/storage
   ```

### Tier 2 — VPS / Cloud VM

Same Docker Compose on a DigitalOcean Droplet, Linode, or EC2 instance.

**Additional steps:**
1. Set up a reverse proxy (nginx, Caddy, or Traefik) for TLS termination
2. Configure `BASE_URL` in `.env` to your public domain (e.g., `https://archive.example.org`)
3. Optionally replace MySQL with a managed database (RDS, PlanetScale) by changing `MYSQL_HOST`

### Tier 3 — Cloud Container Platform (Unsupported)

The Docker images can run on AWS ECS, Google Cloud Run, or Docker Swarm. ADMS does not
ship orchestration configuration for these platforms. An institution choosing Tier 3 is
responsible for the infrastructure layer.

---

## 4. Environment Variables

All variables are documented in `.env.example`. The application refuses to start if
required variables are missing.

### Required

| Variable | Description | Example |
|---|---|---|
| `MYSQL_ROOT_PASSWORD` | MySQL root password | `$(openssl rand -hex 32)` |
| `MYSQL_DATABASE` | Database name | `adms` |
| `MYSQL_USER` | Database user | `adms` |
| `MYSQL_PASSWORD` | Database user password | `$(openssl rand -hex 32)` |
| `SECRET_KEY` | 64-char hex for JWT signing | `$(openssl rand -hex 32)` |
| `STORAGE_ROOT` | File storage path inside container | `/data/storage` |
| `BASE_URL` | Public URL for links and CORS | `http://localhost:3000` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |

### Optional — NoCoDB

| Variable | Description | Example |
|---|---|---|
| `NC_DB` | NoCoDB database connection | `mysql2://db:3306?u=adms&p=PASSWORD&d=adms` |
| `NOCODB_AUTH_TOKEN` | NoCoDB API token | (generated in NoCoDB UI) |

### Optional — LLM

| Variable | Description | Example |
|---|---|---|
| `LLM_PROVIDER` | `openai`, `anthropic`, `ollama`, or `none` | `none` |
| `LLM_API_KEY` | API key for the chosen provider | `sk-...` |
| `LLM_BASE_URL` | Base URL (required for Ollama) | `http://ollama:11434` |
| `LLM_MODEL` | Model name | `gpt-4o-mini` |

### Optional — OCR

| Variable | Description | Default |
|---|---|---|
| `OCR_ENABLED` | Enable/disable OCR processing | `true` |
| `OCR_LANGUAGE` | Tesseract language codes | `eng` |
| `OCR_WORKER_CONCURRENCY` | Max parallel OCR tasks | `2` |

---

## 5. Docker Compose Services

| Service | Image | Internal Port | Default External Port | Purpose |
|---|---|---|---|---|
| `db` | mysql:8.0 | 3306 | 3306 | Primary data store |
| `redis` | redis:7-alpine | 6379 | 6379 | Celery broker + cache |
| `backend` | adms-backend | 8000 | 8000 | FastAPI API server |
| `worker` | adms-backend | — | — | Celery task worker |
| `beat` | adms-backend | — | — | Celery beat scheduler |
| `frontend` | adms-frontend | 80 | 3000 | React SPA via nginx |
| `nocodb` | nocodb/nocodb | 8080 | 8080 | Spreadsheet interface |

### Health Checks

- Backend: `GET /api/v1/health` — returns `{"status": "ok"}`
- MySQL: `mysqladmin ping`
- Redis: `redis-cli ping`

### Service Dependencies

```
frontend → backend → db, redis
worker → db, redis
beat → db, redis
nocodb → db
```

---

## 6. Volumes and Storage

| Volume | Purpose | Bind-mountable |
|---|---|---|
| `adms_mysql_data` | MySQL data directory | Yes |
| `adms_redis_data` | Redis persistence | Yes |
| `adms_storage` | Document file storage | Yes (recommended) |

### Storage Directory Structure

```
{STORAGE_ROOT}/
├── files/           # Permanent document files (organized by storage scheme)
├── .quarantine/     # Files being processed (temporary)
├── .thumbnails/     # Generated thumbnails (WebP, 300px)
│   └── {file_id}/
│       └── {page}.webp
├── .exports/        # Temporary export files (auto-cleaned)
└── .watch/          # Watch folder paths (configurable)
```

### Storage Schemes

The active storage scheme determines how files are organized on disk:

| Scheme | Path Pattern | Best For |
|---|---|---|
| `date` | `{year}/{month}/{accession}/{filename}` | Chronological collections |
| `location` | `{fonds}/{series}/{file}/{accession}/{filename}` | Hierarchical archives |
| `donor` | `donors/{donor_slug}/{accession}/{filename}` | Donor-organized collections |
| `subject` | `subjects/{category}/{accession}/{filename}` | Subject-based organization |
| `record_number` | `records/{prefix}/{accession}/{filename}` | Sequential record systems |

The scheme is selected during first-run setup and affects only physical file layout. It does
not affect how documents appear in the UI.

---

## 7. Reverse Proxy Configuration

ADMS does not terminate TLS. A reverse proxy is required for HTTPS.

### nginx Example

```nginx
server {
    listen 443 ssl http2;
    server_name archive.example.org;

    ssl_certificate /etc/letsencrypt/live/archive.example.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/archive.example.org/privkey.pem;

    client_max_body_size 500M;  # Match ADMS upload limit

    # Frontend (React SPA)
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # OAI-PMH endpoint
    location /oai {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }

    # Persistent URLs
    location /d/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }

    location /ark/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }
}
```

---

## 8. Multi-Instance Deployment

Use `adms-manager` to run multiple isolated ADMS instances on one server.

```bash
cd manager/

# Create a new instance
./adms-manager create falls-church-vfd

# Start it
./adms-manager start falls-church-vfd

# Create another instance
./adms-manager create falls-church-historical

# List all instances
./adms-manager list

# Generate nginx config for all instances
./adms-manager proxy-config > /etc/nginx/sites-available/adms-instances
```

Each instance gets its own:
- MySQL database (separate port)
- Redis instance (separate port)
- Storage volume (separate directory)
- NoCoDB instance (separate port)
- Docker Compose project (prefixed with `adms-`)

See `manager/README.md` for full command reference.

### Port Allocation

| Instance # | Frontend | Backend | MySQL | Redis | NoCoDB |
|---|---|---|---|---|---|
| 1 | 3001 | 8001 | 3307 | 6380 | 8081 |
| 2 | 3002 | 8002 | 3308 | 6381 | 8082 |
| N | 3000+N | 8000+N | 3306+N | 6379+N | 8080+N |

---

## 9. Backup and Restore

### Manual Backup

```bash
# Database dump
docker compose exec db mysqldump -u root -p adms > backup_$(date +%Y%m%d).sql

# Storage files
tar czf storage_$(date +%Y%m%d).tar.gz -C /path/to/storage .

# Environment (contains secrets — store securely)
cp .env .env.backup
```

### Using adms-manager

```bash
./adms-manager backup my-instance
# Creates: /opt/adms/instances/my-instance/backups/2026-04-09T0200.tar.gz

./adms-manager restore my-instance /path/to/backup.tar.gz
```

### Restore Steps

1. Stop the instance: `docker compose down` or `./adms-manager stop <name>`
2. Restore the database: `docker compose exec -T db mysql -u root -p adms < backup.sql`
3. Restore storage files to the `STORAGE_ROOT` path
4. Restart: `docker compose up -d` or `./adms-manager start <name>`

---

## 10. Updating

```bash
# Pull latest images
docker compose pull

# Run database migrations
docker compose run --rm backend alembic upgrade head

# Restart services
docker compose up -d
```

Or with adms-manager:

```bash
./adms-manager update my-instance
```

### Update All Instances

```bash
./adms-manager list | awk -F'|' 'NR>1 {print $1}' | xargs -I{} ./adms-manager update {}
```

Updates run sequentially — one instance at a time.

---

## 11. Local Development

```bash
# Copy the development override
cp docker-compose.override.yml.example docker-compose.override.yml

# Start with hot reload
docker compose up -d

# Backend is accessible at http://localhost:8000
# Frontend dev server at http://localhost:5173 (Vite HMR)
```

The override file:
- Mounts backend source code for auto-reload
- Mounts frontend `src/` for Vite HMR
- Exposes database and Redis ports for inspection
- Sets log level to `DEBUG`

---

## 12. Celery Task Configuration

### Task Queues

| Queue | Tasks | Workers |
|---|---|---|
| `default` | General tasks | `worker` service |
| `ocr` | OCR processing | `worker` service |
| `llm` | LLM suggestions, NER | `worker` service |
| `ingest` | Watch folder ingest | `worker` service |
| `fixity` | Fixity checks | `worker` service |
| `export` | XMP embedding | `worker` service |

### Beat Schedule

| Task | Schedule | Purpose |
|---|---|---|
| `fixity.run_scheduled_fixity` | Weekly, Sunday 2 AM UTC | Verify file integrity |
| `ingest.poll_watch_folders` | Every 60 seconds | Scan watch folders for new files |
| `description.recompute_all_stale` | Daily, 3 AM UTC | Recompute completeness for stale documents |

The fixity schedule is configurable via system settings (`fixity.schedule_cron`).

---

## 13. Troubleshooting

### Services Not Starting

```bash
# Check service logs
docker compose logs backend
docker compose logs db

# Verify health checks
curl http://localhost:8000/api/v1/health
docker compose exec db mysqladmin ping -u root -p
```

### Database Connection Issues

- Verify `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD` in `.env`
- Ensure the `db` service is healthy before starting `backend`
- Check if MySQL has finished initialization (first run may take 30+ seconds)

### OCR Failures

- Check `OCR_LANGUAGE` matches installed Tesseract language packs
- Reduce `OCR_WORKER_CONCURRENCY` on low-RAM hosts (default: 2)
- View OCR errors in the document detail page or `document_files.ocr_error` column

### File Upload Failures

- Check `client_max_body_size` in nginx matches the upload limit (default: 500 MB)
- Verify `STORAGE_ROOT` is writable by the container user
- Check available disk space on the storage volume

### LLM Integration Issues

- Verify `LLM_API_KEY` is set and valid
- For Ollama: ensure `LLM_BASE_URL` points to the Ollama service
- Check worker logs: `docker compose logs worker`
