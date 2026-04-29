import sys
import os
from pathlib import Path
root = Path(r"c:\Users\patid\Desktop\FasalSathi\FasalSaathi")
sys.path.append(str(root))
import asyncio
from google import genai
from app.core.config import settings

async def list_models():
    client = genai.Client(api_key=settings.gemini_api_key)
    print("Listing models...")
    for model in client.models.list():
        print(f"Model: {model.name}, Supported: {model.supported_generation_methods}")

if __name__ == "__main__":
    asyncio.run(list_models())
