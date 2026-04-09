# ADMS Public Exhibition Site Guide

A guide for understanding and navigating the public-facing ADMS exhibition site.
This site requires no login and is accessible to all visitors.

---

## 1. Landing Page

The public landing page at `/public` displays:
- **Institution name and logo** (configured by administrator)
- **Published exhibitions** as a card grid with cover images
- **Featured collections** with document counts

[SCREENSHOT: Public landing page showing institution header, exhibition grid with cover images, and collection section]

### Navigation
The top bar provides links to:
- **Exhibitions** — browse all published exhibitions
- **Collections** — browse the archival hierarchy
- **Search** — full-text search across public documents

---

## 2. Browsing Exhibitions

Navigate to `/public/exhibits` to see all published exhibitions.

- Each exhibition shows: cover image, title, subtitle, description excerpt
- Filter by tag (if exhibitions are tagged)
- Click an exhibition to enter it

[SCREENSHOT: Exhibition browse page showing multiple exhibition cards with cover images and titles]

---

## 3. Exhibition Pages

Each exhibition is organized as a hierarchy of **pages**, each containing **content blocks**.

### Page Navigation
- **Sidebar** on the left shows the page hierarchy (parent/child pages)
- **Current page** is highlighted
- **Previous/Next** navigation appears at the bottom of each page

[SCREENSHOT: Exhibition page with sidebar navigation, content blocks, and prev/next links at bottom]

### Block Types

| Block Type | What It Shows |
|-----------|--------------|
| **Rich Text** | Narrative HTML text written by the curator |
| **File with Text** | Document image alongside narrative text |
| **Gallery** | Grid of document thumbnails (2, 3, or 4 columns) |
| **Document Metadata** | Full document viewer with metadata, citation, and transcript |
| **Map** | Interactive map showing geolocated documents |
| **Timeline** | Chronological display of documents by date |
| **Table of Contents** | Auto-generated page list |
| **Collection Browse** | Grid/list of documents from a collection |
| **Separator** | Visual divider between sections |

[SCREENSHOT: Exhibition page showing a gallery block with document thumbnails and captions]
[SCREENSHOT: Exhibition page showing a map block with document pins and popups]
[SCREENSHOT: Exhibition page showing a timeline block with dated document entries]

### Map Block
- Click pins to see document title and thumbnail in a popup
- Click the popup to go to the full document page
- Toggle **"View as List"** for a text alternative (keyboard/screen reader friendly)

[SCREENSHOT: Map block showing "View as List" toggle and text list of geolocated documents]

---

## 4. Document Viewer

Each public document page at `/public/documents/{id}` shows:

### File Viewer
- Paginated image viewer (Previous/Next page navigation)
- Zoom in/out controls
- PDF embed for PDF files

### Metadata Panel
All public ISAD(G) fields:
- Title, date, creator, accession number
- Scope and content, extent, language
- Access conditions, rights information
- Collection/fonds name with link

### Citation Widget
Click the **citation icon** to generate a formatted citation in:
- Chicago (Note)
- Chicago (Bibliography)
- Turabian
- BibTeX
- RIS

[SCREENSHOT: Public document page showing file viewer, metadata panel, and citation widget with format selector]

### OCR Transcript
If the document has been OCR'd, click **"View Transcript"** to see the extracted text.
This provides a text alternative for the document image.

### Content Advisory
If the document has a content advisory, a banner appears at the top:
> "This item may contain language or content that reflects historical attitudes that are harmful or offensive to modern readers."

[SCREENSHOT: Document page with content advisory banner displayed above the file viewer]

### Related Documents
Links to related documents (replies, predecessors, revisions) appear below the metadata.

---

## 5. Collection Browsing

Navigate to `/public/collections` to browse the archival hierarchy.

- Collections show as cards with title, date range, and document count
- Click a collection to see its description and documents
- Nested collections (series within fonds) show as indented items

[SCREENSHOT: Public collections page showing collection cards with descriptions]

---

