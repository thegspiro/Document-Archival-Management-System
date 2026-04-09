# ADMS API Reference

Complete reference for all REST API endpoints. Base URL: `/api/v1/` (unless noted).

All responses are JSON unless otherwise noted. Authentication uses JWT tokens delivered as httpOnly cookies. All authenticated endpoints return `401 Unauthorized` if no valid token is present and `403 Forbidden` if the user lacks the required role or collection permission.

## Summary

| Resource | Endpoints | Auth Required | Base Prefix |
|----------|-----------|---------------|-------------|
| Health | 1 | No | `/api/v1/health` |
| Authentication | 3 | Partial | `/api/v1/auth` |
| Users | 6 | Admin | `/api/v1/users` |
| Arrangement Nodes | 11 | Yes | `/api/v1/nodes` |
| Documents | 44 | Yes | `/api/v1/documents` |
| Authority Records | 17 | Yes | `/api/v1/authority` |
| Vocabulary | 7 | Yes | `/api/v1/vocabulary` |
| Locations | 7 | Yes | `/api/v1/locations` |
| Events | 14 | Yes | `/api/v1/events` |
| Exhibitions | 14 | Yes | `/api/v1/exhibitions` |
| Review Queue | 5 | Archivist+ | `/api/v1/review` |
| Search & Citation | 2 | Yes | `/api/v1` |
| Reports | 5 | Archivist+ | `/api/v1/reports` |
| Preservation & Admin | 4 | Admin | `/api/v1/admin` |
| CSV Imports | 5 | Admin | `/api/v1/admin/imports` |
| System Settings | 2 | Admin | `/api/v1/settings` |
| Public API | 17 | No | `/api/v1/public` |
| OAI-PMH | 1 (6 verbs) | No | `/oai` |
| Persistent URLs | 2 | No | `/d`, `/ark` |
| **Total** | **167** | | |

---

## 1. Health Check

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/health` | Returns `{"status": "ok"}` | None |

---

## 2. Authentication

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `POST` | `/api/v1/auth/login` | Authenticate with email/password. Sets httpOnly access and refresh token cookies. Returns user object. | None |
| `POST` | `/api/v1/auth/refresh` | Issue new access token from valid refresh token cookie. | Refresh cookie |
| `POST` | `/api/v1/auth/logout` | Revoke refresh token and clear auth cookies. | Authenticated |

---

## 3. Users (Admin Only)

All user management endpoints require `admin` or `superadmin` role.

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/users` | List all users (paginated) | Admin |
| `POST` | `/api/v1/users` | Create a new user account | Admin |
| `GET` | `/api/v1/users/{id}` | Get user by ID | Admin |
| `PATCH` | `/api/v1/users/{id}` | Update user (display name, email, active status) | Admin |
| `DELETE` | `/api/v1/users/{id}` | Deactivate user (soft delete) | Admin |
| `POST` | `/api/v1/users/{id}/roles` | Assign roles to a user | Admin |

---

## 4. Arrangement Nodes

Hierarchical arrangement following ISAD(G) levels (Fonds, Subfonds, Series, Subseries, File, Item).

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/nodes` | List arrangement nodes (tree or flat) | Authenticated |
| `POST` | `/api/v1/nodes` | Create an arrangement node | Archivist+ |
| `GET` | `/api/v1/nodes/{id}` | Get node with hierarchy context | Authenticated |
| `PATCH` | `/api/v1/nodes/{id}` | Update node fields | Archivist+ |
| `DELETE` | `/api/v1/nodes/{id}` | Delete node (must have no children or documents) | Admin |
| `GET` | `/api/v1/nodes/{id}/documents` | List documents attached to this node (paginated) | Authenticated |
| `GET` | `/api/v1/nodes/{id}/permissions` | List collection-level permission grants on this node | Admin |
| `POST` | `/api/v1/nodes/{id}/permissions` | Create a permission grant for a user or role | Admin |
| `DELETE` | `/api/v1/nodes/{id}/permissions/{perm_id}` | Remove a permission grant | Admin |
| `GET` | `/api/v1/nodes/{id}/export` | Export node subtree (`?format=ead3\|csv`) | Authenticated |
| `GET` | `/api/v1/nodes/{id}/cite` | Get archival collection-level citation | Authenticated |

---

## 5. Documents

Core document management. Includes file handling, pages, relationships, authority links, location links, annotations, versioning, citation, export, availability, and deaccession.

### Core CRUD

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/documents` | List documents (paginated, filterable) | Authenticated |
| `POST` | `/api/v1/documents` | Create a new document record (auto-generates accession number) | Contributor+ |
| `GET` | `/api/v1/documents/{id}` | Get full document detail with all metadata | Authenticated |
| `PATCH` | `/api/v1/documents/{id}` | Update document metadata fields | Contributor+ |
| `DELETE` | `/api/v1/documents/{id}` | Delete a document (triggers deaccession workflow) | Admin |

