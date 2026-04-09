# ADMS API Reference

Complete reference for all REST API endpoints. Base URL: `/api/v1/` (unless noted).

## Summary

| Resource | Endpoints | Auth Required |
|----------|-----------|--------------|
| Health | 1 | No |
| Authentication | 3 | Partial |
| Users | 6 | Admin+ |
| Arrangement Nodes | 11 | Yes |
| Documents | 45+ | Yes |
| Authority Records | 17 | Yes |
| Vocabulary | 7 | Partial |
| Locations | 7 | Yes |
| Events | 14 | Yes |
| Exhibitions | 14 | Yes |
| Review Queue | 5 | Archivist+ |
| Search | 2 | Yes |
| Reports | 5 | Archivist+ |
| Preservation | 4 | Admin |
| CSV Imports | 6 | Admin |
| System Settings | 2 | Admin |
| Public API | 17 | No |
| OAI-PMH | 1 (6 verbs) | No |
| Persistent URLs | 2 | No |
| **Total** | **~169** | |

---

## 1. Health Check

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/health` | Returns `{"status": "ok"}` |

---

## 2. Authentication

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `POST` | `/api/v1/auth/login` | Login with email/password. Sets httpOnly cookies. | No |
| `POST` | `/api/v1/auth/refresh` | Refresh access token from refresh cookie. | Cookie |
| `POST` | `/api/v1/auth/logout` | Revoke refresh token, clear cookies. | Yes |

**Login request body:**
```json
{ "email": "user@example.org", "password": "..." }
```
**Response:** Sets `access_token` and `refresh_token` cookies. Returns user object.

---

## 3. Users (Admin Only)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/users` | List all users (paginated) |
| `POST` | `/api/v1/users` | Create a new user |
| `GET` | `/api/v1/users/{id}` | Get user by ID |
| `PATCH` | `/api/v1/users/{id}` | Update user |
| `DELETE` | `/api/v1/users/{id}` | Deactivate user (soft delete) |
| `POST` | `/api/v1/users/{id}/roles` | Assign/remove roles |

---

## 4. Arrangement Nodes

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/nodes` | List/tree of arrangement nodes |
| `POST` | `/api/v1/nodes` | Create node |
| `GET` | `/api/v1/nodes/{id}` | Get node by ID |
| `PATCH` | `/api/v1/nodes/{id}` | Update node |
| `DELETE` | `/api/v1/nodes/{id}` | Delete node (must have no children/documents) |
| `GET` | `/api/v1/nodes/{id}/documents` | List documents in node (paginated) |
| `GET` | `/api/v1/nodes/{id}/permissions` | List permissions on node |
| `POST` | `/api/v1/nodes/{id}/permissions` | Add permission to node |
| `DELETE` | `/api/v1/nodes/{id}/permissions/{perm_id}` | Remove permission |
| `GET` | `/api/v1/nodes/{id}/export?format=ead3\|csv` | Export node as EAD3 XML or CSV |
| `GET` | `/api/v1/nodes/{id}/cite` | Collection-level citation |

---

## 5. Documents

### Core CRUD

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/documents` | List documents (paginated, filterable) |
| `POST` | `/api/v1/documents` | Create document (auto-generates accession number) |
| `GET` | `/api/v1/documents/{id}` | Get document with all metadata |
| `PATCH` | `/api/v1/documents/{id}` | Update document metadata |
| `DELETE` | `/api/v1/documents/{id}` | Delete document |

### Files

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/documents/{id}/files` | Upload file (multipart/form-data) |
| `GET` | `/api/v1/documents/{id}/files/{fid}/download` | Download with XMP metadata |
| `DELETE` | `/api/v1/documents/{id}/files/{fid}` | Delete file |
| `POST` | `/api/v1/documents/{id}/files/{fid}/retry-ocr` | Retry failed OCR |

### Pages

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/documents/{id}/pages` | List document pages |
| `PATCH` | `/api/v1/documents/{id}/pages/{pid}` | Update page (notes, is_public) |

