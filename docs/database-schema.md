# ADMS Database Schema Reference

**43 tables** across 10 domain groups. MySQL 8.0 with utf8mb4 collation.
All tables include `created_at` and `updated_at` (except immutable tables noted below).

---

## Entity-Relationship Overview

```
                    ┌──────────┐
                    │  users   │
                    └────┬─────┘
                         │ 1:N
                    ┌────┴─────┐
                    │user_roles│────── roles
                    └──────────┘

     ┌──────────────────┐        ┌───────────────────┐
     │ arrangement_nodes │◄──────│collection_permissions│
     │  (self-referencing)│       └───────────────────┘
     └────────┬──────────┘
              │ 1:N
     ┌────────┴──────────┐
     │    documents       │──────► authority_records (creator_id)
     │  (core entity)     │──────► vocabulary_terms (type, format, condition)
     │                    │──────► document_version_groups
     │                    │──────► donor_agreements
     └──┬──┬──┬──┬──┬────┘
        │  │  │  │  │
        │  │  │  │  └── document_terms ──► vocabulary_terms
        │  │  │  └───── document_relationships (self-join)
        │  │  └──────── document_authority_links ──► authority_records
        │  └─────────── document_location_links ──► locations
        └────────────── document_files
                           │ 1:N
                        document_pages
                           │
                        document_annotations

     authority_records ◄──► authority_relationships (self-join)

     ┌────────┐
     │ events │──── event_document_links ──► documents
     │        │──── event_authority_links ──► authority_records
     │        │──── event_location_links ──► locations
     └────────┘

     ┌────────────┐
     │ exhibitions │──── exhibition_pages ──── exhibition_page_blocks
     │             │──── exhibition_tags ──► vocabulary_terms
     └─────────────┘

     Immutable logs: audit_log, preservation_events, fixity_checks, deaccession_log
```

---

## Table Groups

### 1. Users & Authentication (4 tables)

**users** — Application user accounts
| Column | Type | Constraints |
|--------|------|------------|
| id | BIGINT PK | AUTO_INCREMENT |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| password_hash | VARCHAR(255) | NOT NULL (bcrypt) |
| display_name | VARCHAR(255) | NOT NULL |
| is_active | BOOLEAN | DEFAULT TRUE |
| is_superadmin | BOOLEAN | DEFAULT FALSE |
| last_login_at | DATETIME | nullable |

**roles** — Role definitions (seeded: superadmin, admin, archivist, contributor, intern, viewer)

**user_roles** — Users ↔ Roles junction (M:N)

**refresh_tokens** — JWT refresh token storage (hashed with SHA-256)

---

### 2. Hierarchy & Storage (3 tables)

**arrangement_nodes** — ISAD(G) hierarchy (self-referencing tree)
| Column | Type | Notes |
|--------|------|-------|
| parent_id | FK self | nullable (root nodes) |
| level_type | ENUM | fonds, subfonds, series, subseries, file, item |
| title | VARCHAR(500) | NOT NULL |
| identifier | VARCHAR(200) | local reference code |
| has_content_advisory | BOOLEAN | DEFAULT FALSE |

**storage_schemes** — File organization scheme configuration (only one active)

**sequences** — Atomic accession number generation (`SELECT ... FOR UPDATE`)

---

### 3. Documents (5 tables)

**documents** — Core entity with 60+ columns covering all ISAD(G) fields
| Area | Key Columns |
|------|------------|
| Identity | title, accession_number (UNIQUE), reference_code, date_display, date_start, date_end, level_of_description, extent |
| Context | creator_id (FK authority_records), administrative_history, archival_history, immediate_source |
| Content | scope_and_content, appraisal_notes, system_of_arrangement |
| Access | access_conditions, reproduction_conditions, language_of_material, physical_characteristics |
| Allied | location_of_originals, location_of_copies, related_units, publication_note |
| Notes | general_note, archivists_note |
| Description Control | rules_or_conventions, description_status (draft/revised/final), described_by |
| Rights | copyright_status, rights_holder, rights_basis, rights_note, embargo_end_date, donor_agreement_id |
| Versioning | version_group_id, version_number, version_label, is_canonical_version |
| Availability | availability_status (available/temporarily_unavailable/deaccessioned), tombstone_disclosure |
| Advisory | has_content_advisory, content_advisory_note |
| Completeness | description_completeness (none/minimal/standard/full) — computed |
| Geolocation | geo_latitude, geo_longitude, geo_location_name |
| Workflow | review_status, inbox_status, deaccession_status, llm_suggestions (JSON) |

