"""OAI-PMH 2.0 endpoint for metadata harvesting.

Implements the six OAI-PMH verbs: Identify, ListMetadataFormats, ListSets,
ListRecords, ListIdentifiers, and GetRecord. Only oai_dc (Dublin Core) format
is supported in phase 1. Only public records are exposed.
"""

from typing import Any

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter()


@router.get("/oai")
async def oai_pmh(
    verb: str = Query(..., description="OAI-PMH verb"),
    identifier: str | None = Query(None, description="OAI record identifier"),
    metadataPrefix: str | None = Query(None, description="Metadata format"),
    set: str | None = Query(None, description="OAI set spec"),
    from_: str | None = Query(None, alias="from", description="From datestamp"),
    until: str | None = Query(None, description="Until datestamp"),
    resumptionToken: str | None = Query(None, description="Resumption token"),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Handle OAI-PMH 2.0 requests. Returns XML responses."""
    from app.services import oai_service

    xml_content = await oai_service.handle_request(
        db,
        verb=verb,
        identifier=identifier,
        metadata_prefix=metadataPrefix,
        oai_set=set,
        from_date=from_,
        until_date=until,
        resumption_token=resumptionToken,
    )
    return Response(content=xml_content, media_type="text/xml; charset=utf-8")
