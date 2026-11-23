"""Thin Gemini adapter. Deterministic app tools remain outside the model."""
import json
from typing import Any
from config import settings

class GeminiUnavailable(RuntimeError):
    pass

class GeminiClient:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key if api_key is not None else settings.gemini_api_key
        self.model = model or settings.gemini_model
        self._client = None
        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except ImportError as exc:
                raise GeminiUnavailable("Install google-genai: pip install google-genai") from exc

    @property
    def configured(self) -> bool:
        return self._client is not None

    def generate_text(self, prompt: str, system_instruction: str = "") -> str:
        if not self.configured:
            raise GeminiUnavailable("Gemini API key not configured. Add GEMINI_API_KEY to .env.")
        from google.genai import types
        response = self._client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction or None,
                temperature=0.2,
                max_output_tokens=700,
            ),
        )
        text = (response.text or "").strip()
        if not text:
            raise GeminiUnavailable("Gemini returned an empty response.")
        return text

    def generate_json(self, prompt: str, system_instruction: str = "") -> dict[str, Any]:
        if not self.configured:
            raise GeminiUnavailable("Gemini API key not configured. Add GEMINI_API_KEY to .env.")
        from google.genai import types
        response = self._client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction or None,
                response_mime_type="application/json",
                temperature=0.1,
                max_output_tokens=700,
            ),
        )
        try:
            value = json.loads(response.text or "{}")
        except json.JSONDecodeError as exc:
            raise GeminiUnavailable("Gemini response was not valid JSON.") from exc
        if not isinstance(value, dict):
            raise GeminiUnavailable("Gemini response must be a JSON object.")
        return value
