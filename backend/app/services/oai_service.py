"""OAI-PMH 2.0 service — implements all six OAI-PMH verbs.

Only the oai_dc (Dublin Core) metadata format is supported in phase 1.
Only public records are exposed. Deaccessioned documents appear as deleted
for 30 days after deaccession. Resumption tokens use cursor-based pagination
(last-seen ID) for ListRecords and ListIdentifiers.
"""

import base64
import json
from datetime import date, datetime, timedelta, timezone
from typing import Any

from lxml import etree
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.export.dublin_core import document_to_dc_dict
from app.models.arrangement import ArrangementNode
from app.models.deaccession_log import DeaccessionLog
from app.models.document import Document

# OAI-PMH namespaces
OAI_NS = "http://www.openarchives.org/OAI/2.0/"
OAI_DC_NS = "http://www.openarchives.org/OAI/2.0/oai_dc/"
DC_NS = "http://purl.org/dc/elements/1.1/"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

OAI_NSMAP = {
    None: OAI_NS,
    "xsi": XSI_NS,
}

DC_NSMAP = {
    "oai_dc": OAI_DC_NS,
    "dc": DC_NS,
    "xsi": XSI_NS,
}

PAGE_SIZE = 100

# Supported verbs
VALID_VERBS = {
    "Identify",
    "ListMetadataFormats",
    "ListSets",
    "ListRecords",
    "ListIdentifiers",
    "GetRecord",
}


def _get_base_domain() -> str:
    """Extract the domain from BASE_URL for OAI identifier prefix."""
    url = settings.BASE_URL
    # Remove scheme
    if "://" in url:
        url = url.split("://", 1)[1]
    # Remove port and path
    url = url.split("/", 1)[0]
    url = url.split(":", 1)[0]
    return url


def _make_oai_identifier(accession_number: str) -> str:
    """Build OAI identifier: oai:{domain}:{accession_number}."""
    domain = _get_base_domain()
    return f"oai:{domain}:{accession_number}"


def _parse_oai_identifier(identifier: str) -> str | None:
    """Extract accession number from OAI identifier."""
    parts = identifier.split(":", 2)
    if len(parts) != 3 or parts[0] != "oai":
        return None
    return parts[2]


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _format_datestamp(dt: datetime | date) -> str:
    """Format a datestamp in OAI-PMH granularity (YYYY-MM-DDThh:mm:ssZ)."""
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"{dt.isoformat()}T00:00:00Z"


def _parse_datestamp(ds: str) -> date | None:
    """Parse an OAI-PMH datestamp (YYYY-MM-DD or YYYY-MM-DDThh:mm:ssZ)."""
    if not ds:
        return None
    try:
        if "T" in ds:
            return datetime.strptime(ds.replace("Z", ""), "%Y-%m-%dT%H:%M:%S").date()
        return date.fromisoformat(ds)
    except ValueError:
        return None


def _encode_resumption_token(last_id: int, metadata_prefix: str, oai_set: str | None,
                              from_date: str | None, until_date: str | None) -> str:
    """Encode cursor-based resumption token as base64 JSON."""
    payload = {
        "last_id": last_id,
        "prefix": metadata_prefix,
    }
    if oai_set:
        payload["set"] = oai_set
    if from_date:
        payload["from"] = from_date
    if until_date:
        payload["until"] = until_date
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()


def _decode_resumption_token(token: str) -> dict[str, Any] | None:
    """Decode a resumption token. Returns None if invalid."""
    try:
        raw = base64.urlsafe_b64decode(token.encode())
        data = json.loads(raw)
        if "last_id" not in data or "prefix" not in data:
            return None
        return data
    except Exception:
        return None


def _build_oai_root(verb: str) -> etree._Element:
    """Build the OAI-PMH root element with standard attributes."""
    root = etree.Element(f"{{{OAI_NS}}}OAI-PMH", nsmap=OAI_NSMAP)
    root.set(
        f"{{{XSI_NS}}}schemaLocation",
        f"{OAI_NS} http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd",
    )
    response_date = etree.SubElement(root, f"{{{OAI_NS}}}responseDate")
    response_date.text = _now_utc().strftime("%Y-%m-%dT%H:%M:%SZ")

    request_el = etree.SubElement(root, f"{{{OAI_NS}}}request")
    request_el.text = f"{settings.BASE_URL}/oai"
    request_el.set("verb", verb)

    return root


