/** Response types mirroring backend Pydantic schemas. */

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface User {
  id: number;
  email: string;
  display_name: string;
  is_active: boolean;
  is_superadmin: boolean;
  roles: Role[];
  last_login_at: string | null;
  created_at: string;
}

export interface Role {
  id: number;
  name: string;
  description: string | null;
}

export interface Document {
  id: number;
  arrangement_node_id: number | null;
  accession_number: string | null;
  version_group_id: number | null;
  version_number: number;
  version_label: string | null;
  is_canonical_version: boolean;
  title: string;
  reference_code: string | null;
  date_display: string | null;
  date_start: string | null;
  date_end: string | null;
  level_of_description: string;
  extent: string | null;
  creator_id: number | null;
  creator: AuthorityRecord | null;
  scope_and_content: string | null;
  access_conditions: string | null;
  language_of_material: string | null;
  copyright_status: string;
  rights_holder: string | null;
  rights_note: string | null;
  description_status: string;
  description_completeness: string;
  review_status: string;
  inbox_status: string;
  is_public: boolean;
  has_content_advisory: boolean;
  content_advisory_note: string | null;
  availability_status: string;
  geo_latitude: number | null;
  geo_longitude: number | null;
  geo_location_name: string | null;
  ark_id: string | null;
  files: DocumentFile[];
  terms: DocumentTerm[];
  llm_suggestions: Record<string, unknown> | null;
  created_by: number | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentCreate {
  title: string;
  arrangement_node_id?: number | null;
  date_display?: string | null;
  date_start?: string | null;
  date_end?: string | null;
  creator_id?: number | null;
  scope_and_content?: string | null;
  level_of_description?: string;
  extent?: string | null;
  language_of_material?: string | null;
  copyright_status?: string;
  [key: string]: unknown;
}

export interface DocumentUpdate extends Partial<DocumentCreate> {}

export interface DocumentFile {
  id: number;
  document_id: number;
  filename: string;
  stored_path: string;
  mime_type: string | null;
  file_size_bytes: number | null;
  file_hash_sha256: string | null;
  page_count: number;
  ocr_status: string;
  ocr_text: string | null;
  ocr_error: string | null;
  thumbnail_path: string | null;
  format_name: string | null;
  format_puid: string | null;
  preservation_warning: string | null;
  created_at: string;
}

export interface DocumentPage {
  id: number;
  document_file_id: number;
  page_number: number;
  ocr_text: string | null;
  notes: string | null;
  is_public: boolean;
  thumbnail_path: string | null;
}

export interface DocumentTerm {
  id: number;
  document_id: number;
  term_id: number;
  term: VocabularyTerm;
}

export interface AuthorityRecord {
  id: number;
  entity_type: 'person' | 'organization' | 'family';
  authorized_name: string;
  variant_names: string | null;
  dates: string | null;
  biographical_history: string | null;
  administrative_history: string | null;
  identifier: string | null;
  notes: string | null;
  is_public: boolean;
  wikidata_qid: string | null;
  wikidata_enrichment: Record<string, unknown> | null;
  created_by_ner: boolean;
  created_at: string;
  updated_at: string;
}

export interface VocabularyDomain {
  id: number;
  name: string;
  description: string | null;
  allows_user_addition: boolean;
}

export interface VocabularyTerm {
  id: number;
  domain_id: number;
  term: string;
  definition: string | null;
  broader_term_id: number | null;
  is_active: boolean;
  sort_order: number;
}

export interface ArrangementNode {
  id: number;
  parent_id: number | null;
  level_type: string;
  title: string;
  identifier: string | null;
  description: string | null;
  date_start: string | null;
  date_end: string | null;
  is_public: boolean;
  sort_order: number;
  children?: ArrangementNode[];
}

export interface Location {
  id: number;
  authorized_name: string;
  variant_names: string | null;
  location_type_id: number | null;
  geo_latitude: number | null;
  geo_longitude: number | null;
  address: string | null;
  description: string | null;
  is_public: boolean;
  created_at: string;
}

export interface Event {
  id: number;
  title: string;
  event_type_id: number;
  date_display: string | null;
  date_start: string | null;
  date_end: string | null;
  primary_location_id: number | null;
  description: string | null;
  is_public: boolean;
  created_at: string;
}

export interface Exhibition {
  id: number;
  title: string;
  slug: string;
  subtitle: string | null;
  description: string | null;
  cover_image_path: string | null;
  is_published: boolean;
  published_at: string | null;
  sort_order: number;
  pages?: ExhibitionPage[];
}

export interface ExhibitionPage {
  id: number;
  exhibition_id: number;
  parent_page_id: number | null;
  title: string;
  slug: string;
  menu_title: string | null;
  is_public: boolean;
  sort_order: number;
  blocks?: ExhibitionPageBlock[];
}

export interface ExhibitionPageBlock {
  id: number;
  page_id: number;
  block_type: string;
  content: Record<string, unknown>;
  layout: string;
  sort_order: number;
}

export interface ReviewQueueItem {
  id: number;
  document_id: number;
  document: Document;
  reason: string;
  assigned_to: number | null;
  priority: string;
  notes: string | null;
  created_at: string;
}

export interface AuditLogEntry {
  id: number;
  user_id: number | null;
  action: string;
  resource_type: string | null;
  resource_id: number | null;
  detail: Record<string, unknown> | null;
  created_at: string;
}