### Files

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `POST` | `/api/v1/documents/{id}/files` | Upload a file (multipart/form-data) | Contributor+ |
| `GET` | `/api/v1/documents/{id}/files/{fid}/download` | Download file with XMP Dublin Core metadata embedded | Authenticated |
| `DELETE` | `/api/v1/documents/{id}/files/{fid}` | Delete a file from a document | Archivist+ |
| `POST` | `/api/v1/documents/{id}/files/{fid}/retry-ocr` | Retry OCR on a failed file | Contributor+ |

### Pages

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/documents/{id}/pages` | List all pages for a document | Authenticated |
| `PATCH` | `/api/v1/documents/{id}/pages/{pid}` | Update page-level metadata (notes, public flag) | Contributor+ |

### Relationships

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/documents/{id}/relationships` | List document-to-document relationships | Authenticated |
| `POST` | `/api/v1/documents/{id}/relationships` | Create a relationship to another document | Archivist+ |
| `DELETE` | `/api/v1/documents/{id}/relationships/{rid}` | Remove a document relationship | Archivist+ |

### Authority Links

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/documents/{id}/authority-links` | List linked authority records (non-creator roles) | Authenticated |
| `POST` | `/api/v1/documents/{id}/authority-links` | Link an authority record with a role | Archivist+ |
| `PATCH` | `/api/v1/documents/{id}/authority-links/{lid}` | Update an authority link (change role or notes) | Archivist+ |
| `DELETE` | `/api/v1/documents/{id}/authority-links/{lid}` | Remove an authority link | Archivist+ |

### Location Links

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/documents/{id}/location-links` | List linked locations | Authenticated |
| `POST` | `/api/v1/documents/{id}/location-links` | Link a location to the document | Archivist+ |
| `DELETE` | `/api/v1/documents/{id}/location-links/{lid}` | Remove a location link | Archivist+ |

### Events

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/documents/{id}/events` | List events linked to this document | Authenticated |

### Annotations (Staff Only)

Internal notes anchored to specific locations in a document. Never exposed publicly. Returns `403` for viewer role.

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/documents/{id}/annotations` | List all annotations on a document | Contributor+ |
| `POST` | `/api/v1/documents/{id}/annotations` | Create a region or text-range annotation | Contributor+ |
| `PATCH` | `/api/v1/documents/{id}/annotations/{aid}` | Update annotation body | Owner/Archivist+ |
| `DELETE` | `/api/v1/documents/{id}/annotations/{aid}` | Delete an annotation | Owner/Archivist+ |
| `POST` | `/api/v1/documents/{id}/annotations/{aid}/resolve` | Mark annotation as resolved | Contributor+ |
| `POST` | `/api/v1/documents/{id}/annotations/{aid}/reopen` | Reopen a resolved annotation | Contributor+ |

### NER

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `POST` | `/api/v1/documents/{id}/run-ner` | Trigger named entity recognition pipeline on document | Archivist+ |

### Versioning

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/documents/{id}/versions` | List all versions in the document's version group | Authenticated |
| `POST` | `/api/v1/documents/{id}/version-group` | Create a new version group from this document (Case A) | Archivist+ |
| `POST` | `/api/v1/documents/{id}/new-version` | Add a new version to an existing group (Case B) | Archivist+ |
| `POST` | `/api/v1/documents/{id}/join-group` | Add this document to an existing version group (Case C) | Archivist+ |
| `POST` | `/api/v1/documents/{id}/set-canonical` | Promote this version to canonical within its group | Archivist+ |
| `POST` | `/api/v1/documents/{id}/set-public-version` | Promote this version to public within its group | Archivist+ |

### Citations and Export

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/documents/{id}/cite` | Generate citation (`?format=chicago_note\|chicago_bib\|turabian\|bibtex\|ris\|zotero_rdf\|csl_json`) | Authenticated |
| `POST` | `/api/v1/documents/{id}/cite/zotero-push` | Push citation to user's configured Zotero library | Authenticated |
| `GET` | `/api/v1/documents/{id}/export` | Export metadata (`?format=dc_xml\|dc_json`) | Authenticated |