def _build_error_response(code: str, message: str, verb: str = "") -> bytes:
    """Build an OAI-PMH error response."""
    root = etree.Element(f"{{{OAI_NS}}}OAI-PMH", nsmap=OAI_NSMAP)
    root.set(
        f"{{{XSI_NS}}}schemaLocation",
        f"{OAI_NS} http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd",
    )
    response_date = etree.SubElement(root, f"{{{OAI_NS}}}responseDate")
    response_date.text = _now_utc().strftime("%Y-%m-%dT%H:%M:%SZ")

    request_el = etree.SubElement(root, f"{{{OAI_NS}}}request")
    request_el.text = f"{settings.BASE_URL}/oai"
    if verb:
        request_el.set("verb", verb)

    error_el = etree.SubElement(root, f"{{{OAI_NS}}}error")
    error_el.set("code", code)
    error_el.text = message

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=True)


def _add_dc_metadata(parent: etree._Element, doc: Document,
                     institution_name: str, base_url: str) -> None:
    """Add a Dublin Core metadata element for a document."""
    metadata_el = etree.SubElement(parent, f"{{{OAI_NS}}}metadata")
    dc_root = etree.SubElement(metadata_el, f"{{{OAI_DC_NS}}}dc", nsmap=DC_NSMAP)
    dc_root.set(
        f"{{{XSI_NS}}}schemaLocation",
        f"{OAI_DC_NS} http://www.openarchives.org/OAI/2.0/oai_dc.xsd",
    )

    dc = document_to_dc_dict(doc, institution_name, base_url)

    def add_el(tag: str, text: str) -> None:
        if text:
            el = etree.SubElement(dc_root, f"{{{DC_NS}}}{tag}")
            el.text = text

    add_el("title", dc.get("title", ""))
    add_el("creator", dc.get("creator", ""))
    for subj in dc.get("subject", []):
        add_el("subject", subj)
    add_el("description", dc.get("description", ""))
    add_el("publisher", dc.get("publisher", ""))
    add_el("date", dc.get("date", ""))
    add_el("type", dc.get("type", ""))
    add_el("format", dc.get("format", ""))
    add_el("identifier", dc.get("identifier", ""))
    add_el("source", dc.get("source", ""))
    add_el("language", dc.get("language", ""))
    add_el("rights", dc.get("rights", ""))
    if dc.get("spatial"):
        add_el("coverage", dc.get("spatial", ""))


def _build_public_filter() -> list:
    """Build SQLAlchemy filter clauses for public records.

    A document is public if: is_public=TRUE AND (embargo_end_date IS NULL
    OR embargo_end_date <= today).
    """
    today = date.today()
    return [
        Document.is_public == True,  # noqa: E712
        or_(
            Document.embargo_end_date.is_(None),
            Document.embargo_end_date <= today,
        ),
        Document.availability_status != "deaccessioned",
    ]


async def _get_institution_name(db: AsyncSession) -> str:
    """Read institution name from system_settings."""
    from app.models.system_setting import SystemSetting

    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == "institution.name")
    )
    setting = result.scalar_one_or_none()
    if setting and setting.value:
        if isinstance(setting.value, str):
            return setting.value
        if isinstance(setting.value, dict):
            return setting.value.get("value", "")
    return ""


async def _get_earliest_datestamp(db: AsyncSession) -> str:
    """Get the earliest created_at of any public document."""
    result = await db.execute(
        select(func.min(Document.created_at)).where(
            Document.is_public == True  # noqa: E712
        )
    )
    earliest = result.scalar_one_or_none()
    if earliest:
        return _format_datestamp(earliest)
    return _format_datestamp(_now_utc())


async def handle_request(
    db: AsyncSession,
    verb: str,
    identifier: str | None = None,
    metadata_prefix: str | None = None,
    oai_set: str | None = None,
    from_date: str | None = None,
    until_date: str | None = None,
    resumption_token: str | None = None,
) -> bytes:
    """Route an OAI-PMH request to the appropriate verb handler."""
    if verb not in VALID_VERBS:
        return _build_error_response("badVerb", f"Illegal verb: {verb}")

    if verb == "Identify":
        return await _handle_identify(db)
    elif verb == "ListMetadataFormats":
        return await _handle_list_metadata_formats(identifier)
    elif verb == "ListSets":
        return await _handle_list_sets(db)
    elif verb == "GetRecord":
        return await _handle_get_record(db, identifier, metadata_prefix)
    elif verb == "ListRecords":
        return await _handle_list_records(
            db, metadata_prefix, oai_set, from_date, until_date,
            resumption_token, include_metadata=True,
        )
    elif verb == "ListIdentifiers":
        return await _handle_list_records(
            db, metadata_prefix, oai_set, from_date, until_date,
            resumption_token, include_metadata=False,
        )

    return _build_error_response("badVerb", f"Unsupported verb: {verb}")


