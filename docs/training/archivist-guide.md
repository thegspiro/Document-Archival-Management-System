# ADMS Archivist Training Guide

A step-by-step guide for archivists and contributors using ADMS to describe,
organize, and publish archival documents.

---

## 1. Logging In and Dashboard

1. Navigate to your ADMS instance URL and enter your email and password.
2. After login, the **Dashboard** shows:
   - **Inbox count** — unprocessed documents awaiting description
   - **Review queue count** — items pending LLM/NER review
   - **Collection stats** — total documents, files, OCR completion rate
   - **Completeness overview** — distribution across none/minimal/standard/full

[SCREENSHOT: Dashboard page showing stats cards, completeness chart, and recent activity feed]

**Session timeout**: You'll see a warning 2 minutes before your session expires (15 minutes). Click "Extend session" to stay logged in.

---

## 2. Navigating the Archive

The left sidebar shows the **arrangement tree** — your collection hierarchy following ISAD(G) levels:

**Fonds → Subfonds → Series → Subseries → File → Item**

Click any node to see its documents in the main panel. The tree supports:
- Expand/collapse with arrow icons
- Current node highlighted in blue

[SCREENSHOT: Archive browse page with tree sidebar on left, document table on right]

### Browse Modes

Besides the hierarchy tree, you can browse by:
- **Donor** — grouped by authority record (person/organization)
- **Subject** — grouped by subject category tags
- **Date** — timeline/decade view using document dates
- **Location** — grouped by linked location entities
- **Event** — grouped by linked historical events

---

## 3. Creating a New Document

1. Click **"New Document"** or navigate to `/archive/documents/new`
2. Fill in required fields:
   - **Title** (required) — the name of the document
   - **Collection** — which arrangement node to attach to
3. Fill in optional ISAD(G) fields organized by area:
   - **Identity**: reference code, dates, level of description, extent
   - **Context**: creator, administrative history, archival history, acquisition source
   - **Content**: scope and content, appraisal notes, arrangement
   - **Access**: conditions, reproduction rights, language, physical characteristics
   - **Allied Materials**: location of originals, related units, publications
   - **Notes**: general note, archivist's note
4. Click **Save**

[SCREENSHOT: New document form showing ISAD(G) field sections collapsed/expanded]

**Accession numbers** are auto-generated in the format `2025-0001`, `2025-0002`, etc. You do not need to enter one manually.

> **Edge case — Unknown dates**: Leave `Date (Start)` and `Date (End)` blank. Use `Date (Display)` for text like "circa 1890" or "undated, probably 1920s". The completeness system treats missing normalized dates as expected for some collections.

---

## 4. Uploading Files

1. Open a document and go to the **Files** tab
2. Click **"Upload File"** and select one or more files
3. ADMS accepts any file type. Enhanced treatment for:
   - **PDF**: page extraction, per-page thumbnails, OCR
   - **Images** (JPEG, PNG, TIFF, WebP): thumbnails, OCR
   - **Other**: stored as-is
4. After upload, the file passes through the ingest pipeline:
   - SHA-256 hash computation
   - MIME type detection
   - Format characterization (Siegfried/PRONOM)
   - Preservation warning evaluation

[SCREENSHOT: File upload dialog with drag-and-drop area]
[SCREENSHOT: File viewer showing paginated document images with thumbnail sidebar]

**Preservation warnings** (e.g., low resolution, lossy format) appear as yellow badges on the file — they don't block upload.

---

## 5. OCR Processing

OCR runs automatically after file upload (if enabled by your administrator).

### OCR Status Indicators
| Status | Meaning |
|--------|---------|
| None | OCR not applicable (non-image file) |
| Queued | Waiting for processing |
| Processing | Currently running |
| Complete | Text extracted successfully |
| Failed | Error occurred (see error message) |

[SCREENSHOT: OCR transcript panel showing extracted text alongside the page image]

### Viewing OCR Text
- Click **"View Transcript"** in the document viewer to see the OCR panel
- Per-page text appears alongside the page image

### Retrying Failed OCR
If OCR fails, you'll see the error message and a **"Retry OCR"** button. Click it to re-queue the task.

[SCREENSHOT: Failed OCR with error message and Retry button]

> **Edge case — Multi-language documents**: OCR uses the system-wide language setting (e.g., `eng` or `eng+fra`). If your document is in a different language, ask your administrator to adjust the OCR language setting.

---

## 6. Working with the Inbox

Documents appear in the inbox when they are:
- Newly uploaded
- Ingested via watch folder
- Imported via CSV

[SCREENSHOT: Inbox queue showing document rows with thumbnails, titles, and dates added]

### Processing Inbox Items
1. Click a document to open it
2. Add or correct metadata
3. The document stays in the inbox until you explicitly clear it

### Bulk Operations
1. Select multiple documents using checkboxes
2. A **bulk action toolbar** appears at the bottom
3. Available actions: apply tags, assign collection, set public, clear inbox

[SCREENSHOT: Inbox with multiple items selected and bulk toolbar visible at bottom]

---

## 7. Description Completeness

ADMS tracks how completely each document is described using four levels:

| Level | Badge Color | Default Required Fields (DACS) |
|-------|-------------|-------------------------------|
| None | Grey | — |
| Minimal | Yellow/Amber | title, date_display, level_of_description, extent |
| Standard | Blue | + creator, scope_and_content, access_conditions, language |
| Full | Green | + archival_history, immediate_source, physical_characteristics, ≥1 tag |

[SCREENSHOT: Document detail showing completeness badge "Standard" with list of missing fields to reach "Full"]

The badge appears on every document in list views and on the detail page. The detail page also shows **which specific fields are missing** to reach the next level.

