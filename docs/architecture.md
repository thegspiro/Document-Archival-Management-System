# ADMS System Architecture

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Host Machine (Docker)                           │
│                                                                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ frontend │  │ backend  │  │  worker   │  │   beat   │  │ nocodb  │ │
│  │ (nginx)  │  │ (FastAPI)│  │ (Celery)  │  │ (Celery) │  │         │ │
│  │  :3000   │  │  :8000   │  │          │  │          │  │  :8080  │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘ │
│       │              │             │              │              │      │
│       │         ┌────┴─────────────┴──────────────┴──────────────┘      │
│       │         │                                                       │
│  ┌────┴────┐  ┌─┴──────┐  ┌───────────────────────────────────┐       │
│  │  React  │  │ MySQL  │  │          Redis (:6379)            │       │
│  │   SPA   │  │ (:3306)│  │  Celery broker + result backend   │       │
│  └─────────┘  └────────┘  └───────────────────────────────────┘       │
│                    │                                                    │
│            ┌───────┴───────────────────────┐                           │
│            │   STORAGE_ROOT (/data/storage) │                           │
│            │   ├── files/                   │                           │
│            │   ├── .quarantine/             │                           │
│            │   ├── .thumbnails/             │                           │
│            │   └── .exports/                │                           │
│            └───────────────────────────────┘                           │
└─────────────────────────────────────────────────────────────────────────┘

External connections:
  ← Browser clients (HTTP/HTTPS via reverse proxy)
  ← OAI-PMH harvesters (GET /oai)
  → LLM APIs (OpenAI/Anthropic/Ollama)
  → Wikidata API (authority enrichment)
  → Nominatim API (geocoding from NER)
```

## 2. Service Topology

| Service | Image | Port | Depends On | Health Check |
|---------|-------|------|-----------|-------------|
| `db` | mysql:8.0 | 3306 | — | `mysqladmin ping` |
| `redis` | redis:7-alpine | 6379 | — | `redis-cli ping` |
| `backend` | adms-backend | 8000 | db, redis | `GET /api/v1/health` |
| `worker` | adms-backend | — | db, redis | — |
| `beat` | adms-backend | — | db, redis | — |
| `frontend` | adms-frontend | 3000 (80 internal) | backend | — |
| `nocodb` | nocodb/nocodb | 8080 | db | — |

**Key**: `backend`, `worker`, and `beat` share the same Docker image but run different commands:
- `backend`: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- `worker`: `celery -A app.workers.celery_app worker --loglevel=info`
- `beat`: `celery -A app.workers.celery_app beat --loglevel=info`

## 3. Data Flow Diagrams

### 3.1 Document Upload and Ingest

```
Browser                    Backend                     Worker (Celery)
  │                          │                              │
  │ POST /documents/{id}/    │                              │
  │      files (multipart)   │                              │
  ├─────────────────────────►│                              │
  │                          │ 1. Validate MIME, size       │
  │                          │ 2. Save to .quarantine/      │
  │                          │ 3. Compute SHA-256 hash      │
  │                          │ 4. Duplicate detection       │
  │                          │ 5. Run Siegfried (PRONOM)     │
  │                          │ 6. Evaluate preservation     │
  │                          │    warnings                  │
  │                          │ 7. Move to permanent path    │
  │                          │ 8. Insert document_files row │
  │                          │ 9. Write preservation_events │
  │                          │    (type=ingest)             │
  │                          │                              │
  │                          │ Queue tasks ────────────────►│
  │                          │                              │ 10. Generate thumbnail
  │    201 Created           │                              │ 11. Run OCR (Tesseract)
  │◄─────────────────────────┤                              │ 12. Run LLM suggestions
  │                          │                              │ 13. Run NER (if enabled)
  │                          │                              │ 14. Recompute completeness
```

### 3.2 Watch Folder Ingest

```
Celery Beat (every 60s)              Worker
  │                                    │
  │ poll_watch_folders ───────────────►│
  │                                    │ For each active watch folder:
  │                                    │   Scan path for new files
  │                                    │   Skip files with .processing lock
  │                                    │   For each new file:
  │                                    │     1. Create .processing lock
  │                                    │     2. Move to .quarantine/
  │                                    │     3. Compute hash, detect MIME
  │                                    │     4. Create document stub
  │                                    │        (inbox_status=inbox)
  │                                    │     5. Apply default_tags
  │                                    │     6. Move to permanent path
  │                                    │     7. Write preservation_events
  │                                    │     8. Queue OCR, thumbnails
  │                                    │     9. Remove .processing lock
