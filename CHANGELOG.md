# Changelog

All notable changes to the Archival Document Management System (ADMS) are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [0.2.0] — 2026-04-09

### Added — Database Completeness

- **Migration 002**: 22 remaining database tables
  - `document_files` — file records with technical metadata (NARA/FADGI), format characterization (PREMIS), OCR status
  - `document_pages` — per-page OCR text, thumbnails, public visibility
  - `document_terms` — document↔vocabulary junction (tags, categories)
  - `document_relationships` — directional document-to-document links (reply_to, revision_of, etc.)
  - `document_authority_links` — document↔authority junction with roles (recipient, signatory, witness, etc.)
  - `authority_relationships` — authority↔authority biographical links (spouse_of, parent_of, member_of, etc.)
  - `locations` — controlled place entities with coordinates and hierarchy
  - `document_location_links` — document↔location junction with link types
  - `events` — named historical occurrences with types and dates
  - `event_document_links`, `event_authority_links`, `event_location_links` — event junction tables
  - `collection_permissions` — node-level RBAC with cascade inheritance
  - `review_queue` — LLM/NER/import/integrity review items with priority and assignment
  - `exhibitions`, `exhibition_tags`, `exhibition_pages`, `exhibition_page_blocks` — full exhibition schema
  - `public_pages` — static narrative pages (About, Credits, etc.)
  - `audit_log` — immutable action log with JSON detail
  - `preservation_events` — PREMIS event entities (ingest, fixity, OCR, etc.)
  - `fixity_checks` — SHA-256 verification records
  - `watch_folders` — consume folder ingest configuration
  - `saved_views` — personal dashboard filter presets
  - `deaccession_log` — immutable AASLH deaccession records
  - `institution_description_standards` — configurable DACS completeness levels
  - `csv_imports`, `csv_import_rows` — import job tracking
  - `document_annotations` — region and text_range staff annotations
- **FULLTEXT index** on `documents(title, scope_and_content, general_note)` for MySQL full-text search
- **150+ vocabulary seed terms** across all 14 domains:
  - `document_type`: 36 terms (letter, deed, photograph, map, report, minutes, etc.)
  - `physical_format`: 10 terms (paper, photographic_print, glass_plate, etc.)
  - `condition`: 5 terms (excellent, good, fair, poor, damaged)
  - `relationship_type`: 8 terms (reply_to, precedes, follows, revision_of, etc.)
  - `access_restriction`: 4 terms (public, restricted, confidential, embargoed)
  - `authority_link_role`: 12 terms (recipient, signatory, witness, mentioned, etc.)
  - `authority_relationship_type`: 11 terms (spouse_of, parent_of, child_of, etc.)
  - `location_type`: 17 terms (building, neighborhood, city, cemetery, etc.)
  - `event_type`: 18 terms (meeting, election, fire, ceremony, etc.)
  - `event_authority_role`: 11 terms (organizer, attendee, speaker, etc.)
  - `deaccession_reason`: 7 terms (mission_misalignment, duplicate, etc.)
  - `language`: 18 ISO 639 codes (eng, fra, deu, spa, etc.)
- **Default DACS description standards** seeded for minimal/standard/full levels

### Added — Backend Features

- **NER Worker** (`app/workers/ner.py`) — spaCy-based named entity recognition pipeline:
  - Extracts PERSON, ORG, GPE, LOC, DATE entities from OCR text
  - Fuzzy matches entities against existing authority records and locations (>0.85 similarity)
  - Creates pending authority records for unmatched persons/organizations
  - Geocodes unmatched locations via Nominatim API (server-side)
  - Stores suggestions in `documents.llm_suggestions.ner` JSON
  - All suggestions require human review — never auto-applied
  - Integrated into Celery autodiscovery and routed to `llm` queue
- **OAI-PMH Service** (`app/services/oai_service.py`) — protocol-compliant metadata harvesting:
  - Full OAI-PMH 2.0 verb support (Identify, ListMetadataFormats, ListRecords, GetRecord, ListIdentifiers, ListSets)
  - Cursor-based resumption tokens for paginated results
  - Deleted record tracking for deaccessioned documents
  - Public-only filtering (is_public=TRUE, embargo checks)
  - Arrangement nodes exposed as OAI sets
