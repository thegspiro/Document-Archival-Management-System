# ADMS Administrator Training Guide

A guide for system administrators managing ADMS instances, users, settings, and workflows.

---

## 1. First-Run Setup Wizard

On first startup (no users in the database), ADMS displays a setup wizard at `/setup`.

### Step 1 — Create Superadmin Account
- Enter email, display name, and password
- This account has full access to everything

[SCREENSHOT: Setup wizard step 1 — superadmin account creation form]

### Step 2 — Institution Configuration
- Institution name (displayed throughout the application and in exports)
- Tagline, contact email
- Logo upload (optional)

[SCREENSHOT: Setup wizard step 2 — institution name and details]

### Step 3 — Storage Scheme
Choose how files are organized on disk:
| Scheme | Best For |
|--------|---------|
| Date | Chronological collections |
| Location | Hierarchical archives (fonds/series structure) |
| Donor | Donor-organized collections |
| Subject | Subject-based organization |
| Record Number | Sequential record systems |

[SCREENSHOT: Setup wizard step 3 — storage scheme selection with descriptions]

### Step 4 — LLM Settings (Optional)
- Provider: OpenAI, Anthropic, Ollama, or None
- API key and model name
- Which fields LLM may suggest
- Whether suggestions require review

After completing setup, you're redirected to the dashboard.

---

## 2. User Management

Navigate to **Admin → Users** (`/admin/users`).

### Creating Users
1. Click **"Create User"**
2. Enter email, display name, password
3. Assign one or more roles

### Role Hierarchy

| Role | Create | Edit | Delete | Manage Users | Manage Settings |
|------|--------|------|--------|-------------|----------------|
| Superadmin | ✓ | ✓ | ✓ | ✓ | ✓ |
| Admin | ✓ | ✓ | ✓ | ✓ | ✓ |
| Archivist | ✓ | ✓ | — | — | — |
| Contributor | ✓ | ✓ | — | — | — |
| Intern | ✓* | — | — | — | — |
| Viewer | — | — | — | — | — |

*Interns can only create in explicitly permitted collections.

[SCREENSHOT: User management table showing users with roles and status]

---

## 3. Collection Permissions

Navigate to any arrangement node and click **"Manage Permissions"**.

### Permission Flags
- `can_view` — read access to documents
- `can_create` — create new documents
- `can_edit` — modify existing documents
- `can_delete` — delete documents
- `can_manage_permissions` — grant/revoke permissions on this node

### Permission Resolution Order (highest wins)
1. **Superadmin**: all permissions everywhere
2. **User-specific** permission on the node
3. **Role-based** permission on the node
4. **Inherited** from parent node (walks up the tree)
5. **Global role default**

[SCREENSHOT: Permission settings dialog on a collection node]

> **Edge case — Elevated intern**: You can grant an intern `can_edit` on a specific collection. They'll be able to edit documents there, but the global role ceiling still prevents deletion.

---

## 4. System Settings

Navigate to **Admin → Settings** (`/admin/settings`).

### Institution Settings
- Institution name, tagline, contact email, logo
- Default content advisory text

### LLM Configuration
- Provider selection (OpenAI/Anthropic/Ollama/None)
- API key, base URL, model name
- Enabled suggestion fields (title, dates, scope, creator, tags, etc.)
- Require review toggle
- Auto-apply confidence threshold (if review not required)

### NER Configuration
- Enable/disable NER
- Run automatically after OCR toggle
- Entity types to extract (PERSON, ORG, GPE, LOC, DATE)
- spaCy model selection

### Accession Number Format
- Format template (default: `{YEAR}-{SEQUENCE:04d}`)
- Tokens: `{YEAR}`, `{MONTH}`, `{DAY}`, `{SEQUENCE}`

### Fixity Check Schedule
- Cron expression (default: `0 2 * * 0` — weekly Sunday 2 AM)

[SCREENSHOT: Admin settings page showing LLM configuration section]

