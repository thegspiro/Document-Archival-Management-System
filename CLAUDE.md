# CLAUDE.md — Archival Document Management System (ADMS)

This file is the authoritative specification for building the Archival Document Management
System. Every implementation decision must conform to this document. Do not invent APIs,
schemas, configuration values, or behaviors not described here. If a requirement is
ambiguous, stop and ask before writing code.

---

## 1. Project Overview

ADMS is a self-hosted, multi-user web application for historians and archivists to ingest,
describe, organize, and publish primary source documents. It manages scanned and digital
documents of any file type, applies professional archival metadata standards (ISAD(G) /
DACS / Dublin Core), supports OCR and LLM-assisted metadata suggestion, exports citations,
provides a public-facing exhibition site, and embeds portable metadata into every exported
file so that archival context is never lost when data moves between systems.

Dublin Core is a first-class metadata layer in ADMS, not merely an export format. Every
document record has a canonical Dublin Core mapping used for XMP embedding, OAI-PMH
harvesting, and dc_xml export. The Dublin Core crosswalk to ISAD(G) fields is defined in
§22 and must be respected throughout all export and import code.

The application writes all data to a MySQL database that is also connected to a NoCoDB
instance, allowing archivists to browse and augment records (such as biographical authority
records) directly through NoCoDB's interface without requiring a separate ETL step.

### 1.1 Guiding Principles

- **Archival standards first.** Metadata schema is grounded in ISAD(G), DACS, ISAAR(CPF),
  Dublin Core (DCMI), OAIS (ISO 14721:2025), and PREMIS v3. See §21 for the full
  standards reference list.
- **Metadata portability.** Every file exported from ADMS carries its archival metadata
  embedded as XMP Dublin Core. Organizational work must survive migration to another system.
- **Portability.** The primary deployment target is Docker Compose on a Linux host
  (Unraid, a home server, a VPS). The Docker images are built to be portable —
  they make no assumptions about the host OS, do not require root access, and use
  only standard environment variables for configuration. A larger institution can
  run these images on AWS ECS or a similar container platform without modifying the
  application code, but ADMS does not ship or support orchestration configuration
  for those environments. Kubernetes is explicitly out of scope (see §33).
- **NoCoDB compatibility.** All tables must be plain MySQL tables readable and writable by
  NoCoDB. No stored procedures, triggers, or views that NoCoDB cannot handle.
- **Correctness over speed.** Validate all inputs. Prefer explicit over implicit behavior.
- **No secrets in code.** All credentials come from environment variables.
- **Long-term preservation.** Every file stored must have its integrity verifiable at any
  future point. Format characterization, fixity checks, and preservation event logging
  are not optional features — they are core to the system's archival purpose.

---

## 2. Technology Stack

| Layer | Technology | Notes |
|---|---|---|
| Backend API | Python 3.12, FastAPI | Async, OpenAPI docs auto-generated |
| Task queue | Celery + Redis | OCR, LLM, thumbnail generation, fixity checks |
| Celery beat | Celery beat scheduler | Scheduled fixity verification (OAIS requirement) |
| Database | MySQL 8.0 | NoCoDB-compatible; all migrations via Alembic |
| ORM | SQLAlchemy 2.x | Async engine |
| Frontend | TypeScript, React 18, Vite | No other frontend frameworks |
| Server state | TanStack Query (React Query v5) | Data fetching, caching, background sync |
| Client state | Zustand | Auth, UI state, inbox count. No Redux. |
| Styling | Tailwind CSS + CSS custom properties | Utility-first; design tokens in `tokens.css` |
| File storage | Mounted volume | Configurable root path via env var |
| OCR | Tesseract 5 via pytesseract | Runs in same container or sidecar |
| XMP embedding | pikepdf (PDF), Pillow (images) | Dublin Core XMP written on every export |
| XML generation | lxml | EAD3, Dublin Core, OAI-PMH XML output |
| Format characterization | Siegfried (via subprocess) | PRONOM registry; OAIS/PREMIS requirement |
| NER (optional) | spaCy 3.x | Named entity extraction; institution opt-in (see §27) |
| LLM | Configurable adapter | OpenAI, Anthropic, or Ollama (see §9) |
| Search | MySQL full-text search (phase 1) | Elasticsearch is a future option |
| Auth | JWT (access + refresh tokens) | Stored in httpOnly cookies |
| Map blocks | Leaflet.js + OpenStreetMap tiles | No API key required; bundled with frontend |
| Timeline blocks | KnightLab TimelineJS (self-hosted) | Bundled with frontend build; no CDN |
| Reverse proxy | User-provided (nginx, Traefik) | ADMS does not terminate TLS |
| Container | Docker Compose | Primary and only supported deployment format |

Do not introduce any dependency not listed here without explicit approval.

---

## 3. Repository Structure

```
adms/
├── CLAUDE.md                  # This file
├── docker-compose.yml
├── docker-compose.override.yml.example
├── .env.example
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/          # One file per migration, never edited after merge
│   ├── app/
│   │   ├── main.py            # FastAPI application factory
│   │   ├── config.py          # Pydantic settings loaded from env
│   │   ├── database.py        # SQLAlchemy async engine and session factory
│   │   ├── deps.py            # FastAPI dependency injection (db, auth, permissions)
│   │   ├── models/            # SQLAlchemy ORM models; one file per domain entity
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── routers/           # FastAPI routers; one file per resource
│   │   ├── services/          # Business logic; no direct HTTP or ORM in routers
│   │   ├── workers/           # Celery task definitions
│   │   ├── ocr/               # OCR adapter
│   │   ├── llm/               # LLM adapter (provider-agnostic interface)
│   │   ├── storage/           # File I/O and path resolution
│   │   ├── xmp/               # XMP metadata embedding (pikepdf / Pillow)
│   │   └── export/            # Citation and export formatters
│   └── tests/
│       ├── conftest.py
│       ├── unit/
│       └── integration/
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html                 # Entry point; sets lang attribute and meta charset
│   ├── src/
│   │   ├── main.tsx               # React root; mounts App into #root
│   │   ├── App.tsx                # Router, theme provider, auth gate
│   │   ├── api/                   # Backend connection layer
│   │   │   ├── client.ts          # Axios/fetch instance; attaches auth headers
│   │   │   ├── documents.ts       # Document API calls
│   │   │   ├── authority.ts       # Authority record API calls
│   │   │   ├── locations.ts       # Location API calls
│   │   │   ├── events.ts          # Event API calls
│   │   │   ├── exhibitions.ts     # Exhibition API calls
│   │   │   ├── vocabulary.ts      # Vocabulary API calls
│   │   │   └── ...                # One file per backend resource
│   │   ├── assets/                # Static files committed to the repo
│   │   │   ├── fonts/             # Self-hosted fonts (no Google Fonts CDN)
│   │   │   ├── icons/             # SVG icon files
│   │   │   └── images/            # Logos, placeholders, default thumbnails
│   │   ├── components/
│   │   │   ├── layout/            # Page shells; used in App.tsx routing
│   │   │   │   ├── AppShell.tsx   # Authenticated layout: nav + sidebar + main
│   │   │   │   ├── PublicShell.tsx # Public site layout: header + footer
│   │   │   │   ├── Navbar.tsx     # Top navigation with inbox badge, user menu
│   │   │   │   ├── Sidebar.tsx    # Collection tree navigation
│   │   │   │   └── Footer.tsx     # Public site footer with institution info
│   │   │   └── ui/                # Reusable, stateless UI primitives
│   │   │       ├── Button.tsx     # All button variants; enforces 44px touch targets
│   │   │       ├── Modal.tsx      # Focus-trapped modal; returns focus on close
│   │   │       ├── Toast.tsx      # aria-live="polite" notification region
│   │   │       ├── Badge.tsx      # Completeness indicator, status badges
│   │   │       ├── Spinner.tsx    # Loading indicator with aria-label
│   │   │       ├── SkipNav.tsx    # "Skip to main content" — first element on page
│   │   │       ├── FileViewer.tsx # Document image/PDF viewer (§31.7)
│   │   │       ├── MapBlock.tsx   # Leaflet map with keyboard controls (§31.8)
│   │   │       └── ...
│   │   ├── context/               # React Context for values that don't need Zustand
│   │   │   ├── ThemeContext.tsx   # light/dark/system theme; reads prefers-color-scheme
│   │   │   └── InstitutionContext.tsx  # Institution name, logo, advisory text
│   │   │   # Note: Auth state lives in stores/auth.ts (Zustand), NOT context.
│   │   │   # Context is for values that change rarely and need no async logic.
│   │   ├── data/                  # Static content and compile-time constants
│   │   │   ├── citationFormats.ts # Citation format definitions (Chicago, Turabian, etc.)
│   │   │   ├── isadFields.ts      # ISAD(G) field labels and help text
│   │   │   └── wcagTokens.ts      # Contrast ratios, focus colors — mirrors CSS tokens
│   │   ├── hooks/                 # Custom React hooks; encapsulate all side effects
│   │   │   ├── useAuth.ts         # Reads from stores/auth.ts; exposes user + role
│   │   │   ├── usePermission.ts   # Returns boolean for a given action + resource
│   │   │   ├── useDocuments.ts    # React Query wrapper for document fetching
│   │   │   ├── useInbox.ts        # Inbox count; polls periodically for badge update
│   │   │   ├── useAnnouncer.ts    # Programmatic ARIA live region announcements
│   │   │   ├── useFocusTrap.ts    # Focus trapping for modals and drawers
│   │   │   ├── useReducedMotion.ts # Reads prefers-reduced-motion media query
│   │   │   └── ...
│   │   ├── pages/                 # Route-level components; one file per route
│   │   │   ├── admin/
│   │   │   ├── archive/
│   │   │   ├── inbox/
│   │   │   ├── review/
│   │   │   ├── events/
│   │   │   ├── locations/
│   │   │   └── public/            # Public exhibition pages
│   │   ├── services/              # Frontend business logic; called by hooks and pages
│   │   │   ├── citation.ts        # Format a document as a citation string client-side
│   │   │   ├── permissions.ts     # Role-based action matrix; used by usePermission
│   │   │   ├── completeness.ts    # Compute description completeness badge client-side
│   │   │   ├── import.ts          # CSV import validation helpers (column type checks)
│   │   │   └── accessibility.ts   # Focus management helpers; announcer queue
│   │   ├── stores/                # Zustand global state (replaces Redux for this app)
│   │   │   ├── auth.ts            # Current user, role, token refresh logic
│   │   │   ├── inbox.ts           # Inbox count; updated by useInbox hook
│   │   │   └── ui.ts              # Sidebar open/closed, active theme, toast queue
│   │   ├── styles/
│   │   │   ├── tokens.css         # Design tokens (colors, contrast ratios) — §31.4
│   │   │   ├── global.css         # Base resets, focus-visible styles, print styles
│   │   │   └── reduced-motion.css # prefers-reduced-motion overrides
│   │   ├── types/                 # TypeScript type definitions
│   │   │   ├── api.ts             # Response types mirroring backend Pydantic schemas
│   │   │   ├── document.ts        # Document, DocumentFile, DocumentPage types
│   │   │   ├── authority.ts       # AuthorityRecord, AuthorityLink types
│   │   │   ├── event.ts           # Event, EventDocumentLink types
│   │   │   └── ...
│   │   └── utils/                 # Pure helper functions; no React, no side effects
│   │       ├── dates.ts           # Date formatting, partial date handling
│   │       ├── accession.ts       # Accession number parsing and formatting
│   │       ├── strings.ts         # Truncation, slugification, sanitization
│   │       └── aria.ts            # ARIA attribute helpers (labelledby id generation)
│   └── tests/
│       ├── components/            # React Testing Library component tests
│       ├── hooks/                 # Vitest unit tests for hooks
│       ├── services/              # Vitest unit tests for service functions
│       └── a11y/                  # vitest-axe accessibility tests per component
└── scripts/                   # Shell utility scripts (POSIX sh, not bash-specific)
└── manager/                   # adms-manager companion tool (see §35)
    ├── adms-manager           # POSIX sh CLI; executable
    ├── templates/
    │   ├── docker-compose.yml.tmpl  # Per-instance compose template
    │   └── env.tmpl                 # Per-instance .env template
    └── README.md              # Installation and usage guide
```

---

## 4. Docker Compose Deployment

### 4.1 Services

```yaml
# docker-compose.yml defines exactly these services:
services:
  db:          # MySQL 8.0
  redis:       # Redis 7 (Celery broker + result backend)
  backend:     # FastAPI application
  worker:      # Celery worker (same image as backend, different command)
  beat:        # Celery beat scheduler (fixity checks, cleanup jobs)
  frontend:    # Vite build served by nginx
  nocodb:      # NoCoDB pointing at the same MySQL instance
```

### 4.2 Volumes

```
adms_mysql_data    → MySQL data directory
adms_redis_data    → Redis persistence
adms_storage       → Document file storage (bind-mountable to Unraid share)
```

The storage volume root is set by `STORAGE_ROOT` env var, defaulting to
`/data/storage` inside the container. On Unraid, the user bind-mounts their
preferred share path to `/data/storage`.

### 4.3 Deployment Paths

ADMS is designed to be deployed and operated by people who are historians and
archivists first, not systems administrators. The deployment experience must
reflect that. Three realistic tiers are supported:

**Tier 1 — Home server or Unraid (primary target)**
One machine. Docker Compose. A `.env` file. One command.
```
docker-compose up -d
```
This is the configuration most ADMS users will run. It is the only configuration
that is actively tested and officially supported. Everything in this spec is
designed to work in this environment.

**Tier 2 — VPS or cloud virtual machine**
Same Docker Compose configuration running on a DigitalOcean Droplet, Linode,
or AWS EC2 instance. The only differences from Tier 1 are the host machine
and the network configuration of the reverse proxy. No application changes needed.
A deployer comfortable with basic Linux administration can run this tier.
Replace the local MySQL service with a managed database (AWS RDS, PlanetScale)
by changing `MYSQL_HOST` in `.env` — no other changes required.

**Tier 3 — Cloud container platform (self-serve, unsupported)**
Institutions with DevOps staff may run the same Docker images on AWS ECS,
Google Cloud Run, or Docker Swarm. Because the images are standard Docker with
all configuration via environment variables, this works without modifying the
application. However, ADMS does not ship orchestration manifests for these
platforms, does not test against them, and cannot provide support for them.
An institution choosing Tier 3 is on its own for the infrastructure layer.

**What ADMS does to support portability across all tiers:**
- All configuration comes from environment variables — no hardcoded paths or hosts
- No assumptions about filesystem layout beyond `STORAGE_ROOT`
- No requirement for root access inside containers (all services run as non-root users)
- Health check endpoints on all services for load balancer and orchestrator use
- Graceful shutdown handling so containers can be stopped and restarted safely

### 4.4 Local Development Override

`docker-compose.override.yml` (not committed; created from `.override.yml.example`)
is used in local development to:
- Mount backend source code for hot reload
- Mount frontend `src/` for Vite HMR
- Expose additional ports for database and Redis inspection
- Override log levels to `DEBUG`
- Disable SSL requirements

Production deployments must never use the override file. The production compose
file is the base `docker-compose.yml` with no overrides.

### 4.3 Required Environment Variables

Document every variable in `.env.example`. The application must refuse to start
if any required variable is missing. Use Pydantic `BaseSettings` to enforce this.

```
# Database
MYSQL_ROOT_PASSWORD=
MYSQL_DATABASE=adms
MYSQL_USER=adms
MYSQL_PASSWORD=

# Application
SECRET_KEY=                    # 64-char random hex; used for JWT signing
STORAGE_ROOT=/data/storage
BASE_URL=http://localhost:3000 # Used for public links and CORS

# Redis
REDIS_URL=redis://redis:6379/0

# NoCoDB
NOCODB_AUTH_TOKEN=             # NoCoDB API token for internal API calls (optional)
NC_DB=mysql2://db:3306?u=adms&p=<password>&d=adms

# LLM (all optional; see §9)
LLM_PROVIDER=                  # openai | anthropic | ollama | none
LLM_API_KEY=
LLM_BASE_URL=                  # Required for Ollama
LLM_MODEL=

# OCR
OCR_ENABLED=true
OCR_LANGUAGE=eng               # Tesseract language code(s), comma-separated
OCR_WORKER_CONCURRENCY=2       # Max parallel OCR tasks; lower on RAM-constrained hosts
```

---

## 5. Database Schema

All migrations live in `backend/alembic/versions/`. Every migration must be
idempotent where possible (use `IF NOT EXISTS`, check before altering). Never
modify a merged migration file; always create a new one.

Primary keys are `BIGINT UNSIGNED AUTO_INCREMENT` unless noted. All tables include
`created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP` and
`updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP`.

String columns use `utf8mb4` collation. Never use `TEXT` for columns that will
be indexed or searched; use `VARCHAR` with a defined length.

### 5.1 Users and Authentication

```sql
users
  id, email (unique), password_hash, display_name, is_active,
  is_superadmin, last_login_at, created_at, updated_at

roles
  id, name (unique), description, created_at, updated_at
  -- Seed values: superadmin, admin, archivist, contributor, intern, viewer

user_roles
  id, user_id (FK users), role_id (FK roles), created_at
  -- A user can hold multiple roles

refresh_tokens
  id, user_id (FK users), token_hash, expires_at, revoked_at, created_at
```

### 5.2 Hierarchical Arrangement (ISAD(G) Levels)

ISAD(G) defines: Fonds → Subfonds → Series → Subseries → File → Item.
This application implements a flexible hierarchy using a self-referencing
`arrangement_nodes` table, where each node has a `level_type` enum.

```sql
arrangement_nodes
  id, parent_id (FK self, nullable),
  level_type ENUM('fonds','subfonds','series','subseries','file','item'),
  title VARCHAR(500) NOT NULL,
  identifier VARCHAR(200),          -- local reference code
  description TEXT,
  date_start DATE,
  date_end DATE,
  is_public BOOLEAN DEFAULT FALSE,
  sort_order INT DEFAULT 0,
  created_by (FK users), created_at, updated_at
```

Documents are attached to a node at the `item` level (or `file` if the item
level is not used). The node tree defines the physical storage hierarchy
the user selected at deployment time.

### 5.3 Storage Schemes

The administrator selects one storage scheme at setup. This controls how files
are physically organized on disk. It does not limit how documents are surfaced
in the UI.

```sql
storage_schemes
  id, name VARCHAR(100), scheme_type ENUM('location','donor','subject','date','record_number'),
  config JSON,    -- scheme-specific configuration (e.g., location hierarchy labels)
  is_active BOOLEAN DEFAULT FALSE,   -- only one may be active
  created_at, updated_at
```

Physical path on disk is always computed deterministically from the scheme
and document identifiers. It is never stored as a raw path string in the
document record (to keep paths portable when the storage root changes).

### 5.4 Documents (ISAD(G) Item Level)

