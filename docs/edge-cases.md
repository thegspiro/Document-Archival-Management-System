# Edge Cases and Special Handling

This document catalogs non-obvious behaviors, boundary conditions, and special handling
throughout ADMS. Every entry references the source code or spec section where the behavior
is implemented.

---

## 1. Accession Numbers

### 1.1 Atomic Generation

Accession numbers are generated atomically using `SELECT ... FOR UPDATE` on the `sequences`
table to prevent gaps or collisions under concurrent inserts.

- **Source**: `backend/app/services/document_service.py` → `create_document()`
- **Edge case**: If two users create documents at the exact same moment, the second request
  blocks until the first transaction commits. This is intentional — accession numbers must
  be strictly sequential with no gaps.

### 1.2 Versioned Accession Number Modification

When an unversioned document (`2025-0042`) is promoted into a version group, its accession
number changes to `2025-0042.1`. This is the **only** situation where an assigned accession
number is modified.

- **Source**: CLAUDE.md §18.1, `documents.py` router → `create_version_group()`
- **Edge case**: External systems that cached the old accession number (`2025-0042`) will no
  longer find it. The `/d/2025-0042` persistent URL should redirect to the canonical version.
- **Mitigation**: An `audit_log` entry records every accession number change.

### 1.3 Version Numbers Are Never Reused

If a version group has versions 1, 2, 3 and version 2 is deaccessioned, the next version
added is version 4 — not version 2. Version numbers are append-only.

- **Source**: CLAUDE.md §5.5 invariants

---

## 2. Document Versioning

### 2.1 Deaccessioning the Canonical Version

If the canonical version in a group is deaccessioned, the application **must** require the
archivist to designate a new canonical version before the deaccession workflow can proceed.
The system will reject the deaccession if no other version exists or no new canonical is set.

- **Source**: CLAUDE.md §20.9
- **UI behavior**: The deaccession confirmation dialog shows a version selector when the
  document is canonical.

### 2.2 Last Version in a Group

If the last remaining version in a group is deaccessioned, the `document_version_groups`
record is retained (for historical reference in the deaccession log) but is no longer
surfaced in the UI. The group's `canonical_document_id` will point to a deaccessioned document.

- **Source**: CLAUDE.md §20.9

### 2.3 Public Version Must Be Public

Setting `document_version_groups.public_document_id` to a document that has `is_public = FALSE`
is a validation error (HTTP 422). The archivist must first make the document public.

- **Source**: CLAUDE.md §20.4

### 2.4 Search Only Returns Canonical Versions

All search and browse queries automatically apply:
```sql
WHERE (version_group_id IS NULL) OR (is_canonical_version = TRUE)
```
Non-canonical versions are reachable only by direct accession number lookup
(`GET /api/v1/documents?accession=2025-0042.2`) or through the version panel.

- **Source**: CLAUDE.md §20.5, `search_service.py`

---

## 3. OCR Processing

### 3.1 Retry Limit

OCR retries up to 3 times with exponential backoff. After 3 failures, status is set to
`failed` and **no further automatic retries occur**. The user must click "Retry OCR"
explicitly, which resets `ocr_attempt_count` to 0.

- **Source**: CLAUDE.md §8.2, `workers/ocr.py`

### 3.2 Multi-Language Documents

The `OCR_LANGUAGE` setting accepts comma-separated Tesseract language codes (e.g., `eng+fra`).
For documents mixing languages, this must be configured at the instance level — per-document
language selection for OCR is not supported in phase 1.

- **Edge case**: A document with `language_of_material = 'fra'` will still be OCR'd with the
  system-wide `OCR_LANGUAGE` setting, not with French-specific models, unless the admin
  changes the setting.

### 3.3 OCR on Non-Text Files

OCR is only attempted for PDFs and images (JPEG, PNG, TIFF, WebP). All other file types
have `ocr_status = 'none'` permanently. The "Retry OCR" button is not shown for these files.

### 3.4 OCR Text Size

`document_files.ocr_text` uses MySQL `LONGTEXT` (4GB max). For extremely large documents
(thousands of pages), OCR text concatenation could be very large. The NER worker truncates
input to 100,000 characters for spaCy processing.

---

## 4. LLM Suggestions

### 4.1 Date Fields Are Never Auto-Applied

The LLM suggestion pipeline **never** automatically commits `date_display`, `date_start`,
or `date_end` to the database, regardless of confidence threshold settings. These always
enter the review queue.

- **Source**: CLAUDE.md §11.5
- **Reason**: OCR frequently picks up incidental dates from document body text rather than
  the document's actual creation date.

### 4.2 LLM Provider Not Configured

If `LLM_PROVIDER` is empty, `none`, or unset, all LLM features are silently disabled.
No errors are thrown; the task returns `{"status": "skipped", "reason": "LLM disabled"}`.

### 4.3 LLM Timeout

