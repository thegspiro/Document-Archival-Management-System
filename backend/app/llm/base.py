"""Provider-agnostic LLM adapter interface."""

from abc import ABC, abstractmethod
from typing import Any


class LLMAdapter(ABC):
    """Base class for LLM provider adapters."""

    @abstractmethod
    async def suggest_metadata(
        self,
        ocr_text: str,
        file_bytes: bytes | None,
        mime_type: str,
        enabled_fields: list[str],
    ) -> dict[str, Any]:
        """Generate metadata suggestions from document content."""
        ...

    def suggest_metadata_sync(
        self,
        ocr_text: str,
        enabled_fields: list[str],
    ) -> dict[str, Any]:
        """Synchronous wrapper for use in Celery tasks."""
        import asyncio
        return asyncio.run(
            self.suggest_metadata(ocr_text, None, "", enabled_fields)
        )