- **12 Test Files** — backend test suite:
  - Unit tests: auth_service, document_service, permission_service, completeness_service, vocabulary_service, storage_resolver, citations, dublin_core
  - Integration tests: auth API, documents API, search API, vocabulary API

### Added — Frontend Components

- **FileViewer** (`components/ui/FileViewer.tsx`) — WCAG 2.2 AA document viewer:
  - Paginated image viewer and PDF embed
  - Zoom controls with accessible labels
  - OCR transcript panel with status indicators
  - Failed OCR error display with retry button
  - Annotation overlay toggle
  - Page thumbnail sidebar
  - Multi-file selector
- **MapBlock** (`components/ui/MapBlock.tsx`) — accessible Leaflet map:
  - OpenStreetMap and satellite basemap options
  - "View as list" text alternative (WCAG 31.8)
  - Keyboard-accessible markers with popups
  - `role="application"` wrapper
- **ExhibitionBlockRenderer** (`components/ui/ExhibitionBlockRenderer.tsx`) — all 9 block types:
  - `html` — DOMPurify-sanitized HTML
  - `file_with_text` — image + text side-by-side with position control
  - `gallery` — responsive 2/3/4-column grid with captions
  - `document_metadata` — full ISAD(G) metadata display
  - `map` — lazy-loaded MapBlock
  - `timeline` — delegates to TimelineBlock
  - `table_of_contents` — recursive page hierarchy
  - `collection_browse` — grid/list collection display
  - `separator` — solid/dashed/blank dividers
  - Layout positioning: full, left, right, center
- **TimelineBlock** (`components/ui/TimelineBlock.tsx`) — vertical timeline:
  - Chronological document display with date markers
  - Thumbnail and description excerpts
  - Proper `aria-posinset`/`aria-setsize` semantics
- **SessionTimeout** (`components/ui/SessionTimeout.tsx`) — WCAG 2.2.1 compliance:
  - Warning modal 2 minutes before JWT expiry
  - Live countdown with `aria-live="polite"`
  - "Extend session" and "Log out" buttons
  - Focus-trapped modal dialog
  - Integrated into AppShell layout
- **ReorderableList** (`components/ui/ReorderableList.tsx`) — WCAG 2.5.7 compliance:
  - Up/Down buttons as keyboard alternative to drag-and-drop
  - Screen reader announcements on reorder
  - Focus follows moved item
- **ColumnMapper** (`components/ui/ColumnMapper.tsx`) — CSV import column mapping:
  - Source column to ADMS field mapping via dropdowns
  - Preview of first 3 rows
  - Required field validation
- **Schema.org JSON-LD** (`utils/structuredData.ts`) — structured data helpers:
  - `generateDocumentLD()` → ArchiveComponent
  - `generateExhibitionLD()` → ExhibitionEvent
  - `generateCollectionLD()` → Collection
  - Integrated into PublicDocumentPage, PublicExhibitPage, PublicCollectionsPage
- **Print Stylesheet** — comprehensive `@media print` rules:
  - Hides navigation, sidebar, footer, interactive elements
  - Serif typography for readability
  - URL display for links, accession number formatting
  - Page break control, metadata definition list styling
- **Form Validation** — react-hook-form + Zod integration:
  - LoginPage: email validation, password paste allowed (WCAG 3.3.8/3.3.9)
  - DocumentEditPage: all ISAD(G) fields with cross-field date validation
  - DocumentNewPage: same validation schema
  - Error summaries with focus management, `aria-invalid`, `aria-describedby`

---

## [0.1.0] — 2026-04-09

### Added — Project Foundation

- **Docker Compose** deployment with 7 services:
  - `db` (MySQL 8.0) — primary data store, utf8mb4 collation
  - `redis` (Redis 7) — Celery broker and result backend
  - `backend` (FastAPI) — async API server with Uvicorn
  - `worker` (Celery) — async task processing
  - `beat` (Celery Beat) — scheduled task execution
  - `frontend` (React/Vite via nginx) — SPA serving
  - `nocodb` (NoCoDB) — spreadsheet interface to same MySQL
- **Environment configuration** via `.env.example` with all required variables
- **Dockerfiles** for backend (Python 3.12, Tesseract, Siegfried) and frontend (Node 20, nginx)

### Added — Backend (Python/FastAPI)