---

## 5. Storage and Preservation

Navigate to **Admin → Preservation** (`/admin/preservation`).

### Format Inventory
Table showing all file formats in the repository:
- Format name, PRONOM PUID, file count, total size
- Helps identify formats needing migration

### Fixity Report
Summary of recent fixity check results:
- Total files checked
- Matches, mismatches, missing files
- Click any mismatch to see the affected document

### On-Demand Fixity Run
Click **"Run Fixity Check Now"** to trigger an immediate check of all files.

[SCREENSHOT: Preservation dashboard with format inventory table and fixity summary cards]

> **Edge case — Fixity mismatch**: Automatically creates a high-priority review queue item with reason `integrity_failure`. All admins see a dashboard alert. The file may be corrupted — investigate immediately.

---

## 6. Watch Folders

Navigate to **Admin → Settings** and find the Watch Folders section.

### Configuration
- **Path**: Directory relative to STORAGE_ROOT to monitor
- **Target collection**: Where ingested documents are placed
- **Default tags**: Automatically applied to ingested documents
- **Poll interval**: How often to scan (default: 60 seconds)
- **Active**: Enable/disable the folder

[SCREENSHOT: Watch folder configuration form]

### How It Works
1. Scanner finds new files (ignores dot-files and files with `.processing` lock)
2. File moves to quarantine → standard ingest pipeline runs
3. Document stub created with `inbox_status = 'inbox'`
4. File moves to permanent storage
5. OCR and other tasks are queued

> **Edge case — Error during ingest**: The file remains in `.quarantine/` — it is never deleted. A `preservation_events` row with `event_outcome = 'failure'` is written. An admin alert appears on the dashboard.

---

## 7. CSV Import

Navigate to **Admin → Imports** (`/admin/imports`).

### Template Mode
1. Download the official CSV template
2. Fill in your data
3. Upload — no column mapping needed

### Mapped Mode
1. Upload any CSV from a legacy system
2. Use the **Column Mapper** to connect source columns to ADMS fields
3. Required: map at least `title`

[SCREENSHOT: CSV import column mapping UI showing source columns on left, ADMS fields on right]