async def _handle_identify(db: AsyncSession) -> bytes:
    """OAI-PMH Identify verb."""
    root = _build_oai_root("Identify")
    identify_el = etree.SubElement(root, f"{{{OAI_NS}}}Identify")

    institution_name = await _get_institution_name(db)
    repo_name = institution_name or "ADMS Repository"

    elements = [
        ("repositoryName", repo_name),
        ("baseURL", f"{settings.BASE_URL}/oai"),
        ("protocolVersion", "2.0"),
        ("earliestDatestamp", await _get_earliest_datestamp(db)),
        ("deletedRecord", "transient"),
        ("granularity", "YYYY-MM-DDThh:mm:ssZ"),
    ]

    for tag, text in elements:
        el = etree.SubElement(identify_el, f"{{{OAI_NS}}}{tag}")
        el.text = text

    # Admin email from settings if available
    admin_email_el = etree.SubElement(identify_el, f"{{{OAI_NS}}}adminEmail")
    admin_email_el.text = "admin@example.org"

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=True)


async def _handle_list_metadata_formats(identifier: str | None) -> bytes:
    """OAI-PMH ListMetadataFormats verb."""
    # We always support oai_dc regardless of identifier
    root = _build_oai_root("ListMetadataFormats")
    list_el = etree.SubElement(root, f"{{{OAI_NS}}}ListMetadataFormats")

    fmt = etree.SubElement(list_el, f"{{{OAI_NS}}}metadataFormat")
    prefix_el = etree.SubElement(fmt, f"{{{OAI_NS}}}metadataPrefix")
    prefix_el.text = "oai_dc"
    schema_el = etree.SubElement(fmt, f"{{{OAI_NS}}}schema")
    schema_el.text = "http://www.openarchives.org/OAI/2.0/oai_dc.xsd"
    ns_el = etree.SubElement(fmt, f"{{{OAI_NS}}}metadataNamespace")
    ns_el.text = OAI_DC_NS

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=True)


async def _handle_list_sets(db: AsyncSession) -> bytes:
    """OAI-PMH ListSets verb — returns arrangement_nodes as sets."""
    root = _build_oai_root("ListSets")
    list_el = etree.SubElement(root, f"{{{OAI_NS}}}ListSets")

    result = await db.execute(
        select(ArrangementNode)
        .where(ArrangementNode.is_public == True)  # noqa: E712
        .order_by(ArrangementNode.id)
    )
    nodes = result.scalars().all()

    for node in nodes:
        set_el = etree.SubElement(list_el, f"{{{OAI_NS}}}set")
        spec_el = etree.SubElement(set_el, f"{{{OAI_NS}}}setSpec")
        spec_el.text = f"col_{node.id}"
        name_el = etree.SubElement(set_el, f"{{{OAI_NS}}}setName")
        name_el.text = node.title
        if node.description:
            desc_el = etree.SubElement(set_el, f"{{{OAI_NS}}}setDescription")
            dc_root = etree.SubElement(desc_el, f"{{{OAI_DC_NS}}}dc", nsmap=DC_NSMAP)
            dc_desc = etree.SubElement(dc_root, f"{{{DC_NS}}}description")
            dc_desc.text = node.description

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=True)