**document_version_groups** — Ties multiple document records as versions of one item
- base_accession_number (UNIQUE), canonical_document_id, public_document_id

**document_files** — Physical files with technical metadata
- filename, stored_path, mime_type, file_size_bytes, file_hash_sha256
- OCR: ocr_status, ocr_text (LONGTEXT), ocr_error, ocr_attempt_count
- Technical (NARA/FADGI): scan_resolution_ppi, bit_depth, color_space, scanner_make
- Format (PREMIS): format_name, format_puid, format_version, format_registry
- preservation_warning

**document_pages** — Per-page records (OCR text, thumbnails, public visibility)

**document_annotations** — Staff annotations (region or text_range type)
- annotation_type ENUM(region, text_range)
- region_geometry JSON (percentage-based x1,y1,x2,y2)
- text_range JSON (start_offset, end_offset, quoted_text)
- is_resolved, resolved_by, resolved_at

---

### 4. Classification (3 tables)

**vocabulary_domains** — Controlled vocabulary categories (14 seeded domains)

**vocabulary_terms** — Terms within domains. UNIQUE(domain_id, term).
- Supports hierarchy via broader_term_id (self-FK)

**document_terms** — Documents ↔ Terms junction. UNIQUE(document_id, term_id).

**Seeded domains:** document_type (36 terms), physical_format (10), condition (5), tag, subject_category, relationship_type (8), access_restriction (4), language (18), authority_link_role (12), authority_relationship_type (11), location_type (17), event_type (18), event_authority_role (11), deaccession_reason (7)

---

### 5. Relationships & Links (4 tables)

**document_relationships** — Directional doc-to-doc links
- source_document_id, target_document_id, relationship_type_id (FK vocabulary_terms)
- UNIQUE(source, target, type)

**document_authority_links** — Doc ↔ Authority with role
- role_id FK vocabulary_terms (authority_link_role domain)
- UNIQUE(document_id, authority_id, role_id)

**document_location_links** — Doc ↔ Location with link type
- link_type ENUM(mentioned, depicted, created_at, event_location)

---

### 6. Authority Records (2 tables)

**authority_records** — Persons, organizations, families
| Column | Type | Notes |
|--------|------|-------|
| entity_type | ENUM | person, organization, family |
| authorized_name | VARCHAR(500) | NOT NULL |
| variant_names | TEXT | pipe-delimited |
| dates | VARCHAR(200) | e.g., "1842-1918" |
| wikidata_qid | VARCHAR(20) | e.g., "Q42" |
| wikidata_enrichment | JSON | cached Wikidata data |
| created_by_ner | BOOLEAN | TRUE if NER-suggested |

**authority_relationships** — Authority ↔ Authority biographical links
- relationship_type_id FK vocabulary_terms (authority_relationship_type domain)

---

### 7. Places & Events (5 tables)

**locations** — Controlled place entities with hierarchy
- authorized_name, variant_names, geo_latitude, geo_longitude
- location_type_id FK vocabulary_terms
- parent_location_id FK self

**events** — Named historical occurrences
- title, event_type_id FK vocabulary_terms, date_display, date_start, date_end
- primary_location_id FK locations

**event_document_links** — link_type ENUM(produced_by, about, referenced_in, precedes, follows)

**event_authority_links** — role_id FK vocabulary_terms (event_authority_role domain)

**event_location_links** — link_type ENUM(primary, secondary, mentioned)

---

### 8. Exhibitions (4 tables)

**exhibitions** — Published exhibit with metadata
- title, slug (UNIQUE), subtitle, description, credits, cover/header images
- accent_color, show_summary_page, is_published

