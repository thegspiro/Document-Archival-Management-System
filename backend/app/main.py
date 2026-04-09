"""FastAPI application factory."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup and shutdown events."""
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="ADMS — Archival Document Management System",
        description="API for managing archival documents, metadata, and exhibitions.",
        version="0.1.0",
        docs_url="/api/v1/docs",
        openapi_url="/api/v1/openapi.json",
        lifespan=lifespan,
    )

    # CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.BASE_URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    from app.routers import (
        auth,
        users,
        nodes,
        documents,
        authority,
        vocabulary,
        locations,
        events,
        exhibitions,
        review,
        search,
        public,
        settings_router,
        reports,
        preservation,
        imports,
        health,
    )

    application.include_router(health.router)
    application.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    application.include_router(users.router, prefix="/api/v1/users", tags=["users"])
    application.include_router(nodes.router, prefix="/api/v1/nodes", tags=["arrangement"])
    application.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
    application.include_router(authority.router, prefix="/api/v1/authority", tags=["authority"])
    application.include_router(vocabulary.router, prefix="/api/v1/vocabulary", tags=["vocabulary"])
    application.include_router(locations.router, prefix="/api/v1/locations", tags=["locations"])
    application.include_router(events.router, prefix="/api/v1/events", tags=["events"])
    application.include_router(
        exhibitions.router, prefix="/api/v1/exhibitions", tags=["exhibitions"]
    )
    application.include_router(review.router, prefix="/api/v1/review", tags=["review"])
    application.include_router(search.router, prefix="/api/v1", tags=["search"])
    application.include_router(public.router, prefix="/api/v1/public", tags=["public"])
    application.include_router(
        settings_router.router, prefix="/api/v1/settings", tags=["settings"]
    )
    application.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
    application.include_router(
        preservation.router, prefix="/api/v1/admin", tags=["preservation"]
    )
    application.include_router(imports.router, prefix="/api/v1/admin/imports", tags=["imports"])

    # --- Root-level routes (not under /api/v1) ---

    from app.routers import oai, persistent_url

    application.include_router(oai.router, tags=["oai-pmh"])
    application.include_router(persistent_url.router, tags=["persistent-urls"])

    return application


app = create_app()