### Preservation Events

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/documents/{id}/preservation-events` | List PREMIS preservation events for this document | Authenticated |

### Availability and Deaccession

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `POST` | `/api/v1/documents/{id}/make-unavailable` | Set document as temporarily unavailable (creates tombstone) | Archivist+ |
| `POST` | `/api/v1/documents/{id}/restore` | Restore a temporarily unavailable document | Archivist+ |
| `POST` | `/api/v1/documents/{id}/deaccession/propose` | Propose deaccession of a document | Archivist+ |
| `POST` | `/api/v1/documents/{id}/deaccession/approve` | Approve a proposed deaccession | Admin |
| `POST` | `/api/v1/documents/{id}/deaccession/execute` | Execute approved deaccession (deletes file after logging) | Admin |

### Bulk Operations

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `POST` | `/api/v1/documents/bulk` | Perform bulk action on selected documents | Varies by action |

**Bulk action types:** `apply_terms`, `remove_terms`, `assign_node`, `set_public`, `clear_inbox`, `add_to_review`, `export_zip`, `delete` (admin only)

---

## 6. Authority Records

Persons, organizations, and families referenced in archival metadata. Supports Wikidata enrichment and NER suggestion review.

### CRUD

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/authority` | List authority records (paginated, filterable by entity type) | Authenticated |
| `POST` | `/api/v1/authority` | Create a new authority record | Archivist+ |
| `GET` | `/api/v1/authority/{id}` | Get authority record detail | Authenticated |
| `PATCH` | `/api/v1/authority/{id}` | Update authority record fields | Archivist+ |
| `DELETE` | `/api/v1/authority/{id}` | Delete an authority record | Admin |

### Linked Documents

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/authority/{id}/documents` | Documents where this record is the ISAD(G) creator (paginated) | Authenticated |
| `GET` | `/api/v1/authority/{id}/document-links` | All document links in any role | Authenticated |

### Authority-to-Authority Relationships

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/authority/{id}/relationships` | List relationships to other authority records | Authenticated |
| `POST` | `/api/v1/authority/{id}/relationships` | Create a relationship to another authority record | Archivist+ |
| `DELETE` | `/api/v1/authority/{id}/relationships/{rid}` | Delete an authority relationship | Archivist+ |

### Linked Events

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/authority/{id}/events` | List events this authority record is linked to | Authenticated |

### Wikidata Integration

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/authority/{id}/wikidata` | Fetch live Wikidata enrichment data | Archivist+ |
| `POST` | `/api/v1/authority/{id}/wikidata/link` | Link authority record to a Wikidata Q identifier | Archivist+ |
| `DELETE` | `/api/v1/authority/{id}/wikidata/link` | Unlink from Wikidata; clear cached enrichment | Archivist+ |

### NER Suggestions

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/authority/ner-suggestions` | List pending NER-generated authority suggestions (paginated) | Archivist+ |
| `POST` | `/api/v1/authority/ner-suggestions/{id}/accept` | Accept NER suggestion (creates or links authority record) | Archivist+ |
| `POST` | `/api/v1/authority/ner-suggestions/{id}/reject` | Reject NER suggestion permanently | Archivist+ |

---

## 7. Vocabulary

Controlled vocabulary management for tags, document types, subject categories, relationship types, and all other enumerated domains.

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/vocabulary/domains` | List all vocabulary domains | Authenticated |
| `POST` | `/api/v1/vocabulary/domains` | Create a new vocabulary domain | Admin |
| `GET` | `/api/v1/vocabulary/domains/{did}/terms` | List terms in a domain (paginated) | Authenticated |
| `POST` | `/api/v1/vocabulary/domains/{did}/terms` | Create a new term in a domain | Archivist+ |
| `PATCH` | `/api/v1/vocabulary/terms/{id}` | Update a vocabulary term | Archivist+ |
| `DELETE` | `/api/v1/vocabulary/terms/{id}` | Delete a vocabulary term | Admin |
| `POST` | `/api/v1/vocabulary/terms/{id}/merge` | Merge this term into another (bulk reassignment) | Admin |

