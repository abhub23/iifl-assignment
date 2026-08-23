"""Google Gemini integration.

Calls the Gemini REST API directly over HTTP (no SDK) so the request/response
handling stays explicit and easy to mock in tests.

The model is instructed to answer with strict JSON; we still parse defensively
because "the model said so" is not a contract.
"""

import json
import logging
import re

import httpx

from app.config import Settings, get_settings
from app.schemas import AIResult

logger = logging.getLogger(__name__)

FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)

SYSTEM_INSTRUCTION = (
    "You are a content analysis assistant. You always reply with a single JSON "
    "object and nothing else: no markdown, no explanations."
)

USER_PROMPT_TEMPLATE = """Summarize the following text and tag it.

Respond with ONLY this JSON structure:
{{
  "summary": "<concise 1-3 sentence summary>",
  "tags": ["<tag-1>", "<tag-2>", "<tag-3>"]
}}

Rules:
- "summary" must be a plain string of at most 3 sentences.
- "tags" must contain exactly 3 short lowercase keywords (single words or hyphenated).
- Do not include any other keys, markdown fences or commentary.

Text:
{text}"""


class AIServiceError(Exception):
    """The AI provider could not be reached or returned an error."""


class AIParseError(Exception):
    """The AI replied but the output could not be shaped into summary + 3 tags."""


def _build_payload(text: str) -> dict:
    return {
        "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
        "contents": [{"role": "user", "parts": [{"text": USER_PROMPT_TEMPLATE.format(text=text)}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }


def _extract_text(response_json: dict) -> str:
    try:
        candidates = response_json["candidates"]
        parts = candidates[0]["content"]["parts"]
        return "".join(part.get("text", "") for part in parts)
    except (KeyError, IndexError, TypeError) as exc:
        raise AIParseError(f"unexpected AI response shape: {response_json!r}") from exc


def _strip_code_fences(raw: str) -> str:
    stripped = raw.strip()
    if stripped.startswith("```"):
        stripped = FENCE_RE.sub("", stripped)
    return stripped.strip()


def _parse_ai_output(raw_text: str) -> AIResult:
    try:
        data = json.loads(_strip_code_fences(raw_text))
    except json.JSONDecodeError as exc:
        raise AIParseError(f"AI returned invalid JSON: {raw_text[:200]!r}") from exc

    if not isinstance(data, dict):
        raise AIParseError("AI JSON was not an object")

    try:
        return AIResult.model_validate(data)
    except Exception as exc:
        raise AIParseError(f"AI JSON did not match the expected schema: {exc}") from exc


async def generate_summary_and_tags(
    text: str, settings: Settings | None = None
) -> AIResult:
    settings = settings or get_settings()

    if not settings.gemini_api_key:
        raise AIServiceError("GEMINI_API_KEY is not configured")

    url = f"{settings.gemini_base_url}/models/{settings.gemini_model}:generateContent"
    headers = {"x-goog-api-key": settings.gemini_api_key}

    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            response = await client.post(url, json=_build_payload(text), headers=headers)
            response.raise_for_status()
            response_json = response.json()
    except httpx.TimeoutException as exc:
        logger.warning("Gemini request timed out after %.0fs", settings.request_timeout_seconds)
        raise AIServiceError("the AI request timed out") from exc
    except httpx.HTTPStatusError as exc:
        logger.warning("Gemini returned HTTP %s", exc.response.status_code)
        raise AIServiceError(f"the AI provider returned HTTP {exc.response.status_code}") from exc
    except httpx.HTTPError as exc:
        logger.warning("Gemini request failed: %s", exc)
        raise AIServiceError("could not reach the AI provider") from exc
    except json.JSONDecodeError as exc:
        raise AIParseError("the AI provider returned a non-JSON HTTP body") from exc

    return _parse_ai_output(_extract_text(response_json))