External LLM API calls (OpenAI, Anthropic) can take 30+ seconds. The Ollama adapter
uses a 120-second timeout for local models. If the call times out, it is logged as an error
but does not fail the entire ingest pipeline — the document is still created and accessible.

---

## 5. NER Processing

### 5.1 NER Never Auto-Applies

NER suggestions are **never auto-applied**, regardless of confidence score. This is a hard
rule with no configuration option to override it. Historical documents with OCR noise, archaic
spelling, and unusual proper nouns have too high an error rate.

- **Source**: CLAUDE.md §24.5

### 5.2 Pending Authority Records

When NER creates a new authority record (no fuzzy match found), the record has
`created_by_ner = TRUE` and `created_by = NULL`. A pending authority record **must never**
be used as a `creator_id` on a document until reviewed.

- **Source**: CLAUDE.md §5.7

### 5.3 Fuzzy Match Threshold

The default fuzzy match threshold is 0.85 (SequenceMatcher ratio). This means "John Smith"
matches "John H. Smith" (ratio ~0.87) but not "J. Smith" (ratio ~0.67).

- **Edge case**: An authority record for "Falls Church Volunteer Fire Department" will not
  match the NER extraction "Falls Church VFD" (ratio ~0.58). The system creates a new
  pending authority record instead.
- **Mitigation**: After reviewing NER suggestions, the archivist can merge duplicate
  authority records manually.

---

## 6. File Storage and Preservation

### 6.1 Quarantine on Error

If any step of the ingest pipeline fails (hash computation, MIME detection, Siegfried
characterization), the file **remains in quarantine** — it is never deleted. An admin
alert appears on the dashboard.

- **Source**: CLAUDE.md §22.3 (watch folder), §6.2 (upload flow)

### 6.2 Duplicate File Detection

SHA-256 hashes are computed on upload and compared against `document_files.file_hash_sha256`.
If a duplicate is detected, the upload **is not rejected** — it proceeds with a warning.
This is intentional: the same scan may legitimately belong to multiple document records
(e.g., a photograph appearing in two different fonds).

### 6.3 Fixity Check Failures

Any `mismatch` or `file_missing` outcome in a fixity check triggers three actions:
1. A `preservation_events` row with `event_outcome = 'failure'`
2. A `review_queue` entry with `reason = 'integrity_failure'` and `priority = 'high'`
3. A dashboard alert visible to all admins

- **Source**: CLAUDE.md §5.25

### 6.4 Original Files Are Never Modified

XMP metadata embedding and document splitting create temporary files in
`{STORAGE_ROOT}/.exports/` — the original stored file is never touched. The export
file is streamed to the client and then deleted.

- **Source**: CLAUDE.md §16.1, `workers/export.py`

### 6.5 Preservation Warnings Are Non-Blocking

Low resolution, lossy-only format, and other preservation concerns are stored in
`document_files.preservation_warning` but **do not block upload or ingest**. They
are displayed as warnings in the UI.

---

## 7. Permissions

### 7.1 Superadmin Bypass

Superadmins have all permissions everywhere. They cannot be restricted by collection-level
`collection_permissions` rows.

- **Source**: CLAUDE.md §7.2

### 7.2 Permission Inheritance Stops at First Match

When resolving permissions for a node, the system walks up the arrangement tree. It stops
at the **first** node where a permission row exists (either user-specific or role-based).
It does not merge permissions from multiple ancestor nodes.

- **Source**: `permission_service.py` → `check_permission()`

### 7.3 Exactly One of user_id or role_id

A `collection_permissions` row must have exactly one of `user_id` or `role_id` non-null.
This is enforced in the application layer, not the database.

### 7.4 Global Role Ceiling

Collection-level permissions can grant additional rights but cannot elevate beyond the
user's global role ceiling. An intern given `can_delete = TRUE` on a collection will
still be denied deletion because the intern role's global ceiling does not include delete.

- **Exception**: Superadmins are exempt from role ceilings.

---

## 8. Public Site and Tombstones

### 8.1 Public Visibility Requires All Ancestors

A document is visible on the public site only if:
1. `documents.is_public = TRUE`
2. `documents.embargo_end_date` is null or in the past
3. Every ancestor `arrangement_node` has `is_public = TRUE`
4. The exhibition page (if accessed through one) is public and the exhibition is published

- **Edge case**: Making a series-level node private hides all documents in that series from
  the public site, even if individual documents have `is_public = TRUE`.

### 8.2 Tombstone Disclosure Levels

| Level | What is shown |
|---|---|
| `none` | "This item is no longer publicly available." + contact info |
| `accession_only` | Accession number + contact info |
| `collection_and_accession` | Collection name + accession number + contact info |

The tombstone **never** reveals: title, description, creator, file contents, or any metadata
beyond what `tombstone_disclosure` permits.

### 8.3 Temporarily Unavailable vs Deaccessioned

