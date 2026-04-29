import json
from google import genai
from google.genai import types
from typing import Optional, Dict, Any
from app.core.config import settings


class GeminiClient:
    def __init__(self):
        self.client = None
        if settings.gemini_api_key:
            self.client = genai.Client(api_key=settings.gemini_api_key)
        self.chat_model = settings.gemini_chat_model
        self.embedding_model = settings.gemini_embedding_model

    async def generate_text(self, prompt: str) -> str:
        if not self.client:
            return "API Key not configured."
        try:
            response = self.client.models.generate_content(
                model=self.chat_model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"Error generating text: {e}")
            return ""

    async def generate_json(self, prompt: str) -> Dict[str, Any]:
        if not self.client:
            return {}
        try:
            response = self.client.models.generate_content(
                model=self.chat_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"Error generating JSON: {e}")
            # Fallback
            try:
                response = self.client.models.generate_content(
                    model=self.chat_model,
                    contents=prompt
                )
                text = response.text
                clean_text = text.replace("```json", "").replace("```", "").strip()
                return json.loads(clean_text)
            except:
                return {}

    async def generate_embedding(self, text: str) -> list:
        if not self.client:
            return []
        try:
            result = self.client.models.embed_content(
                model=self.embedding_model,
                contents=text,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
            )
            if hasattr(result, 'embeddings'):
                return result.embeddings[0].values
            return []
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []


gemini_client = GeminiClient()