```sql
documents
  id,
  arrangement_node_id (FK arrangement_nodes, nullable),  -- physical location in hierarchy
  accession_number VARCHAR(200) UNIQUE,   -- full versioned accession, e.g. '2025-0042' or '2025-0042.1'
  -- Version group fields (null when document has no versions)
  version_group_id BIGINT UNSIGNED,       -- FK to document_version_groups; null = unversioned
  version_number INT UNSIGNED DEFAULT 1,  -- 1, 2, 3... within the group
  version_label VARCHAR(200),             -- human label: "1978 Revision", "Smith Donation Copy"
  is_canonical_version BOOLEAN DEFAULT FALSE,  -- the default version shown in search/browse
  title VARCHAR(1000) NOT NULL,
  -- ISAD(G) Identity Statement Area
  reference_code VARCHAR(200),
  date_display VARCHAR(200),             -- free-text date as written on document
  date_start DATE,                       -- normalized start date
  date_end DATE,                         -- normalized end date (same as start if single date)
  level_of_description ENUM('fonds','subfonds','series','subseries','file','item') DEFAULT 'item',
  extent VARCHAR(500),                   -- e.g. "3 pages", "1 photograph"
  -- ISAD(G) Context Area
  creator_id BIGINT UNSIGNED,            -- FK to authority_records (persons/orgs)
  administrative_history TEXT,
  archival_history TEXT,
  immediate_source TEXT,                 -- acquisition source
  -- ISAD(G) Content and Structure Area
  scope_and_content TEXT,
  appraisal_notes TEXT,
  accruals TEXT,
  system_of_arrangement TEXT,
  -- ISAD(G) Conditions of Access Area
  access_conditions TEXT,
  reproduction_conditions TEXT,
  language_of_material VARCHAR(500),     -- ISO 639 codes, comma-separated
  physical_characteristics TEXT,
  finding_aids TEXT,
  -- ISAD(G) Allied Materials Area
  location_of_originals TEXT,
  location_of_copies TEXT,
  related_units TEXT,
  publication_note TEXT,
  -- ISAD(G) Notes Area
  general_note TEXT,
  archivists_note TEXT,
  -- ISAD(G) Description Control Area
  rules_or_conventions VARCHAR(200) DEFAULT 'DACS',
  description_status ENUM('draft','revised','final') DEFAULT 'draft',
  description_date DATE,
  described_by (FK users),
  -- Rights and Copyright (AASLH, PREMIS, SAA requirements)
  copyright_status ENUM('copyrighted','public_domain','unknown','orphan_work','creative_commons') DEFAULT 'unknown',
  rights_holder VARCHAR(500),            -- name of copyright holder
  rights_basis VARCHAR(200),             -- 'statute', 'license', 'donor_agreement', 'contract'
  rights_note TEXT,
  embargo_end_date DATE,                 -- access embargoed until this date
  donor_agreement_id BIGINT UNSIGNED,    -- FK to donor_agreements
  -- Application fields
  document_type_id BIGINT UNSIGNED,      -- FK to controlled_vocabulary
  physical_format_id BIGINT UNSIGNED,    -- FK to controlled_vocabulary
  condition_id BIGINT UNSIGNED,          -- FK to controlled_vocabulary
  original_location TEXT,               -- physical location of paper original
  scan_date DATE,
  scanned_by (FK users),
  is_public BOOLEAN DEFAULT FALSE,          -- must be explicitly enabled; never auto-set to true
  public_title VARCHAR(1000),               -- optional alternate title for public site
  -- Tombstone and availability control
  availability_status ENUM('available','temporarily_unavailable','deaccessioned') DEFAULT 'available',
  -- 'temporarily_unavailable' = pulled for correction; URL resolves to tombstone
  -- 'deaccessioned' = permanently removed; URL resolves to tombstone forever
  unavailable_reason TEXT,                  -- shown on tombstone if institution permits
  unavailable_since DATETIME,
  unavailable_until DATE,                   -- optional expected return date; shown on tombstone
  tombstone_disclosure ENUM('none','accession_only','collection_and_accession') DEFAULT 'accession_only',
  -- 'none' = "This item is no longer available." No other info.
  -- 'accession_only' = Shows accession number and contact info.
  -- 'collection_and_accession' = Also shows the collection/fonds name.
  -- Content advisory (reparative description support)
  has_content_advisory BOOLEAN DEFAULT FALSE,
  content_advisory_note TEXT,               -- contextual note explaining advisory; institution-authored
  -- Description completeness (computed by Celery task; never manually set)
  description_completeness ENUM('none','minimal','standard','full') DEFAULT 'none',
  description_completeness_updated_at DATETIME,
  -- Persistent identifier
  ark_id VARCHAR(200),                      -- e.g. 'ark:/99999/fk4abc123'; null if not assigned
  review_status ENUM('none','pending','approved','rejected') DEFAULT 'none',
  review_notes TEXT,
  llm_suggestions JSON,                     -- raw LLM output stored for audit
  inbox_status ENUM('inbox','processed') DEFAULT 'inbox',
  deaccession_status ENUM('none','proposed','approved','complete') DEFAULT 'none',
  created_by (FK users), created_at, updated_at
```

### 5.5 Document Version Groups

A version group ties together multiple document records that represent different states,
scans, or copies of the same intellectual item — adopted revisions of bylaws, rescans at
higher resolution, or copies donated by different sources.

```sql
document_version_groups
  id,
  base_accession_number VARCHAR(200) UNIQUE NOT NULL,  -- shared base, e.g. '2025-0042'
  canonical_document_id BIGINT UNSIGNED NOT NULL,       -- FK to documents; default for search/browse
  public_document_id BIGINT UNSIGNED,                   -- FK to documents; shown on public site
  -- null = same as canonical; set explicitly when org chooses a different public version
  title VARCHAR(1000) NOT NULL,                         -- group-level title (mirrors canonical)
  created_by (FK users), created_at, updated_at
```

**Invariants enforced in the application layer (not the database):**
- `canonical_document_id` must point to a document whose `version_group_id` equals this group's `id`.
- `public_document_id`, if set, must point to a document in this group that has `is_public = TRUE`.
- Exactly one document per group must have `is_canonical_version = TRUE`.
- Version numbers within a group are unique and assigned sequentially. They are never reused,
  even if an intermediate version is deaccessioned.

### 5.6 Document Files and Pages

A document can have one or more physical files (e.g., a scanned multi-page PDF
is one file; a collection of JPEGs is multiple files).

```sql
document_files
  id, document_id (FK documents),
  filename VARCHAR(500) NOT NULL,        -- original uploaded filename
  stored_path VARCHAR(2000) NOT NULL,    -- path relative to STORAGE_ROOT
  mime_type VARCHAR(200),
  file_size_bytes BIGINT UNSIGNED,
  file_hash_sha256 CHAR(64),             -- for deduplication and integrity checks
  page_count INT UNSIGNED DEFAULT 1,
  sort_order INT DEFAULT 0,
  ocr_status ENUM('none','queued','processing','complete','failed') DEFAULT 'none',
  ocr_text LONGTEXT,
  ocr_completed_at DATETIME,
  ocr_error TEXT,                        -- error message from last failed attempt
  ocr_attempt_count TINYINT UNSIGNED DEFAULT 0,
  thumbnail_path VARCHAR(2000),
  -- Technical metadata (NARA/FADGI digitization guidelines; PREMIS technical metadata)
  scan_resolution_ppi INT UNSIGNED,      -- pixels per inch at time of scanning
  bit_depth TINYINT UNSIGNED,            -- e.g. 8, 16, 24
  color_space VARCHAR(50),               -- e.g. 'sRGB', 'Grayscale', 'CMYK', 'Bitonal'
  scanner_make VARCHAR(200),
  scanner_model VARCHAR(200),
  scanning_software VARCHAR(200),
  image_quality_rating ENUM('preservation_master','production_master','access_copy','unknown') DEFAULT 'unknown',
  -- Format characterization (PREMIS / OAIS; populated by Siegfried on ingest)
  format_name VARCHAR(200),              -- human-readable format name from PRONOM
  format_version VARCHAR(50),            -- format version string
  format_puid VARCHAR(50),               -- PRONOM unique identifier, e.g. 'fmt/353'
  format_registry VARCHAR(50) DEFAULT 'PRONOM',
  format_validated BOOLEAN DEFAULT FALSE,
  format_validated_at DATETIME,
  -- Preservation warnings (non-blocking; displayed in UI)
  preservation_warning TEXT,             -- null if no issues; populated by ingest logic
  created_at, updated_at

document_pages
  id, document_file_id (FK document_files),
  page_number INT UNSIGNED NOT NULL,
  ocr_text TEXT,
  notes TEXT,                            -- per-page archivist notes
  is_public BOOLEAN DEFAULT FALSE,
  thumbnail_path VARCHAR(2000),
  created_at, updated_at
```

### 5.7 Authority Records (Persons, Organizations, Families)

This table models creators, donors, and other named entities referenced in
document metadata. NoCoDB users can add biographical/historical notes here
without going through the main application UI.

```sql
authority_records
  id,
  entity_type ENUM('person','organization','family') NOT NULL,
  authorized_name VARCHAR(500) NOT NULL,
  variant_names TEXT,                   -- pipe-delimited alternate names
  dates VARCHAR(200),                   -- e.g. "1842-1918"
  biographical_history TEXT,
  administrative_history TEXT,          -- for organizations
  identifier VARCHAR(200),              -- ISAAR identifier
  sources TEXT,
  notes TEXT,
  is_public BOOLEAN DEFAULT FALSE,
  -- Wikidata / Linked Open Data (§26)
  wikidata_qid VARCHAR(20),             -- e.g. 'Q42'; null if not linked
  wikidata_last_synced_at DATETIME,     -- when enrichment was last fetched
  wikidata_enrichment JSON,             -- cached enrichment data from Wikidata API
  -- NER provenance
  created_by_ner BOOLEAN DEFAULT FALSE, -- true if this record was suggested by NER
  created_by (FK users, nullable),      -- null if created_by_ner = TRUE and not yet reviewed
  created_at, updated_at
```

The `created_by` field is nullable to allow NER-suggested authority records to exist
in a pending state before an archivist claims or rejects them. A pending authority
record must never be used as a `creator_id` on a document until reviewed.

### 5.8 Controlled Vocabulary

All tag types, relationship types, document types, and similar enumerations
use this single vocabulary table.

```sql
vocabulary_domains
  id, name VARCHAR(200) UNIQUE,         -- e.g. 'document_type', 'tag', 'relationship_type',
  description TEXT,                     -- 'physical_format', 'condition', 'subject',
  allows_user_addition BOOLEAN DEFAULT TRUE,
  created_at, updated_at

vocabulary_terms
  id, domain_id (FK vocabulary_domains),
  term VARCHAR(500) NOT NULL,
  definition TEXT,
  broader_term_id (FK self, nullable),  -- for hierarchical terms (LCSH-style)
  is_active BOOLEAN DEFAULT TRUE,
  sort_order INT DEFAULT 0,
  created_by (FK users), created_at, updated_at
  UNIQUE KEY (domain_id, term)
```

Seed domains (created by first migration):
- `document_type` (letter, deed, photograph, map, report, minutes, etc.)
- `physical_format` (paper, photographic print, glass plate, microfilm, etc.)
- `condition` (excellent, good, fair, poor, damaged)
- `tag` (free-form subject/keyword tags)
- `subject_category` (broad topical categories)
- `relationship_type` (reply_to, precedes, follows, revision_of, related_to, etc.)
- `access_restriction` (public, restricted, confidential, embargoed)
- `language` (pre-populated with ISO 639 common languages)
- `authority_link_role` (recipient, signatory, witness, mentioned, depicted, etc.) — see §5.11
- `authority_relationship_type` (spouse_of, parent_of, member_of, etc.) — see §5.12
- `location_type` (building, neighborhood, city, cemetery, etc.) — see §5.13
- `event_type` (meeting, election, fire, ceremony, legal_proceeding, etc.) — see §5.15
- `event_authority_role` (organizer, attendee, speaker, witness, etc.) — see §5.17

**Vocabulary term merging:** When an administrator merges term A into term B
(e.g., correcting a bulk misspelling imported via CSV), the application:
1. Updates all `document_terms` rows from `term_id = A` to `term_id = B` in a
   single transaction.
2. Deletes term A.
3. Writes an `audit_log` entry recording the merge: which term was replaced,
   which term it was merged into, how many documents were affected, and who
   performed the action.

