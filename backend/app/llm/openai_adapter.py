"""OpenAI LLM adapter."""

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


class OpenAIAdapter(LLMAdapter):
    async def suggest_metadata(
        self,
        ocr_text: str,
        file_bytes: bytes | None,
        mime_type: str,
        enabled_fields: list[str],
    ) -> dict[str, Any]:
        import openai

        client = openai.AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL or None,
        )

        response = await client.chat.completions.create(
            model=settings.LLM_MODEL or "gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Suggest values for these fields: {', '.join(enabled_fields)}\n\n"
                        f"Document OCR text:\n{ocr_text[:8000]}"
                    ),
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )

        content = response.choices[0].message.content or "{}"
        return json.loads(content)