**exhibition_pages** — Hierarchical pages within an exhibition
- parent_page_id FK self, title, slug, menu_title
- UNIQUE(exhibition_id, slug)

**exhibition_page_blocks** — Content blocks on pages
- block_type ENUM(html, file_with_text, gallery, document_metadata, map, timeline, table_of_contents, collection_browse, separator)
- content JSON, layout ENUM(full, left, right, center)

**exhibition_tags** — Exhibition ↔ Vocabulary Terms junction

---

### 9. Preservation (3 tables — immutable)

**preservation_events** — PREMIS event entities (no updated_at)
- event_type ENUM(ingest, fixity_check, format_validation, virus_scan, ocr, migration, deletion, access, modification, replication)
- event_outcome ENUM(success, failure, warning)
- agent (user ID or system process name)

**fixity_checks** — SHA-256 verification records (no updated_at)
- stored_hash, computed_hash, outcome ENUM(match, mismatch, file_missing)

**deaccession_log** — Immutable deaccession records (no updated_at)
- document_id (preserved after document deletion), accession_number, title
- disposition ENUM(destroyed, transferred, returned, sold, donated)

---

### 10. Administration (9 tables)

**audit_log** — Immutable action log (no updated_at)
- action VARCHAR(200), resource_type, resource_id, detail JSON, ip_address

**system_settings** — Key-value JSON settings store

**collection_permissions** — Node-level RBAC
- can_view, can_create, can_edit, can_delete, can_manage_permissions
- Exactly one of user_id or role_id must be non-null

**review_queue** — Items pending human review
- reason ENUM(llm_suggestions, manual_flag, import, initial_review, integrity_failure)
- priority ENUM(low, normal, high)

**donor_agreements** — Deed of gift, deposit, loan records (AASLH requirement)

**watch_folders** — Consume folder ingest configuration

**saved_views** — Personal dashboard filter presets

**csv_imports** / **csv_import_rows** — Import job tracking with per-row validation

**institution_description_standards** — Configurable completeness levels (3 rows: minimal, standard, full)

**public_pages** — Static narrative pages (About, Credits, etc.)

---

## Migration History

| Revision | File | Tables Created | Seed Data |
|----------|------|---------------|-----------|
| 001 | `001_initial_schema.py` | 15 core tables (users, roles, documents, vocabulary, authority_records, arrangement_nodes, etc.) | 6 roles, 14 vocabulary domains |
| 002 | `002_remaining_tables_and_seeds.py` | 28 remaining tables + FULLTEXT index | 150+ vocabulary terms across all domains, 3 description standards |

---

## Key Invariants (Application-Layer Enforced)

1. **Version group canonical**: Exactly one document per group has `is_canonical_version = TRUE`
2. **Version numbers**: Sequential within group, never reused
3. **Public version**: `public_document_id` must reference a document with `is_public = TRUE`
4. **Permission exclusivity**: `collection_permissions` rows have exactly one of `user_id` or `role_id` non-null
5. **Audit immutability**: `audit_log` and `preservation_events` rows are never updated or deleted
6. **Accession uniqueness**: `documents.accession_number` is UNIQUE (enforced at DB level)
7. **Annotation constraints**: Region annotations require `region_geometry`; text ranges require `text_range` with `start_offset < end_offset`
8. **Pending authority records**: Records with `created_by_ner = TRUE` and `created_by = NULL` must not be used as `creator_id`
9. **Deaccession log permanence**: `deaccession_log` rows are never deleted, even if the document is

---

## NoCoDB Access Patterns

NoCoDB connects to the same MySQL instance and auto-discovers all 43 tables.

**Safe for NoCoDB editing:** `authority_records` (bio notes, variant names), `vocabulary_terms` (definitions), `documents` (descriptive metadata)

**Must be read-only in NoCoDB:** `document_files.stored_path`, `document_files.file_hash_sha256`, `document_files.ocr_status`, `users.password_hash`, all `refresh_tokens` columns

**Bypass warning:** NoCoDB edits skip permission checks, audit logging, and completeness recomputation. Restrict access to admin-level users.
