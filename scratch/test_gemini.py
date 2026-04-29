import sys
import os
from pathlib import Path

# Add the project root to sys.path
root = Path(r"c:\Users\patid\Desktop\FasalSathi\FasalSaathi")
sys.path.append(str(root))

import asyncio
from app.services.ask_sathi.gemini import gemini_client
from app.core.config import settings

async def test_gemini():
    print(f"Testing Gemini with model: {settings.gemini_chat_model}")
    print(f"API Key: {settings.gemini_api_key[:10]}...")
    
    try:
        prompt = "Say 'Hello, I am Sathi' in Hindi and English."
        response = await gemini_client.generate_text(prompt)
        if not response:
            print("Received empty response! Checking if there was an internal error.")
        else:
            print(f"Response: {response}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Caught top-level error: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini())