## 6. Public Search

Navigate to `/public/search` for full-text search.

### Search Features
- Search across document titles, OCR text, and descriptions
- **Faceted filters**:
  - Document type (letter, photograph, map, etc.)
  - Date range
  - Creator
  - Language
  - Subject tags

### Results
- Thumbnail, title, date, collection
- Relevance ranking
- Pagination

[SCREENSHOT: Public search page with search box, facet filters in sidebar, and results grid]

> **Edge case — Embargoed documents**: Documents with an active embargo (`embargo_end_date` in the future) do not appear in public search results, even if `is_public = TRUE`.

---

## 7. Accessibility Features

The ADMS public site conforms to **WCAG 2.2 Level AA**. Key features:

### Keyboard Navigation
- **Tab/Shift+Tab**: move between interactive elements
- **Enter/Space**: activate buttons and links
- **Escape**: close modals and menus
- **Arrow keys**: navigate within menus and trees
- **"Skip to main content"** link (visible on Tab)

### Screen Reader Support
- Semantic HTML throughout (`<nav>`, `<main>`, `<article>`, `<header>`, `<footer>`)
- ARIA labels on all interactive elements
- Live regions announce dynamic content changes
- Document images have meaningful alt text based on OCR availability

### Visual Preferences
- **Dark mode**: automatically follows `prefers-color-scheme` system setting, or toggle manually via the theme button
- **Reduced motion**: animations are disabled when `prefers-reduced-motion: reduce` is set

[SCREENSHOT: Public site in dark mode showing exhibition page]
[SCREENSHOT: Skip navigation link visible when focused at top of page]

### Map Accessibility
- Maps include visible keyboard pan and zoom controls
- Every map has a **"View as List"** toggle showing all documents as a text list
- Maps are never the only path to documents

---

## 8. Content Advisories

Some documents may display a content advisory banner. This indicates that the document contains language or imagery reflecting historical attitudes that may be harmful or offensive.

The advisory is provided by the institution to give context, not to censor. The document content itself is unmodified.

[SCREENSHOT: Content advisory banner with institution-authored contextual note]

---

## 9. Tombstone Pages

When you follow a link to a document that is no longer available, you'll see a **tombstone page** instead of a 404 error.

### Temporarily Unavailable
"This record is temporarily unavailable."
- May show an expected return date
- HTTP 503 status

### Deaccessioned
"This item is no longer publicly available."
- Depending on the institution's disclosure setting, may show the accession number and collection name
- HTTP 410 status

[SCREENSHOT: Tombstone page showing "This item is no longer publicly available" with accession number and contact info]

### What Tombstones Never Show
Regardless of disclosure level, tombstones never reveal: title, description, creator, file contents, or any metadata beyond what the institution's `tombstone_disclosure` setting permits.

> **Edge case — Non-public page in a public exhibition**: If an exhibition page is marked non-public but its parent exhibition is published, that page is omitted from the sidebar navigation and returns 404 on direct URL access. Other pages remain accessible.

> **Edge case — Document with no OCR**: The transcript panel shows "No transcript available." The document image is still viewable. The alt text reads "Page N of M. No transcript available."

---

## 10. Structured Data

Every public document page includes Schema.org structured data (JSON-LD) for search engine discovery:
- Documents use `@type: "ArchiveComponent"`
- Exhibitions use `@type: "ExhibitionEvent"`
- Collections use `@type: "Collection"`

This allows Google, Bing, and other search engines to understand the archival nature of the content and display rich results.

---

## 11. Permanent URLs

Every document has a permanent URL based on its accession number:

```
https://archive.example.org/d/2025-0042
```

These URLs are stable and suitable for citation. They resolve regardless of the document's current availability status:
- Available → redirects to full document page
- Unavailable → shows tombstone page
- Version-specific → `https://archive.example.org/d/2025-0042.2`

If the institution has registered an ARK NAAN, documents may also have ARK identifiers:
```
https://archive.example.org/ark:/99999/2025-0042
```