```

### 3.3 Authentication Flow

```
Browser                    Backend                     MySQL
  │                          │                           │
  │ POST /auth/login         │                           │
  │ {email, password}        │                           │
  ├─────────────────────────►│ SELECT user WHERE email   │
  │                          ├──────────────────────────►│
  │                          │◄──────────────────────────┤
  │                          │ bcrypt.verify(password)    │
  │                          │ Generate JWT access token  │
  │                          │   (15-min expiry, HS256)   │
  │                          │ Generate refresh token     │
  │                          │   (30-day, stored hashed)  │
  │  Set-Cookie: access_token│                           │
  │  Set-Cookie: refresh_token (httpOnly, SameSite=Strict)
  │◄─────────────────────────┤                           │
  │                          │                           │
  │ [13 minutes later...]    │                           │
  │ SessionTimeout warning   │                           │
  │ "Extend session" click   │                           │
  │                          │                           │
  │ POST /auth/refresh       │                           │
  │ Cookie: refresh_token    │                           │
  ├─────────────────────────►│ Hash token, lookup in DB  │
  │                          │ Verify not expired/revoked│
  │                          │ Issue new access token    │
  │  Set-Cookie: access_token│                           │
  │◄─────────────────────────┤                           │
```

### 3.4 Search Flow

```
Browser                    Backend (SearchService)      MySQL
  │                          │                           │
  │ GET /api/v1/search       │                           │
  │ ?q=jones+mill&           │                           │
  │  date_from=1890-01-01    │                           │
  ├─────────────────────────►│                           │
  │                          │ Build query:              │
  │                          │  MATCH(title,scope,note)  │
  │                          │  AGAINST('jones mill')    │
  │                          │  + MATCH(ocr_text)        │
  │                          │  + WHERE date_start >=    │
  │                          │  + Version filter:        │
  │                          │    (version_group_id IS   │
  │                          │     NULL OR               │
  │                          │     is_canonical = TRUE)  │
  │                          │  + Permission filter      │
  │                          │  + Pagination             │
  │                          ├──────────────────────────►│
  │                          │◄──────────────────────────┤
  │  {items, total, page}    │ Rank by relevance score   │
  │◄─────────────────────────┤                           │
```

### 3.5 Export Flow (Download with XMP)

```
Browser                    Backend                     Worker
  │                          │                           │
  │ GET /documents/{id}/     │                           │
  │  files/{fid}/download    │                           │
  ├─────────────────────────►│                           │
  │                          │ 1. Load document metadata │
  │                          │ 2. Build Dublin Core dict │
  │                          │    (ISAD(G) → DC crosswalk│
  │                          │     per CLAUDE.md §22)    │
  │                          │ 3. Copy file to .exports/ │
  │                          │ 4. Embed XMP metadata:    │
  │                          │    PDF → pikepdf          │
  │                          │    Image → Pillow         │
  │                          │ 5. Stream file to client  │
  │  File with embedded XMP  │ 6. Delete temp export     │
  │◄─────────────────────────┤                           │
```

### 3.6 Fixity Check Flow

```
Celery Beat (weekly)         Worker                     MySQL
  │                           │                           │
  │ run_scheduled_fixity ────►│                           │
  │                           │ SELECT all document_files │
  │                           │ with file_hash_sha256     │
  │                           │                           │
  │                           │ For each file:            │
  │                           │   1. Read file from disk  │
  │                           │   2. Compute SHA-256      │
  │                           │   3. Compare with stored  │
  │                           │                           │
  │                           │ If MATCH:                 │
  │                           │   Write fixity_checks     │
  │                           │   (outcome=match)         │
  │                           │   Write preservation_events│
  │                           │   (outcome=success)       │
  │                           │                           │
  │                           │ If MISMATCH or MISSING:   │
  │                           │   Write fixity_checks     │
  │                           │   (outcome=mismatch)      │
  │                           │   Write preservation_events│
  │                           │   (outcome=failure)       │
  │                           │   Create review_queue     │
  │                           │   (reason=integrity_failure│
  │                           │    priority=high)         │
  │                           │   Set dashboard alert     │