### Relationships

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/documents/{id}/relationships` | List document relationships |
| `POST` | `/api/v1/documents/{id}/relationships` | Create relationship |
| `DELETE` | `/api/v1/documents/{id}/relationships/{rid}` | Delete relationship |

### Authority Links

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/documents/{id}/authority-links` | List authority links |
| `POST` | `/api/v1/documents/{id}/authority-links` | Create authority link |
| `PATCH` | `/api/v1/documents/{id}/authority-links/{lid}` | Update link |
| `DELETE` | `/api/v1/documents/{id}/authority-links/{lid}` | Delete link |

### Location Links

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/documents/{id}/location-links` | List location links |
| `POST` | `/api/v1/documents/{id}/location-links` | Create location link |
| `DELETE` | `/api/v1/documents/{id}/location-links/{lid}` | Delete location link |

### Events, Annotations, NER

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/documents/{id}/events` | List linked events |
| `GET` | `/api/v1/documents/{id}/annotations` | List annotations (staff only) |
| `POST` | `/api/v1/documents/{id}/annotations` | Create annotation |
| `PATCH` | `/api/v1/documents/{id}/annotations/{aid}` | Update annotation |
| `DELETE` | `/api/v1/documents/{id}/annotations/{aid}` | Delete annotation |
| `POST` | `/api/v1/documents/{id}/annotations/{aid}/resolve` | Resolve annotation |
| `POST` | `/api/v1/documents/{id}/annotations/{aid}/reopen` | Reopen annotation |
| `POST` | `/api/v1/documents/{id}/run-ner` | Trigger NER pipeline |

### Versioning

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/documents/{id}/versions` | List all versions in group |
| `POST` | `/api/v1/documents/{id}/version-group` | Create new version group |
| `POST` | `/api/v1/documents/{id}/new-version` | Add version to existing group |
| `POST` | `/api/v1/documents/{id}/join-group` | Join an existing group |
| `POST` | `/api/v1/documents/{id}/set-canonical` | Set as canonical version |
| `POST` | `/api/v1/documents/{id}/set-public-version` | Set as public version |
| `PATCH` | `/api/v1/version-groups/{gid}` | Update group (canonical/public IDs) |

### Citations and Export

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/documents/{id}/cite?format=...` | Generate citation |
| `POST` | `/api/v1/cite/bulk` | Bulk citation export |
| `POST` | `/api/v1/documents/{id}/cite/zotero-push` | Push to Zotero |
| `GET` | `/api/v1/documents/{id}/export?format=dc_xml\|dc_json` | Dublin Core export |
| `GET` | `/api/v1/documents/{id}/preservation-events` | Preservation event log |

### Availability and Deaccession

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/documents/{id}/make-unavailable` | Set temporarily unavailable |
| `POST` | `/api/v1/documents/{id}/restore` | Restore availability |
| `POST` | `/api/v1/documents/{id}/deaccession/propose` | Propose deaccession |
| `POST` | `/api/v1/documents/{id}/deaccession/approve` | Approve deaccession |
| `POST` | `/api/v1/documents/{id}/deaccession/execute` | Execute deaccession |

### Bulk Operations

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/documents/bulk` | Bulk action on selected documents |

**Bulk action types:** `apply_terms`, `remove_terms`, `assign_node`, `set_public`, `clear_inbox`, `add_to_review`, `export_zip`, `delete`

---

## 6. Authority Records

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/authority` | List authority records |
| `POST` | `/api/v1/authority` | Create authority record |
| `GET` | `/api/v1/authority/{id}` | Get authority record |
| `PATCH` | `/api/v1/authority/{id}` | Update authority record |
| `DELETE` | `/api/v1/authority/{id}` | Delete authority record |
| `GET` | `/api/v1/authority/{id}/documents` | Documents where this is creator |
| `GET` | `/api/v1/authority/{id}/document-links` | All document links (any role) |
| `GET` | `/api/v1/authority/{id}/relationships` | Authority-to-authority links |
| `POST` | `/api/v1/authority/{id}/relationships` | Create relationship |
| `DELETE` | `/api/v1/authority/{id}/relationships/{rid}` | Delete relationship |
| `GET` | `/api/v1/authority/{id}/events` | Linked events |
| `GET` | `/api/v1/authority/{id}/wikidata` | Fetch Wikidata enrichment |
| `POST` | `/api/v1/authority/{id}/wikidata/link` | Link to Wikidata Q-ID |
| `DELETE` | `/api/v1/authority/{id}/wikidata/link` | Unlink from Wikidata |
| `GET` | `/api/v1/authority/ner-suggestions` | List pending NER suggestions |
| `POST` | `/api/v1/authority/ner-suggestions/{id}/accept` | Accept NER suggestion |
| `POST` | `/api/v1/authority/ner-suggestions/{id}/reject` | Reject NER suggestion |

---

## 7. Vocabulary

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/vocabulary/domains` | List vocabulary domains |
| `POST` | `/api/v1/vocabulary/domains` | Create domain (admin) |
| `GET` | `/api/v1/vocabulary/domains/{did}/terms` | List terms in domain |
| `POST` | `/api/v1/vocabulary/domains/{did}/terms` | Create term |
| `PATCH` | `/api/v1/vocabulary/terms/{id}` | Update term |
| `DELETE` | `/api/v1/vocabulary/terms/{id}` | Delete term |
| `POST` | `/api/v1/vocabulary/terms/{id}/merge` | Merge term into another |