async def _handle_get_record(
    db: AsyncSession,
    identifier: str | None,
    metadata_prefix: str | None,
) -> bytes:
    """OAI-PMH GetRecord verb."""
    if not identifier:
        return _build_error_response(
            "badArgument", "Missing required argument: identifier", "GetRecord"
        )
    if not metadata_prefix:
        return _build_error_response(
            "badArgument", "Missing required argument: metadataPrefix", "GetRecord"
        )
    if metadata_prefix != "oai_dc":
        return _build_error_response(
            "cannotDisseminateFormat",
            f"Unsupported metadata format: {metadata_prefix}",
            "GetRecord",
        )

    accession = _parse_oai_identifier(identifier)
    if not accession:
        return _build_error_response(
            "idDoesNotExist", f"Invalid identifier format: {identifier}", "GetRecord"
        )

    institution_name = await _get_institution_name(db)
    today = date.today()

    # Try to find the document (public or recently deaccessioned for deleted status)
    result = await db.execute(
        select(Document)
        .options(selectinload(Document.creator), selectinload(Document.files),
                 selectinload(Document.terms))
        .where(Document.accession_number == accession)
    )
    doc = result.scalar_one_or_none()

    if not doc:
        return _build_error_response(
            "idDoesNotExist",
            f"No record found for identifier: {identifier}",
            "GetRecord",
        )

    root = _build_oai_root("GetRecord")
    get_record_el = etree.SubElement(root, f"{{{OAI_NS}}}GetRecord")

    record_el = etree.SubElement(get_record_el, f"{{{OAI_NS}}}record")

    # Header
    header_el = etree.SubElement(record_el, f"{{{OAI_NS}}}header")

    # Check if deaccessioned (deleted)
    is_deleted = doc.deaccession_status == "complete"
    if is_deleted:
        # Check if within 30-day window
        deaccession_result = await db.execute(
            select(DeaccessionLog)
            .where(DeaccessionLog.document_id == doc.id)
            .order_by(DeaccessionLog.created_at.desc())
            .limit(1)
        )
        deaccession_entry = deaccession_result.scalar_one_or_none()
        if deaccession_entry:
            days_since = (today - deaccession_entry.deaccession_date).days
            if days_since > 30:
                return _build_error_response(
                    "idDoesNotExist",
                    f"No record found for identifier: {identifier}",
                    "GetRecord",
                )
        header_el.set("status", "deleted")
    elif not doc.is_public or (
        doc.embargo_end_date and doc.embargo_end_date > today
    ):
        return _build_error_response(
            "idDoesNotExist",
            f"No record found for identifier: {identifier}",
            "GetRecord",
        )

    id_el = etree.SubElement(header_el, f"{{{OAI_NS}}}identifier")
    id_el.text = _make_oai_identifier(accession)
    datestamp_el = etree.SubElement(header_el, f"{{{OAI_NS}}}datestamp")
    datestamp_el.text = _format_datestamp(doc.updated_at)

    if doc.arrangement_node_id:
        set_spec_el = etree.SubElement(header_el, f"{{{OAI_NS}}}setSpec")
        set_spec_el.text = f"col_{doc.arrangement_node_id}"

    # Metadata (only for non-deleted records)
    if not is_deleted:
        _add_dc_metadata(record_el, doc, institution_name, settings.BASE_URL)

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=True)