- **30+ SQLAlchemy ORM models** covering all ISAD(G) fields, DACS, PREMIS, Dublin Core
- **Migration 001**: core tables (users, roles, documents, vocabulary, authority_records, arrangement_nodes, version_groups, storage_schemes, sequences, system_settings, donor_agreements)
- **Alembic** migration framework with env.py and script template
- **Pydantic v2 schemas** (14 schema files) for all request/response types
- **20 FastAPI routers** with 169 total endpoints covering:
  - Authentication (JWT with httpOnly cookies, refresh tokens)
  - Full CRUD for documents, authority records, locations, events, exhibitions, vocabulary
  - File upload/download with XMP metadata embedding
  - Document versioning workflow (create group, add version, set canonical/public)
  - Citation export (Chicago, Turabian, BibTeX, RIS, CSL-JSON)
  - Metadata export (Dublin Core XML/JSON, EAD3 XML)
  - OAI-PMH 2.0 endpoint
  - Persistent URL resolution (/d/{accession} and /ark/{naan}/{id})
  - Public API (unauthenticated exhibition/document access)
  - Admin: reports, preservation, imports, settings, users
- **19 service modules** with business logic:
  - Permission resolution (5-level cascade: superadmin → user → role → inherited → global)
  - Atomic accession number generation with `SELECT ... FOR UPDATE`
  - Description completeness scoring against configurable standards
  - Vocabulary term merging with document reassignment
  - Audit logging on all CUD operations
  - Search with MySQL FULLTEXT + version filtering
- **8 Celery workers**:
  - OCR (Tesseract via pytesseract, 3 retries with exponential backoff)
  - LLM metadata suggestions (OpenAI, Anthropic, Ollama adapters)
  - Fixity checks (SHA-256 verification, weekly via beat)
  - Watch folder ingest (60-second polling, quarantine pipeline)
  - Thumbnail generation (300px WebP via Pillow/pdf2image)
  - Description completeness recomputation (nightly batch)
  - XMP metadata embedding (pikepdf for PDF, Pillow for images)
- **Export modules**:
  - Dublin Core crosswalk (ISAD(G) → DC mapping, XML/JSON/XMP dict)
  - EAD3 XML generation for collection subtrees
  - Citation formatting (6 formats with version support)
- **3 LLM adapters** (OpenAI, Anthropic, Ollama) with provider-agnostic interface
- **Storage resolver** with 5 path schemes (date, location, donor, subject, record_number)

### Added — Frontend (TypeScript/React 18/Vite)

- **30 page components** covering all routes:
  - Archive browse, document CRUD, inbox queue, review queue
  - Authority records, locations, events (list + detail)
  - Vocabulary management, exhibitions
  - Full-text search with faceted filters
  - 5 admin pages (users, settings, preservation, imports, reports)
  - 6 public pages (home, exhibits, exhibit detail, document, search, collections)
- **State management**:
  - TanStack Query (React Query v5) for all server state
  - Zustand stores for auth, inbox count, UI state (sidebar, theme, toasts)
  - React Context for theme and institution settings
- **7 custom hooks**: useAuth, useDocuments, usePermission, useInbox, useAnnouncer, useFocusTrap, useReducedMotion
- **7 API client modules**: documents, authority, locations, events, exhibitions, vocabulary, base client
- **5 service modules**: permissions, citation, completeness, import validation, accessibility
- **6 UI components**: Button, Modal, Toast, Badge, Spinner, SkipNav
- **4 layout components**: AppShell, PublicShell, Navbar, Sidebar, Footer
- **WCAG 2.2 AA compliance**:
  - Design tokens (tokens.css) with documented contrast ratios
  - Focus-visible outlines (3px solid, #005fcc/#66b3ff)
  - Skip navigation link
  - ARIA live regions for dynamic content
  - 44px minimum touch targets
  - Dark mode (prefers-color-scheme)
  - Reduced motion (prefers-reduced-motion)

### Added — Operations

- **adms-manager** POSIX shell tool for multi-instance management:
  - `create` — interactive wizard with auto port assignment
  - `list`, `start`, `stop`, `restart`, `update`
  - `backup` (mysqldump + storage tar), `restore`
  - `logs`, `status`
  - `proxy-config` — nginx server block generation
  - `destroy` — with confirmation prompt
  - Per-instance templates (.env, docker-compose.yml)
  - Registry file at ~/.adms/registry