- `temporarily_unavailable`: HTTP 503, may show `unavailable_until` date. Document can be restored.
- `deaccessioned`: HTTP 410, permanent. Document URL resolves to tombstone forever.

### 8.4 Non-Public Pages in Public Exhibitions

If an exhibition page has `is_public = FALSE` but its parent exhibition is published, the
page is omitted from the sidebar navigation and returns 404 on direct access. Other pages
in the exhibition remain accessible.

---

## 9. Exhibitions

### 9.1 Block Content Validation

Each block type has a specific JSON content schema (CLAUDE.md §12.5). The backend validates
content structure on block creation/update. Invalid content returns HTTP 422.

### 9.2 Map Blocks with No Geolocated Documents

If a map block's document list or query returns documents with no `geo_latitude`/`geo_longitude`,
those documents are simply omitted from the map. If all documents lack coordinates, the map
shows tiles at the configured center/zoom with no markers. A message is not shown.

### 9.3 Gallery Blocks with Missing Files

If a gallery references a `document_id` that has been deaccessioned or made non-public,
that item is omitted from the gallery grid. The gallery renders the remaining items without
gaps. A broken-image placeholder is never shown.

---

## 10. CSV Import

### 10.1 Auto-Created Vocabulary Terms

When a CSV contains values for enum fields (document_type, condition, etc.) that don't match
existing vocabulary terms, the import **does not fail**. Instead, it flags these as "will
create new vocabulary term" in the validation report. The user must confirm before import.

- **Post-import action**: Admin should audit new terms and merge misspellings via the
  vocabulary management page.

### 10.2 Duplicate Accession Numbers

If a CSV row's accession number matches an existing document, the validation report flags it
as a warning (not an error). The user chooses: "update" (patch existing record) or "skip"
(leave the row un-imported).

### 10.3 All Imports Are Private

No CSV import can set `is_public = TRUE`. All imported documents start with
`is_public = FALSE` and `inbox_status = 'inbox'`. The archivist must review and publish
each document explicitly.

- **Source**: CLAUDE.md §29.4

### 10.4 Row Limit

CSV files exceeding 50,000 rows are rejected at upload time. This limit is configurable
via `system_settings['import.max_rows']`.

---

## 11. Authentication

### 11.1 Token Storage

JWT access and refresh tokens are delivered as `httpOnly`, `SameSite=Strict` cookies.
They are **never** in response bodies or localStorage.

### 11.2 Session Timeout Warning

The frontend shows a modal warning 2 minutes before the 15-minute access token expires,
satisfying WCAG 2.2.1 (Timing Adjustable). Auto-logout without warning is prohibited.

### 11.3 Refresh Token Revocation

Logging out revokes the refresh token by setting `revoked_at` in the database. The access
token remains valid until it expires naturally (max 15 minutes). This is acceptable because
the access token is short-lived and httpOnly.

---

## 12. Content Advisories

### 12.1 Collection-Level Inheritance

If an `arrangement_node` has `has_content_advisory = TRUE`, all documents in that collection
inherit the advisory **unless** the document explicitly sets `has_content_advisory = FALSE`.

### 12.2 Advisory in Exports

The content advisory note is included in Dublin Core XML exports and OAI-PMH feeds, prefixed
with "Content Advisory: " to distinguish it from the scope and content description.

---

## 13. Vocabulary Term Merging

When merging term A into term B:
1. All `document_terms` rows with `term_id = A` are updated to `term_id = B` in a single
   transaction.
2. Duplicate key conflicts (document already has term B) are silently skipped.
3. Term A is deleted.
4. An `audit_log` entry records: which term was replaced, which term it was merged into,
   how many documents were affected, and who performed the action.

- **Source**: CLAUDE.md §5.8, `vocabulary_service.py`

---

## 14. NoCoDB Write Safety

NoCoDB users editing records directly bypass:
- Application business logic
- Permission checks
- Audit logging
- Completeness recomputation

The following columns must be marked read-only in NoCoDB:
- `document_files.stored_path`, `document_files.file_hash_sha256`, `document_files.ocr_status`
- `users.password_hash`
- All `refresh_tokens` columns

- **Source**: CLAUDE.md §13.3
- **Recommendation**: Only admin-level users should have NoCoDB access.

---

## 15. Watch Folder Processing

### 15.1 Lock Files

The watch folder scanner uses `.processing` lock files to prevent double-ingestion of the
same file across overlapping poll cycles. The lock file is deleted after processing completes
or fails.

### 15.2 Hidden Files

Files starting with `.` (dot files) are ignored by the watch folder scanner. This includes
macOS `.DS_Store` files and the `.processing` lock files themselves.

### 15.3 File Naming

The document title is derived from the filename: underscores and hyphens are replaced with
spaces, and the result is title-cased. Example: `jones_mill_deed_1892.pdf` becomes
"Jones Mill Deed 1892". The archivist should correct this during inbox processing.