---

## 8. Locations

Canonical location entities representing named places. Supports hierarchical nesting and geolocation.

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/locations` | List locations (paginated) | Authenticated |
| `POST` | `/api/v1/locations` | Create a new location | Archivist+ |
| `GET` | `/api/v1/locations/{id}` | Get location detail | Authenticated |
| `PATCH` | `/api/v1/locations/{id}` | Update location fields | Archivist+ |
| `DELETE` | `/api/v1/locations/{id}` | Delete a location | Admin |
| `GET` | `/api/v1/locations/{id}/documents` | List documents linked to this location (paginated) | Authenticated |
| `GET` | `/api/v1/locations/{id}/events` | List events at this location | Authenticated |

---

## 9. Events

First-class entities representing specific historical occurrences. Link to documents, authority records, and locations.

### CRUD

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/events` | List events (paginated) | Authenticated |
| `POST` | `/api/v1/events` | Create a new event | Archivist+ |
| `GET` | `/api/v1/events/{id}` | Get event detail | Authenticated |
| `PATCH` | `/api/v1/events/{id}` | Update event fields | Archivist+ |
| `DELETE` | `/api/v1/events/{id}` | Delete an event | Admin |

### Event-Document Links

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/events/{id}/documents` | List documents linked to this event | Authenticated |
| `POST` | `/api/v1/events/{id}/documents` | Link a document to this event | Archivist+ |
| `DELETE` | `/api/v1/events/{id}/documents/{lid}` | Remove a document link | Archivist+ |

### Event-Authority Links

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/events/{id}/authorities` | List authority records linked to this event | Authenticated |
| `POST` | `/api/v1/events/{id}/authorities` | Link an authority record with a role | Archivist+ |
| `DELETE` | `/api/v1/events/{id}/authorities/{lid}` | Remove an authority link | Archivist+ |

### Event-Location Links

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/events/{id}/locations` | List locations linked to this event | Authenticated |
| `POST` | `/api/v1/events/{id}/locations` | Link a location to this event | Archivist+ |
| `DELETE` | `/api/v1/events/{id}/locations/{lid}` | Remove a location link | Archivist+ |

---

## 10. Exhibitions

Multi-page exhibition builder with block-based content composition (modeled on Omeka S).

### Exhibition CRUD

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/exhibitions` | List exhibitions (paginated) | Authenticated |
| `POST` | `/api/v1/exhibitions` | Create a new exhibition | Archivist+ |
| `GET` | `/api/v1/exhibitions/{id}` | Get exhibition detail | Authenticated |
| `PATCH` | `/api/v1/exhibitions/{id}` | Update exhibition metadata | Archivist+ |
| `DELETE` | `/api/v1/exhibitions/{id}` | Delete an exhibition | Admin |

### Exhibition Pages

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/exhibitions/{id}/pages` | List pages in the exhibition (tree structure) | Authenticated |
| `POST` | `/api/v1/exhibitions/{id}/pages` | Create a new page | Archivist+ |
| `GET` | `/api/v1/exhibitions/{id}/pages/{pid}` | Get a single page with its blocks | Authenticated |
| `PATCH` | `/api/v1/exhibitions/{id}/pages/{pid}` | Update page metadata | Archivist+ |
| `DELETE` | `/api/v1/exhibitions/{id}/pages/{pid}` | Delete a page | Archivist+ |

### Exhibition Page Blocks

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `POST` | `/api/v1/exhibitions/{id}/pages/{pid}/blocks` | Create a content block on a page | Archivist+ |
| `PATCH` | `/api/v1/exhibitions/{id}/pages/{pid}/blocks/{bid}` | Update a content block | Archivist+ |
| `DELETE` | `/api/v1/exhibitions/{id}/pages/{pid}/blocks/{bid}` | Delete a content block | Archivist+ |
| `POST` | `/api/v1/exhibitions/{id}/pages/{pid}/blocks/reorder` | Reorder blocks within a page | Archivist+ |

**Block types:** `html`, `file_with_text`, `gallery`, `document_metadata`, `map`, `timeline`, `table_of_contents`, `collection_browse`, `separator`

---

## 11. Review Queue

LLM and NER suggestion review workflow.

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/review` | List review queue items (paginated, filterable) | Archivist+ |
| `GET` | `/api/v1/review/{document_id}` | Get review item with suggestions | Archivist+ |
| `POST` | `/api/v1/review/{document_id}/approve` | Approve and apply suggestions | Archivist+ |
| `POST` | `/api/v1/review/{document_id}/reject` | Reject suggestions | Archivist+ |
| `PATCH` | `/api/v1/review/{document_id}/assign` | Assign review item to a user | Archivist+ |

