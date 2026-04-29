import json
import re
from google import genai
from google.genai import types
from typing import Dict, Any
from app.core.config import settings


class GeminiClient:
    def __init__(self):
        self.chat_client = None
        self.normal_client = None
        
        # Use specific chat key if provided, otherwise fallback to default
        chat_key = settings.gemini_chat_api_key or settings.gemini_api_key
        if chat_key:
            self.chat_client = genai.Client(api_key=chat_key)
            
        if settings.gemini_api_key:
            self.normal_client = genai.Client(api_key=settings.gemini_api_key)
            
        self.chat_model = settings.gemini_chat_model
        self.embedding_model = settings.gemini_embedding_model

    async def generate_text(self, prompt: str) -> str:
        if not self.chat_client:
            print("Gemini chat client is not configured.")
            return ""
        try:
            response = await self.chat_client.aio.models.generate_content(
                model=self.chat_model,
                contents=prompt
            )
            return (getattr(response, "text", None) or "").strip()
        except Exception as e:
            print(f"Error generating text from Gemini ({self.chat_model}): {e}")
            return ""

    def _parse_json_text(self, text: str) -> Dict[str, Any]:
        if not text:
            return {}

        clean_text = text.strip()
        clean_text = re.sub(r"^```(?:json)?\s*", "", clean_text, flags=re.IGNORECASE)
        clean_text = re.sub(r"\s*```$", "", clean_text)

        try:
            parsed = json.loads(clean_text)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", clean_text, flags=re.DOTALL)
        if not match:
            return {}

        try:
            parsed = json.loads(match.group(0))
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError as e:
            print(f"Gemini JSON extraction failed: {e}")
            return {}

    async def generate_json(self, prompt: str) -> Dict[str, Any]:
        if not self.chat_client:
            print("Gemini chat client is not configured.")
            return {}
        try:
            response = await self.chat_client.aio.models.generate_content(
                model=self.chat_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
            parsed = self._parse_json_text(getattr(response, "text", "") or "")
            if parsed:
                return parsed
            print("Gemini returned empty or invalid JSON in JSON mode.")
        except Exception as e:
            print(f"Error generating JSON from Gemini ({self.chat_model}): {e}")

        try:
            response = await self.chat_client.aio.models.generate_content(
                model=self.chat_model,
                contents=f"{prompt}\n\nReturn only valid JSON. Do not include markdown."
            )
            return self._parse_json_text(getattr(response, "text", "") or "")
        except Exception as inner_e:
            print(f"Fallback JSON generation failed: {inner_e}")
            return {}

    async def generate_embedding(self, text: str) -> list:
        if not self.normal_client:
            print("Gemini embedding client is not configured.")
            return []
        try:
            result = await self.normal_client.aio.models.embed_content(
                model=self.embedding_model,
                contents=text,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
            )
            if hasattr(result, 'embeddings'):
                return result.embeddings[0].values
            return []
        except Exception as e:
            print(f"Error generating embedding from Gemini ({self.embedding_model}): {e}")
            return []


gemini_client = GeminiClient()