---

## 8. Locations

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/locations` | List locations |
| `POST` | `/api/v1/locations` | Create location |
| `GET` | `/api/v1/locations/{id}` | Get location |
| `PATCH` | `/api/v1/locations/{id}` | Update location |
| `DELETE` | `/api/v1/locations/{id}` | Delete location |
| `GET` | `/api/v1/locations/{id}/documents` | Linked documents |
| `GET` | `/api/v1/locations/{id}/events` | Linked events |

---

## 9. Events

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/events` | List events |
| `POST` | `/api/v1/events` | Create event |
| `GET` | `/api/v1/events/{id}` | Get event |
| `PATCH` | `/api/v1/events/{id}` | Update event |
| `DELETE` | `/api/v1/events/{id}` | Delete event |
| `GET` | `/api/v1/events/{id}/documents` | Linked documents |
| `POST` | `/api/v1/events/{id}/documents` | Link document to event |
| `DELETE` | `/api/v1/events/{id}/documents/{lid}` | Unlink document |
| `GET` | `/api/v1/events/{id}/authorities` | Linked authority records |
| `POST` | `/api/v1/events/{id}/authorities` | Link authority to event |
| `DELETE` | `/api/v1/events/{id}/authorities/{lid}` | Unlink authority |
| `GET` | `/api/v1/events/{id}/locations` | Linked locations |
| `POST` | `/api/v1/events/{id}/locations` | Link location to event |
| `DELETE` | `/api/v1/events/{id}/locations/{lid}` | Unlink location |

---

## 10. Exhibitions

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/exhibitions` | List exhibitions |
| `POST` | `/api/v1/exhibitions` | Create exhibition |
| `GET` | `/api/v1/exhibitions/{id}` | Get exhibition |
| `PATCH` | `/api/v1/exhibitions/{id}` | Update exhibition |
| `DELETE` | `/api/v1/exhibitions/{id}` | Delete exhibition |
| `GET` | `/api/v1/exhibitions/{id}/pages` | List pages |
| `POST` | `/api/v1/exhibitions/{id}/pages` | Create page |
| `GET` | `/api/v1/exhibitions/{id}/pages/{pid}` | Get page |
| `PATCH` | `/api/v1/exhibitions/{id}/pages/{pid}` | Update page |
| `DELETE` | `/api/v1/exhibitions/{id}/pages/{pid}` | Delete page |
| `POST` | `/api/v1/exhibitions/{id}/pages/{pid}/blocks` | Create block |
| `PATCH` | `/api/v1/exhibitions/{id}/pages/{pid}/blocks/{bid}` | Update block |
| `DELETE` | `/api/v1/exhibitions/{id}/pages/{pid}/blocks/{bid}` | Delete block |
| `POST` | `/api/v1/exhibitions/{id}/pages/{pid}/blocks/reorder` | Reorder blocks |

---

## 11. Review Queue

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/v1/review` | List review queue (filterable) | Archivist+ |
| `GET` | `/api/v1/review/{document_id}` | Get review item | Archivist+ |
| `POST` | `/api/v1/review/{document_id}/approve` | Approve (accept suggestions) | Archivist+ |
| `POST` | `/api/v1/review/{document_id}/reject` | Reject suggestions | Archivist+ |
| `PATCH` | `/api/v1/review/{document_id}/assign` | Assign reviewer | Admin |