### Validation Report
After upload, ADMS validates every row:
- **Errors** (block import): missing title, invalid date format
- **Warnings** (don't block): unknown vocabulary terms, duplicate accession numbers, unmatched creator names

[SCREENSHOT: Validation report showing error/warning counts and per-row details]

### Import Execution
1. Review the validation report
2. Choose what to do with duplicates: **Update** existing or **Skip**
3. Click **"Confirm Import"**
4. All imported documents start as `is_public = FALSE` and `inbox_status = 'inbox'`

> **Edge case — New vocabulary terms**: Import auto-creates unknown terms (e.g., a new document_type). After import, audit these in the Vocabulary page and merge any misspellings.

> **Edge case — Duplicate accession numbers**: If a CSV row matches an existing accession, you choose to update or skip. No accidental overwrites.

---

## 8. Vocabulary Management

Navigate to **Vocabulary** (`/vocabulary`).

### Managing Terms
- Select a domain (e.g., `document_type`, `tag`, `condition`)
- Add new terms with definitions
- Deactivate terms (soft delete)

### Merging Terms
For bulk correction of misspellings imported via CSV:
1. Select the incorrect term
2. Click **"Merge Into..."**
3. Select the correct term
4. All document associations are reassigned atomically
5. The incorrect term is deleted
6. An audit log entry records the merge

[SCREENSHOT: Vocabulary page with merge dialog showing term A merging into term B]

---

## 9. Deaccession Workflow

Deaccession is a formal process, not a simple delete.

### Lifecycle
`active → proposed → approved → complete`

1. **Propose**: Archivist clicks "Propose Deaccession" — enters reason, disposition
2. **Approve**: Admin reviews and approves (or rejects)
3. **Execute**: System writes `deaccession_log` row, deletes physical file, sets `availability_status = 'deaccessioned'`

[SCREENSHOT: Deaccession workflow showing propose/approve steps]

The `deaccession_log` is immutable — it is never deleted, even if the document record is.

> **Edge case — Deaccessioning canonical version**: The archivist must designate a new canonical version before proceeding. If it's the last version in a group, the group record is retained for historical reference.

---

## 10. Exhibitions and Public Site

Navigate to **Exhibitions** (`/exhibitions`).

### Creating an Exhibition
1. Set title, slug, description, cover image
2. Add **pages** (supports hierarchy: parent/child pages)
3. Add **blocks** to each page:
   - HTML (rich text)
   - File with Text (image + narrative)
   - Gallery (thumbnail grid)
   - Document Metadata (full viewer + metadata)
   - Map (Leaflet with geolocated documents)
   - Timeline (chronological document display)
   - Table of Contents (auto-generated)
   - Collection Browse (grid/list of collection items)
   - Separator (visual divider)

### Publishing
Toggle **"Published"** on the exhibition. Only published exhibitions appear on the public site.

[SCREENSHOT: Exhibition page builder showing block list with drag/reorder and add block button]

---

## 11. Reports

Navigate to **Admin → Reports** (`/admin/reports`).

| Report | Purpose | Key Metrics |
|--------|---------|-------------|
| Accessions | Grant reporting, board presentations | Accessions by date, who accessioned, completeness |
| Processing | Identify backlogs | Per-collection completeness distribution |
| User Activity | Staff contributions, volunteer recognition | Creates, updates, OCR retries per user |
| Collection Summary | Collection assessments | Total docs, files, storage, OCR%, public% |
| Public Access | Demonstrate public value | Published docs, exhibitions, downloads |

All reports are exportable as CSV.

[SCREENSHOT: Reports selection page showing 5 report cards]

---

## 12. NoCoDB Integration

NoCoDB provides a spreadsheet interface to the same MySQL database.

### Safe to Edit in NoCoDB
- `authority_records` — biographical notes, variant names
- `vocabulary_terms` — definitions, sort order
- `documents` — descriptive metadata fields

### Read-Only (Do Not Edit)
- `document_files.stored_path`, `file_hash_sha256`, `ocr_status`
- `users.password_hash`
- All `refresh_tokens` columns

[SCREENSHOT: NoCoDB spreadsheet view showing authority_records table]

> **Edge case**: NoCoDB edits bypass the application's permission checks, audit logging, and completeness recomputation. Restrict NoCoDB access to admin-level users only.

---

## 13. Multi-Instance Management

Use `adms-manager` to run multiple isolated ADMS instances on one server.

```bash
./adms-manager create falls-church-vfd
./adms-manager start falls-church-vfd
./adms-manager list
./adms-manager backup falls-church-vfd
./adms-manager proxy-config > /etc/nginx/sites-available/adms
```

Each instance is completely isolated: separate database, storage, Redis, NoCoDB.

[SCREENSHOT: Terminal showing adms-manager list output with two instances]

---

## 14. Troubleshooting

### Common Issues

| Symptom | Cause | Solution |
|---------|-------|---------|
| OCR always fails | Wrong language pack | Set `OCR_LANGUAGE` in `.env` |
| Upload fails at 10MB | Reverse proxy limit | Set `client_max_body_size 500M` in nginx |
| LLM suggestions not appearing | Provider not configured | Check `LLM_PROVIDER` and `LLM_API_KEY` in settings |
| Fixity mismatch alert | File corruption or move | Check file on disk, restore from backup |
| NoCoDB can't see tables | Wrong NC_DB connection | Verify `NC_DB` in `.env` matches MySQL credentials |

### Viewing Logs
```bash
docker compose logs backend      # API server
docker compose logs worker        # Celery workers
docker compose logs beat          # Scheduled tasks
docker compose logs db            # MySQL
```

Or with adms-manager:
```bash
./adms-manager logs my-instance worker
```