> **Edge case — Legitimately unknown fields**: Your administrator can remove fields like `date_display` from the minimal requirements if your collection has many undated items.

---

## 8. Authority Records (People and Organizations)

### Creator Field vs Authority Links
- **Creator** (ISAD(G) Context Area): The primary person/organization that created the document. Set on the main document form.
- **Authority links**: All other people mentioned, depicted, or connected to the document. Managed in the **Authority Links** tab.

### Link Roles
| Role | Meaning |
|------|---------|
| `recipient` | Person/org the document was sent to |
| `signatory` | Person who signed the document |
| `witness` | Person who witnessed a legal act |
| `mentioned` | Named in the document's text |
| `depicted` | Shown in a photograph or image |
| `correspondent` | Part of a correspondence |
| `donor` | Donated this document to the archive |

[SCREENSHOT: Authority record linking panel showing linked people with their roles]

### NER-Suggested Records
If NER is enabled, the system may suggest new authority records extracted from OCR text. These appear with an "NER" badge and must be reviewed before use as a creator.

> **Edge case — Name variants**: Use the `variant_names` field (pipe-separated) for alternate spellings: `"John Smith|J. Smith|Jno. Smith"`

---

## 9. Locations and Events

### Linking Locations
From the document detail **Locations** tab:
- Search for an existing location or create a new one
- Select a **link type**: `mentioned`, `depicted`, `created_at`, or `event_location`

[SCREENSHOT: Location linking with link type dropdown and map preview]

### Linking Events
From the document detail **Events** tab:
- Search for or create an event (e.g., "City Council Meeting, April 1925")
- Select a **link type**: `produced_by`, `about`, `referenced_in`, `precedes`, or `follows`

---

## 10. Document Versions

Versioning handles situations where the same item exists in multiple states — adopted revisions, rescans, or copies from different sources.

### Creating a Version Group
1. On an existing document, click **"Create Version Group"**
2. The document becomes version 1 (accession `2025-0042` → `2025-0042.1`)
3. Click **"Add New Version"** to create version 2 (`2025-0042.2`)

### Setting Canonical and Public Versions
- **Canonical**: appears in search results and browse views
- **Public**: shown on the public exhibition site

[SCREENSHOT: Version panel showing 3 versions with canonical and public indicators]

> **Edge case — Deaccessioning the canonical version**: You must designate a new canonical version before the deaccession can proceed.

---

## 11. Annotations

Annotations are internal staff notes anchored to specific locations in a document.

### Region Annotations
1. In the document viewer, select the **annotation tool**
2. Click and drag a rectangle on the page image
3. Enter your note text
4. Save

[SCREENSHOT: Region annotation rectangle on a document page with tooltip showing note text]

### Text Range Annotations
1. In the OCR transcript panel, select text
2. Click **"Annotate Selection"**
3. Enter your note

[SCREENSHOT: Highlighted text in OCR panel with annotation popover]

Annotations can be **resolved** (marked as addressed) and are never shown on the public site.

---

## 12. Review Queue

The review queue contains documents flagged for human review — from LLM suggestions, NER extractions, imports, or integrity failures.

### Reviewing LLM Suggestions
1. Navigate to `/review` and open an item
2. The review page shows **current values** on the left and **suggested values** on the right
3. For each field, click **Accept**, **Edit**, or **Reject**
4. Click **Approve** or **Reject** the entire review when done

[SCREENSHOT: Review detail page showing side-by-side comparison of LLM-suggested metadata]

> **Edge case — Date fields**: LLM-suggested dates always require review and are never auto-applied, regardless of confidence threshold. OCR frequently picks up incidental dates.

---

## 13. Search

Navigate to `/search` for full-text search across:
- Document titles
- OCR text
- Scope and content
- General notes

### Faceted Filters
- **Date range**: filter by date_start
- **Creator**: filter by authority record
- **Document type**: from vocabulary
- **Language**: ISO 639 codes
- **Tags/subjects**: vocabulary terms
- **Review status**: none, pending, approved, rejected

[SCREENSHOT: Search results page with facet filters in sidebar and results showing thumbnails]

**Note**: Only canonical versions appear in search results. To find a specific non-canonical version, search by its exact accession number (e.g., `2025-0042.2`).

---

## 14. Citations and Export

### Citation Widget
On any document, click the **citation icon** to generate formatted citations:
- Chicago (Note and Bibliography)
- Turabian
- BibTeX
- RIS (for Zotero/Mendeley)
- CSL-JSON

[SCREENSHOT: Citation widget showing Chicago note format with copy button]

### Metadata Export
- **Dublin Core XML/JSON** — for interoperability
- **EAD3 XML** — collection-level finding aid (export from a collection node)
- **CSV** — flat spreadsheet export

### XMP Embedding
Every file downloaded from ADMS has Dublin Core metadata embedded as XMP. The original file is never modified — a temporary copy with XMP is created and streamed.

---

## 15. Content Advisories

For documents containing potentially harmful historical language:

1. Check **"Has Content Advisory"** on the document edit form
2. Enter a contextual note explaining the advisory
3. The advisory appears as a banner on the document — both in the staff view and on the public site

[SCREENSHOT: Content advisory banner on a document detail page]

If a collection-level advisory is set on an arrangement node, all documents in that collection inherit it unless explicitly opted out.

---

## 16. Tags and Vocabulary

### Adding Tags
1. On the document detail or edit page, find the **Tags** section
2. Search for existing tags or type a new one
3. Tags come from controlled vocabulary domains: `tag`, `subject_category`, `document_type`

[SCREENSHOT: Tag management section on document edit form]

### Requesting New Terms
If the vocabulary domain allows user additions, you can create new terms inline. Otherwise, ask your administrator to add them through the vocabulary management page.
