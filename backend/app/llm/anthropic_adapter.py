"""Anthropic LLM adapter."""

import json
from typing import Any

from app.config import settings
from app.llm.base import LLMAdapter

SYSTEM_PROMPT = """You are an archival metadata assistant. Given the OCR text of a historical document,
suggest metadata values for the specified fields. Return a JSON object where each key is a field name
and the value is an object with "value" (your suggestion) and "confidence" (0.0 to 1.0).

Only suggest values for fields listed in the request. Be conservative — if you are not confident,
set a low confidence score. Never invent dates that are not clearly present in the text.
For date fields, use ISO 8601 format (YYYY-MM-DD)."""


class AnthropicAdapter(LLMAdapter):
    async def suggest_metadata(
        self,
        ocr_text: str,
        file_bytes: bytes | None,
        mime_type: str,
        enabled_fields: list[str],
    ) -> dict[str, Any]:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.LLM_API_KEY)

        response = await client.messages.create(
            model=settings.LLM_MODEL or "claude-sonnet-4-20250514",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Suggest values for these fields: {', '.join(enabled_fields)}\n\n"
                        f"Document OCR text:\n{ocr_text[:8000]}"
                    ),
                },
            ],
        )

        content = response.content[0].text
        return json.loads(content)