async def _handle_list_records(
    db: AsyncSession,
    metadata_prefix: str | None,
    oai_set: str | None,
    from_date: str | None,
    until_date: str | None,
    resumption_token: str | None,
    include_metadata: bool = True,
) -> bytes:
    """OAI-PMH ListRecords and ListIdentifiers verbs.

    Uses cursor-based pagination with last-seen ID for resumption tokens.
    """
    verb = "ListRecords" if include_metadata else "ListIdentifiers"

    # If resumption token provided, decode it and override params
    last_id = 0
    if resumption_token:
        token_data = _decode_resumption_token(resumption_token)
        if token_data is None:
            return _build_error_response(
                "badResumptionToken",
                "Invalid or expired resumption token",
                verb,
            )
        last_id = token_data["last_id"]
        metadata_prefix = token_data["prefix"]
        oai_set = token_data.get("set")
        from_date = token_data.get("from")
        until_date = token_data.get("until")

    if not metadata_prefix:
        return _build_error_response(
            "badArgument", "Missing required argument: metadataPrefix", verb
        )
    if metadata_prefix != "oai_dc":
        return _build_error_response(
            "cannotDisseminateFormat",
            f"Unsupported metadata format: {metadata_prefix}",
            verb,
        )

    institution_name = await _get_institution_name(db)
    today = date.today()

    # Build query for public documents
    filters = _build_public_filter()
    filters.append(Document.accession_number.isnot(None))

    # Cursor filter
    if last_id > 0:
        filters.append(Document.id > last_id)

    # Set filter (arrangement_node_id)
    if oai_set:
        if oai_set.startswith("col_"):
            try:
                node_id = int(oai_set[4:])
                filters.append(Document.arrangement_node_id == node_id)
            except ValueError:
                return _build_error_response(
                    "badArgument", f"Invalid set spec: {oai_set}", verb
                )
        else:
            return _build_error_response(
                "badArgument", f"Invalid set spec: {oai_set}", verb
            )

    # Date filters
    if from_date:
        from_d = _parse_datestamp(from_date)
        if from_d is None:
            return _build_error_response(
                "badArgument", f"Invalid from date: {from_date}", verb
            )
        filters.append(Document.updated_at >= datetime(from_d.year, from_d.month, from_d.day))

    if until_date:
        until_d = _parse_datestamp(until_date)
        if until_d is None:
            return _build_error_response(
                "badArgument", f"Invalid until date: {until_date}", verb
            )
        # Until is inclusive, so include the entire day
        filters.append(
            Document.updated_at <= datetime(until_d.year, until_d.month, until_d.day, 23, 59, 59)
        )

    # Also include recently deaccessioned documents (deleted within 30 days)
    thirty_days_ago = today - timedelta(days=30)
    deaccession_filters = [
        Document.deaccession_status == "complete",
        Document.accession_number.isnot(None),
    ]
    if last_id > 0:
        deaccession_filters.append(Document.id > last_id)
    if oai_set and oai_set.startswith("col_"):
        try:
            node_id = int(oai_set[4:])
            deaccession_filters.append(Document.arrangement_node_id == node_id)
        except ValueError:
            pass

    # Fetch public documents (PAGE_SIZE + 1 to detect if more exist)
    query = (
        select(Document)
        .options(selectinload(Document.creator), selectinload(Document.files),
                 selectinload(Document.terms))
        .where(and_(*filters))
        .order_by(Document.id)
        .limit(PAGE_SIZE + 1)
    )
    result = await db.execute(query)
    documents = list(result.scalars().all())

    # Fetch recently deaccessioned documents
    deaccession_query = (
        select(Document)
        .where(and_(*deaccession_filters))
        .order_by(Document.id)
        .limit(PAGE_SIZE + 1)
    )
    deaccession_result = await db.execute(deaccession_query)
    deaccessioned_docs = list(deaccession_result.scalars().all())

    # Filter deaccessioned docs to those within 30 days
    valid_deaccessioned: list[Document] = []
    for ddoc in deaccessioned_docs:
        da_result = await db.execute(
            select(DeaccessionLog)
            .where(DeaccessionLog.document_id == ddoc.id)
            .order_by(DeaccessionLog.created_at.desc())
            .limit(1)
        )
        da_entry = da_result.scalar_one_or_none()
        if da_entry and da_entry.deaccession_date >= thirty_days_ago:
            valid_deaccessioned.append(ddoc)

    # Merge and sort by ID
    all_docs = sorted(documents + valid_deaccessioned, key=lambda d: d.id)

    # Check for more results
    has_more = len(all_docs) > PAGE_SIZE
    if has_more:
        all_docs = all_docs[:PAGE_SIZE]

    if not all_docs:
        return _build_error_response("noRecordsMatch", "No records match the request", verb)

    root = _build_oai_root(verb)
    list_el = etree.SubElement(root, f"{{{OAI_NS}}}{verb}")

    for doc in all_docs:
        record_el = etree.SubElement(list_el, f"{{{OAI_NS}}}record")
        header_el = etree.SubElement(record_el, f"{{{OAI_NS}}}header")

        is_deleted = doc.deaccession_status == "complete"
        if is_deleted:
            header_el.set("status", "deleted")

        id_el = etree.SubElement(header_el, f"{{{OAI_NS}}}identifier")
        id_el.text = _make_oai_identifier(doc.accession_number or "")
        datestamp_el = etree.SubElement(header_el, f"{{{OAI_NS}}}datestamp")
        datestamp_el.text = _format_datestamp(doc.updated_at)

        if doc.arrangement_node_id:
            set_spec_el = etree.SubElement(header_el, f"{{{OAI_NS}}}setSpec")
            set_spec_el.text = f"col_{doc.arrangement_node_id}"

        # Metadata (only for non-deleted and when include_metadata)
        if include_metadata and not is_deleted:
            _add_dc_metadata(record_el, doc, institution_name, settings.BASE_URL)

    # Resumption token
    if has_more:
        last_doc_id = all_docs[-1].id
        token = _encode_resumption_token(
            last_doc_id, metadata_prefix, oai_set, from_date, until_date
        )
        token_el = etree.SubElement(list_el, f"{{{OAI_NS}}}resumptionToken")
        token_el.text = token
    elif resumption_token:
        # Empty resumption token signals end of list
        token_el = etree.SubElement(list_el, f"{{{OAI_NS}}}resumptionToken")

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=True)