---

## 12. Search and Bulk Citation

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/search` | Full-text and faceted search across documents | Authenticated |
| `POST` | `/api/v1/cite/bulk` | Bulk citation export for multiple documents | Authenticated |

**Search parameters:** `q`, `creator_id`, `date_from`, `date_to`, `term_ids`, `authority_ids`, `location_ids`, `event_ids`, `node_id`, `document_type`, `language`, `review_status`, `is_public`, `page`, `per_page`

Search automatically filters to canonical versions only (unversioned documents or `is_canonical_version = TRUE`).

---

## 13. Reports (Archivist+)

All reports require at minimum `archivist` role. Admins see all collections; archivists see only their accessible collections. Reports support CSV and PDF export.

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/reports/accessions` | Accession report by date range. Params: `date_from`, `date_to`, `node_id`, `created_by` | Archivist+ |
| `GET` | `/api/v1/reports/processing` | Description completeness by collection. Params: `node_id`, `as_of_date` | Archivist+ |
| `GET` | `/api/v1/reports/users` | User activity report. Params: `date_from`, `date_to`, `user_id` | Archivist+ |
| `GET` | `/api/v1/reports/collection` | Full collection summary (storage, OCR, public stats). Params: `node_id` | Archivist+ |
| `GET` | `/api/v1/reports/public-access` | Public access summary (published items, downloads). Params: `date_from`, `date_to` | Archivist+ |

---

## 14. Preservation and Admin (Admin Only)

Administrative endpoints for OAIS/PREMIS compliance: format inventory, fixity verification, and deaccession records.

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/admin/format-inventory` | Format distribution across all stored files (PRONOM PUIDs) | Admin |
| `GET` | `/api/v1/admin/fixity-report` | Fixity check results summary (matches, mismatches, missing) | Admin |
| `POST` | `/api/v1/admin/fixity-run` | Trigger an on-demand fixity check across all files | Admin |
| `GET` | `/api/v1/admin/deaccession-log` | List deaccession log entries (paginated) | Admin |

---

## 15. CSV Imports (Admin Only)

Bulk import from CSV files. Supports template mode (ADMS format) and mapped mode (custom column mapping).

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/admin/imports/template` | Download the official ADMS CSV import template | Admin |
| `GET` | `/api/v1/admin/imports` | List all import jobs (paginated) | Admin |
| `POST` | `/api/v1/admin/imports` | Upload a CSV file and begin validation (multipart/form-data) | Admin |
| `GET` | `/api/v1/admin/imports/{id}` | Get import job status, validation report, and progress | Admin |
| `POST` | `/api/v1/admin/imports/{id}/confirm` | Execute the import after reviewing validation report | Admin |
| `DELETE` | `/api/v1/admin/imports/{id}` | Discard an import job | Admin |

---

## 16. System Settings (Admin Only)

Admin-only configuration for institution name, LLM settings, NER settings, accession format, fixity schedule, and all other `system_settings` keys.

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/settings` | Get all system settings | Admin |
| `PATCH` | `/api/v1/settings` | Update system settings | Admin |

---

## 17. Public API (No Auth)

All public endpoints require no authentication. They return only records where `is_public = TRUE`, embargo dates have passed, and parent collections are public. No session, cookie, or token is required.

### Exhibitions

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/public/exhibitions` | List published exhibitions |
| `GET` | `/api/v1/public/exhibitions/{slug}` | Exhibition summary with page tree |
| `GET` | `/api/v1/public/exhibitions/{slug}/pages/{page-slug}` | Single exhibition page with resolved blocks |