```

## 4. Connection Points

| From | To | Protocol | Purpose |
|------|-----|----------|---------|
| Frontend (nginx) | Backend | HTTP (proxy_pass) | API calls `/api/v1/*` |
| Backend | MySQL | MySQL protocol (aiomysql) | Async ORM queries |
| Backend | Redis | Redis protocol | Celery task dispatch |
| Worker | MySQL | MySQL protocol (mysqlclient) | Sync ORM queries in tasks |
| Worker | Redis | Redis protocol | Task receipt + result storage |
| Worker | STORAGE_ROOT | Filesystem | File I/O (read/write/move) |
| Worker | LLM API | HTTPS | Metadata suggestions |
| Worker | Wikidata API | HTTPS | Authority enrichment |
| Worker | Nominatim API | HTTPS | Geocoding from NER |
| Beat | Redis | Redis protocol | Schedule publishing |
| NoCoDB | MySQL | MySQL protocol | Direct table access |
| External harvesters | Backend | HTTP (OAI-PMH) | Metadata harvesting |
| Browsers | Frontend | HTTPS (via proxy) | SPA loading |
| Browsers | Backend | HTTPS (via proxy) | API requests |

## 5. State Management

| State Type | Location | Technology | Scope |
|-----------|----------|-----------|-------|
| Persistent data | MySQL | SQLAlchemy 2.x (async) | All application data |
| Task queue | Redis | Celery broker | Pending/active tasks |
| Task results | Redis | Celery result backend | Task outcomes |
| Document files | STORAGE_ROOT volume | Filesystem | Original files, thumbnails, exports |
| Server state cache | Browser | React Query (TanStack) | Fetched API data with stale/refetch |
| Auth state | Browser | Zustand (`stores/auth.ts`) | Current user, JWT refresh |
| UI state | Browser | Zustand (`stores/ui.ts`) | Sidebar, theme, toasts |
| Inbox count | Browser | Zustand (`stores/inbox.ts`) | Badge count, polled every 30s |
| Theme preference | Browser | React Context | Light/dark/system |
| Form state | Browser | React useState / react-hook-form | Field values, validation |

## 6. Security Boundaries

### Authentication
- JWT access tokens (15-min, HS256, httpOnly cookie)
- JWT refresh tokens (30-day, stored as SHA-256 hash in DB, httpOnly cookie)
- No tokens in response bodies or localStorage
- CORS restricted to `BASE_URL`

### Permission Resolution (5-level cascade)
1. **Superadmin** — all permissions everywhere (bypass)
2. **User-specific** — `collection_permissions` row for this user on this node
3. **Role-based** — `collection_permissions` row for user's role on this node
4. **Inherited** — walk up arrangement tree to find first matching permission
5. **Global default** — role's default capabilities

### Public vs Authenticated
- Public routes: `/api/v1/public/*`, `/oai`, `/d/*`, `/ark/*` — no auth required
- Public routes only return records where `is_public = TRUE` and embargo has passed
- Authenticated routes: `/api/v1/*` — require valid JWT
- Admin routes: require `admin` or `superadmin` role

## 7. Celery Task Architecture

### Queue Routing

| Queue | Tasks | Purpose |
|-------|-------|---------|
| `default` | General tasks | Catch-all |
| `ocr` | `workers.ocr.*` | CPU-intensive OCR |
| `llm` | `workers.llm.*`, `workers.ner.*` | External API calls |
| `ingest` | `workers.ingest.*` | Watch folder processing |
| `fixity` | `workers.fixity.*` | File integrity checks |
| `export` | `workers.export.*` | XMP embedding |

### Beat Schedule

| Task | Schedule | Configurable |
|------|----------|-------------|
| `fixity.run_scheduled_fixity` | Sunday 2 AM UTC | Yes (`fixity.schedule_cron`) |
| `ingest.poll_watch_folders` | Every 60 seconds | Per watch folder |
| `description.recompute_all_stale` | Daily 3 AM UTC | No |

### Retry Policies
- **OCR**: 3 retries, exponential backoff. After 3 failures → `failed` status, manual retry required.
- **LLM/NER**: No automatic retry. Failures logged, don't block ingest.
- **Fixity**: No retry. Failures create high-priority review queue items.

## 8. File Storage Architecture

### Path Resolution

Physical paths are computed from the active storage scheme at runtime. The `stored_path` column holds a relative path; `StorageResolver.resolve_absolute()` prepends `STORAGE_ROOT`.

| Scheme | Pattern | Example |
|--------|---------|---------|
| `date` | `{year}/{month}/{accession}/{filename}` | `2025/06/2025-0042/deed.pdf` |
| `location` | `{fonds}/{series}/{file}/{accession}/{filename}` | `vfd/minutes/1925/2025-0042/minutes.pdf` |
| `donor` | `donors/{slug}/{accession}/{filename}` | `donors/smith_family/2025-0042/photo.jpg` |
| `subject` | `subjects/{category}/{accession}/{filename}` | `subjects/legal/2025-0042/deed.pdf` |
| `record_number` | `records/{prefix}/{accession}/{filename}` | `records/20/2025-0042/scan.tiff` |

### Special Directories

| Directory | Purpose | Cleanup |
|-----------|---------|---------|
| `.quarantine/` | Files being processed | Moved to permanent path on success; remains on failure |
| `.thumbnails/{file_id}/` | WebP thumbnails (300px) | Permanent |
| `.exports/{uuid}/` | Temporary files for download with XMP | Deleted after streaming |

### Path Sanitization
All path components are: lowercased, spaces → underscores, non-alphanumeric (except `-` and `_`) removed. Empty components become `"unknown"`.

---

*Source files: `backend/app/main.py`, `backend/app/config.py`, `backend/app/database.py`, `backend/app/workers/celery_app.py`, `backend/app/storage/resolver.py`, `docker-compose.yml`*