---

## 12. Search

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/search` | Full-text search with faceted filters |
| `POST` | `/api/v1/cite/bulk` | Bulk citation export |

**Search parameters:** `q`, `creator_id`, `date_from`, `date_to`, `term_ids`, `authority_ids`, `location_ids`, `event_ids`, `node_id`, `document_type`, `language`, `review_status`, `is_public`, `page`, `per_page`

---

## 13. Reports (Archivist+)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/reports/accessions` | Accession report by date range |
| `GET` | `/api/v1/reports/processing` | Completeness by collection |
| `GET` | `/api/v1/reports/users` | User activity report |
| `GET` | `/api/v1/reports/collection` | Collection summary |
| `GET` | `/api/v1/reports/public-access` | Public access metrics |

---

## 14. Preservation (Admin)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/admin/format-inventory` | Format distribution (PRONOM) |
| `GET` | `/api/v1/admin/fixity-report` | Fixity check results |
| `POST` | `/api/v1/admin/fixity-run` | Trigger on-demand fixity check |
| `GET` | `/api/v1/admin/deaccession-log` | Deaccession log |

---

## 15. CSV Imports (Admin)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/admin/imports/template` | Download CSV template |
| `GET` | `/api/v1/admin/imports` | List import jobs |
| `POST` | `/api/v1/admin/imports` | Upload CSV and begin validation |
| `GET` | `/api/v1/admin/imports/{id}` | Get import status + validation report |
| `POST` | `/api/v1/admin/imports/{id}/confirm` | Execute import |
| `DELETE` | `/api/v1/admin/imports/{id}` | Discard import job |

---

## 16. System Settings (Admin)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/settings` | Get all system settings |
| `PATCH` | `/api/v1/settings` | Update system settings |

---

## 17. Public API (No Auth)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/public/exhibitions` | List published exhibitions |
| `GET` | `/api/v1/public/exhibitions/{slug}` | Exhibition summary + page tree |
| `GET` | `/api/v1/public/exhibitions/{slug}/pages/{page-slug}` | Exhibition page with blocks |
| `GET` | `/api/v1/public/documents/{id}` | Public document with metadata |
| `GET` | `/api/v1/public/documents/{id}/files/{fid}` | Serve public file |
| `GET` | `/api/v1/public/documents/{id}/pages` | Public document pages |
| `GET` | `/api/v1/public/search` | Search public documents |
| `GET` | `/api/v1/public/authority/{id}` | Public authority record |
| `GET` | `/api/v1/public/collections` | Public collection browse |
| `GET` | `/api/v1/public/collections/{node_id}` | Public collection detail |
| `GET` | `/api/v1/public/pages` | List static narrative pages |
| `GET` | `/api/v1/public/pages/{slug}` | Static page content |
| `GET` | `/api/v1/public/locations` | Browse public locations |
| `GET` | `/api/v1/public/locations/{id}` | Public location detail |
| `GET` | `/api/v1/public/events` | Browse public events |
| `GET` | `/api/v1/public/events/{id}` | Public event detail |
| `GET` | `/api/v1/public/map-items` | Map query for geolocated documents |

---

## 18. OAI-PMH (No Auth)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/oai` | OAI-PMH 2.0 endpoint |

**Supported verbs:** `Identify`, `ListMetadataFormats`, `ListRecords`, `GetRecord`, `ListIdentifiers`, `ListSets`

**Metadata format:** `oai_dc` (Dublin Core)
**OAI identifier:** `oai:{domain}:{accession_number}`

---

## 19. Persistent URLs (No Auth)

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| `GET` | `/d/{accession_number}` | Resolve document by accession | 301 → public page, or tombstone |
| `GET` | `/ark/{naan}/{id}` | Resolve ARK identifier | 301 → public page |

---

## Common Response Formats

### Pagination
```json
{
  "items": [...],
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
  "code": "machine_code"
}
```

### HTTP Status Codes
| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 204 | No Content (successful delete) |
| 400 | Bad Request |
| 401 | Unauthorized (not logged in) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 409 | Conflict (duplicate) |
| 422 | Validation Error |
| 500 | Internal Server Error |
