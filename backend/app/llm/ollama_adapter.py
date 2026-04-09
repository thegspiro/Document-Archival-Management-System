"""Ollama (local) LLM adapter."""

import json
from typing import Any

import httpx

from app.config import settings
from app.llm.base import LLMAdapter

SYSTEM_PROMPT = """You are an archival metadata assistant. Given the OCR text of a historical document,
suggest metadata values for the specified fields. Return a JSON object where each key is a field name
and the value is an object with "value" (your suggestion) and "confidence" (0.0 to 1.0).

Only suggest values for fields listed in the request. Be conservative — if you are not confident,
set a low confidence score. Never invent dates that are not clearly present in the text.
For date fields, use ISO 8601 format (YYYY-MM-DD)."""


class OllamaAdapter(LLMAdapter):
    async def suggest_metadata(
        self,
        ocr_text: str,
        file_bytes: bytes | None,
        mime_type: str,
        enabled_fields: list[str],
    ) -> dict[str, Any]:
        base_url = settings.LLM_BASE_URL or "http://localhost:11434"

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{base_url}/api/generate",
                json={
                    "model": settings.LLM_MODEL or "llama3",
                    "system": SYSTEM_PROMPT,
                    "prompt": (
                        f"Suggest values for these fields: {', '.join(enabled_fields)}\n\n"
                        f"Document OCR text:\n{ocr_text[:8000]}"
                    ),
                    "format": "json",
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()

        return json.loads(data.get("response", "{}"))