This is the correct approach for bulk corrections. Individual term renames
(changing a term's display text without merging) are handled by
`PATCH /api/v1/vocabulary/terms/{id}` with no document reassignment needed.

### 5.9 Document Tags and Categories

```sql
document_terms
  id, document_id (FK documents), term_id (FK vocabulary_terms),
  created_by (FK users), created_at
  UNIQUE KEY (document_id, term_id)
```

One table handles tags, categories, and any other vocabulary domain.
Filter by `vocabulary_terms.domain_id` to separate them.

### 5.10 Document Relationships

```sql
document_relationships
  id,
  source_document_id (FK documents),
  target_document_id (FK documents),
  relationship_type_id (FK vocabulary_terms),  -- must be in 'relationship_type' domain
  description TEXT,                            -- optional free-text note on the relationship
  created_by (FK users), created_at, updated_at
  UNIQUE KEY (source_document_id, target_document_id, relationship_type_id)
```

Relationships are directional. The UI must present them bidirectionally
(if A is a reply_to B, then B should show A as "has reply").

### 5.11 Document–Authority Record Links

This junction table tracks every named person, organization, or family referenced
in a document beyond the primary ISAD(G) creator. The `creator_id` field on
`documents` remains the authoritative ISAD(G) creator; this table handles all
other roles.

```sql
document_authority_links
  id,
  document_id (FK documents) NOT NULL,
  authority_id (FK authority_records) NOT NULL,
  role_id (FK vocabulary_terms) NOT NULL,   -- must be in 'authority_link_role' domain
  notes TEXT,                               -- optional context for this specific link
  created_by (FK users), created_at, updated_at
  UNIQUE KEY (document_id, authority_id, role_id)
```

Seed values for `authority_link_role` vocabulary domain:
`recipient`, `signatory`, `witness`, `mentioned`, `depicted`, `correspondent`,
`subject_of`, `co_creator`, `collector`, `transcribed_by`, `donor`, `addressee`

This enables: "Find all documents in which John Smith appears in any role" and
"Find all documents where Mary Jones was a recipient."

### 5.12 Authority Record Relationships

Authority records can be linked to each other to represent biographical and
organizational relationships. This is the data layer that will support the
future biographical network page.

```sql
authority_relationships
  id,
  source_authority_id (FK authority_records) NOT NULL,
  target_authority_id (FK authority_records) NOT NULL,
  relationship_type_id (FK vocabulary_terms) NOT NULL, -- 'authority_relationship_type' domain
  date_start DATE,
  date_end DATE,
  notes TEXT,
  created_by (FK users), created_at, updated_at
  UNIQUE KEY (source_authority_id, target_authority_id, relationship_type_id)
```

Relationships are directional but asymmetric inference is handled in the UI:
if A is `parent_of` B, then B should show A as "child of A."

Seed values for `authority_relationship_type` vocabulary domain:
`spouse_of`, `parent_of`, `child_of`, `sibling_of`, `colleague_of`,
`member_of`, `employed_by`, `founded`, `associated_with`, `succeeded_by`,
`preceded_by`

### 5.13 Locations

Locations are controlled entities — the equivalent of authority records for
places. Every named place mentioned across documents, events, and authority
records resolves to a canonical location record, enabling reliable cross-document
location browsing.

```sql
locations
  id,
  authorized_name VARCHAR(500) NOT NULL,    -- canonical form: "Jones Mill, Falls Church, Virginia"
  variant_names TEXT,                       -- pipe-delimited: "Jones's Mill|Jones' Mill"
  location_type_id (FK vocabulary_terms),   -- 'location_type' domain
  geo_latitude DECIMAL(9,6),
  geo_longitude DECIMAL(9,6),
  address TEXT,
  description TEXT,
  date_established DATE,                    -- when the place came into existence
  date_ceased DATE,                         -- when the place ceased to exist (demolished, renamed, etc.)
  parent_location_id (FK self, nullable),   -- hierarchy: mill → neighborhood → city → county → state
  wikidata_qid VARCHAR(20),
  is_public BOOLEAN DEFAULT FALSE,
  public_description TEXT,
  created_by (FK users), created_at, updated_at
```

Seed values for `location_type` vocabulary domain:
`building`, `room`, `neighborhood`, `district`, `city`, `county`, `state`,
`country`, `farm`, `mill`, `cemetery`, `park`, `road`, `bridge`, `body_of_water`,
`battlefield`, `institution`

### 5.14 Document–Location Links

```sql
document_location_links
  id,
  document_id (FK documents) NOT NULL,
  location_id (FK locations) NOT NULL,
  link_type ENUM('mentioned','depicted','created_at','event_location') DEFAULT 'mentioned',
  notes TEXT,
  created_by (FK users), created_at
  UNIQUE KEY (document_id, location_id, link_type)
```

The `link_type` distinguishes: a photograph *depicting* Jones Mill differs from
a deed *created at* the courthouse and a letter that merely *mentions* the mill
in passing.

Documents retain their existing `geo_latitude`, `geo_longitude`, and
`geo_location_name` fields as quick-entry shortcuts for documents not yet
linked to a full location entity. When a document is linked to a location, those
fields may be left as-is or synced from the location record — the archivist's choice.

### 5.15 Events

Events are first-class entities representing specific named historical occurrences.
They are instances, not categories: "City Council Meeting, April 2025" is an event;
"meeting" is an event type. Documents, authority records, and locations all link
to events.

```sql
events
  id,
  title VARCHAR(500) NOT NULL,              -- "Annual Meeting of Falls Church VFD, 1925"
  event_type_id (FK vocabulary_terms) NOT NULL,  -- 'event_type' domain
  date_display VARCHAR(200),                -- free-text date as written in sources
  date_start DATE,
  date_end DATE,
  primary_location_id (FK locations, nullable),
  description TEXT,
  is_public BOOLEAN DEFAULT FALSE,
  public_description TEXT,
  created_by (FK users), created_at, updated_at
```

Seed values for `event_type` vocabulary domain:
`meeting`, `election`, `fire`, `flood`, `disaster`, `ceremony`, `dedication`,
`legal_proceeding`, `trial`, `construction`, `demolition`, `birth`, `death`,
`marriage`, `publication`, `incorporation`, `annexation`, `military_action`

### 5.16 Event–Document Links

```sql
event_document_links
  id,
  event_id (FK events) NOT NULL,
  document_id (FK documents) NOT NULL,
  link_type ENUM('produced_by','about','referenced_in','precedes','follows') DEFAULT 'about',
  notes TEXT,
  created_by (FK users), created_at
  UNIQUE KEY (event_id, document_id)
```

`produced_by` — the document was created as a result of the event (meeting minutes)
`about` — the document discusses or describes the event
`referenced_in` — the event is mentioned incidentally in the document
`precedes` — this document came before the event and contributed to it (an agenda)
`follows` — this document was produced after the event in response to it (a report)

### 5.17 Event–Authority Record Links

```sql
event_authority_links
  id,
  event_id (FK events) NOT NULL,
  authority_id (FK authority_records) NOT NULL,
  role_id (FK vocabulary_terms) NOT NULL,   -- 'event_authority_role' domain
  notes TEXT,
  created_by (FK users), created_at
  UNIQUE KEY (event_id, authority_id, role_id)
```

Seed values for `event_authority_role` vocabulary domain:
`organizer`, `attendee`, `speaker`, `presiding_officer`, `witness`,
`subject`, `signatory`, `candidate`, `elected`, `deceased`, `married`

### 5.18 Event–Location Links

An event may relate to multiple locations (it started at one venue, moved to another;
a fire originated at one address and spread to a second).

```sql
event_location_links
  id,
  event_id (FK events) NOT NULL,
  location_id (FK locations) NOT NULL,
  link_type ENUM('primary','secondary','mentioned') DEFAULT 'primary',
  notes TEXT,
  created_by (FK users), created_at
  UNIQUE KEY (event_id, location_id)
```

### 5.19 Collection Permissions

Permissions are granted at the `arrangement_nodes` level and cascade downward
unless overridden. Absence of a row means no access beyond the user's global role.

```sql
collection_permissions
  id,
  arrangement_node_id (FK arrangement_nodes),
  user_id (FK users, nullable),          -- null means applies to a role
  role_id (FK roles, nullable),          -- null means applies to a user
  can_view BOOLEAN DEFAULT FALSE,
  can_create BOOLEAN DEFAULT FALSE,
  can_edit BOOLEAN DEFAULT FALSE,
  can_delete BOOLEAN DEFAULT FALSE,
  can_manage_permissions BOOLEAN DEFAULT FALSE,
  created_by (FK users), created_at, updated_at
  -- Exactly one of user_id or role_id must be non-null (enforce in application layer)
```

Permission resolution order (highest wins):
1. Superadmin: all permissions everywhere
2. User-specific permission on the node
3. Role-based permission on the node
4. Inherited permission from parent node (walk up tree)
5. Global role default (no collection-specific grant)

### 5.20 Review Queue

```sql
review_queue
  id,
  document_id (FK documents) UNIQUE,
  reason ENUM('llm_suggestions','manual_flag','import','initial_review','integrity_failure') NOT NULL,
  assigned_to (FK users, nullable),
  priority ENUM('low','normal','high') DEFAULT 'normal',
  notes TEXT,
  created_by (FK users), created_at, updated_at
```

### 5.21 Public Exhibition

```sql
exhibitions
  id,
  title VARCHAR(500) NOT NULL,
  slug VARCHAR(200) UNIQUE NOT NULL,     -- URL slug for public site
  description TEXT,
  cover_image_path VARCHAR(2000),
  is_published BOOLEAN DEFAULT FALSE,
  published_at DATETIME,
  sort_order INT DEFAULT 0,
  created_by (FK users), created_at, updated_at

exhibition_items
  id, exhibition_id (FK exhibitions),
  document_id (FK documents, nullable),
  arrangement_node_id (FK arrangement_nodes, nullable),
  caption TEXT,
  display_order INT DEFAULT 0,
  created_at, updated_at
  -- One of document_id or arrangement_node_id must be set
```

### 5.22 Audit Log

```sql
audit_log
  id BIGINT UNSIGNED AUTO_INCREMENT,
  user_id (FK users, nullable),
  action VARCHAR(200) NOT NULL,          -- e.g. 'document.create', 'document.delete'
  resource_type VARCHAR(100),
  resource_id BIGINT UNSIGNED,
  detail JSON,
  ip_address VARCHAR(45),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
  -- No updated_at; audit rows are immutable
```

All create, update, delete, and permission change operations must write an
audit row. This is non-negotiable.

### 5.23 Donor Agreements (AASLH requirement)

```sql
donor_agreements
  id,
  donor_id (FK authority_records) NOT NULL,
  agreement_date DATE,
  agreement_type ENUM('deed_of_gift','deposit','loan','purchase','transfer') NOT NULL,
  restrictions TEXT,
  embargo_end_date DATE,
  allows_reproduction BOOLEAN DEFAULT TRUE,
  allows_publication BOOLEAN DEFAULT TRUE,
  physical_items_description TEXT,
  agreement_document_path VARCHAR(2000),  -- path to scanned agreement file
  notes TEXT,
  created_by (FK users), created_at, updated_at
```

### 5.24 Preservation Events (PREMIS / OAIS requirement)

Records every preservation action taken on a digital object. Immutable rows only.
This is the application's implementation of PREMIS Event entities.

```sql
preservation_events
  id BIGINT UNSIGNED AUTO_INCREMENT,
  document_file_id (FK document_files, nullable),
  document_id (FK documents, nullable),
  event_type ENUM(
    'ingest',
    'fixity_check',
    'format_validation',
    'virus_scan',
    'ocr',
    'migration',
    'deletion',
    'access',
    'modification',
    'replication'
  ) NOT NULL,
  event_outcome ENUM('success','failure','warning') NOT NULL,
  event_detail TEXT,
  agent VARCHAR(200),                    -- user ID or system process name
  event_datetime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
  -- No updated_at; preservation events are immutable
```

A `preservation_events` row must be written for every ingest, every fixity check,
every OCR run, and every format validation. This is not optional.

### 5.25 Fixity Check Log (OAIS requirement)

```sql
fixity_checks
  id BIGINT UNSIGNED AUTO_INCREMENT,
  document_file_id (FK document_files) NOT NULL,
  checked_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  stored_hash CHAR(64) NOT NULL,
  computed_hash CHAR(64) NOT NULL,
  outcome ENUM('match','mismatch','file_missing') NOT NULL,
  checked_by VARCHAR(200)               -- 'celery_beat' or user ID
```

Any `mismatch` or `file_missing` outcome must:
1. Write a `preservation_events` row with `event_outcome = 'failure'`.
2. Create a `review_queue` entry with reason `integrity_failure` and priority `high`.
3. Set a dashboard alert flag visible to all admins.

The Celery beat schedule for fixity checks is configurable via system settings
(`fixity.schedule_cron`, default `0 2 * * 0` — weekly, Sunday at 2 AM).

### 5.26 Watch Folders (Consume Folder Ingest)

Historians frequently scan physical documents with sheet-fed scanners that deposit files
into a local folder or network share. Watch folders enable automatic ingest without
requiring manual uploads through the UI.

```sql
watch_folders
  id,
  name VARCHAR(200) NOT NULL,
  path VARCHAR(2000) NOT NULL,              -- path relative to STORAGE_ROOT
  target_node_id (FK arrangement_nodes, nullable),
  default_tags JSON,                        -- list of vocabulary_term IDs to auto-apply
  poll_interval_seconds INT DEFAULT 60,
  is_active BOOLEAN DEFAULT TRUE,
  created_by (FK users), created_at, updated_at
```

The Celery beat task `workers.ingest.poll_watch_folders` runs every 60 seconds for
each active watch folder. New files are moved to quarantine and processed through
the standard ingest pipeline (§6.2), then placed in the inbox queue.

### 5.27 Saved Views

Personal dashboard filter presets that eliminate repetitive search setup.

```sql
saved_views
  id,
  user_id (FK users) NOT NULL,
  name VARCHAR(200) NOT NULL,
  filter_params JSON NOT NULL,    -- same query params as GET /api/v1/search
  display_type ENUM('count','list','grid') DEFAULT 'list',
  sort_order INT DEFAULT 0,
  created_at, updated_at
```

### 5.28 Deaccession Log (AASLH requirement)

```sql
deaccession_log
  id,
  document_id BIGINT UNSIGNED NOT NULL,  -- preserved even after document is deleted
  accession_number VARCHAR(200),
  title VARCHAR(1000),
  deaccession_date DATE NOT NULL,
  reason_code_id (FK vocabulary_terms),
  reason_note TEXT NOT NULL,
  disposition ENUM('destroyed','transferred','returned','sold','donated') NOT NULL,
  transfer_destination TEXT,
  authorized_by (FK users) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
```

Deaccession is a workflow, not a delete endpoint. The lifecycle is:
`active → deaccession_proposed → deaccession_approved → deaccessed`

Tracked in `documents.deaccession_status ENUM('none','proposed','approved','complete')`.
The physical file is deleted only after the `deaccession_log` row is committed.
The `deaccession_log` row is never deleted.

### 5.29 Institution Description Standards

Each institution configures which document fields are required to reach each
completeness level. The system auto-computes `documents.description_completeness`
against these standards whenever a document is saved.

```sql
institution_description_standards
  id,
  level ENUM('minimal','standard','full') NOT NULL,
  required_fields JSON NOT NULL,
  -- Array of document field names that must be non-null/non-empty to reach this level.
  -- Example: ["title","date_display","creator_id","scope_and_content"]
  -- The 'title' field is always required regardless of institution settings.
  -- Fields that may legitimately be unknown (e.g. date) should only appear at
  -- 'standard' or 'full' levels, never 'minimal', per institution policy.
  notes TEXT,
  updated_by (FK users), updated_at
  -- One row per level; three rows total. Created during first-run setup.
```

The Celery task `workers.description.recompute_completeness(document_id)` runs
whenever a document's descriptive fields are updated. It evaluates the document
against each level in ascending order and sets `description_completeness` to the
highest level all required fields satisfy. Documents with only a title satisfy
`none`. A document meeting all `minimal` fields but not `standard` is `'minimal'`.

### 5.30 CSV Import Jobs

```sql
csv_imports
  id,
  filename VARCHAR(500) NOT NULL,
  import_mode ENUM('template','mapped') NOT NULL,
  status ENUM('uploaded','validating','validation_failed','ready','importing','complete','failed') DEFAULT 'uploaded',
  total_rows INT UNSIGNED DEFAULT 0,
  valid_rows INT UNSIGNED DEFAULT 0,
  warning_rows INT UNSIGNED DEFAULT 0,
  error_rows INT UNSIGNED DEFAULT 0,
  imported_rows INT UNSIGNED DEFAULT 0,
  target_node_id (FK arrangement_nodes, nullable),  -- default collection for imported documents
  column_mapping JSON,                              -- maps CSV column names to ADMS field names
  validation_report JSON,                           -- full per-row validation output
  new_vocabulary_terms JSON,                        -- terms auto-created during import
  created_by (FK users), created_at, updated_at

csv_import_rows
  id,
  import_id (FK csv_imports) NOT NULL,
  row_number INT UNSIGNED NOT NULL,
  raw_data JSON NOT NULL,               -- original CSV row as key-value pairs
  mapped_data JSON,                     -- after column mapping is applied
  document_id (FK documents, nullable), -- set after successful import of this row
  status ENUM('pending','valid','warning','error','imported','skipped') DEFAULT 'pending',
  messages JSON                         -- array of {level, field, message} objects
```

### 5.31 Document Annotations

Annotations are staff-only notes anchored to a specific location in a document.
They are strictly internal — never exposed on public routes or in any export format.
Public-facing contextual information belongs in `documents.general_note` or
`documents.scope_and_content`, not here.

Two annotation types are supported:
- `region` — a bounding box on a specific page image
- `text_range` — a highlighted span within the OCR text of a specific page

Both types share one table.

```sql
document_annotations
  id,
  document_id (FK documents) NOT NULL,
  document_file_id (FK document_files) NOT NULL,
  document_page_id (FK document_pages, nullable),  -- required for region and text_range types
  annotation_type ENUM('region','text_range') NOT NULL,
  -- Region annotation geometry (percentage-based, resolution-independent)
  -- Stored only when annotation_type = 'region'
  region_geometry JSON,
  -- { "x1": 12.5, "y1": 34.1, "x2": 45.0, "y2": 52.3 }
  -- All values are percentages (0–100) of image width/height
  -- Text range annotation (stored only when annotation_type = 'text_range')
  text_range JSON,
  -- { "start_offset": 142, "end_offset": 198, "quoted_text": "John Harrington" }
  -- Offsets are character positions within document_pages.ocr_text
  -- Content
  body TEXT NOT NULL,                   -- the annotation text
  -- State
  is_resolved BOOLEAN DEFAULT FALSE,    -- marks annotation as addressed/no longer active
  resolved_by (FK users, nullable),
  resolved_at DATETIME,
  created_by (FK users) NOT NULL,
  created_at, updated_at
```

**Constraints enforced in the application layer:**
- `region_geometry` must be present and `text_range` must be null when
  `annotation_type = 'region'`, and vice versa.
- Region geometry values must be numeric, between 0 and 100, with `x1 < x2`
  and `y1 < y2`.
- `text_range.start_offset` must be less than `text_range.end_offset`.
- `document_page_id` is required for both types.
- OCR text must exist on the page (`document_pages.ocr_text IS NOT NULL`) before
  a `text_range` annotation can be created.

---

## 6. File Storage

### 6.1 Path Resolution

Physical file paths on disk are computed from the active storage scheme and
are never stored as absolute paths. The `storage` service resolves a
`document_file.stored_path` (relative) against `STORAGE_ROOT` at runtime.

Path formats by scheme:

| Scheme | Path pattern |
|---|---|
| `date` | `{year}/{month}/{accession_number}/{filename}` |
| `location` | `{fonds_id}/{series_id}/{file_id}/{accession_number}/{filename}` |
| `donor` | `donors/{donor_slug}/{accession_number}/{filename}` |
| `subject` | `subjects/{category_slug}/{accession_number}/{filename}` |
| `record_number` | `records/{record_number_prefix}/{accession_number}/{filename}` |

All path components are sanitized: lowercased, spaces replaced with underscores,
non-alphanumeric characters (except `-` and `_`) removed.

### 6.2 Upload Flow

1. Client POSTs file to `POST /api/v1/documents/{id}/files`.
2. Backend validates MIME type (allow-list, not block-list), file size (configurable
   max, default 500 MB), and filename.
3. File is saved to a quarantine directory first: `{STORAGE_ROOT}/.quarantine/{uuid}`.
4. SHA-256 hash is computed; duplicate detection runs against `document_files.file_hash_sha256`.
5. Siegfried runs format characterization; PRONOM PUID, format name, and version are stored.
6. Preservation warnings are evaluated (low resolution, lossy-only format, etc.) and stored
   in `document_files.preservation_warning` if applicable. These are non-blocking.
7. File is moved to its resolved permanent path.
8. `document_files` row is inserted.
9. A `preservation_events` row is written with `event_type = 'ingest'`.
10. Celery tasks are queued: thumbnail generation, OCR (if enabled), LLM suggestion
    (if enabled and configured), format validation.

### 6.3 Supported File Types

The application is file-type neutral. Any file type may be stored. The following
types receive enhanced treatment:

| Type | Treatment |
|---|---|
| PDF | Page count extraction, per-page thumbnail, OCR |
| JPEG, PNG, TIFF, WebP | Thumbnail generation, OCR |
| TIFF | Special handling for multi-page TIFFs |
| Other | Stored as-is; no thumbnail or OCR |

MIME type is detected from file content (python-magic), not filename extension.

### 6.4 Thumbnails

- Stored at `{STORAGE_ROOT}/.thumbnails/{document_file_id}/{page_number}.webp`.
- Generated at 300px wide, maintaining aspect ratio.
- Use `pillow` for images; `pdf2image` (poppler) for PDFs.
- Missing thumbnails return a generic placeholder; do not 404.

---

## 7. Authentication and Permissions

### 7.1 Auth Flow

- JWT access tokens: 15-minute expiry, signed with `SECRET_KEY`.
- JWT refresh tokens: 30-day expiry, stored in `refresh_tokens` table.
- Both tokens delivered as `httpOnly`, `SameSite=Strict` cookies.
- No tokens in response bodies or localStorage.
- `POST /api/v1/auth/login` — issues both tokens.
- `POST /api/v1/auth/refresh` — issues new access token from refresh token.
- `POST /api/v1/auth/logout` — revokes refresh token.

### 7.2 Role Hierarchy (Global Defaults)

| Role | Default Capabilities |
|---|---|
| `superadmin` | All actions everywhere; cannot be restricted by collection permissions |
| `admin` | All actions on all collections; manage users and roles |
| `archivist` | Create, edit, describe documents in permitted collections; manage vocabulary |
| `contributor` | Create and edit documents in permitted collections; cannot delete |
| `intern` | Create documents in explicitly permitted collections only |
| `viewer` | Read-only access to permitted collections |

Global roles set the floor. Collection-level `collection_permissions` rows can
grant additional rights (e.g., elevate an intern on one collection) but cannot
elevate beyond the user's global role ceiling unless the user is a superadmin.

### 7.3 Permission Checks

All permission checks must go through a single `PermissionService` class.
Routers must not contain inline permission logic. The dependency `deps.require_permission`
accepts the required permission flag and the relevant resource.

---

## 8. OCR

### 8.1 Configuration

OCR is enabled/disabled via `OCR_ENABLED` env var. Language is set via
`OCR_LANGUAGE` (Tesseract language code, e.g., `eng`, `eng+fra`).
Parallelism is controlled by `OCR_WORKER_CONCURRENCY` (default 2) to prevent
memory exhaustion on low-RAM hosts during large ingest batches.

### 8.2 Processing

- OCR runs as a Celery task: `workers.ocr.process_file`.
- Input: `document_file_id`.
- For PDFs: convert each page to an image with `pdf2image`, then run Tesseract.
- For images: run Tesseract directly.
- Output: full-document OCR text written to `document_files.ocr_text`; per-page
  text written to `document_pages.ocr_text`.
- `document_files.ocr_status` transitions: `none → queued → processing → complete | failed`.
- On failure: store the exception message in `document_files.ocr_error`, increment
  `document_files.ocr_attempt_count`. Retry up to 3 times with exponential back-off.
  After 3 failures set status to `failed` — do not retry further without explicit user action.
- Full OCR text is indexed for full-text search (MySQL FULLTEXT index on
  `document_files.ocr_text`).
- A `preservation_events` row is written on OCR completion or final failure.

### 8.3 Manual Retry

If `ocr_status = 'failed'`, the document detail view must display the `ocr_error`
message and a "Retry OCR" button. Clicking it calls `POST /api/v1/documents/{id}/files/{fid}/retry-ocr`,
which resets `ocr_attempt_count` to 0, sets `ocr_status` to `queued`, and re-queues
the Celery task. Only users with edit permission on the document may trigger a retry.

---

## 9. LLM Integration

### 9.1 Provider Adapter

All LLM calls go through a provider-agnostic `LLMAdapter` interface defined in
`app/llm/base.py`. Concrete implementations: `OpenAIAdapter`, `AnthropicAdapter`,
`OllamaAdapter`. The active adapter is selected at startup from `LLM_PROVIDER`.
If `LLM_PROVIDER` is empty or `none`, LLM features are silently disabled.

```python
# app/llm/base.py
class LLMAdapter(ABC):
    async def suggest_metadata(
        self,
        ocr_text: str,
        file_bytes: bytes | None,
        mime_type: str,
        enabled_fields: list[str],
    ) -> dict[str, Any]: ...
```

### 9.2 Institution LLM Settings

Administrators configure LLM behavior in the admin UI. Settings are stored in
a `system_settings` table (key-value, JSON value):

```sql
system_settings
  id, key VARCHAR(200) UNIQUE, value JSON, updated_by (FK users), updated_at
```

Relevant keys:
- `llm.provider` — overrides env var at runtime if set
- `llm.enabled_suggestion_fields` — list of document fields the LLM may suggest
- `llm.require_review` — boolean; if true, all LLM suggestions go to review queue
- `llm.auto_apply_threshold` — float 0–1; confidence above which suggestions
  are auto-applied without review (only used if `require_review` is false)

### 9.3 Suggestion Fields

The following document fields may be enabled for LLM suggestion (all off by default):
`title`, `date_display`, `date_start`, `date_end`, `creator` (matched to authority_records),
`scope_and_content`, `language_of_material`, `document_type`, `extent`, `tags`, `general_note`.

### 9.4 Suggestion Workflow

1. Celery task `workers.llm.suggest_metadata` runs after OCR completes (or immediately
   if OCR is disabled) using the OCR text and/or raw file bytes.
2. LLM response is stored in `documents.llm_suggestions` (JSON) for audit purposes.
3. If `require_review` is true: document `review_status` is set to `pending`;
   a row is created in `review_queue` with reason `llm_suggestions`.
4. If `require_review` is false and confidence meets threshold: suggestions are
   auto-applied; audit log entry written.
5. The review UI shows the original value, the suggested value, and a confidence
   score (if provided by the LLM) for each field. The reviewer can accept, edit,
   or reject each field independently.

---

## 10. Search and Browsing

### 10.1 Browse Modes

The frontend must support all of the following browse modes simultaneously.
Browse mode does not affect physical storage; it affects how the UI surfaces documents.

| Mode | Description |
|---|---|
| Hierarchy | Tree view mirroring `arrangement_nodes` (Fonds → ... → Item) |
| Donor | Group by authority record of type `person` or `organization` |
| Subject | Group by `subject_category` vocabulary terms |
| Date | Timeline/decade view using `documents.date_start` |
| Record Number | Sequential list by `accession_number` |

### 10.2 Search API

`GET /api/v1/search` accepts:

| Parameter | Type | Description |
|---|---|---|
| `q` | string | Full-text query (searches title, OCR text, scope_and_content, notes) |
| `creator_id` | int | Filter by authority record |
| `date_from` | date | Filter by date_start |
| `date_to` | date | Filter by date_end |
| `term_ids` | int[] | Filter by vocabulary term IDs (AND) |
| `authority_ids` | int[] | Filter by linked authority records (any role, including creator) |
| `location_ids` | int[] | Filter by linked location records |
| `event_ids` | int[] | Filter by linked events |
| `node_id` | int | Filter to a subtree of arrangement_nodes |
| `document_type` | string | Vocabulary term in document_type domain |
| `language` | string | ISO 639 code |
| `review_status` | enum | Filter by review status |
| `is_public` | bool | Filter public/private |
| `page` | int | Default 1 |
| `per_page` | int | Default 25, max 100 |

Full-text search uses MySQL `MATCH ... AGAINST` in natural language mode across
a FULLTEXT index on `(title, scope_and_content, general_note)` on the `documents`
table, plus a separate FULLTEXT index on `ocr_text` in `document_files`.
Results are unioned and ranked by relevance score.

**Version filter:** All search and browse queries automatically restrict to documents
where `version_group_id IS NULL OR is_canonical_version = TRUE`. Non-canonical versions
are never returned in search results. A researcher can retrieve a specific non-canonical
version by exact accession number lookup: `GET /api/v1/documents?accession=2025-0042.2`.

---

## 11. Citation and Metadata Export

### 11.1 Citation Formats

| Format | Endpoint |
|---|---|
| Chicago (note) | `GET /api/v1/documents/{id}/cite?format=chicago_note` |
| Chicago (bibliography) | `GET /api/v1/documents/{id}/cite?format=chicago_bib` |
| Turabian | `GET /api/v1/documents/{id}/cite?format=turabian` |
| BibTeX | `GET /api/v1/documents/{id}/cite?format=bibtex` |
| RIS | `GET /api/v1/documents/{id}/cite?format=ris` |
| Zotero RDF | `GET /api/v1/documents/{id}/cite?format=zotero_rdf` |
| CSL-JSON | `GET /api/v1/documents/{id}/cite?format=csl_json` |

Bulk export: `POST /api/v1/cite/bulk` accepts a list of document IDs and a format,
returns a single file (`.bib`, `.ris`, or JSON array).

### 11.2 Metadata Export Formats

| Format | Endpoint | Notes |
|---|---|---|
| Dublin Core XML | `GET /api/v1/documents/{id}/export?format=dc_xml` | DCMI `oai_dc` schema |
| Dublin Core JSON | `GET /api/v1/documents/{id}/export?format=dc_json` | For API consumers |
| EAD3 XML | `GET /api/v1/nodes/{id}/export?format=ead3` | Collection-level subtree |
| CSV | `GET /api/v1/nodes/{id}/export?format=csv` | Flat spreadsheet import/export |
| METS | `GET /api/v1/documents/{id}/export?format=mets` | Phase 2 — out of scope now |

All export formats are generated by modules in `app/export/`. The Dublin Core export
module is at `app/export/dublin_core.py` and uses the crosswalk defined in §22.

### 11.3 Zotero Integration

`POST /api/v1/documents/{id}/cite/zotero-push` pushes the document to the user's
Zotero library via the Zotero API. User must configure their Zotero User ID and
API key in their profile settings (stored encrypted in `user_settings` table).

### 11.4 Citation Metadata Mapping

Citation formatters live in `app/export/citations.py`. They map from the
`Document` model to each citation format. Use `citeproc-py` for CSL-based formats.
Map ADMS fields to CSL-JSON fields as the intermediate representation, then
render to target formats from CSL-JSON. The Dublin Core crosswalk (§22) is used
as the shared mapping layer wherever DC fields overlap with citation fields.

### 11.5 LLM Must Never Auto-Apply Date Fields

The LLM suggestion pipeline must never automatically commit `date_display`,
`date_start`, or `date_end` to the database without explicit human review,
regardless of confidence threshold settings. Date fields are too frequently
incorrect (OCR picks up incidental dates in document body text rather than
the document's actual creation date) to be auto-applied. The LLM may suggest
dates, but those suggestions must always enter the review queue.

---

## 12. Public Exhibition Site

The public exhibition system is modeled on the capabilities of Omeka S's Exhibit Builder,
with an architecture suited to ADMS's data model. The key structural difference from the
original spec is that exhibitions are organized as a hierarchy of **pages**, each composed
of **content blocks** — not a flat list of items. This enables full narrative exhibit design.

### 12.1 Architecture

The public site is served by the same frontend application at a separate
route prefix (`/public`). It reads from the same API via a separate router
prefix (`/api/v1/public`). All public API endpoints require no authentication
and return only records where `is_public = TRUE`.

The institution is responsible for setting up a reverse proxy (nginx, Traefik,
Caddy) to expose the public routes externally while keeping admin routes internal
or protected. ADMS does not manage TLS or external routing.

### 12.2 Schema: Exhibitions (Revised)

The original flat `exhibition_items` table is replaced by a page+block hierarchy.

```sql
exhibitions
  id,
  title VARCHAR(500) NOT NULL,
  slug VARCHAR(200) UNIQUE NOT NULL,
  subtitle VARCHAR(500),
  description TEXT,                          -- intro text shown on summary page
  credits TEXT,                              -- public acknowledgment of contributors
  cover_image_path VARCHAR(2000),
  header_image_path VARCHAR(2000),           -- banner image displayed on all pages
  accent_color VARCHAR(7),                   -- hex color for per-exhibit theming (e.g. #8B1A1A)
  show_summary_page BOOLEAN DEFAULT TRUE,    -- if false, goes straight to first page
  is_published BOOLEAN DEFAULT FALSE,
  published_at DATETIME,
  sort_order INT DEFAULT 0,
  created_by (FK users), created_at, updated_at

exhibition_tags
  id, exhibition_id (FK exhibitions), term_id (FK vocabulary_terms),
  UNIQUE KEY (exhibition_id, term_id)
  -- term_id must belong to the 'tag' vocabulary domain

exhibition_pages
  id,
  exhibition_id (FK exhibitions) NOT NULL,
  parent_page_id (FK self, nullable),        -- enables parent/child page nesting
  title VARCHAR(500) NOT NULL,
  slug VARCHAR(200) NOT NULL,
  menu_title VARCHAR(200),                   -- shorter title for sidebar navigation
  is_public BOOLEAN DEFAULT TRUE,
  sort_order INT DEFAULT 0,
  created_at, updated_at
  UNIQUE KEY (exhibition_id, slug)

exhibition_page_blocks
  id,
  page_id (FK exhibition_pages) NOT NULL,
  block_type ENUM(
    'html',               -- rich narrative text (HTML, sanitized server-side)
    'file_with_text',     -- one document file + text, side by side
    'gallery',            -- grid of document file thumbnails
    'document_metadata',  -- document file viewer + full public metadata display
    'map',                -- interactive map of geolocated documents
    'timeline',           -- chronological display of documents by date_start
    'table_of_contents',  -- auto-generated from exhibition_pages hierarchy
    'collection_browse',  -- grid browse of a collection (arrangement_node subtree)
    'separator'           -- visual line break
  ) NOT NULL,
  content JSON NOT NULL,    -- block-type-specific configuration (see §12.5)
  layout ENUM('full','left','right','center') DEFAULT 'full',
  sort_order INT DEFAULT 0,
  created_at, updated_at
```

The old `exhibition_items` table is removed. All item attachment is handled through
`exhibition_page_blocks.content` JSON for block types that reference documents.

### 12.3 Schema: Document Geolocation (new field)

To support map blocks, documents may be geolocated. Add to the `documents` table:

```sql
-- Add to documents table:
geo_latitude DECIMAL(9,6),
geo_longitude DECIMAL(9,6),
geo_location_name VARCHAR(500)   -- human-readable place name (e.g. "Falls Church, VA")
```

These fields are optional. Documents without coordinates are simply omitted from map blocks.

### 12.4 Schema: Static Narrative Pages (Omeka's "Simple Pages")

Free-standing public pages for About, Credits, Copyright, project descriptions, or essays.
These are independent of exhibitions.

```sql
public_pages
  id,
  title VARCHAR(500) NOT NULL,
  slug VARCHAR(200) UNIQUE NOT NULL,
  body_html TEXT NOT NULL,              -- sanitized HTML; edited via rich text editor
  is_published BOOLEAN DEFAULT FALSE,
  show_in_navigation BOOLEAN DEFAULT TRUE,
  sort_order INT DEFAULT 0,
  created_by (FK users), created_at, updated_at
```

### 12.5 Block Content JSON Specification

Each block type stores its configuration in `exhibition_page_blocks.content` as JSON.
The following defines the required and optional keys for each block type. Claude Code
must validate these structures when writing the block service.

```
html:
  { "html": "<p>...</p>" }
  -- html value is run through bleach/DOMPurify before storage

file_with_text:
  {
    "document_id": 123,
    "file_id": 456,          -- optional; defaults to first file
    "caption": "...",
    "text_html": "<p>...</p>",
    "image_position": "left" | "right"
  }

gallery:
  {
    "items": [
      { "document_id": 123, "file_id": 456, "caption": "..." },
      ...
    ],
    "columns": 2 | 3 | 4,
    "show_captions": true | false
  }

document_metadata:
  {
    "document_id": 123,
    "show_citation": true | false,
    "show_download": true | false,
    "show_transcription": true | false    -- shows OCR text if available
  }

map:
  {
    "center_lat": 38.88,
    "center_lon": -77.17,
    "zoom": 10,
    "document_ids": [123, 456, ...],      -- explicit list, OR use query below
    "query": {                            -- optional dynamic query instead of explicit list
      "term_ids": [1, 2],
      "node_id": 5,
      "date_from": "1900-01-01",
      "date_to": "1950-12-31"
    },
    "show_popups": true,                  -- popup with title + thumbnail on pin click
    "basemap": "openstreetmap" | "satellite"
  }

timeline:
  {
    "document_ids": [...],                -- explicit list, OR use query
    "query": { ... },                     -- same structure as map query
    "title_field": "title",              -- which document field to use as timeline label
    "date_field": "date_start" | "date_display",
    "show_descriptions": true | false
  }

table_of_contents:
  { "depth": 1 | 2 | 3 }               -- how many levels of child pages to show

collection_browse:
  {
    "node_id": 5,                        -- arrangement_node to browse
    "display": "grid" | "list",
    "per_page": 12,
    "show_metadata": true | false
  }

separator:
  { "style": "solid" | "dashed" | "blank" }
```

### 12.6 Public Document Rules

A document is visible on the public site only if ALL of the following are true:
1. `documents.is_public = TRUE`
2. `documents.embargo_end_date` is null OR is in the past
3. The document's `arrangement_node` has `is_public = TRUE` at every ancestor level,
   OR `is_public` is explicitly set to TRUE on the document itself independently
4. The exhibition page (if accessed through one) has `is_public = TRUE` and the
   parent exhibition has `is_published = TRUE`

Individual document pages are shown/hidden by `document_pages.is_public`. If a page is
not public, its thumbnail and OCR text are withheld; the page number still appears
so visitors know pages exist.

### 12.7 Public API Endpoints

```
GET /api/v1/public/exhibitions                         — list published exhibitions
GET /api/v1/public/exhibitions/{slug}                  — exhibition summary + page tree
GET /api/v1/public/exhibitions/{slug}/pages/{page-slug} — single page with its blocks resolved
GET /api/v1/public/documents/{id}                      — public document with metadata
GET /api/v1/public/documents/{id}/files/{fid}          — serve public document file
GET /api/v1/public/documents/{id}/pages                — public document pages
GET /api/v1/public/search                              — search public documents
GET /api/v1/public/authority/{id}                      — public authority record
GET /api/v1/public/collections                         — public collection browse
GET /api/v1/public/collections/{node_id}               — public collection detail
GET /api/v1/public/pages                               — list static narrative pages
GET /api/v1/public/pages/{slug}                        — static narrative page content
GET /api/v1/public/locations                           — browse public locations
GET /api/v1/public/locations/{id}                      — public location with linked documents/events
GET /api/v1/public/events                              — browse public events
GET /api/v1/public/events/{id}                         — public event with documents, people, places
```

For the map block, the API must also accept the map query parameters dynamically:
`GET /api/v1/public/map-items?term_ids=1,2&node_id=5&date_from=1900-01-01`

### 12.8 Exhibition Builder UI (Admin)

The admin UI for building exhibitions must closely mirror Omeka's exhibit builder workflow.
Claude Code must implement the following admin pages:

```
/exhibitions/{id}/edit
  — Edit exhibition metadata (title, description, credits, cover image, accent color,
    summary page toggle, publish toggle)

/exhibitions/{id}/pages
  — Page tree view with drag-and-drop reordering
  — Add page button; child pages shown indented below parent
  — Each page shows title, slug, visibility toggle, edit and delete buttons

/exhibitions/{id}/pages/{page_id}/edit
  — Page title, menu title, slug, visibility toggle
  — Block editor: list of current blocks with drag-to-reorder handles
  — "Add block" button opens a block type picker (icon + label for each type)
  — Each block has an inline edit form appropriate to its type:
    * html: rich text editor (use Quill or similar; no external CDN)
    * file_with_text: document picker + text editor + position toggle
    * gallery: multi-document picker with drag-to-reorder
    * document_metadata: document picker with display option checkboxes
    * map: lat/lon/zoom controls + document picker or query builder
    * timeline: document picker or query builder + display options
    * table_of_contents: depth selector
    * collection_browse: node picker + display options
    * separator: style selector
  — "Preview" button opens the public page in a new tab

/exhibitions/{id}/pages/{page_id}/preview
  — Live preview of the page as the public will see it
```

### 12.9 Public Exhibition UI

The public site must implement the following pages:

```
/public
  — Institution landing page: name, logo, tagline (from system_settings)
  — Grid of published exhibitions with cover images
  — Featured documents section (manually curated via system_settings)
  — Links to static narrative pages in navigation

/public/exhibits
  — Browse all published exhibitions; filter by tag

/public/exhibits/{slug}
  — Exhibition summary page (if show_summary_page = true):
    header image, title, subtitle, description, credits, page navigation menu
  — OR redirects to first page if show_summary_page = false

/public/exhibits/{slug}/{page-slug}
  — Exhibition page with rendered blocks
  — Sidebar navigation showing page hierarchy (parent/child)
  — Previous/next page navigation at bottom
  — Exhibition title and breadcrumb at top

/public/documents/{id}
  — Document detail: full-width file viewer (paginated images or PDF embed)
  — Metadata panel: all public ISAD(G) fields
  — Creator link to authority record
  — Related documents (from document_relationships)
  — Tags with browse-by-tag links
  — Citation widget with format selector (Chicago, Turabian, BibTeX, RIS)
  — If geolocated: small embedded map showing document origin

/public/collections
  — Browse public arrangement_nodes (fonds/series level)

/public/collections/{node_id}
  — Collection detail: description, date range, document grid

/public/search
  — Full-text search with faceted filtering:
    document type, date range, creator, language, subject tags
  — Results show thumbnail, title, date, collection

/public/pages/{slug}
  — Static narrative page

/public/authority/{id}
  — Authority record detail: name, dates, biography/history,
    linked documents the person created or appears in
```

### 12.10 Public Site: Technical Requirements

**Accessibility**
The public site must conform to WCAG 2.2 Level AA. Full requirements are specified
in §31. The public site is subject to all the same requirements as the authenticated
application. There are no reduced accessibility obligations for the public interface.

Key items that apply specifically to the public site:
- Every public document page must have `lang="{code}"` on the `<html>` element,
  derived from `documents.language_of_material` when that field is set.
- The `/public` site must function completely without any cookie, token, or session
  (including for accessibility features — no login required to use keyboard navigation,
  screen reader support, or reduced-motion preferences).
- Document images must have meaningful alt text per §31.7.
- The OCR transcript must be available as a text alternative per §31.7.
- Map blocks must have keyboard controls and a text list alternative per §31.8.

---

## 13. NoCoDB Integration

### 13.1 Configuration

NoCoDB connects to the same MySQL instance as the backend. Set NoCoDB's `NC_DB`
environment variable in `docker-compose.yml`:

```
NC_DB=mysql2://db:3306?u=${MYSQL_USER}&p=${MYSQL_PASSWORD}&d=${MYSQL_DATABASE}
```

NoCoDB will auto-discover all tables. No NoCoDB-specific schema changes are
needed — all tables are designed to be fully browsable in NoCoDB out of the box.

### 13.2 NoCoDB Use Cases

- Archivists add biographical history to `authority_records` directly in NoCoDB.
- Administrators audit `audit_log` in NoCoDB.
- Bulk metadata corrections via NoCoDB's spreadsheet view.
- Building custom views and filters for reporting.

### 13.3 Write Safety

NoCoDB users editing records directly bypass the application's business logic,
permission checks, and audit log. Document this clearly in the admin UI and in
deployment documentation. Recommend that only admin-level users access NoCoDB.
The following columns must be marked read-only in NoCoDB via field configuration:
`document_files.stored_path`, `document_files.file_hash_sha256`,
`document_files.ocr_status`, `users.password_hash`, `refresh_tokens.*`.

---

## 14. API Design

### 14.1 Conventions

- All routes are prefixed `/api/v1/`.
- JSON request and response bodies only (except file uploads: `multipart/form-data`).
- HTTP status codes: 200 OK, 201 Created, 204 No Content, 400 Bad Request,
  401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Unprocessable Entity,
  500 Internal Server Error.
- Errors return `{ "detail": "human-readable message", "code": "machine_code" }`.
- Pagination: `{ "items": [...], "total": N, "page": N, "per_page": N, "pages": N }`.
- All datetime fields are ISO 8601 with UTC timezone.

### 14.2 Core Resource Endpoints

```
# Auth
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
POST   /api/v1/auth/refresh

# Users (admin only)
GET    /api/v1/users
POST   /api/v1/users
GET    /api/v1/users/{id}
PATCH  /api/v1/users/{id}
DELETE /api/v1/users/{id}
POST   /api/v1/users/{id}/roles

# Arrangement
GET    /api/v1/nodes                    — tree or flat list
POST   /api/v1/nodes
GET    /api/v1/nodes/{id}
PATCH  /api/v1/nodes/{id}
DELETE /api/v1/nodes/{id}
GET    /api/v1/nodes/{id}/documents

# Documents
GET    /api/v1/documents
POST   /api/v1/documents
GET    /api/v1/documents/{id}
PATCH  /api/v1/documents/{id}
DELETE /api/v1/documents/{id}
POST   /api/v1/documents/{id}/files
GET    /api/v1/documents/{id}/files/{file_id}/download        — download with XMP metadata embedded by default
DELETE /api/v1/documents/{id}/files/{file_id}
GET    /api/v1/documents/{id}/pages
PATCH  /api/v1/documents/{id}/pages/{page_id}
GET    /api/v1/documents/{id}/relationships
POST   /api/v1/documents/{id}/relationships
DELETE /api/v1/documents/{id}/relationships/{rel_id}
GET    /api/v1/documents/{id}/authority-links   — people linked to this document (non-creator)
POST   /api/v1/documents/{id}/authority-links
PATCH  /api/v1/documents/{id}/authority-links/{link_id}
DELETE /api/v1/documents/{id}/authority-links/{link_id}
GET    /api/v1/documents/{id}/location-links    — locations mentioned in this document
POST   /api/v1/documents/{id}/location-links
DELETE /api/v1/documents/{id}/location-links/{link_id}
GET    /api/v1/documents/{id}/events            — events this document is linked to
GET    /api/v1/documents/{id}/annotations     — staff only; 403 if viewer role
POST   /api/v1/documents/{id}/annotations
PATCH  /api/v1/documents/{id}/annotations/{ann_id}
DELETE /api/v1/documents/{id}/annotations/{ann_id}
POST   /api/v1/documents/{id}/annotations/{ann_id}/resolve
POST   /api/v1/documents/{id}/annotations/{ann_id}/reopen
POST   /api/v1/documents/{id}/run-ner         — trigger NER pipeline on this document

# Review Queue
GET    /api/v1/review
GET    /api/v1/review/{document_id}
POST   /api/v1/review/{document_id}/approve
POST   /api/v1/review/{document_id}/reject
PATCH  /api/v1/review/{document_id}/assign

# Authority Records
GET    /api/v1/authority
POST   /api/v1/authority
GET    /api/v1/authority/{id}
PATCH  /api/v1/authority/{id}
DELETE /api/v1/authority/{id}
GET    /api/v1/authority/{id}/documents       — documents where this record is creator
GET    /api/v1/authority/{id}/document-links  — all document links (any role)
GET    /api/v1/authority/{id}/relationships   — authority-to-authority relationships
POST   /api/v1/authority/{id}/relationships
DELETE /api/v1/authority/{id}/relationships/{rel_id}
GET    /api/v1/authority/{id}/events          — events this authority is linked to
GET    /api/v1/authority/{id}/wikidata        — fetch live Wikidata enrichment
POST   /api/v1/authority/{id}/wikidata/link
DELETE /api/v1/authority/{id}/wikidata/link
GET    /api/v1/authority/ner-suggestions
POST   /api/v1/authority/ner-suggestions/{id}/accept
POST   /api/v1/authority/ner-suggestions/{id}/reject

# Locations
GET    /api/v1/locations
POST   /api/v1/locations
GET    /api/v1/locations/{id}
PATCH  /api/v1/locations/{id}
DELETE /api/v1/locations/{id}
GET    /api/v1/locations/{id}/documents       — all documents linking to this location
GET    /api/v1/locations/{id}/events          — events at this location

# Events
GET    /api/v1/events
POST   /api/v1/events
GET    /api/v1/events/{id}
PATCH  /api/v1/events/{id}
DELETE /api/v1/events/{id}
GET    /api/v1/events/{id}/documents
POST   /api/v1/events/{id}/documents
DELETE /api/v1/events/{id}/documents/{link_id}
GET    /api/v1/events/{id}/authorities
POST   /api/v1/events/{id}/authorities
DELETE /api/v1/events/{id}/authorities/{link_id}
GET    /api/v1/events/{id}/locations
POST   /api/v1/events/{id}/locations
DELETE /api/v1/events/{id}/locations/{link_id}

# Vocabulary
GET    /api/v1/vocabulary/domains
POST   /api/v1/vocabulary/domains
GET    /api/v1/vocabulary/domains/{domain_id}/terms
POST   /api/v1/vocabulary/domains/{domain_id}/terms
PATCH  /api/v1/vocabulary/terms/{id}
DELETE /api/v1/vocabulary/terms/{id}
POST   /api/v1/vocabulary/terms/{id}/merge  — merge this term into another; body: { "into_term_id": N }

# CSV Import
GET    /api/v1/admin/imports/template        — download ADMS CSV template
GET    /api/v1/admin/imports
POST   /api/v1/admin/imports                 — upload CSV and begin validation
GET    /api/v1/admin/imports/{id}            — import job status + validation report
POST   /api/v1/admin/imports/{id}/confirm    — execute import after review
DELETE /api/v1/admin/imports/{id}            — discard import job

# Reports
GET    /api/v1/reports/accessions            — new accessions by date range
GET    /api/v1/reports/processing            — description completeness by collection
GET    /api/v1/reports/users                 — documents created/updated per user
GET    /api/v1/reports/collection            — full collection summary
GET    /api/v1/reports/public-access         — published items and exhibitions

# Persistent URL resolution (public; no auth required)
GET    /d/{accession_number}                 — resolves to public document or tombstone
GET    /ark/{naan}/{id}                      — ARK resolution (if NAAN configured)

# Exhibitions
GET    /api/v1/exhibitions
POST   /api/v1/exhibitions
GET    /api/v1/exhibitions/{id}
PATCH  /api/v1/exhibitions/{id}
DELETE /api/v1/exhibitions/{id}
GET    /api/v1/exhibitions/{id}/pages
POST   /api/v1/exhibitions/{id}/pages
GET    /api/v1/exhibitions/{id}/pages/{page_id}
PATCH  /api/v1/exhibitions/{id}/pages/{page_id}
DELETE /api/v1/exhibitions/{id}/pages/{page_id}
POST   /api/v1/exhibitions/{id}/pages/{page_id}/blocks
PATCH  /api/v1/exhibitions/{id}/pages/{page_id}/blocks/{block_id}
DELETE /api/v1/exhibitions/{id}/pages/{page_id}/blocks/{block_id}
POST   /api/v1/exhibitions/{id}/pages/{page_id}/blocks/reorder

# Search
GET    /api/v1/search

# Citation
GET    /api/v1/documents/{id}/cite
POST   /api/v1/cite/bulk
POST   /api/v1/documents/{id}/cite/zotero-push
GET    /api/v1/nodes/{id}/cite           — archival collection-level citation

# Interoperability Exports (SAA/EAD, Dublin Core, OAI-PMH)
GET    /api/v1/nodes/{id}/export?format=ead3    — EAD3 XML for a collection subtree
GET    /api/v1/nodes/{id}/export?format=csv
GET    /api/v1/documents/{id}/export?format=dc_xml
GET    /oai                                      — OAI-PMH 2.0 endpoint

# System Settings (admin only)
GET    /api/v1/settings
PATCH  /api/v1/settings

# Preservation (OAIS/PREMIS)
GET    /api/v1/admin/format-inventory            — format distribution across repository
GET    /api/v1/admin/fixity-report               — fixity check results summary
POST   /api/v1/admin/fixity-run                  — trigger on-demand fixity check
GET    /api/v1/documents/{id}/preservation-events

# Document availability (tombstone management)
POST   /api/v1/documents/{id}/make-unavailable
POST   /api/v1/documents/{id}/restore

# Deaccession (AASLH requirement)
POST   /api/v1/documents/{id}/deaccession/propose
POST   /api/v1/documents/{id}/deaccession/approve
POST   /api/v1/documents/{id}/deaccession/execute
GET    /api/v1/admin/deaccession-log

# Permissions
GET    /api/v1/nodes/{id}/permissions
POST   /api/v1/nodes/{id}/permissions
DELETE /api/v1/nodes/{id}/permissions/{perm_id}
```

---

## 15. Frontend Pages

### 15.1 Authenticated Application

```
/login
/dashboard                     — recent activity, review queue count, stats
/archive                       — browse by hierarchy (tree nav + document list)
/archive/browse/donor          — browse by creator/donor
/archive/browse/subject        — browse by subject category
/archive/browse/date           — timeline browse
/archive/browse/location       — browse by linked location
/archive/browse/event          — browse by linked event
/archive/nodes/{id}            — collection/series/file detail
/archive/documents/new         — create document
/archive/inbox                 — inbox queue: all unprocessed documents for current user
/archive/documents/{id}        — document detail view
/archive/documents/{id}/edit   — edit metadata
/archive/documents/{id}/files  — manage files, view pages, split pages
/archive/documents/{id}/versions — version panel: all versions in group, set canonical/public
/review                        — review queue list
/review/{documentId}           — review a single document (side-by-side LLM suggestions)
/people                        — authority records list
/people/{id}                   — authority record detail: documents, events, relationships
/locations                     — location entity list
/locations/new                 — create location
/locations/{id}                — location detail: documents, events, map
/locations/{id}/edit           — edit location
/events                        — event list
/events/new                    — create event
/events/{id}                   — event detail: documents, people, locations, timeline
/events/{id}/edit              — edit event
/vocabulary                    — controlled vocabulary management
/exhibitions                   — exhibition management list
/exhibitions/new               — create exhibition
/exhibitions/{id}/edit         — edit exhibition metadata
/exhibitions/{id}/pages        — page tree manager
/exhibitions/{id}/pages/{pid}/edit — block editor (Omeka-style page builder)
/exhibitions/{id}/pages/{pid}/preview — live preview as public user
/search                        — full-text + faceted search
/admin/users                   — user management
/admin/roles                   — role management
/admin/settings                — system settings (LLM config, storage scheme, accession format, fixity schedule)
/admin/storage                 — storage scheme configuration
/admin/nocodb                  — link to NoCoDB instance + documentation
/admin/preservation            — format inventory, fixity report, preservation event log
/admin/deaccession             — deaccession log and workflow queue
/admin/donor-agreements        — donor agreement management
/admin/watch-folders           — watch folder configuration
/admin/imports                 — CSV import job list
/admin/imports/new             — upload CSV and begin import workflow
/admin/imports/{id}            — import validation report and confirm/discard
/admin/reports                 — report selection landing page
/admin/reports/accessions      — accession report
/admin/reports/processing      — processing progress report
/admin/reports/users           — user activity report
/admin/reports/collection      — collection summary report
/admin/reports/public-access   — public access summary report
```

### 15.2 Public Site

```
/public                        — institution landing page + published exhibitions grid
/public/exhibits               — browse all exhibitions, filterable by tag
/public/exhibits/{slug}        — exhibition summary page (or first page if no summary)
/public/exhibits/{slug}/{page-slug} — exhibition page with rendered blocks
/public/documents/{id}         — document detail with file viewer + metadata + citation
/public/collections            — browse public collection hierarchy
/public/collections/{node_id}  — collection detail
/public/search                 — full-text + faceted search
/public/pages/{slug}           — static narrative page (About, Credits, etc.)
/public/authority/{id}         — public authority record with linked documents
/public/locations              — browse public locations
/public/locations/{id}         — location detail: documents, events, map
/public/events                 — browse public events
/public/events/{id}            — event detail: documents, people, places
```

### 15.3 UI Requirements

- The authenticated app and the public site share no session state.
- Navigation must clearly indicate the current user's name and role.
- The inbox count (documents with `inbox_status = 'inbox'` in the user's accessible
  collections) must be prominently displayed in the navigation at all times.
- The review queue count must be visible in the navigation when the user has
  documents awaiting review.
- The document list view must support multi-select checkboxes. When one or more
  documents are selected, a bulk action toolbar must appear with the following actions:
  apply/remove terms, assign collection, set public flag, clear inbox, add to review
  queue, export as ZIP, and delete (admin only with confirmation).
- The document detail view must display a version panel whenever the document belongs
  to a version group (§20.6). The panel shows all versions with their labels, canonical
  and public status indicators, and a one-click "Set as canonical" or "Set as public"
  action for users with sufficient permissions. For unversioned documents with no group,
  the panel shows a "Create version group" button instead.
- The document file viewer page must show OCR status clearly. If OCR has failed,
  the error message must be displayed and a "Retry OCR" button must be visible.
  If OCR is in progress, show a progress indicator, not a blank panel.
- The document detail view must display a full-resolution file viewer:
  paginated image viewer for image files, embedded PDF viewer for PDFs.
- All forms must validate client-side before submitting; display server
  validation errors inline next to the relevant fields.
- Loading states and error boundaries are required on all data-fetching pages.
- Do not use `alert()` or `confirm()` dialogs; use a toast notification system
  and modal confirmation dialogs built with Tailwind.

---

## 16. Coding Standards

### 16.1 Python

- Python 3.12+. All type hints required. No bare `except:`.
- `pyproject.toml` manages dependencies (not `requirements.txt`).
- Linting: `ruff`. Formatting: `black`. Type checking: `mypy --strict`.
- Docstrings on all public functions and classes. Explain *why*, not *what*.
  Include parameter descriptions for any non-obvious argument.
- No TODO comments. Unfinished work is a failing test or a filed issue.
- SQL injection prevention: use SQLAlchemy parameterized queries only.
  Never interpolate user input into query strings.
- All file I/O must go through `app/storage/`. No raw `open()` calls in
  routers or services.
- XMP metadata embedding uses `pikepdf` for PDFs and `Pillow` for images.
  The `embed_metadata` worker must never modify the stored original; it writes
  to a temporary file and streams it to the client.
- Document splitting uses `pikepdf` for PDFs and `Pillow` for multi-page TIFFs.
  The original file is never modified; splitting creates new files.
- All secrets come from `app/config.py` (Pydantic Settings). Never access
  `os.environ` directly in application code.

### 16.2 TypeScript / React

- TypeScript strict mode. No `any` except in type narrowing with a comment.
- JSDoc on all exported functions and components. Explain *why* a component
  exists, not what React already makes obvious.
- No TODO comments.
- All API calls go through `src/api/`. No raw `fetch()` calls in components.

**State management — three layers with distinct responsibilities:**

| Layer | Tool | What goes here |
|---|---|---|
| Server state | React Query (TanStack Query) | All data fetched from the backend. Caching, background refetch, invalidation. |
| Client global state | Zustand (`src/stores/`) | Auth token + current user, inbox count, sidebar state, toast queue, active theme. |
| Component state | `useState` / `useReducer` | Form field values, UI toggles, local loading states. |
| Rare shared values | React Context (`src/context/`) | Theme object, institution settings — values that change infrequently and need no async logic. |

**Redux is not used in this project.** The combination of React Query and Zustand
handles every state management requirement with less boilerplate. Do not introduce
Redux or any Redux-adjacent library (Redux Toolkit, Recoil, Jotai as a Redux substitute).
If a future requirement genuinely cannot be met by React Query + Zustand, it must
be raised for explicit approval before any Redux code is written.

**Frontend services layer (`src/services/`):**
Business logic that is complex enough to test in isolation but does not belong
in a hook or component belongs in a service module. Services are pure TypeScript
functions — no React, no side effects, no direct API calls. Examples:

- `citation.ts` — takes a `Document` object, returns a formatted citation string
- `permissions.ts` — takes a user role and an action, returns a boolean
- `completeness.ts` — takes a `Document` and institution standards, returns
  the computed completeness level
- `accessibility.ts` — focus management helpers, ARIA id generator

Services must have 100% unit test coverage.

- No prop-drilling beyond two levels.
- Escape all user-supplied content rendered as HTML. Never use
  `dangerouslySetInnerHTML` except for sanitized, trusted HTML from the server
  (exhibition descriptions), and even then run it through DOMPurify first.
- Forms: React Hook Form + Zod schema validation.
- Accessibility is a first-class coding requirement, not a post-launch concern.
  See §31 for all requirements. Key rules for component authors:
  - Never use `outline: none` without a compliant visible alternative.
  - Every interactive component must be keyboard-operable and have an accessible name.
  - Run `axe-core` locally before submitting any UI-related PR.
  - Every drag-and-drop interaction must have a keyboard/button alternative (§31.3).

### 16.3 Shell Scripts

- POSIX `sh`. No bash-specific syntax. No hardcoded paths.
- All scripts accept configuration via environment variables with documented
  defaults.

---

## 17. Testing Requirements

### 17.1 Backend

- `pytest` with `pytest-asyncio`.
- Unit tests for all service and utility functions.
- Integration tests for all API endpoints using a real test MySQL database
  (Docker service in CI, local Docker in dev).
- Test fixtures in `tests/conftest.py`: database session, authenticated test
  client for each role, temp storage directory.
- Coverage target: 80% line coverage minimum.
- All permission boundary cases must have tests: verify that forbidden actions
  return 403, not 404 or 500.

### 17.2 Frontend

- Vitest for unit tests on hooks and utility functions.
- React Testing Library for component tests.
- `vitest-axe` (wraps axe-core) for accessibility testing on every component.
  Any axe violation at `critical` or `serious` severity fails the test.
- No snapshot tests.

### 17.3 CI

- All tests must pass on `main` branch and on every PR.
- Ruff, black, mypy, and TypeScript compiler must all report zero errors.
- axe-core violations at `critical` or `serious` severity block merge (§31.13).

---

## 18. Accession Number Format

The accession number format is configurable by the administrator in system settings.
The default format is `{YEAR}-{SEQUENCE:04d}` (e.g., `2025-0001`). The format
string supports tokens: `{YEAR}`, `{MONTH}`, `{DAY}`, `{SEQUENCE}` (auto-increment
per year by default). Assignment is atomic (use a database transaction with a
`SELECT ... FOR UPDATE` on a `sequences` table to prevent gaps or collisions).

```sql
sequences
  id, name VARCHAR(200) UNIQUE,   -- e.g. 'accession_2025'
  current_value BIGINT UNSIGNED DEFAULT 0,
  updated_at DATETIME
```

### 18.1 Versioned Accession Numbers

When a document belongs to a version group, its accession number includes a version
suffix separated by a period:

| Scenario | Accession number |
|---|---|
| Unversioned document | `2025-0042` |
| First version in a group | `2025-0042.1` |
| Second version | `2025-0042.2` |
| Third version | `2025-0042.3` |

The `document_version_groups.base_accession_number` stores the shared base (`2025-0042`).
When an unversioned document is promoted into a version group for the first time, its
`accession_number` is updated from `2025-0042` to `2025-0042.1` in the same transaction
that creates the group record. This is the only situation in which an already-assigned
accession number is modified; it must be logged in `audit_log`.

Version numbers within a group are always sequential integers starting at 1 and are
assigned by the application — never by the user. Version numbers are never reused even
if an intermediate version is deaccessioned. The label the archivist assigns (e.g.,
"1978 Revision," "Smith Donation Copy") is stored in `documents.version_label` and is
distinct from the numeric version suffix.

---

## 19. First-Run Setup

On first startup (no users in `users` table), the application must:
1. Run all Alembic migrations automatically.
2. Seed vocabulary domains and default terms.
3. Seed default roles.
4. Display a setup wizard in the frontend to create the superadmin account,
   configure the institution name, set the storage scheme, and optionally
   configure LLM settings.

The setup wizard routes (`/setup/*`) must redirect to `/dashboard` once setup
is complete.

---

## 20. Document Versioning

### 20.1 Overview

Document versioning handles situations where the same intellectual item exists in
multiple distinct states or physical forms — adopted revisions of a living document
(bylaws amended in 1965, 1978, and 2003), rescans at higher resolution or with
improved equipment, or copies donated by separate sources that may differ in condition
or completeness.

Versioning is **distinct from document relationships**. Relationships (§5.10) model
the path between versions — the proposed amendments, committee drafts, and vote records
that connect one adopted bylaw to the next. Versioning models the adopted states
themselves as a coherent family sharing an identity.

Each version is a **full, independent document record** with its own files, OCR text,
metadata, and preservation events. The version group binds them together and designates
which is canonical (used in search and browse) and which is public (shown on the exhibit
site).

### 20.2 Version Creation Workflow

**Case A: Creating the first version of an existing unversioned document**

1. Archivist clicks "Create version group" on an existing document.
2. The application prompts: "This will create a version family starting with the current
   document as version 1. Are you sure?" — confirmation required.
3. In a single transaction:
   a. Insert a `document_version_groups` row with `base_accession_number` = current
      document's accession number (e.g., `2025-0042`).
   b. Update the document's `accession_number` to `2025-0042.1`,
      `version_number` to `1`, `version_group_id` to the new group, and
      `is_canonical_version` to `TRUE`.
   c. Update `document_version_groups.canonical_document_id` to this document.
   d. Write an `audit_log` row recording the accession number change.
4. The archivist may then add additional versions (Case B).

**Case B: Adding a new version to an existing group**

1. Archivist opens any document in a version group and clicks "Add new version."
2. Application creates a new `documents` row with:
   - `accession_number` = `{base}.{next_version_number}` (atomically incremented)
   - `version_number` = next integer in the group
   - `version_group_id` = same as source document's group
   - `is_canonical_version` = `FALSE`
   - `inbox_status` = `'inbox'`
   - `description_status` = `'draft'`
   - All descriptive metadata **copied from the canonical version** as defaults
     (the archivist can override any field)
3. The new version appears in the archivist's inbox for file upload and metadata review.
4. No files are pre-populated — the archivist uploads the new version's file(s).

**Case C: Converting two separately ingested documents into a version group**

Sometimes an archivist realizes after ingestion that two separate records are actually
versions of the same item. From either document's detail view, an archivist can click
"Add to version group" and either:
- Create a new group containing both documents, OR
- Add the current document to an existing group (selected by accession number lookup)

When merging into a new group, the archivist designates which document becomes version 1
and which becomes version 2. Both accession numbers are updated accordingly.

### 20.3 Canonical Version

The canonical version is the default representation of the document family. It is the
version that appears in search results, browse views, and the document list.

**Rules:**
- Exactly one document per version group has `is_canonical_version = TRUE`.
- Setting a new canonical version atomically sets the previous canonical's flag to `FALSE`
  in the same transaction.
- When the canonical version changes, `document_version_groups.canonical_document_id`
  is updated in the same transaction.
- The archivist sets the canonical version from the version panel on any document in
  the group. Requires at minimum `archivist` role plus edit permission on the collection.

**The canonical version is surfaced by default everywhere in the authenticated UI.**
Non-canonical versions are reachable only through the version panel on the document
detail view.

### 20.4 Public Version

The public version is what appears on the public exhibition site. It defaults to the
canonical version but may be set independently.

**Rules:**
- `document_version_groups.public_document_id` stores the public version. If `NULL`,
  the canonical version is used.
- The public version must have `documents.is_public = TRUE`.
- Setting a public version that has `is_public = FALSE` is a validation error.
- Only one version per group is publicly visible at a time.
- Non-public versions are never accessible from public routes, even if their URL is known.
- When the public version is changed, the old version does not automatically lose its
  `is_public` flag — the archivist must explicitly set it if they want it hidden.

### 20.5 Search and Browse Behavior

Search and browse only surface canonical versions. This is enforced at the query layer,
not in application logic, so it applies consistently across all search paths.

**SQL filter applied to all search/browse queries:**
```sql
WHERE (documents.version_group_id IS NULL)
   OR (documents.is_canonical_version = TRUE)
```

A document detail view for a canonical version shows a version indicator:
"Version 2 of 3 · [View all versions]". Clicking opens the version panel.

A user searching for a specific non-canonical version (e.g., from a saved citation) can
reach it by direct accession number lookup: `GET /api/v1/documents?accession=2025-0042.2`.
This returns the specific version regardless of canonical status, so researchers can
always retrieve the exact version they cited.

### 20.6 Version Panel (UI)

Every document detail view — authenticated and public — that belongs to a version group
must display a version panel. Its content differs by context:

**Authenticated view:**
- Version badge: "Version {n} of {total}" with the version label if set
- List of all versions in the group, showing: version number, label, date range,
  canonical indicator, public indicator, and `description_status`
- Actions per version: "Set as canonical," "Set as public," "View," "Edit"
- "Add new version" button (for users with edit permission)

**Public view:**
- Shows only versions that have `is_public = TRUE`
- For each public version: version label, date range, and a link to that version
- If only one version is public (the normal case), the panel is minimal:
  "Earlier versions of this document exist. Contact [repository] for access."
- If multiple versions are public: "Multiple versions available — select a version:"

### 20.7 Citation of Versioned Documents

When a document belongs to a version group, the citation must identify the specific
version consulted. The versioned accession number (`2025-0042.3`) appears in the
identifier field of all citation formats. The `version_label` (e.g., "1978 Revision")
appears in the description field where the citation format supports it.

Chicago note format for a versioned document:
> Falls Church Volunteer Fire Department Bylaws, 1978 Revision [version 3], Accession
> 2025-0042.3, Falls Church VFD Archives, Falls Church, VA.

The citation export module must include version information whenever
`documents.version_group_id IS NOT NULL`.

### 20.8 Versioning API Endpoints

```
GET    /api/v1/documents/{id}/versions         — all versions in the group; authenticated only
POST   /api/v1/documents/{id}/version-group    — create a new group from this document (Case A)
POST   /api/v1/documents/{id}/new-version      — add a new version to existing group (Case B)
POST   /api/v1/documents/{id}/join-group       — add to an existing group (Case C)
PATCH  /api/v1/version-groups/{group_id}       — set canonical_document_id or public_document_id
POST   /api/v1/documents/{id}/set-canonical    — promote this version to canonical
POST   /api/v1/documents/{id}/set-public-version — promote this version to public
```

`PATCH /api/v1/version-groups/{group_id}` accepts:
```json
{
  "canonical_document_id": 456,
  "public_document_id": 457
}
```

Either field may be omitted if only one is being changed. The endpoint validates that
both referenced documents belong to the group and that `public_document_id`, if set,
has `is_public = TRUE`.

### 20.9 Version Deaccession

When a version is deaccessioned, the `deaccession_log` records its versioned accession
number and the group's base accession number. The version number is not reused. If the
canonical version is deaccessioned, the application requires the archivist to designate a
new canonical version before the deaccession workflow can proceed. If the last remaining
version in a group is deaccessioned, the group record is retained with no active members
(for historical reference in the deaccession log) but is no longer surfaced in the UI.

---

## 21. Bulk Operations

All document list views (archive browse, inbox, search results) must support
multi-select with a bulk action toolbar. This is a first-class feature, not a
nice-to-have — batch processing of scanned materials is a core historian workflow.

### 20.1 Bulk Action API

`POST /api/v1/documents/bulk` accepts:

```json
{
  "document_ids": [1, 2, 3, ...],
  "action": {
    "type": "apply_terms" | "remove_terms" | "assign_node" | "set_public" |
             "clear_inbox" | "add_to_review" | "export_zip" | "delete",
    "term_ids": [...],        -- for apply_terms / remove_terms
    "node_id": 5,             -- for assign_node
    "is_public": true,        -- for set_public
    "reason": "..."           -- required for delete (logged to audit_log)
  }
}
```

The `delete` action requires the user to have admin role. It calls the deaccession
workflow for each document rather than performing a bare delete. The `reason` field
is stored in `deaccession_log.reason_note`.

The `export_zip` action creates a ZIP file containing the original files for all
selected documents, each with XMP Dublin Core metadata embedded. The ZIP is streamed
back in the response; it is never written to disk on the server.

### 20.2 Bulk Action UI Requirements

- Multi-select via checkboxes appears on the document list view at all times, not
  only in a special "edit mode."
- A "Select all on this page" checkbox appears in the column header.
- When any documents are selected, a sticky toolbar appears at the bottom of the
  viewport showing the selected count and available actions.
- Bulk actions are confirmed in a modal before execution.
- After bulk execution, a toast notification summarizes the result
  (e.g., "Applied 3 tags to 47 documents").
- Permission filtering: the available bulk actions in the toolbar are limited to
  what the current user's role allows. Delete only shows for admins.

---

## 22. Watch Folder Ingest Pipeline

### 21.1 Overview

The Celery beat task `workers.ingest.poll_watch_folders` runs every 60 seconds.
For each active watch folder, it scans the configured path for new files and
processes them through the standard ingest pipeline.

### 21.2 Pipeline Steps

1. Discover all files in the watch folder path not currently being processed
   (use a `.processing` lock file to prevent double-ingestion).
2. For each file:
   a. Move the file to `{STORAGE_ROOT}/.quarantine/{uuid}_{filename}`.
   b. Run the standard ingest pipeline (§6.2): hash, MIME detection, Siegfried,
      preservation warning evaluation.
   c. Create a `documents` stub record with:
      - `title` set to the original filename (without extension) as a placeholder
      - `description_status = 'draft'`
      - `inbox_status = 'inbox'`
      - `arrangement_node_id` from the watch folder's `target_node_id` if set
      - All `default_tags` from the watch folder applied
   d. Move the file to its permanent path.
   e. Queue OCR, LLM suggestion (if enabled), and thumbnail generation tasks.
3. Write a `preservation_events` row with `event_type = 'ingest'` and
   `agent = 'watch_folder:{watch_folder_id}'`.
4. The document appears in the inbox queue with `inbox_status = 'inbox'`.

### 21.3 Error Handling

If any step fails, the file must remain in quarantine (not deleted), the error
must be written to `preservation_events` with `event_outcome = 'failure'`, and
an admin alert must appear on the dashboard. Files must never be silently lost.

---

## 23. Document Annotations

### 23.1 Overview

Annotations allow archivists and contributors to attach structured notes to specific
locations within a document — either a drawn region on a page image or a highlighted
span of OCR text. They are strictly internal: never returned on public API routes,
never included in any export, and never visible to unauthenticated users.

The distinction from other note fields is intentional:
- `documents.archivists_note` — formal archival description note, part of the record
- `documents.general_note` — general note, may inform public description
- **Document annotations** — informal working notes, interpretive observations,
  questions, and corrections anchored to a specific location on a specific page

### 23.2 Permission Rules

- Any user with `can_edit = TRUE` on the document's collection may create annotations.
- Viewers (`can_view = TRUE` only) cannot create, read, or modify annotations.
- A user may edit or delete their own annotations. Admins and archivists may edit
  or delete any annotation in their accessible collections.
- All annotation activity is written to `audit_log`.

### 23.3 Region Annotation

A region annotation draws a bounding box on a page image. Coordinates are stored
as percentages of the image's displayed width and height (0–100), making them
resolution-independent. The viewer scales them to actual pixels at render time.

**Creating a region annotation:**
1. User selects the region annotation tool in the document file viewer.
2. User click-drags a rectangle on the page image.
3. A popover appears with a text input for the annotation body.
4. On save, a `POST /api/v1/documents/{id}/annotations` request is sent with:
   ```json
   {
     "document_file_id": 123,
     "document_page_id": 456,
     "annotation_type": "region",
     "region_geometry": { "x1": 12.5, "y1": 34.1, "x2": 45.0, "y2": 52.3 },
     "body": "Signature identified as Thomas Gray, Secretary 1887–1901"
   }
   ```

**Displaying region annotations:**
- Each annotation is rendered as a semi-transparent colored rectangle overlaid on the
  page image, with a small badge showing the annotation count in the corner.
- Hovering over the rectangle shows the annotation body and creator name in a tooltip.
- Resolved annotations are shown in a muted color and collapsed by default.
- A toggle in the viewer toolbar shows/hides all annotations.

### 23.4 Text Range Annotation

A text range annotation highlights a span of characters in the OCR transcription panel.

**Creating a text range annotation:**
1. User selects text in the OCR transcription panel.
2. A "Annotate selection" button appears near the selection.
3. User clicks it, enters the annotation body in a popover.
4. On save, a `POST /api/v1/documents/{id}/annotations` request is sent with:
   ```json
   {
     "document_file_id": 123,
     "document_page_id": 456,
     "annotation_type": "text_range",
     "text_range": {
       "start_offset": 142,
       "end_offset": 157,
       "quoted_text": "John Harrington"
     },
     "body": "OCR read 'Harrison' — correct spelling is 'Harrington' per deed book 4, p.23"
   }
   ```

**Displaying text range annotations:**
- Annotated text spans are highlighted in the OCR panel.
- Clicking a highlight opens a popover showing the annotation body, creator, and date.
- The `quoted_text` is stored at creation time as a snapshot. If OCR text is later
  corrected, the `quoted_text` remains as a reference; the offsets may become stale
  (display a warning if `start_offset` no longer matches `quoted_text` in current OCR).

### 23.5 Resolved State

Annotations can be marked resolved (e.g., "the transcription correction was applied,"
or "the signature was formally identified and linked to an authority record"). Resolved
annotations are visually distinct and hidden by default but never deleted — they form
part of the working history of the document's processing.

### 23.6 Frontend Requirements

- The document file viewer must include a toolbar toggle for annotations (show/hide).
- The page thumbnail sidebar must show a small indicator badge on pages that have
  unresolved annotations.
- A document-level annotation summary panel lists all annotations across all pages
  of the document, grouped by page, with links to navigate to each.
- Annotations are loaded asynchronously after the page viewer loads — they must not
  block the initial document render.

---

## 24. Named Entity Recognition (NER)

### 24.1 Overview

NER automatically extracts named entities — persons, organizations, locations, and
dates — from OCR text after it is generated. It is an institutional opt-in feature.
When enabled, it suggests tags, links to authority records, and geolocation data.
All suggestions require human review before being applied to the document record.

NER is a complement to, not a replacement for, the LLM suggestion pipeline. NER is
faster and cheaper for entity extraction across large batches; the LLM is better for
holistic metadata suggestions (title, scope, document type). Both can run independently.

### 24.2 Configuration

NER is enabled per institution via system settings. The following keys control it:

```
ner.enabled              — boolean; default false
ner.run_after_ocr        — boolean; if true, NER runs automatically after OCR completes
ner.entity_types         — list: ["PERSON", "ORG", "GPE", "LOC", "DATE"]
ner.suggest_authority    — boolean; suggest creating authority records for PERSON/ORG
ner.suggest_geolocation  — boolean; suggest geo_lat/geo_lon for GPE/LOC entities
ner.suggest_tags         — boolean; add extracted entities as tag suggestions
ner.require_review       — boolean; if true, all suggestions go to review queue
ner.model                — spaCy model name; default "en_core_web_lg"
```

Multiple spaCy language models can be installed. Institutions working with non-English
documents should install the appropriate model (e.g., `fr_core_news_lg` for French).
The `ner.model` setting selects which installed model to use.

### 24.3 Processing Pipeline

The Celery task `workers.ner.process_document(document_id)` runs after OCR completes
when `ner.run_after_ocr = true`, or on-demand via
`POST /api/v1/documents/{id}/run-ner`.

**Steps:**
1. Concatenate OCR text from all pages of the document.
2. Run spaCy NER on the combined text. Extract entities of the configured types.
3. Deduplicate entities (e.g., "John Smith" appearing 12 times = one suggestion).
4. For each unique entity:
   - `PERSON` / `ORG`: Search existing `authority_records` for a fuzzy name match.
     - If a confident match (>0.85 similarity) exists: suggest adding a
       `document_authority_links` row linking the document to that authority
       record with role `mentioned`.
     - If no match: create a new `authority_records` row with `created_by_ner = TRUE`
       and `created_by = NULL`, marked as pending review. Also suggest a
       `document_authority_links` row once the authority record is confirmed.
   - `GPE` / `LOC`: Search existing `locations` for a fuzzy name match.
     - If a confident match exists: suggest adding a `document_location_links` row
       with `link_type = 'mentioned'`.
     - If no match and `ner.suggest_geolocation = true`: attempt to geocode via
       Nominatim and suggest creating a new `locations` record.
   - All entity types: If `ner.suggest_tags = true`, add the entity text as a tag
     suggestion in the LLM/review suggestion format.
5. Store all suggestions in `documents.llm_suggestions` JSON under a `ner` key.
6. If `ner.require_review = true`: set `review_status = 'pending'` and add to
   review queue with reason `ner_suggestions`.
7. Write a `preservation_events` row with `event_type = 'ner'`.

### 24.4 NER Suggestions Review UI

NER suggestions appear in the same review queue UI as LLM suggestions, in a separate
tab labeled "NER Entities." The reviewer sees:

- Entity text and type (PERSON, ORG, GPE, etc.)
- Number of occurrences in the document
- For PERSON/ORG: matched authority record (if found) or proposed new record name
- For GPE/LOC: proposed place name and geocoordinates on a small map preview
- For tags: proposed tag term

Actions per suggestion: Accept, Edit then Accept, Reject.

Accepting a PERSON/ORG match links the document to the existing authority record.
Accepting a new PERSON/ORG creates and links a new reviewed authority record.
Accepting a GPE/LOC sets the document's geolocation fields.
Rejecting removes the suggestion permanently.

### 24.5 NER Does Not Modify Records Without Review

NER suggestions are **never auto-applied**, regardless of confidence score. This is
a hard rule with no configuration option to override it. The error rate on historical
documents — especially those with OCR noise, archaic spelling, and unusual proper nouns
— is too high to allow automatic commits. All NER output flows through the review queue.

---

## 25. Wikidata Integration

### 25.1 Overview

Authority records in ADMS can be optionally linked to Wikidata entities by their
Q identifier (e.g., `Q42` for Douglas Adams). Linking is voluntary and reversible.
It enriches the authority record with external biographical or organizational data
and makes ADMS records interoperable with the broader cultural heritage linked data
ecosystem.

### 25.2 Linking an Authority Record

From the authority record detail page, an archivist can:
1. Click "Link to Wikidata."
2. Enter a Q identifier directly, OR search Wikidata by name using the Wikidata
   search API (`GET https://www.wikidata.org/w/api.php?action=wbsearchentities`).
3. Review the proposed match (name, description, dates from Wikidata).
4. Confirm the link.

On confirmation, `authority_records.wikidata_qid` is set and
`POST /api/v1/authority/{id}/wikidata/link` fetches and caches enrichment data
in `authority_records.wikidata_enrichment` (JSON). All Wikidata API calls are
server-side — no client-side calls to external APIs.

### 25.3 Enrichment Data Cached

The following Wikidata fields are cached in `wikidata_enrichment` when available:

| Field | Wikidata property | Use in ADMS |
|---|---|---|
| Description | `schema:description` | Shown in authority record detail |
| Birth date | P569 | Pre-fills `dates` if not already set |
| Death date | P570 | Pre-fills `dates` if not already set |
| Occupation | P106 | Shown in authority record detail |
| Notable works | P800 | Shown in authority record detail |
| Image | P18 | Thumbnail on authority record page (served proxied, not hotlinked) |
| VIAF ID | P214 | Shown as external identifier link |
| LCNAF ID | P244 | Shown as external identifier link |

Cached enrichment is **display-only** — it does not overwrite any ADMS field unless
the archivist explicitly applies a suggestion. The cache is refreshed when
`wikidata_last_synced_at` is more than 30 days old, or on-demand via
`GET /api/v1/authority/{id}/wikidata`.

### 25.4 Unlinking

`DELETE /api/v1/authority/{id}/wikidata/link` clears `wikidata_qid`,
`wikidata_last_synced_at`, and `wikidata_enrichment`. The authority record is
otherwise unchanged.

### 25.5 Privacy and External Calls

All Wikidata API calls are made server-side from the backend container, never from
the browser. No user data is sent to Wikidata — queries contain only the Q identifier
or a search string derived from the authority record's `authorized_name`. Wikidata
enrichment is never exposed on public routes.

---

## 26. Permanent URLs and Tombstones

### 26.1 Permanent URL Structure

Every document has a permanent, accession-number-based URL that resolves regardless
of the document's current availability status. These URLs are stable across server
migrations because they are based on the archival accession number, not the
database row ID.

**URL format:** `{BASE_URL}/d/{accession_number}`
Examples: `https://archive.example.org/d/2025-0042` or `/d/2025-0042.1`

This route is served by the FastAPI backend — not the React frontend — so it can
issue HTTP 301 redirects, return tombstone HTML, or serve the public document view
depending on the document's `availability_status`. The React frontend's public routes
(`/public/documents/{id}`) remain available for browsing, but the `/d/` route is the
citable, permanent identifier.

### 26.2 ARK Identifier Support (Optional)

Institutions may register a Name Assigning Authority Number (NAAN) with the
California Digital Library for free and assign ARK identifiers to their documents.

When `system_settings['institution.naan']` is set, the first-run setup and import
pipeline can auto-assign ARK identifiers in the format `ark:/{NAAN}/{accession_number}`.
The application resolves ARKs at `GET /ark/{naan}/{id}` with an HTTP 301 to the
document's public URL.

ARK assignment is optional at the document level. Documents without `ark_id` set
resolve only via the `/d/` route. ARK identifiers are displayed in citations and
on the public document page when set.

### 26.3 Availability States and Tombstone Behavior

| State | Who set it | Public URL resolves to | HTTP status |
|---|---|---|---|
| `available` + `is_public = TRUE` | — | Full public document page | 200 |
| `available` + `is_public = FALSE` | — | Tombstone (not publicly available) | 410 |
| `temporarily_unavailable` | Archivist action | Tombstone (in review) | 503 |
| `deaccessioned` | Deaccession workflow | Tombstone (permanently removed) | 410 |

**Tombstone content by `tombstone_disclosure` setting:**

| Disclosure level | What is shown |
|---|---|
| `none` | "This item is no longer publicly available. Contact [institution] for information." |
| `accession_only` | Accession number + "Contact [institution] for information." |
| `collection_and_accession` | Collection/fonds name + accession number + contact info |

For `temporarily_unavailable` documents, the tombstone additionally shows:
"This record is temporarily unavailable. [Expected return: {unavailable_until}]"
when `unavailable_until` is set.

The tombstone never reveals: title, description, creator, file contents, or any
other metadata beyond what `tombstone_disclosure` permits.

### 26.4 Making a Document Temporarily Unavailable

`POST /api/v1/documents/{id}/make-unavailable` sets `availability_status = 'temporarily_unavailable'`.

Required body:
```json
{
  "reason": "Record under review for metadata correction",
  "unavailable_until": "2025-09-01",
  "tombstone_disclosure": "accession_only"
}
```

`POST /api/v1/documents/{id}/restore` returns it to `availability_status = 'available'`.
Both actions are logged in `audit_log` and `preservation_events`.

---

## 27. Content Advisory System

### 27.1 Overview

Some documents contain language or imagery that may be harmful, offensive, or
distressing to researchers — particularly materials from earlier periods that
use terminology now recognized as harmful toward marginalized communities.
The content advisory system allows institutions to flag these documents and
provide contextual notes, following NARA, SAA, and DACS reparative description
principles, without modifying the original content or metadata.

This is an institution-configured, opt-in feature. Institutions make their own
decisions about what requires an advisory and what language to use. ADMS provides
the mechanism; the institution provides the judgment.

### 27.2 Document-Level Advisory

A document with `has_content_advisory = TRUE` displays an advisory banner:
- On the authenticated document detail view (staff)
- On the public document page if `is_public = TRUE`
- In the exhibition viewer when the document appears in a public exhibition block

The banner text is taken from `documents.content_advisory_note`. If this field is
null, the institution's default advisory text from
`system_settings['content_advisory.default_text']` is used.

**Default text if neither is set:**
"This item may contain language or content that reflects historical attitudes
 that are harmful or offensive to modern readers."

### 27.3 Collection-Level Inheritance

An `arrangement_node` may also have `has_content_advisory = TRUE` and a
`content_advisory_note`. All documents in that collection inherit the advisory
unless the document explicitly sets `has_content_advisory = FALSE`.

Add to `arrangement_nodes`:
```sql
has_content_advisory BOOLEAN DEFAULT FALSE,
content_advisory_note TEXT
```

### 27.4 Advisory in Exports and Feeds

The content advisory note is included as `dc:description` supplementary text
in Dublin Core XML exports and OAI-PMH feeds when `has_content_advisory = TRUE`.
It is prefixed with "Content Advisory: " to distinguish it from the scope and
content description.

---

## 28. Description Completeness Standards

### 28.1 Overview

Not every document in a collection will ever have a complete description. Some
dates are genuinely unknown; some creators are unidentified. The description
completeness system lets institutions define what constitutes acceptable minimum,
standard, and full description for their context — and lets the system
automatically track where every document stands against those standards.

This is different from `description_status` (draft/revised/final), which tracks
the workflow state. Completeness measures data richness, not workflow state.

### 28.2 Configuration

During first-run setup, the administrator configures required fields for each
completeness level. These are stored in `institution_description_standards`.
Defaults are pre-populated based on DACS minimum requirements:

**Default minimal fields** (matches DACS Single-Level Minimum):
`title`, `date_display`, `level_of_description`, `extent`

**Default standard fields** (matches DACS Single-Level Optimum):
All minimal fields plus: `creator_id`, `scope_and_content`, `access_conditions`,
`language_of_material`

**Default full fields:**
All standard fields plus: `archival_history`, `immediate_source`, `physical_characteristics`,
at least one `document_terms` tag entry

Administrators may remove any field from these lists (e.g., removing `date_display`
from minimal because their collection often has undated items) or add fields.
The one non-negotiable field is `title` — it is always required for `minimal`.

### 28.3 Completeness Computation

The Celery task `workers.description.recompute_completeness(document_id)` runs:
- After every save to `documents`
- After every add/remove to `document_terms`
- As a nightly batch job for any document not recalculated in 24 hours

The task checks each required field for non-null, non-empty-string values in
ascending level order. It sets `description_completeness` to the highest level
fully satisfied.

### 28.4 Completeness in the UI

- Every document list view (archive browse, search, inbox) shows a small colored
  indicator badge: grey (none), yellow (minimal), blue (standard), green (full).
- The document detail view shows the completeness level with a breakdown: which
  required fields are missing to reach the next level.
- The health dashboard (`/admin/preservation`) includes a completeness distribution
  chart per collection.

### 28.5 Completeness in Reports

The processing report (`GET /api/v1/reports/processing`) groups documents by
completeness level within each collection, enabling grant reports that quantify
"percentage of collection fully described" without manual counting.

---

## 29. CSV Import

### 29.1 Two Import Modes

**Template mode** is for small collections or users comfortable formatting their
data to match ADMS's structure. The user downloads the official ADMS CSV template,
fills it in, and uploads it. No column mapping step is needed.

**Mapped mode** is for large collections or legacy exports from PastPerfect,
ContentDM, Access databases, or other systems. The user uploads their existing
CSV with whatever column names they have. A visual mapping UI lets them connect
each source column to an ADMS field.

### 29.2 CSV Template

The downloadable template (`GET /api/v1/admin/imports/template`) is a CSV file
with these column headers:

```
accession_number, title, date_display, date_start (YYYY-MM-DD), date_end (YYYY-MM-DD),
creator_name, document_type, extent, language_of_material, scope_and_content,
access_conditions, reproduction_conditions, copyright_status, rights_holder, rights_note,
location_of_originals, physical_format, condition, general_note, archivists_note,
tags (pipe-separated), subject_categories (pipe-separated), geo_location_name,
geo_latitude, geo_longitude, original_location, scan_date (YYYY-MM-DD),
has_content_advisory (TRUE/FALSE), content_advisory_note
```

The template includes a second sheet (in the XLSX version) with field
descriptions, accepted values for enum fields, and examples. A plain CSV
version is also provided for users who cannot open XLSX.

### 29.3 Validation Pipeline

Both modes pass through the same validation pipeline before any data is committed.
The pipeline runs as a Celery task and writes results to `csv_imports.validation_report`.

**Stage 1 — File parsing:**
Detect encoding (UTF-8, UTF-8-BOM, Latin-1), detect delimiter (comma, semicolon, tab).
Reject if file is not parseable or exceeds 50,000 rows (configurable via system settings).

**Stage 2 — Column presence:**
Template mode: verify all required columns are present.
Mapped mode: verify all ADMS required fields have been mapped.

**Stage 3 — Row-level validation:**
For each row, validate:
- `title` is non-empty
- `accession_number` format matches institution's configured format, OR is blank
  (blank accession numbers are auto-assigned at import time)
- `accession_number` does not duplicate an existing record (flag as warning,
  not error — the user may be updating an existing record)
- Date fields are valid dates or blank
- Enum fields (`copyright_status`, `condition`, `document_type`, etc.) contain
  known values OR new values (new values are flagged as "will create new vocabulary term")
- `creator_name` matches an existing authority record (fuzzy match; no match
  is a warning — a new authority record will be created)

**Stage 4 — Dry-run report:**
The validation report shows a summary:
- Total rows / valid rows / warning rows / error rows
- List of new vocabulary terms that will be auto-created
- List of new authority records that will be auto-created
- List of duplicate accession numbers (update vs. skip choice)
- Sample of the first 10 rows showing mapped values

The import job enters `validation_failed` if any error-level issues exist.
Warning-level issues do not block import but are shown for review. The user must
explicitly confirm they have reviewed the report before the import executes.

### 29.4 Import Execution

After the user confirms, `POST /api/v1/admin/imports/{id}/confirm` triggers the
import Celery task. The import:

1. Creates all new vocabulary terms flagged in the dry-run.
2. Creates all new authority records flagged in the dry-run (with `created_by_ner = FALSE`
   and `created_by = importing_user`).
3. For each valid row: creates a `documents` record, inserts `document_terms` rows,
   resolves creator name to authority record ID.
4. For duplicate accession numbers: if the user chose "update," patches the existing
   record; if "skip," writes the row as `skipped` in `csv_import_rows`.
5. All imported documents start with `inbox_status = 'inbox'` so they appear in
   the archivist's inbox for review.
6. All imported documents start with `is_public = FALSE`. No import can make
   documents public automatically.

Import progress is visible in real time at `GET /api/v1/admin/imports/{id}`.

### 29.5 Post-Import Vocabulary Cleanup

After an import, the administrator should audit new vocabulary terms created
automatically. The admin vocabulary management page (`/vocabulary`) shows terms
recently created by import with an "Imported" badge. Terms that are misspellings
or near-duplicates of existing terms can be merged using the term merge workflow
(§5.8).

---

## 30. Reporting

### 30.1 Overview

All reports are accessible to users with at minimum `archivist` role. Admins
see all collections; archivists see only their accessible collections. All reports
are exportable as CSV and PDF.

Report generation is synchronous for small collections (<10,000 documents) and
asynchronous (Celery task) for larger ones. The API returns a 202 with a job ID
for async reports; the job ID is polled until complete.

### 30.2 Available Reports

**Accession Report** — `GET /api/v1/reports/accessions`

Parameters: `date_from`, `date_to`, `node_id` (optional collection filter), `created_by` (optional user filter)

Shows: accession numbers, titles, date accessioned, accessioned by, collection, description completeness level.
Designed for: annual reports, NHPRC grant reporting, board presentations.

**Processing Progress Report** — `GET /api/v1/reports/processing`

Parameters: `node_id` (optional), `as_of_date` (optional)

Shows: per-collection breakdown of documents at each completeness level (none/minimal/standard/full),
as counts and percentages. Highlights collections with zero fully-described items.
Designed for: identifying backlogs, prioritizing processing work, grant reporting.

**User Activity Report** — `GET /api/v1/reports/users`

Parameters: `date_from`, `date_to`, `user_id` (optional)

Shows: per-user counts of documents created, documents updated (any field), OCR retries
triggered, annotations created, imports completed.
Designed for: recognizing volunteer and staff contributions, performance reviews,
demonstrating project activity to funders.

**Collection Summary Report** — `GET /api/v1/reports/collection`

Parameters: `node_id` (optional)

Shows: total documents, total files, total storage used, % with OCR complete, % public,
% with content advisory, description completeness distribution, language distribution.
Designed for: collection assessments, AASLH StEPs documentation.

**Public Access Summary** — `GET /api/v1/reports/public-access`

Parameters: `date_from`, `date_to`

Shows: documents published, exhibitions published, public searches (count only, no
query content), documents downloaded (count by accession number).
Designed for: demonstrating public value, grant reporting, annual reports.

### 30.3 Report Storage and Scheduling

Generated reports are not stored permanently — they are computed on demand. Scheduled
reports (e.g., monthly accession report emailed to board) are a Phase 2 feature (see §32).

---

## 31. Accessibility Standards

### 31.1 Conformance Target

ADMS must conform to **WCAG 2.2 Level AA** across all interfaces — both the public
exhibition site and the authenticated staff application. This is a hard requirement,
not a goal. Code that demonstrably fails WCAG 2.2 AA must not be merged.

Where WCAG 2.2 Level AAA criteria are achievable without significant engineering
cost, they must be implemented. Specific AAA criteria that are required in ADMS
are called out explicitly in this section.

WCAG 2.2 supersedes WCAG 2.1. All previous references to "WCAG 2.1 Level AA" in
this document are superseded by this section. Section 508 compliance is achieved
as a consequence of WCAG 2.2 AA conformance.

### 31.2 Scope

Accessibility requirements apply to:
- The public exhibition site (`/public/*`)
- The authenticated staff application (all `/archive`, `/admin`, `/events`, etc. routes)
- All form elements, modals, toasts, and dynamic UI components
- The document file viewer (image and PDF)
- The exhibition block editor
- Map and timeline blocks
- All email output (Phase 2, but design for it now)

There are no second-class interfaces. Staff who are archivists, historians, or
volunteers may have disabilities. The admin application must be as accessible
as the public site.

### 31.3 WCAG 2.2 New Criteria — All Required at AA

The following nine criteria are new in WCAG 2.2 and are all required:

**2.4.11 Focus Not Obscured (Minimum) — AA**
When a component receives keyboard focus, it must not be entirely hidden by
author-created content. Sticky navigation bars, fixed headers, and toast
notifications must not fully cover a focused element. Use `scroll-padding-top`
equal to the sticky header height to keep focused elements visible below it.

**2.4.12 Focus Not Obscured (Enhanced) — AAA — Required in ADMS**
No part of the focused element may be covered. This is stricter than 2.4.11.
Open modals must trap focus inside themselves. Drawers and sidepanels must
not leave focusable content behind them accessible to keyboard users. This
criterion is required (not merely aspirational) because ADMS has modal dialogs,
slideover panels, and a sticky navigation bar throughout.

**2.4.13 Focus Appearance — AAA — Required in ADMS**
The visible focus indicator must meet both a minimum area and contrast requirement.
This is required in ADMS because we control all CSS and can achieve it at no
additional cost. Implementation: the global focus style must be:
```css
:focus-visible {
  outline: 3px solid var(--color-focus);   /* #005fcc on light, #66b3ff on dark */
  outline-offset: 3px;
  border-radius: 2px;
}
```
Never use `outline: none` or `outline: 0` without providing a fully visible
alternative. Never suppress `:focus` without suppressing only on pointer input
via `:focus:not(:focus-visible)`.

**2.5.7 Dragging Movements — AA**
Every drag-and-drop interaction in ADMS must have a non-drag alternative.
This affects the following components, each of which must implement the
specified alternative:

| Component | Drag behavior | Required alternative |
|---|---|---|
| Exhibition page reorder | Drag page cards | Up/Down buttons on each page row |
| Exhibition block reorder | Drag blocks within a page | Up/Down buttons on each block |
| Arrangement node reorder | Drag nodes in tree | Position number input or Up/Down buttons |
| Bulk document reorder | (not used — bulk actions are not ordered) | N/A |

Drag remains available as an enhancement for pointer users. The keyboard/button
alternative is required and must work without mouse input.

**2.5.8 Target Size (Minimum) — AA**
All interactive targets must be at least **24×24 CSS pixels**. This minimum is
achieved via padding, not by enlarging visual elements. Recommended and preferred
size is **44×44 CSS pixels** (WCAG 2.2 AAA 2.5.5). Exceptions:
- Inline text links (size constrained by line height)
- Controls whose size is determined by the browser (native `<select>`, file inputs)
The 24px minimum applies to: icon buttons, close buttons, pagination controls,
tag delete buttons, checkbox hit areas, and all navigation links.

**3.2.6 Consistent Help — AA**
Help content (documentation links, support email, contextual tooltips) must
appear in the same relative location across all pages. The help icon in the
navigation must always be in the top-right of the header, on both public and
authenticated interfaces.

**3.3.7 Redundant Entry — AA**
Information a user has already provided must not be requested again in the same
session unless re-entry is necessary (e.g., password confirmation) or the
information is for security purposes. In ADMS: if an archivist fills out creator
information on one document, linking the same creator to a second document must
not require re-entering the name.

**3.3.8 Accessible Authentication (Minimum) — AA**
Login must not require a cognitive function test (CAPTCHA, image recognition,
puzzle) unless an alternative is provided. ADMS uses username/password
authentication. Password paste must not be blocked. If future MFA is added,
it must not require image recognition.

**3.3.9 Accessible Authentication (Enhanced) — AAA — Required in ADMS**
No cognitive function test of any kind at any authentication step. ADMS does
not implement CAPTCHA or image-based verification; this criterion is met by
design and must remain met.

### 31.4 Color and Contrast

**Text contrast:**
- Normal text (< 18pt or < 14pt bold): 4.5:1 minimum (AA), 7:1 target (AAA)
- Large text (≥ 18pt or ≥ 14pt bold): 3:1 minimum (AA), 4.5:1 target (AAA)

**Non-text contrast (form borders, icons, focus indicators):** 3:1 minimum against adjacent background.

**Design token requirements:**
The Tailwind configuration must define a color palette where every pairing
used in the UI has its contrast ratio documented. No color combination may be
used in production whose contrast ratio is unknown. The palette is defined in
`frontend/src/styles/tokens.css`:

```css
:root {
  /* Text */
  --color-text-primary: #1a1a1a;          /* 16:1 on white */
  --color-text-secondary: #595959;        /* 7:1 on white */
  --color-text-muted: #767676;            /* 4.5:1 on white — minimum */
  --color-text-inverse: #ffffff;

  /* Interactive */
  --color-focus: #005fcc;                 /* focus ring */
  --color-link: #0056b3;                  /* 4.7:1 on white */
  --color-link-visited: #6b21a8;

  /* Status */
  --color-error: #b91c1c;                 /* 5.9:1 on white */
  --color-warning: #92400e;              /* 4.5:1 on white */
  --color-success: #166534;              /* 7.1:1 on white */

  /* Completeness badges */
  --color-completeness-none: #6b7280;    /* grey */
  --color-completeness-minimal: #b45309; /* amber — 4.5:1 on white */
  --color-completeness-standard: #1d4ed8; /* blue — 5.9:1 on white */
  --color-completeness-full: #166534;    /* green — 7.1:1 on white */
}
```

Never convey information by color alone. Every status indicator must also use
a text label, icon, or pattern in addition to color.

### 31.5 Keyboard Navigation

Every interactive element must be reachable and operable by keyboard alone.

**Required keyboard behaviors:**
- Tab / Shift+Tab: forward and backward focus movement
- Enter / Space: activate buttons and links
- Arrow keys: navigate within composite widgets (menus, tabs, listboxes, trees)
- Escape: close modals, drawers, dropdown menus; cancel in-progress actions
- Home / End: first/last item in lists and grids where applicable

**Skip navigation:** Every page must have a "Skip to main content" link as the
first focusable element. It may be visually hidden until focused but must never
be `display: none` or `visibility: hidden`.

**Tab order:** Must follow the visual reading order (left-to-right, top-to-bottom).
No `tabindex` values greater than 0. Use `tabindex="0"` to add non-interactive
elements to tab order when necessary; use `tabindex="-1"` to manage focus
programmatically without adding to the tab sequence.

**Focus management in dynamic content:**
- When a modal opens: focus moves to the first focusable element inside it
- When a modal closes: focus returns to the element that triggered it
- When a toast appears: it is announced by screen readers as a live region;
  it does not receive focus unless it contains a required action
- When a form is submitted and errors appear: focus moves to the error summary
  or to the first invalid field

### 31.6 Semantic HTML and ARIA

Use semantic HTML elements for their intended purpose. Use ARIA only when no
native HTML element achieves the required semantic.

**Required HTML structure on every page:**
```html
<header role="banner">
  <!-- Skip nav link, site name, primary navigation -->
</header>
<nav aria-label="Primary navigation">...</nav>
<main id="main-content">
  <!-- Page content -->
</main>
<footer role="contentinfo">...</footer>
```

**ARIA live regions for dynamic content:**
```html
<!-- Inbox count update -->
<span aria-live="polite" aria-atomic="true" class="sr-only" id="inbox-count-live">
  <!-- Updated programmatically when count changes -->
</span>

<!-- Toast notifications -->
<div role="status" aria-live="polite" aria-atomic="true" id="toast-region">
  <!-- Toasts injected here -->
</div>

<!-- Import job progress -->
<div role="progressbar" aria-valuenow="{n}" aria-valuemin="0" aria-valuemax="100"
     aria-label="Import progress">
</div>
```

**Icon buttons must always have accessible names:**
```html
<!-- Wrong -->
<button><svg>...</svg></button>

<!-- Correct -->
<button aria-label="Delete annotation"><svg aria-hidden="true">...</svg></button>
```

**Required ARIA patterns for complex widgets:**

| Widget | Required pattern |
|---|---|
| Document tree navigation | `role="tree"`, `role="treeitem"`, `aria-expanded` |
| Exhibition page reorder list | `role="listbox"` or `role="list"` with move buttons |
| Tabbed interfaces | `role="tablist"`, `role="tab"`, `role="tabpanel"` |
| Faceted search filters | `role="group"` with `aria-labelledby` |
| Annotation overlay on image | `role="img"` on canvas, annotations as `role="note"` |
| Map block | `role="application"` with full keyboard pan/zoom controls |
| Completion badge | `role="img"` with descriptive `aria-label` |
| Bulk select checkbox | `aria-label="Select document: {title}"` |

### 31.7 Document File Viewer Accessibility

The image/PDF viewer is the most complex accessible widget in ADMS. It must:

- Wrap the entire viewer in `role="region"` with `aria-label="Document viewer: {title}"`
- Each page image must have a meaningful `alt` attribute:
  - If OCR text is available: `alt="Page {n} of {total}. Transcript available below."`
  - If OCR failed: `alt="Page {n} of {total}. No transcript available."`
  - If no OCR attempted: `alt="Page {n} of {total}."`
  - If the image is decorative (e.g., a blank page): `alt=""`
- The OCR transcript panel must be available as a text alternative linked from the
  viewer with a prominent "View transcript" button that remains keyboard-accessible
  when the transcript panel is visible
- Pagination controls:
  ```html
  <nav aria-label="Document pages">
    <button aria-label="Previous page" aria-disabled="{first-page}">◀</button>
    <span aria-current="page">Page {n} of {total}</span>
    <button aria-label="Next page" aria-disabled="{last-page}">▶</button>
  </nav>
  ```
- Zoom controls must have accessible labels and must not trap keyboard focus
- When OCR has failed, the failure message must be announced as an alert:
  `role="alert"` on the error container

### 31.8 Map Block Accessibility

Leaflet maps are not inherently keyboard-accessible. Every map block must:

- Wrap the map in `role="application"` with `aria-label` describing its contents
- Provide visible keyboard pan controls (North/South/East/West buttons)
- Provide visible zoom in/out buttons labeled as such
- For each map pin/marker: provide a focusable element with `role="button"` and
  an `aria-label` describing the linked document
- Include a text alternative list of all documents shown on the map, accessible
  via a "View as list" toggle, for users who cannot use the map interface
- Never use the map as the only path to linked documents

### 31.9 Forms and Error Handling

Every form field must:
- Have a visible `<label>` element associated via `for`/`id` or wrapped around the input
- Never use `placeholder` as the only label (placeholder disappears on input)
- Required fields must be marked `aria-required="true"` AND have a visible indicator
  (text "(required)" or an asterisk with a legend explaining the asterisk)
- Descriptions or hints use `aria-describedby` pointing to the hint text element

Error messages:
- Every error message must be associated with its field via `aria-describedby`
- Error messages must be visible text, not just color or icon
- When form validation fails on submit, focus moves to an error summary at the top
  of the form, or to the first invalid field
- `aria-invalid="true"` must be set on all invalid fields

Autocomplete fields (creator search, location search, vocabulary term search):
- Must use `role="combobox"` with `aria-expanded`, `aria-autocomplete`, and `aria-controls`
- The dropdown list uses `role="listbox"` with `role="option"` items
- Arrow keys navigate the options; Enter selects; Escape closes

### 31.10 Color Scheme and Motion

**Dark mode:** The public site and admin application must respect the
`prefers-color-scheme: dark` media query. Provide a full dark theme with all
contrast ratios verified. Users may also toggle manually via a theme selector
in the site header.

**Reduced motion:** All animations and transitions must respect `prefers-reduced-motion`:
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```
No content may flash more than three times per second under any conditions.
Auto-advancing carousels or slideshows are prohibited.

**Print stylesheet:** The public document detail page and collection summary page
must have a `@media print` stylesheet that removes navigation, produces a clean
printable version with full metadata, and resolves accession-number-based citations.

### 31.11 Language and Internationalization

Every HTML page must have `lang="en"` (or the appropriate ISO 639-1 code) on the
`<html>` element. If a document's content is in a language other than the page
language, the containing element must have `lang="{code}"` set from
`documents.language_of_material`.

All user-facing text must use plain language. The Flesch-Kincaid reading level
for instructional UI text (form labels, help text, error messages) should not
exceed grade 8.

### 31.12 Session Management

JWT access tokens expire after 15 minutes. Before expiry the application must
display a visible, keyboard-accessible warning: "Your session will expire in
{N} minutes. [Extend session] [Log out]" — satisfying WCAG 2.2.1 (Timing Adjustable).
The warning must appear at least 2 minutes before expiry. Auto-logout without
warning is a WCAG failure and is prohibited.

### 31.13 Testing Requirements

Accessibility is tested at four levels, all mandatory:

**Level 1 — Automated (CI gate):**
`axe-core` runs on every page component via `vitest-axe` in the frontend test suite.
Any axe violation at level `critical` or `serious` fails the CI build.
No merging of code with outstanding axe violations.

**Level 2 — Automated (full-page):**
Playwright end-to-end tests inject axe-core and run it on every route in both
authenticated and public states. Run on every PR against a seeded test database.

**Level 3 — Manual keyboard testing:**
Before any UI component is marked complete, the developer must verify:
- Tab through every interactive element in logical order
- Operate every control using only keyboard
- Confirm focus is always visible and never obscured
- Confirm modals trap focus and return focus on close
- Confirm all drag interactions have working button alternatives

**Level 4 — Screen reader testing:**
Before each release, the following combinations must be tested:
- NVDA + Firefox (Windows) — most common free screen reader
- VoiceOver + Safari (macOS/iOS)
- JAWS + Chrome (Windows) — most common enterprise screen reader

Test the following flows:
1. Unauthenticated: browse exhibitions, view a document, read OCR transcript
2. Authenticated: upload a file, fill in metadata, add an authority link, save

Test results are documented in `docs/accessibility/screen-reader-testing.md`
and committed with each release.

### 31.14 Prohibited Patterns

The following patterns are explicitly banned and must never appear in merged code:

- `outline: none` or `outline: 0` without a WCAG-compliant visible alternative
- `tabindex` values greater than 0 (breaks natural tab order)
- Color as the sole differentiator of state or meaning
- `aria-hidden="true"` on any element that contains focusable children
- `display: none` on content that is only conditionally hidden for visual reasons
  (use `visibility: hidden` + `pointer-events: none` or proper modal trapping)
- Placeholder text used as the only label for an input
- Tooltips as the only accessible name for a control (tooltips are not exposed
  reliably by all screen reader / browser combinations)
- `<div>` or `<span>` used as interactive elements without `role`, `tabindex="0"`,
  and keyboard event handlers
- Auto-playing media without pause controls
- CAPTCHA or image-based authentication
- Blocking paste in password fields

---

## 32. Dublin Core Integration

Dublin Core is the universal metadata interoperability layer. Every document in
ADMS has a canonical Dublin Core representation used for XMP embedding, OAI-PMH
harvesting, `dc_xml` export, and social sharing metadata. This section defines
the authoritative crosswalk.

### 34.1 ADMS → Dublin Core Crosswalk

The fifteen DCMI metadata terms and their ADMS sources:

| DC Element | DCMI URI | ADMS Source Field(s) | Notes |
|---|---|---|---|
| `dc:title` | `dcterms:title` | `documents.title` | Use `public_title` if set and document is public |
| `dc:creator` | `dcterms:creator` | `authority_records.authorized_name` via `creator_id` | Free text if no authority record |
| `dc:subject` | `dcterms:subject` | `vocabulary_terms.term` where domain = `tag` or `subject_category` | Pipe-delimited in flat formats |
| `dc:description` | `dcterms:description` | `documents.scope_and_content` | Fall back to `general_note` if null |
| `dc:publisher` | `dcterms:publisher` | `system_settings['institution.name']` | Repository name |
| `dc:contributor` | `dcterms:contributor` | Additional creators from `document_relationships` where type = `contributor` | Optional |
| `dc:date` | `dcterms:date` | `documents.date_display` | Prefer human-readable over normalized |
| `dc:date` (created) | `dcterms:created` | `documents.date_start` | ISO 8601 |
| `dc:type` | `dcterms:type` | `vocabulary_terms.term` where domain = `document_type` | DCMI Type Vocabulary where mappable |
| `dc:format` | `dcterms:format` | `document_files.mime_type` | First file's MIME type |
| `dc:format` (extent) | `dcterms:extent` | `documents.extent` | e.g., "3 pages" |
| `dc:identifier` | `dcterms:identifier` | `documents.accession_number` | Prefix with repository base URL for URIs |
| `dc:source` | `dcterms:source` | `documents.location_of_originals` | Physical location of original |
| `dc:language` | `dcterms:language` | `documents.language_of_material` | ISO 639-2 codes |
| `dc:relation` | `dcterms:relation` | `document_relationships` | Formatted as accession number or URI |
| `dc:coverage` | `dcterms:spatial` | `documents.geo_location_name` | Geographic coverage |
| `dc:coverage` | `dcterms:temporal` | `documents.date_start` + `date_end` | Date range if both set |
| `dc:rights` | `dcterms:rights` | `documents.copyright_status` + `rights_note` | Human-readable rights statement |
| `dc:rights` | `dcterms:license` | `documents.rights_basis` | License URI where applicable |

### 34.2 DCMI Type Vocabulary Mapping

When `document_type` vocabulary terms can be mapped to the DCMI Type Vocabulary, they
should be. The following mappings are pre-seeded:

| ADMS document_type | DCMI Type |
|---|---|
| `photograph` | `dctype:StillImage` |
| `map` | `dctype:StillImage` |
| `oral_history` | `dctype:Sound` |
| `letter`, `deed`, `manuscript`, `report`, `minutes`, `petition`, `memoir` | `dctype:Text` |
| All others | `dctype:PhysicalObject` or left as free text |

### 34.3 XMP Dublin Core Embedding

Every file served via `GET /api/v1/documents/{id}/files/{fid}/download` (and in
ZIP exports) must have Dublin Core XMP embedded in the file before it is sent to
the client. The embedding runs in the Celery task
`workers.export.embed_xmp_metadata(document_id, file_id, output_path)`.

**For PDF files** — use `pikepdf` to write XMP metadata:
```python
# app/xmp/pdf.py
import pikepdf
from pikepdf import Dictionary, Name, String

def embed_dc_xmp(input_path: Path, dc: dict, output_path: Path) -> None:
    """Write Dublin Core XMP into a PDF without modifying the original."""
    with pikepdf.open(input_path) as pdf:
        with pdf.open_metadata() as meta:
            meta["dc:title"] = dc.get("title", "")
            meta["dc:creator"] = dc.get("creator", [])
            meta["dc:description"] = dc.get("description", "")
            meta["dc:date"] = dc.get("date", "")
            meta["dc:identifier"] = dc.get("identifier", "")
            meta["dc:subject"] = dc.get("subject", [])
            meta["dc:rights"] = dc.get("rights", "")
            meta["dc:language"] = dc.get("language", "")
            meta["dc:publisher"] = dc.get("publisher", "")
            meta["dc:format"] = "application/pdf"
        pdf.save(output_path)
```

**For image files** — use Pillow with piexif for JPEG/TIFF, or write XMP sidecar for
formats that do not support embedded XMP natively. For PNG files, embed XMP as a
PNG text chunk using the `iTXt` chunk type.

The original stored file is never modified. A temporary output file is written to
`{STORAGE_ROOT}/.exports/{uuid}/` and streamed to the client, then deleted.

### 34.4 OAI-PMH Endpoint

`GET /oai` implements the OAI-PMH 2.0 protocol for metadata harvesting. This allows
external aggregators, library catalogs, and other archival systems (including AtoM
installations) to harvest ADMS records automatically.

**Required verbs:**
- `Identify` — repository name, admin email, earliest datestamp
- `ListMetadataFormats` — supports `oai_dc` (Dublin Core); `oai_ead` is Phase 2
- `ListRecords` — paginates through all public documents as `oai_dc` records
- `GetRecord` — returns a single record by OAI identifier
- `ListIdentifiers` — returns identifiers without full records
- `ListSets` — returns arrangement_nodes as OAI sets

**OAI identifier format:** `oai:{BASE_DOMAIN}:{accession_number}`
Example: `oai:adms.fallschurch.org:2025-0042`

**Resumption tokens:** Required for `ListRecords` and `ListIdentifiers` when the
result set exceeds 100 records. Use cursor-based pagination (last seen ID), not
offset, to ensure stability.

**Deleted records:** Records that are deaccessioned must remain in OAI-PMH with
`status="deleted"` for a minimum of 30 days so harvesters can remove them.

**Only public records are exposed.** Documents with `is_public = FALSE` or
`embargo_end_date` in the future must not appear in OAI-PMH responses.

### 34.5 Dublin Core XML Export Format

The `dc_xml` export produces a valid `oai_dc:dc` document:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<oai_dc:dc
  xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:dcterms="http://purl.org/dc/terms/"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/
    http://www.openarchives.org/OAI/2.0/oai_dc.xsd">
  <dc:title>{title}</dc:title>
  <dc:creator>{creator}</dc:creator>
  <dc:subject>{subject}</dc:subject>
  ...
</oai_dc:dc>
```

This is generated by `app/export/dublin_core.py` using `lxml`. The same module
provides `to_dict()` for the JSON variant and `to_xmp_dict()` for pikepdf embedding.

### 34.6 Schema.org Structured Data (Public Site)

Every public document page must include a `<script type="application/ld+json">` block
with schema.org structured data derived from the Dublin Core crosswalk. This enables
Google, Bing, and other search engines to understand the archival nature of the content.

```json
{
  "@context": "https://schema.org",
  "@type": "ArchiveComponent",
  "name": "{dc:title}",
  "creator": { "@type": "Person", "name": "{dc:creator}" },
  "dateCreated": "{dc:date}",
  "description": "{dc:description}",
  "identifier": "{dc:identifier}",
  "inLanguage": "{dc:language}",
  "holdingArchive": { "@type": "ArchiveOrganization", "name": "{dc:publisher}" },
  "rights": "{dc:rights}"
}
```

Exhibition pages use `@type: "ExhibitionEvent"`. Collection (arrangement_node) pages
use `@type: "Collection"`.

---

## 33. Out of Scope (Do Not Implement)

The following are explicitly out of scope for the initial build:

- Email notifications, including scheduled report delivery (design for it; do not implement yet)
- Elasticsearch integration (MySQL full-text is sufficient for phase 1)
- IIIF image server (future enhancement)
- MARC21 export (future enhancement)
- METS export (future enhancement; schema noted in §11.2)
- Audio/video file playback and oral history metadata fields (Phase 2)
- Crowdsourced community transcription (Phase 2; public user accounts not in scope now)
- Researcher access request and reading room appointment system (Phase 2)
- Printable finding aid PDF generator (Phase 2; EAD export covers machine-readable finding aids)
- Biographical network visualization page for authority records (Phase 2; the data layer — §5.12 `authority_relationships` and §5.11 `document_authority_links` — is built in Phase 1)
- **Kubernetes deployment manifests.** ADMS's target users are historians and archivists
  running Docker Compose on a home server or VPS. Kubernetes requires dedicated
  infrastructure expertise that most institutions in this domain do not have and
  should not need to acquire to manage their archives. The Docker images are
  portable and could be deployed to Kubernetes by an institution with the staff
  to support it, but ADMS will not ship, test, or support Kubernetes configuration.
  See §4.3 for the supported deployment tiers.
- AWS ECS task definitions, Helm charts, or any other cloud-specific orchestration
  configuration (same reasoning as Kubernetes above)
- Docker Swarm configuration (same reasoning; Tier 2 VPS deployment covers the use case)
- OAI-EAD metadata format in OAI-PMH (Phase 2; `oai_dc` is sufficient for phase 1)
- Scheduled/automated reports delivered by email or calendar (Phase 2)
- Mobile app
- Real-time collaborative editing
- Automated format migration (fixity checking and format inventory are in scope;
  actual migration of files to new formats is not)
- ISO 16363 certification audit tooling (the schema supports a self-assessment;
  automated certification tooling is out of scope)
- ARK identifier assignment at import time (the schema and routing support ARKs;
  bulk ARK minting and NAAN registration workflows are Phase 2)

Do not add stubs, TODO comments, or placeholder routes for these features.
They will be designed and added in a future phase.

---

## 34. Professional Standards Reference

The application implements or aligns with the following professional standards.
These must be cited in the application's documentation, help pages, and about screen.

| Standard | Body | Scope in ADMS |
|---|---|---|
| **DACS** (Describing Archives: A Content Standard, 2nd ed., 2019) | Society of American Archivists | Primary U.S. descriptive standard; all document metadata fields |
| **ISAD(G)** (General International Standard Archival Description, 2nd ed., 2000) | International Council on Archives | All 26 elements across 7 areas in the documents schema |
| **ISAAR(CPF)** (International Standard Archival Authority Record, 2nd ed., 2004) | International Council on Archives | authority_records table; creator/donor linking |
| **EAD3** (Encoded Archival Description, version 3, 2015) | SAA / Library of Congress | EAD3 XML export for collection-level descriptions |
| **Dublin Core (DCMI Metadata Terms)** | Dublin Core Metadata Initiative | Native crosswalk (§22); XMP embedding; OAI-PMH; dc_xml export; schema.org |
| **OAIS** (ISO 14721:2025, Reference Model for an Open Archival Information System) | ISO / CCSDS | Fixity checking, preservation events, format characterization, ingest workflow |
| **PREMIS v3** (Data Dictionary for Preservation Metadata, 2015) | Library of Congress / OCLC | preservation_events table; technical metadata fields on document_files |
| **NARA Technical Guidelines for Digitizing Archival Materials** | U.S. National Archives | Technical metadata fields; preservation format warnings; image quality ratings |
| **LoC Recommended Formats Statement** | Library of Congress | Preferred format guidance; preservation warnings for sub-standard formats |
| **AASLH Statement of Standards and Ethics** (revised 2018) | American Association for State and Local History | Deaccession workflow; donor agreements; rights metadata; collections stewardship |
| **SAA Core Values and Code of Ethics** | Society of American Archivists | Audit log; transparency; access control; preservation commitment |
| **Chicago Manual of Style, 17th edition** | University of Chicago Press | Citation export format for archival documents and collections |
| **OHA Archiving Oral History Best Practices** | Oral History Association | Oral history document type in controlled vocabulary; schema does not block audio/video |

### 24.1 Controlled Vocabulary Seed Data

The initial database migration must seed the following vocabulary domain terms, in addition
to those listed in §5.7:

**document_type domain** (comprehensive seed list):
`letter`, `deed`, `legal_document`, `photograph`, `map`, `report`, `minutes`,
`memorandum`, `telegram`, `diary`, `ledger`, `census_record`, `newspaper_clipping`,
`pamphlet`, `broadside`, `manuscript`, `petition`, `ordinance`, `court_record`,
`military_record`, `oral_history`, `birth_certificate`, `death_certificate`,
`land_patent`, `survey`, `blueprint`, `scrapbook`, `postcard`, `invoice`, `receipt`,
`will`, `inventory`, `subscription_list`, `election_record`, `tax_record`, `permit`

**deaccession_reason domain** (required for deaccession workflow):
`mission_misalignment`, `poor_condition_irreparable`, `duplicate`,
`donor_request`, `legal_requirement`, `transfer_to_better_repository`, `out_of_scope`

**image_quality_rating domain** (informational reference):
`preservation_master` (uncompressed TIFF or PDF/A at 300+ PPI),
`production_master` (high-quality derivative, minimal compression),
`access_copy` (JPEG or compressed derivative for display only),
`unknown`

**dc_type domain** (DCMI Type Vocabulary; used in Dublin Core crosswalk):
`dctype:Collection`, `dctype:Dataset`, `dctype:Event`, `dctype:Image`,
`dctype:InteractiveResource`, `dctype:MovingImage`, `dctype:PhysicalObject`,
`dctype:Service`, `dctype:Software`, `dctype:Sound`, `dctype:StillImage`, `dctype:Text`

---

## 35. Multi-Instance Management

### 35.1 Architecture

Each organization or repository is a completely isolated ADMS installation: its
own Docker Compose stack, its own MySQL database, its own Redis, its own storage
volume, its own NoCoDB, and its own public URL. There is no shared infrastructure
between instances. A staff member at the Falls Church VFD cannot see or access
anything from the Falls Church Historical Society, and vice versa — not through
the application, not through NoCoDB, and not through the database.

This isolation is the correct architecture because the five answers to the
multi-tenancy design questions were all "separate." When nothing is shared,
combining instances adds complexity with no benefit and introduces risk.

The operational challenge of running multiple isolated stacks on one server is
solved by the `adms-manager` companion tool, not by modifying the application.

### 35.2 How a Single Server Hosts Multiple Instances

```
Host server (Unraid, VPS, or any Linux host)
│
├── Shared reverse proxy (nginx)        ← maps domains to instance ports
│   ├── vfd.example.org → :3001
│   ├── history.example.org → :3002
│   └── church.example.org → :3003
│
├── Instance: falls-church-vfd          ← docker compose project "adms-vfd"
│   ├── frontend → :3001 (internal)
│   ├── backend  → :8001 (internal)
│   ├── mysql    → :3307 (internal)
│   ├── redis    → :6380 (internal)
│   └── nocodb   → :8081 (internal)
│
├── Instance: falls-church-historical   ← docker compose project "adms-hist"
│   ├── frontend → :3002 (internal)
│   ├── backend  → :8002 (internal)
│   ├── mysql    → :3308 (internal)
│   ├── redis    → :6381 (internal)
│   └── nocodb   → :8082 (internal)
│
└── Instance storage
    ├── /mnt/user/adms/vfd/storage/
    └── /mnt/user/adms/hist/storage/
```

The reverse proxy is the only shared component. It is responsible for routing
traffic by hostname to the correct instance's frontend port. Each instance's
ports are internal to the host — they do not need to be exposed externally.

### 35.3 The adms-manager Tool

`adms-manager` is a POSIX sh script in the `manager/` directory of the ADMS
repository. It handles the repetitive operational work of managing multiple
instances: creating, starting, stopping, updating, backing up, and destroying them.

It maintains a registry file at `~/.adms/registry` (or a path set via
`ADMS_REGISTRY_PATH` env var) that tracks all instances on the host.

**Registry file format (`~/.adms/registry`):**
```
# adms instance registry
# format: name|directory|domain|frontend_port|backend_port|mysql_port|redis_port|nocodb_port|created_at
falls-church-vfd|/opt/adms/instances/falls-church-vfd|vfd.example.org|3001|8001|3307|6380|8081|2025-01-15
falls-church-hist|/opt/adms/instances/falls-church-hist|history.example.org|3002|8002|3308|6381|8082|2025-02-01
```

Plain text, tab-separated, no dependencies. Readable and editable with any text editor.

### 35.4 adms-manager Commands

All commands follow the pattern `adms-manager <command> [instance-name]`.
Instance names must be lowercase letters, numbers, and hyphens only.

```
adms-manager create [name]
    Interactive wizard. Prompts for:
    - Instance name (e.g. falls-church-vfd)
    - Institution name (written into .env as INSTITUTION_NAME)
    - Public domain (e.g. vfd.example.org)
    - Storage path on host (e.g. /mnt/user/adms/vfd/storage)
    - Admin email address
    Assigns unique ports automatically by scanning the registry.
    Generates docker-compose.yml and .env from templates.
    Writes the instance to the registry.
    Does NOT start the instance — run "adms-manager start <name>" next.

adms-manager list
    Prints all registered instances with their domain, ports, and current
    status (running / stopped / partially running).

adms-manager start <name>
    Runs: docker compose -p adms-<name> -f <instance-dir>/docker-compose.yml up -d
    Waits for the health check endpoints to respond before returning.

adms-manager stop <name>
    Runs: docker compose -p adms-<name> stop
    Does not remove containers or volumes.

adms-manager restart <name>
    Stop then start.

adms-manager update <name>
    Pulls the latest ADMS images, runs database migrations, restarts the instance.
    Sequence:
    1. docker compose pull
    2. docker compose run --rm backend alembic upgrade head
    3. docker compose up -d

adms-manager backup <name>
    Creates a timestamped backup archive at <instance-dir>/backups/.
    Contains:
    - mysqldump of the instance database (compressed)
    - tar of the instance storage directory
    - copy of the current .env file (secrets included — store backups securely)
    Prints the backup filename on completion.

adms-manager restore <name> <backup-file>
    Restores from a backup archive created by "adms-manager backup".
    Stops the instance, restores database and files, restarts.
    Requires explicit confirmation before proceeding.

adms-manager logs <name> [service]
    Tails logs for the instance. If [service] is provided (backend, worker,
    frontend, db, nocodb), tails only that service's logs.

adms-manager status <name>
    Shows the running status of each container in the instance,
    storage usage, and last backup date.

adms-manager proxy-config
    Generates an nginx server block configuration for all registered instances.
    Prints to stdout; the operator pipes it to the appropriate nginx config file.
    Example output for one instance:
    server {
        listen 80;
        server_name vfd.example.org;
        location / { proxy_pass http://localhost:3001; }
    }
    The operator is responsible for TLS termination on top of this config.

adms-manager destroy <name>
    Permanently removes the instance. Sequence:
    1. Prints a warning listing what will be deleted.
    2. Prompts the operator to type the instance name to confirm.
    3. Stops all containers.
    4. Removes containers and volumes.
    5. Removes the instance directory.
    6. Removes the instance from the registry.
    Storage data is NOT deleted by default. A separate flag --delete-storage
    must be passed to also remove the storage directory.
```

### 35.5 Per-Instance File Structure

```
/opt/adms/instances/falls-church-vfd/    (or wherever the operator chooses)
├── docker-compose.yml    # Generated from template; do not edit by hand
├── .env                  # Instance configuration; edit to change settings
├── backups/              # Created by adms-manager backup
│   └── 2025-01-15T0200.tar.gz
└── data -> /mnt/user/adms/vfd/storage   # Symlink to actual storage path
```

The `docker-compose.yml` for each instance is generated from
`manager/templates/docker-compose.yml.tmpl` with the instance's ports and
project name substituted. It is identical to the base `docker-compose.yml`
in the ADMS repo except for:
- Port bindings (unique per instance)
- Volume names prefixed with `adms-{name}-`
- Docker Compose project name set to `adms-{name}`
- `STORAGE_ROOT` set to the instance's storage path

### 35.6 Port Assignment

Ports are assigned sequentially starting from base values, with each instance
taking the next available block of 5 ports:

| Instance # | Frontend | Backend | MySQL | Redis | NoCoDB |
|---|---|---|---|---|---|
| 1 | 3001 | 8001 | 3307 | 6380 | 8081 |
| 2 | 3002 | 8002 | 3308 | 6381 | 8082 |
| 3 | 3003 | 8003 | 3309 | 6382 | 8083 |
| N | 3000+N | 8000+N | 3306+N | 6379+N | 8080+N |

`adms-manager create` reads the registry to find the highest-numbered port
in use and assigns the next block. It also checks with `ss -tlnp` that the
assigned ports are not already in use by another process before committing them.

### 35.7 NoCoDB Per Instance

Each instance's Docker Compose stack includes its own NoCoDB container, configured
to point at that instance's MySQL database. The NoCoDB admin interface is accessible
at `http://host:8081` (or the instance's NoCoDB port) directly, or through the
reverse proxy at `nocodb.vfd.example.org` if the operator chooses to expose it.

Each instance's NoCoDB is entirely independent — a separate NoCoDB installation
with its own admin account, its own API tokens, and its own base configuration.
There is no shared NoCoDB installation.

### 35.8 Reverse Proxy Configuration

The operator is responsible for configuring and maintaining the reverse proxy
on the host. `adms-manager proxy-config` generates the nginx server blocks;
the operator applies them.

A minimal working nginx setup for two instances on a host with TLS via Certbot:

```nginx
# /etc/nginx/sites-available/adms-vfd
server {
    listen 443 ssl;
    server_name vfd.example.org;
    ssl_certificate /etc/letsencrypt/live/vfd.example.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/vfd.example.org/privkey.pem;

    location / {
        proxy_pass http://localhost:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto https;
    }
}

# /etc/nginx/sites-available/adms-hist
server {
    listen 443 ssl;
    server_name history.example.org;
    ssl_certificate /etc/letsencrypt/live/history.example.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/history.example.org/privkey.pem;

    location / {
        proxy_pass http://localhost:3002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

On Unraid, the built-in nginx proxy manager or the Nginx Proxy Manager Docker
container can replace this configuration with a GUI-based setup pointing to
the same localhost ports.

### 35.9 Updating All Instances

To update all instances to the latest ADMS version:

```sh
adms-manager list | awk -F'|' 'NR>1 {print $1}' | xargs -I{} adms-manager update {}
```

Updates run sequentially — one instance at a time. This prevents a failed
update from taking down multiple organizations simultaneously. Each instance
goes through its own migration before restart.

### 35.10 Isolation Guarantee

The isolation between instances is enforced at the infrastructure level, not
the application level. Even if a bug were introduced into ADMS, it could not
cause data from one instance to appear in another, because:

- Each instance has its own MySQL database on a different port
- Each instance's Docker Compose volumes are prefixed with the instance name
- Each instance's storage is in a separate directory on the host
- Containers in different Docker Compose projects share no network by default
- Each instance's NoCoDB connects only to its own MySQL

An operator who wants additional isolation (e.g., two instances must not share
the same host for compliance reasons) should deploy each to a separate server
as two completely independent Docker Compose stacks with no shared tooling.
`adms-manager` in that scenario is still useful on each individual server.
