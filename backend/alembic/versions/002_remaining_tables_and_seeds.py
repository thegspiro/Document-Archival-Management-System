"""Complete remaining tables and seed vocabulary terms

Revision ID: 002
Revises: 001
Create Date: 2025-01-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Document Files ──
    op.create_table(
        "document_files",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("document_id", sa.BigInteger, sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("stored_path", sa.String(2000), nullable=False),
        sa.Column("mime_type", sa.String(200), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger, nullable=True),
        sa.Column("file_hash_sha256", sa.CHAR(64), nullable=True),
        sa.Column("page_count", sa.Integer, default=1, nullable=False),
        sa.Column("sort_order", sa.Integer, default=0, nullable=False),
        sa.Column("ocr_status", sa.Enum("none", "queued", "processing", "complete", "failed"), default="none", nullable=False),
        sa.Column("ocr_text", mysql.LONGTEXT, nullable=True),
        sa.Column("ocr_completed_at", sa.DateTime, nullable=True),
        sa.Column("ocr_error", sa.Text, nullable=True),
        sa.Column("ocr_attempt_count", sa.SmallInteger, default=0, nullable=False),
        sa.Column("thumbnail_path", sa.String(2000), nullable=True),
        # Technical metadata (NARA/FADGI)
        sa.Column("scan_resolution_ppi", sa.Integer, nullable=True),
        sa.Column("bit_depth", sa.SmallInteger, nullable=True),
        sa.Column("color_space", sa.String(50), nullable=True),
        sa.Column("scanner_make", sa.String(200), nullable=True),
        sa.Column("scanner_model", sa.String(200), nullable=True),
        sa.Column("scanning_software", sa.String(200), nullable=True),
        sa.Column("image_quality_rating", sa.Enum("preservation_master", "production_master", "access_copy", "unknown"), default="unknown"),
        # Format characterization (PREMIS/OAIS)
        sa.Column("format_name", sa.String(200), nullable=True),
        sa.Column("format_version", sa.String(50), nullable=True),
        sa.Column("format_puid", sa.String(50), nullable=True),
        sa.Column("format_registry", sa.String(50), default="PRONOM"),
        sa.Column("format_validated", sa.Boolean, default=False),
        sa.Column("format_validated_at", sa.DateTime, nullable=True),
        sa.Column("preservation_warning", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_document_files_document_id", "document_files", ["document_id"])
    op.create_index("ix_document_files_hash", "document_files", ["file_hash_sha256"])

    # ── Document Pages ──
    op.create_table(
        "document_pages",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("document_file_id", sa.BigInteger, sa.ForeignKey("document_files.id", ondelete="CASCADE"), nullable=False),
        sa.Column("page_number", sa.Integer, nullable=False),
        sa.Column("ocr_text", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("is_public", sa.Boolean, default=False, nullable=False),
        sa.Column("thumbnail_path", sa.String(2000), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # ── Document Terms (tags/categories) ──
    op.create_table(
        "document_terms",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("document_id", sa.BigInteger, sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("term_id", sa.BigInteger, sa.ForeignKey("vocabulary_terms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by", sa.BigInteger, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("document_id", "term_id", name="uq_document_term"),
    )

    # ── Document Relationships ──
    op.create_table(
        "document_relationships",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("source_document_id", sa.BigInteger, sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_document_id", sa.BigInteger, sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relationship_type_id", sa.BigInteger, sa.ForeignKey("vocabulary_terms.id"), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_by", sa.BigInteger, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("source_document_id", "target_document_id", "relationship_type_id", name="uq_doc_relationship"),
    )

    # ── Document–Authority Links ──
    op.create_table(
        "document_authority_links",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("document_id", sa.BigInteger, sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("authority_id", sa.BigInteger, sa.ForeignKey("authority_records.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_id", sa.BigInteger, sa.ForeignKey("vocabulary_terms.id"), nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_by", sa.BigInteger, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("document_id", "authority_id", "role_id", name="uq_doc_authority_link"),
    )

    # ── Authority Relationships ──
    op.create_table(
        "authority_relationships",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("source_authority_id", sa.BigInteger, sa.ForeignKey("authority_records.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_authority_id", sa.BigInteger, sa.ForeignKey("authority_records.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relationship_type_id", sa.BigInteger, sa.ForeignKey("vocabulary_terms.id"), nullable=False),
        sa.Column("date_start", sa.Date, nullable=True),
        sa.Column("date_end", sa.Date, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_by", sa.BigInteger, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("source_authority_id", "target_authority_id", "relationship_type_id", name="uq_authority_rel"),
    )

    # ── Locations ──
    op.create_table(
        "locations",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("authorized_name", sa.String(500), nullable=False),
        sa.Column("variant_names", sa.Text, nullable=True),
        sa.Column("location_type_id", sa.BigInteger, sa.ForeignKey("vocabulary_terms.id"), nullable=True),
        sa.Column("geo_latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("geo_longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("date_established", sa.Date, nullable=True),
        sa.Column("date_ceased", sa.Date, nullable=True),
        sa.Column("parent_location_id", sa.BigInteger, sa.ForeignKey("locations.id"), nullable=True),
        sa.Column("wikidata_qid", sa.String(20), nullable=True),
        sa.Column("is_public", sa.Boolean, default=False, nullable=False),
        sa.Column("public_description", sa.Text, nullable=True),
        sa.Column("created_by", sa.BigInteger, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # ── Document–Location Links ──
    op.create_table(
        "document_location_links",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("document_id", sa.BigInteger, sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("location_id", sa.BigInteger, sa.ForeignKey("locations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("link_type", sa.Enum("mentioned", "depicted", "created_at", "event_location"), default="mentioned"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_by", sa.BigInteger, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("document_id", "location_id", "link_type", name="uq_doc_location_link"),
    )

    # ── Events ──
    op.create_table(
        "events",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("event_type_id", sa.BigInteger, sa.ForeignKey("vocabulary_terms.id"), nullable=False),
        sa.Column("date_display", sa.String(200), nullable=True),
        sa.Column("date_start", sa.Date, nullable=True),
        sa.Column("date_end", sa.Date, nullable=True),
        sa.Column("primary_location_id", sa.BigInteger, sa.ForeignKey("locations.id"), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_public", sa.Boolean, default=False, nullable=False),
        sa.Column("public_description", sa.Text, nullable=True),
        sa.Column("created_by", sa.BigInteger, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # ── Event–Document Links ──
    op.create_table(
        "event_document_links",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.BigInteger, sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", sa.BigInteger, sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("link_type", sa.Enum("produced_by", "about", "referenced_in", "precedes", "follows"), default="about"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_by", sa.BigInteger, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("event_id", "document_id", name="uq_event_document"),
    )

    # ── Event–Authority Links ──
    op.create_table(
        "event_authority_links",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.BigInteger, sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("authority_id", sa.BigInteger, sa.ForeignKey("authority_records.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_id", sa.BigInteger, sa.ForeignKey("vocabulary_terms.id"), nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_by", sa.BigInteger, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("event_id", "authority_id", "role_id", name="uq_event_authority"),
    )

    # ── Event–Location Links ──
    op.create_table(
        "event_location_links",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.BigInteger, sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("location_id", sa.BigInteger, sa.ForeignKey("locations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("link_type", sa.Enum("primary", "secondary", "mentioned"), default="primary"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_by", sa.BigInteger, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("event_id", "location_id", name="uq_event_location"),
    )

    # ── Collection Permissions ──
    op.create_table(
        "collection_permissions",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("arrangement_node_id", sa.BigInteger, sa.ForeignKey("arrangement_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("role_id", sa.BigInteger, sa.ForeignKey("roles.id"), nullable=True),
        sa.Column("can_view", sa.Boolean, default=False, nullable=False),
        sa.Column("can_create", sa.Boolean, default=False, nullable=False),
        sa.Column("can_edit", sa.Boolean, default=False, nullable=False),
        sa.Column("can_delete", sa.Boolean, default=False, nullable=False),
        sa.Column("can_manage_permissions", sa.Boolean, default=False, nullable=False),
        sa.Column("created_by", sa.BigInteger, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # ── Review Queue ──
    op.create_table(
        "review_queue",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("document_id", sa.BigInteger, sa.ForeignKey("documents.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("reason", sa.Enum("llm_suggestions", "manual_flag", "import", "initial_review", "integrity_failure"), nullable=False),
        sa.Column("assigned_to", sa.BigInteger, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("priority", sa.Enum("low", "normal", "high"), default="normal"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_by", sa.BigInteger, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # ── Exhibitions ──
    op.create_table(
        "exhibitions",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("slug", sa.String(200), unique=True, nullable=False),
        sa.Column("subtitle", sa.String(500), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("credits", sa.Text, nullable=True),
        sa.Column("cover_image_path", sa.String(2000), nullable=True),
        sa.Column("header_image_path", sa.String(2000), nullable=True),
        sa.Column("accent_color", sa.String(7), nullable=True),
        sa.Column("show_summary_page", sa.Boolean, default=True, nullable=False),
        sa.Column("is_published", sa.Boolean, default=False, nullable=False),
        sa.Column("published_at", sa.DateTime, nullable=True),
        sa.Column("sort_order", sa.Integer, default=0, nullable=False),
        sa.Column("created_by", sa.BigInteger, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "exhibition_tags",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("exhibition_id", sa.BigInteger, sa.ForeignKey("exhibitions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("term_id", sa.BigInteger, sa.ForeignKey("vocabulary_terms.id"), nullable=False),
        sa.UniqueConstraint("exhibition_id", "term_id", name="uq_exhibition_tag"),
    )

    op.create_table(
        "exhibition_pages",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("exhibition_id", sa.BigInteger, sa.ForeignKey("exhibitions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_page_id", sa.BigInteger, sa.ForeignKey("exhibition_pages.id"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("slug", sa.String(200), nullable=False),
        sa.Column("menu_title", sa.String(200), nullable=True),
        sa.Column("is_public", sa.Boolean, default=True, nullable=False),
        sa.Column("sort_order", sa.Integer, default=0, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("exhibition_id", "slug", name="uq_exhibition_page_slug"),
    )

    op.create_table(
        "exhibition_page_blocks",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("page_id", sa.BigInteger, sa.ForeignKey("exhibition_pages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("block_type", sa.Enum(
            "html", "file_with_text", "gallery", "document_metadata",
            "map", "timeline", "table_of_contents", "collection_browse", "separator"
        ), nullable=False),
        sa.Column("content", mysql.JSON, nullable=False),
        sa.Column("layout", sa.Enum("full", "left", "right", "center"), default="full"),
        sa.Column("sort_order", sa.Integer, default=0, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # ── Public Pages (static narrative) ──
    op.create_table(
        "public_pages",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("slug", sa.String(200), unique=True, nullable=False),
        sa.Column("body_html", sa.Text, nullable=False),
        sa.Column("is_published", sa.Boolean, default=False, nullable=False),
        sa.Column("show_in_navigation", sa.Boolean, default=True, nullable=False),
        sa.Column("sort_order", sa.Integer, default=0, nullable=False),
        sa.Column("created_by", sa.BigInteger, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # ── Audit Log ──
    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(200), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=True),
        sa.Column("resource_id", sa.BigInteger, nullable=True),
        sa.Column("detail", mysql.JSON, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_log_user_id", "audit_log", ["user_id"])
    op.create_index("ix_audit_log_action", "audit_log", ["action"])
    op.create_index("ix_audit_log_resource", "audit_log", ["resource_type", "resource_id"])

    # ── Preservation Events (PREMIS) ──
    op.create_table(
        "preservation_events",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("document_file_id", sa.BigInteger, sa.ForeignKey("document_files.id"), nullable=True),
        sa.Column("document_id", sa.BigInteger, sa.ForeignKey("documents.id"), nullable=True),
        sa.Column("event_type", sa.Enum(
            "ingest", "fixity_check", "format_validation", "virus_scan",
            "ocr", "migration", "deletion", "access", "modification", "replication"
        ), nullable=False),
        sa.Column("event_outcome", sa.Enum("success", "failure", "warning"), nullable=False),
        sa.Column("event_detail", sa.Text, nullable=True),
        sa.Column("agent", sa.String(200), nullable=True),
        sa.Column("event_datetime", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # ── Fixity Checks (OAIS) ──
    op.create_table(
        "fixity_checks",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("document_file_id", sa.BigInteger, sa.ForeignKey("document_files.id"), nullable=False),
        sa.Column("checked_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("stored_hash", sa.CHAR(64), nullable=False),
        sa.Column("computed_hash", sa.CHAR(64), nullable=False),
        sa.Column("outcome", sa.Enum("match", "mismatch", "file_missing"), nullable=False),
        sa.Column("checked_by", sa.String(200), nullable=True),
    )

    # ── Watch Folders ──
    op.create_table(
        "watch_folders",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("path", sa.String(2000), nullable=False),
        sa.Column("target_node_id", sa.BigInteger, sa.ForeignKey("arrangement_nodes.id"), nullable=True),
        sa.Column("default_tags", mysql.JSON, nullable=True),
        sa.Column("poll_interval_seconds", sa.Integer, default=60, nullable=False),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("created_by", sa.BigInteger, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # ── Saved Views ──
    op.create_table(
        "saved_views",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("filter_params", mysql.JSON, nullable=False),
        sa.Column("display_type", sa.Enum("count", "list", "grid"), default="list"),
        sa.Column("sort_order", sa.Integer, default=0, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # ── Deaccession Log (AASLH) ──
    op.create_table(
        "deaccession_log",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("document_id", sa.BigInteger, nullable=False),
        sa.Column("accession_number", sa.String(200), nullable=True),
        sa.Column("title", sa.String(1000), nullable=True),
        sa.Column("deaccession_date", sa.Date, nullable=False),
        sa.Column("reason_code_id", sa.BigInteger, sa.ForeignKey("vocabulary_terms.id"), nullable=True),
        sa.Column("reason_note", sa.Text, nullable=False),
        sa.Column("disposition", sa.Enum("destroyed", "transferred", "returned", "sold", "donated"), nullable=False),
        sa.Column("transfer_destination", sa.Text, nullable=True),
        sa.Column("authorized_by", sa.BigInteger, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # ── Institution Description Standards ──
    op.create_table(
        "institution_description_standards",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("level", sa.Enum("minimal", "standard", "full"), nullable=False),
        sa.Column("required_fields", mysql.JSON, nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("updated_by", sa.BigInteger, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # ── CSV Imports ──
    op.create_table(
        "csv_imports",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("import_mode", sa.Enum("template", "mapped"), nullable=False),
        sa.Column("status", sa.Enum("uploaded", "validating", "validation_failed", "ready", "importing", "complete", "failed"), default="uploaded"),
        sa.Column("total_rows", sa.Integer, default=0, nullable=False),
        sa.Column("valid_rows", sa.Integer, default=0, nullable=False),
        sa.Column("warning_rows", sa.Integer, default=0, nullable=False),
        sa.Column("error_rows", sa.Integer, default=0, nullable=False),
        sa.Column("imported_rows", sa.Integer, default=0, nullable=False),
        sa.Column("target_node_id", sa.BigInteger, sa.ForeignKey("arrangement_nodes.id"), nullable=True),
        sa.Column("column_mapping", mysql.JSON, nullable=True),
        sa.Column("validation_report", mysql.JSON, nullable=True),
        sa.Column("new_vocabulary_terms", mysql.JSON, nullable=True),
        sa.Column("created_by", sa.BigInteger, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "csv_import_rows",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("import_id", sa.BigInteger, sa.ForeignKey("csv_imports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("row_number", sa.Integer, nullable=False),
        sa.Column("raw_data", mysql.JSON, nullable=False),
        sa.Column("mapped_data", mysql.JSON, nullable=True),
        sa.Column("document_id", sa.BigInteger, sa.ForeignKey("documents.id"), nullable=True),
        sa.Column("status", sa.Enum("pending", "valid", "warning", "error", "imported", "skipped"), default="pending"),
        sa.Column("messages", mysql.JSON, nullable=True),
    )

    # ── Document Annotations ──
    op.create_table(
        "document_annotations",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("document_id", sa.BigInteger, sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_file_id", sa.BigInteger, sa.ForeignKey("document_files.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_page_id", sa.BigInteger, sa.ForeignKey("document_pages.id"), nullable=True),
        sa.Column("annotation_type", sa.Enum("region", "text_range"), nullable=False),
        sa.Column("region_geometry", mysql.JSON, nullable=True),
        sa.Column("text_range", mysql.JSON, nullable=True),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("is_resolved", sa.Boolean, default=False, nullable=False),
        sa.Column("resolved_by", sa.BigInteger, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resolved_at", sa.DateTime, nullable=True),
        sa.Column("created_by", sa.BigInteger, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # ── FULLTEXT indexes for search ──
    op.execute(
        "ALTER TABLE documents ADD FULLTEXT INDEX ft_documents_search "
        "(title, scope_and_content, general_note)"
    )

    # ── Seed institution description standards (DACS defaults) ──
    op.execute(
        "INSERT INTO institution_description_standards (level, required_fields) VALUES "
        """('minimal', '["title", "date_display", "level_of_description", "extent"]'), """
        """('standard', '["title", "date_display", "level_of_description", "extent", "creator_id", "scope_and_content", "access_conditions", "language_of_material"]'), """
        """('full', '["title", "date_display", "level_of_description", "extent", "creator_id", "scope_and_content", "access_conditions", "language_of_material", "archival_history", "immediate_source", "physical_characteristics"]')"""
    )

    # ═══════════════════════════════════════════════════════════════════
    # SEED ALL VOCABULARY TERMS (from CLAUDE.md §5.8, §5.11–§5.17, §34.1)
    # ═══════════════════════════════════════════════════════════════════

    # Helper: terms are inserted referencing domains by name via subquery
    def _seed_terms(domain_name: str, terms: list[str]) -> None:
        values = ", ".join(
            f"((SELECT id FROM vocabulary_domains WHERE name = '{domain_name}'), '{t}', {i})"
            for i, t in enumerate(terms)
        )
        op.execute(
            f"INSERT INTO vocabulary_terms (domain_id, term, sort_order) VALUES {values}"
        )

    # document_type (§34.1)
    _seed_terms("document_type", [
        "letter", "deed", "legal_document", "photograph", "map", "report", "minutes",
        "memorandum", "telegram", "diary", "ledger", "census_record", "newspaper_clipping",
        "pamphlet", "broadside", "manuscript", "petition", "ordinance", "court_record",
        "military_record", "oral_history", "birth_certificate", "death_certificate",
        "land_patent", "survey", "blueprint", "scrapbook", "postcard", "invoice", "receipt",
        "will", "inventory", "subscription_list", "election_record", "tax_record", "permit",
    ])

    # physical_format
    _seed_terms("physical_format", [
        "paper", "photographic_print", "glass_plate", "microfilm", "vellum",
        "parchment", "textile", "metal", "ceramic", "digital_born",
    ])

    # condition
    _seed_terms("condition", [
        "excellent", "good", "fair", "poor", "damaged",
    ])

    # relationship_type (§5.10)
    _seed_terms("relationship_type", [
        "reply_to", "precedes", "follows", "revision_of", "related_to",
        "supplement_to", "translation_of", "copy_of",
    ])

    # access_restriction
    _seed_terms("access_restriction", [
        "public", "restricted", "confidential", "embargoed",
    ])

    # authority_link_role (§5.11)
    _seed_terms("authority_link_role", [
        "recipient", "signatory", "witness", "mentioned", "depicted",
        "correspondent", "subject_of", "co_creator", "collector",
        "transcribed_by", "donor", "addressee",
    ])

    # authority_relationship_type (§5.12)
    _seed_terms("authority_relationship_type", [
        "spouse_of", "parent_of", "child_of", "sibling_of", "colleague_of",
        "member_of", "employed_by", "founded", "associated_with",
        "succeeded_by", "preceded_by",
    ])

    # location_type (§5.13)
    _seed_terms("location_type", [
        "building", "room", "neighborhood", "district", "city", "county",
        "state", "country", "farm", "mill", "cemetery", "park", "road",
        "bridge", "body_of_water", "battlefield", "institution",
    ])

    # event_type (§5.15)
    _seed_terms("event_type", [
        "meeting", "election", "fire", "flood", "disaster", "ceremony",
        "dedication", "legal_proceeding", "trial", "construction",
        "demolition", "birth", "death", "marriage", "publication",
        "incorporation", "annexation", "military_action",
    ])

    # event_authority_role (§5.17)
    _seed_terms("event_authority_role", [
        "organizer", "attendee", "speaker", "presiding_officer", "witness",
        "subject", "signatory", "candidate", "elected", "deceased", "married",
    ])

    # deaccession_reason (§34.1)
    _seed_terms("deaccession_reason", [
        "mission_misalignment", "poor_condition_irreparable", "duplicate",
        "donor_request", "legal_requirement", "transfer_to_better_repository",
        "out_of_scope",
    ])

    # language — common ISO 639 languages
    _seed_terms("language", [
        "eng", "fra", "deu", "spa", "ita", "por", "nld", "rus", "zho",
        "jpn", "kor", "ara", "heb", "lat", "grc", "pol", "swe", "nor",
    ])


def downgrade() -> None:
    tables = [
        "document_annotations", "csv_import_rows", "csv_imports",
        "institution_description_standards", "deaccession_log",
        "saved_views", "watch_folders", "fixity_checks",
        "preservation_events", "audit_log", "public_pages",
        "exhibition_page_blocks", "exhibition_pages", "exhibition_tags",
        "exhibitions", "review_queue", "collection_permissions",
        "event_location_links", "event_authority_links",
        "event_document_links", "events", "document_location_links",
        "locations", "authority_relationships",
        "document_authority_links", "document_relationships",
        "document_terms", "document_pages", "document_files",
    ]
    for table in tables:
        op.drop_table(table)
