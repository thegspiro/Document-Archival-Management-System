"""CSV import service — upload, validation, and execution of CSV import jobs."""

import csv
import io
from datetime import date, datetime, timezone
from typing import Any

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.authority_record import AuthorityRecord
from app.models.csv_import import CsvImport, CsvImportRow
from app.models.document import Document
from app.models.document_term import DocumentTerm
from app.models.vocabulary import VocabularyDomain, VocabularyTerm
from app.services.audit_service import AuditService
from app.services.document_service import DocumentService

# Columns present in the ADMS CSV template (§29.2).
TEMPLATE_COLUMNS = [
    "accession_number", "title", "date_display", "date_start", "date_end",
    "creator_name", "document_type", "extent", "language_of_material",
    "scope_and_content", "access_conditions", "reproduction_conditions",
    "copyright_status", "rights_holder", "rights_note", "location_of_originals",
    "physical_format", "condition", "general_note", "archivists_note",
    "tags", "subject_categories", "geo_location_name", "geo_latitude",
    "geo_longitude", "original_location", "scan_date",
    "has_content_advisory", "content_advisory_note",
]

VALID_COPYRIGHT_STATUSES = {
    "copyrighted", "public_domain", "unknown", "orphan_work", "creative_commons",
}


class ImportService:
    """Manages the CSV import lifecycle: upload, validation, and execution."""

    # ------------------------------------------------------------------
    # Create import job
    # ------------------------------------------------------------------

    @staticmethod
    async def create_import(
        db: AsyncSession,
        *,
        upload: UploadFile,
        import_mode: str = "template",
        target_node_id: int | None = None,
        column_mapping: dict[str, str] | None = None,
        created_by: int | None = None,
        ip_address: str | None = None,
    ) -> CsvImport:
        """Upload a CSV file and create an import job record.

        Does not yet validate; call ``validate_csv`` next.
        """
        filename = upload.filename or "import.csv"
        contents = await upload.read()

        job = CsvImport(
            filename=filename,
            import_mode=import_mode,
            target_node_id=target_node_id,
            column_mapping=column_mapping,
            created_by=created_by,
        )
        db.add(job)
        await db.flush()

        # Parse rows and store them.
        text_content = contents.decode("utf-8-sig")  # Handle BOM
        reader = csv.DictReader(io.StringIO(text_content))
        row_number = 0
        for row_data in reader:
            row_number += 1
            db.add(CsvImportRow(
                import_id=job.id,
                row_number=row_number,
                raw_data=dict(row_data),
            ))

        job.total_rows = row_number
        await db.flush()

        await AuditService.log(
            db,
            user_id=created_by,
            action="csv_import.create",
            resource_type="csv_import",
            resource_id=job.id,
            detail={"filename": filename, "total_rows": row_number, "mode": import_mode},
            ip_address=ip_address,
        )
        return job

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    async def validate_csv(
        db: AsyncSession,
        *,
        import_id: int,
    ) -> CsvImport:
        """Run the validation pipeline on an uploaded CSV import job.

        Updates row statuses and the job's validation_report field.
        """
        result = await db.execute(
            select(CsvImport).where(CsvImport.id == import_id)
        )
        job = result.scalar_one_or_none()
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Import job not found",
            )

        job.status = "validating"
        await db.flush()

        rows_result = await db.execute(
            select(CsvImportRow)
            .where(CsvImportRow.import_id == import_id)
            .order_by(CsvImportRow.row_number)
        )
        rows = list(rows_result.scalars().all())

        valid_count = 0
        warning_count = 0
        error_count = 0
        new_terms: list[str] = []
        new_authorities: list[str] = []
        duplicate_accessions: list[str] = []

        for row in rows:
            messages: list[dict[str, str]] = []
            data = row.raw_data or {}

            # Apply column mapping for mapped mode.
            if job.import_mode == "mapped" and job.column_mapping:
                mapped: dict[str, Any] = {}
                for src_col, adms_field in job.column_mapping.items():
                    if src_col in data:
                        mapped[adms_field] = data[src_col]
                row.mapped_data = mapped
                data = mapped
            else:
                row.mapped_data = data

            # Validate title (required).
            if not data.get("title", "").strip():
                messages.append({"level": "error", "field": "title", "message": "Title is required"})

            # Validate dates.
            for date_field in ("date_start", "date_end", "scan_date"):
                val = data.get(date_field, "").strip()
                if val:
                    try:
                        datetime.strptime(val, "%Y-%m-%d")
                    except ValueError:
                        messages.append({
                            "level": "error",
                            "field": date_field,
                            "message": f"Invalid date format: '{val}'. Expected YYYY-MM-DD.",
                        })

            # Validate copyright_status.
            cs = data.get("copyright_status", "").strip()
            if cs and cs not in VALID_COPYRIGHT_STATUSES:
                messages.append({
                    "level": "warning",
                    "field": "copyright_status",
                    "message": f"Unknown copyright status: '{cs}'. Will default to 'unknown'.",
                })

            # Check accession number for duplicates.
            accession = data.get("accession_number", "").strip()
            if accession:
                existing = await db.execute(
                    select(Document.id).where(Document.accession_number == accession)
                )
                if existing.scalar_one_or_none() is not None:
                    messages.append({
                        "level": "warning",
                        "field": "accession_number",
                        "message": f"Accession '{accession}' already exists. Will skip or update.",
                    })
                    duplicate_accessions.append(accession)

            # Check creator_name against authority records.
            creator = data.get("creator_name", "").strip()
            if creator:
                auth_result = await db.execute(
                    select(AuthorityRecord.id).where(
                        AuthorityRecord.authorized_name == creator
                    )
                )
                if auth_result.scalar_one_or_none() is None:
                    messages.append({
                        "level": "warning",
                        "field": "creator_name",
                        "message": f"No matching authority record for '{creator}'. Will create new.",
                    })
                    if creator not in new_authorities:
                        new_authorities.append(creator)

            # Check vocabulary terms (document_type, tags, etc.).
            for vocab_field, domain_name in [
                ("document_type", "document_type"),
                ("physical_format", "physical_format"),
                ("condition", "condition"),
            ]:
                val = data.get(vocab_field, "").strip()
                if val:
                    domain_result = await db.execute(
                        select(VocabularyDomain.id).where(VocabularyDomain.name == domain_name)
                    )
                    domain_id = domain_result.scalar_one_or_none()
                    if domain_id:
                        term_result = await db.execute(
                            select(VocabularyTerm.id).where(
                                VocabularyTerm.domain_id == domain_id,
                                VocabularyTerm.term == val,
                            )
                        )
                        if term_result.scalar_one_or_none() is None:
                            messages.append({
                                "level": "warning",
                                "field": vocab_field,
                                "message": f"New term '{val}' will be created in '{domain_name}' domain.",
                            })
                            term_key = f"{domain_name}:{val}"
                            if term_key not in new_terms:
                                new_terms.append(term_key)

            # Determine row status.
            has_errors = any(m["level"] == "error" for m in messages)
            has_warnings = any(m["level"] == "warning" for m in messages)

            if has_errors:
                row.status = "error"
                error_count += 1
            elif has_warnings:
                row.status = "warning"
                warning_count += 1
            else:
                row.status = "valid"
                valid_count += 1

            row.messages = messages

        job.valid_rows = valid_count
        job.warning_rows = warning_count
        job.error_rows = error_count
        job.new_vocabulary_terms = {"terms": new_terms}
        job.validation_report = {
            "valid_rows": valid_count,
            "warning_rows": warning_count,
            "error_rows": error_count,
            "new_vocabulary_terms": new_terms,
            "new_authority_records": new_authorities,
            "duplicate_accessions": duplicate_accessions,
        }
        job.status = "validation_failed" if error_count > 0 else "ready"
        await db.flush()

        return job

    # ------------------------------------------------------------------
    # Execute import
    # ------------------------------------------------------------------

    @staticmethod
    async def execute_import(
        db: AsyncSession,
        *,
        import_id: int,
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> CsvImport:
        """Execute a validated import job, creating document records.

        Only rows with status ``'valid'`` or ``'warning'`` are imported.
        All imported documents start with ``inbox_status='inbox'`` and
        ``is_public=False``.
        """
        result = await db.execute(
            select(CsvImport).where(CsvImport.id == import_id)
        )
        job = result.scalar_one_or_none()
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Import job not found",
            )

        if job.status not in ("ready",):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Import job is in '{job.status}' state; must be 'ready' to execute",
            )

        job.status = "importing"
        await db.flush()

        rows_result = await db.execute(
            select(CsvImportRow)
            .where(
                CsvImportRow.import_id == import_id,
                CsvImportRow.status.in_(["valid", "warning"]),
            )
            .order_by(CsvImportRow.row_number)
        )
        rows = list(rows_result.scalars().all())

        imported_count = 0

        for row in rows:
            data = row.mapped_data or row.raw_data or {}
            try:
                doc_data: dict[str, Any] = {
                    "title": data.get("title", "Untitled"),
                    "date_display": data.get("date_display"),
                    "scope_and_content": data.get("scope_and_content"),
                    "access_conditions": data.get("access_conditions"),
                    "reproduction_conditions": data.get("reproduction_conditions"),
                    "rights_holder": data.get("rights_holder"),
                    "rights_note": data.get("rights_note"),
                    "location_of_originals": data.get("location_of_originals"),
                    "general_note": data.get("general_note"),
                    "archivists_note": data.get("archivists_note"),
                    "geo_location_name": data.get("geo_location_name"),
                    "original_location": data.get("original_location"),
                    "language_of_material": data.get("language_of_material"),
                    "extent": data.get("extent"),
                    "inbox_status": "inbox",
                    "is_public": False,
                }

                # Parse dates.
                for df in ("date_start", "date_end", "scan_date"):
                    val = data.get(df, "").strip() if data.get(df) else ""
                    if val:
                        try:
                            doc_data[df] = datetime.strptime(val, "%Y-%m-%d").date()
                        except ValueError:
                            pass

                # Accession number.
                accession = data.get("accession_number", "").strip() if data.get("accession_number") else ""
                if accession:
                    doc_data["accession_number"] = accession

                # Copyright status.
                cs = data.get("copyright_status", "").strip() if data.get("copyright_status") else ""
                if cs in VALID_COPYRIGHT_STATUSES:
                    doc_data["copyright_status"] = cs

                # Content advisory.
                ha = data.get("has_content_advisory", "").strip().upper() if data.get("has_content_advisory") else ""
                if ha == "TRUE":
                    doc_data["has_content_advisory"] = True
                    doc_data["content_advisory_note"] = data.get("content_advisory_note")

                # Geo coordinates.
                for geo_field in ("geo_latitude", "geo_longitude"):
                    val = data.get(geo_field, "").strip() if data.get(geo_field) else ""
                    if val:
                        try:
                            doc_data[geo_field] = float(val)
                        except ValueError:
                            pass

                # Target node from job settings.
                if job.target_node_id:
                    doc_data["arrangement_node_id"] = job.target_node_id

                doc = await DocumentService.create_document(
                    db,
                    data=doc_data,
                    created_by=acting_user_id,
                    ip_address=ip_address,
                )

                row.document_id = doc.id
                row.status = "imported"
                imported_count += 1

            except Exception as exc:
                row.status = "error"
                row.messages = (row.messages or []) + [
                    {"level": "error", "field": "general", "message": str(exc)}
                ]

        job.imported_rows = imported_count
        job.status = "complete"
        await db.flush()

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="csv_import.execute",
            resource_type="csv_import",
            resource_id=job.id,
            detail={"imported_rows": imported_count, "total_rows": job.total_rows},
            ip_address=ip_address,
        )
        return job

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    @staticmethod
    async def get_import_status(
        db: AsyncSession,
        *,
        import_id: int,
    ) -> CsvImport:
        """Return the current state of an import job, or raise 404."""
        result = await db.execute(
            select(CsvImport).where(CsvImport.id == import_id)
        )
        job = result.scalar_one_or_none()
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Import job not found",
            )
        return job