### Documents

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/public/documents/{id}` | Public document with full metadata |
| `GET` | `/api/v1/public/documents/{id}/files/{fid}` | Serve a public document file |
| `GET` | `/api/v1/public/documents/{id}/pages` | Public document pages |

### Search

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/public/search` | Full-text search across public documents with faceted filtering |

### Authority Records

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/public/authority/{id}` | Public authority record with linked documents |

### Collections

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/public/collections` | Browse public collection hierarchy |
| `GET` | `/api/v1/public/collections/{node_id}` | Public collection detail with documents |

### Static Pages

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/public/pages` | List published static narrative pages |
| `GET` | `/api/v1/public/pages/{slug}` | Static narrative page content |

### Locations

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/public/locations` | Browse public locations |
| `GET` | `/api/v1/public/locations/{id}` | Public location detail with linked documents and events |

### Events

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/public/events` | Browse public events |
| `GET` | `/api/v1/public/events/{id}` | Public event detail with documents, people, and places |

### Map

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/public/map-items` | Geolocated documents for map display. Params: `term_ids`, `node_id`, `date_from`, `date_to` |

---

## 18. OAI-PMH (No Auth)

Standard OAI-PMH 2.0 protocol endpoint for metadata harvesting.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/oai` | OAI-PMH 2.0 endpoint |

**Supported verbs:** `Identify`, `ListMetadataFormats`, `ListRecords`, `GetRecord`, `ListIdentifiers`, `ListSets`

**Metadata format:** `oai_dc` (Dublin Core)

**OAI identifier format:** `oai:{domain}:{accession_number}`

Resumption tokens use cursor-based pagination for result sets exceeding 100 records. Deaccessioned records remain with `status="deleted"` for 30 days.

---

## 19. Persistent URLs (No Auth)

Stable, accession-number-based URLs that resolve regardless of document availability status. Served by the FastAPI backend (not the React frontend) to support HTTP redirects and tombstone responses.

| Method | Path | Description | HTTP Status |
|--------|------|-------------|-------------|
| `GET` | `/d/{accession_number}` | Resolve accession number to public document or tombstone | 200, 301, 410, or 503 |
| `GET` | `/ark/{naan}/{ark_id}` | Resolve ARK identifier (if institution NAAN configured) | 301 to document |

**Tombstone behavior by document status:**

| Document State | HTTP Status | Response |
|----------------|-------------|----------|
| `available` + `is_public = TRUE` | 200 | Full public document page |
| `available` + `is_public = FALSE` | 410 | Tombstone (not publicly available) |
| `temporarily_unavailable` | 503 | Tombstone (in review, optional return date shown) |
| `deaccessioned` | 410 | Tombstone (permanently removed) |

---

## Common Response Formats

### Pagination

All paginated list endpoints return:

```json
{
  "items": [],
  "total": 150,
  "page": 1,
  "per_page": 25,
  "pages": 6
}
```

### Error

```json
{
  "detail": "Human-readable error message",
  "code": "machine_readable_code"
}
```

### HTTP Status Codes

| Code | Usage |
|------|-------|
| 200 | Successful read or update |
| 201 | Successful creation |
| 204 | Successful deletion (no body) |
| 400 | Malformed request |
| 401 | Unauthorized (not logged in or token expired) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Resource not found |
| 409 | Conflict (duplicate accession number, etc.) |
| 422 | Validation error (invalid field values) |
| 500 | Internal server error |

---

## Authentication Details

- JWT access tokens expire after 15 minutes
- JWT refresh tokens expire after 30 days
- Both tokens are delivered as `httpOnly`, `SameSite=Strict` cookies
- No tokens are returned in response bodies or stored in localStorage
- The frontend handles transparent token refresh before expiry
- A session expiry warning is shown 2 minutes before access token expiry

## Role Hierarchy

| Role | Scope |
|------|-------|
| `superadmin` | All actions everywhere; cannot be restricted by collection permissions |
| `admin` | All actions on all collections; manage users and roles |
| `archivist` | Create, edit, describe in permitted collections; manage vocabulary |
| `contributor` | Create and edit in permitted collections; cannot delete |
| `intern` | Create in explicitly permitted collections only |
| `viewer` | Read-only access to permitted collections |

Global roles set the floor. Collection-level `collection_permissions` can grant additional rights up to (but not exceeding) the user's global role ceiling.

All datetime values are ISO 8601 with UTC timezone.
