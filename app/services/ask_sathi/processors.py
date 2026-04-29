from typing import List, Dict, Any, Tuple
from .gemini import gemini_client
from . import prompts

async def process_language(query: str) -> Dict[str, Any]:
    """Detect language and translate to English."""
    prompt = prompts.build_language_prompt(query)
    result = await gemini_client.generate_json(prompt)
    
    return {
        "normalized_text": result.get("normalizedText", query),
        "original_language": result.get("originalLanguage", "english")
    }

async def resolve_history(history: List[Dict[str, str]], query: str) -> str:
    """Turn a follow-up query into a standalone one based on history."""
    if not history:
        return query
    
    prompt = prompts.build_standalone_query_prompt(history, query)
    result = await gemini_client.generate_json(prompt)
    
    return result.get("standaloneQuery", query)

async def parse_query(query: str, language: str) -> Dict[str, Any]:
    """Extract crop, issue, symptoms, and intent from the query."""
    prompt = prompts.build_query_parser_prompt(query, language)
    result = await gemini_client.generate_json(prompt)
    
    return {
        "crop": result.get("crop", ""),
        "issue": result.get("issue", ""),
        "symptoms": result.get("symptoms", ""),
        "intent": result.get("intent", ""),
        "language": language
    }

def needs_clarification(parsed_query: Dict[str, Any]) -> Tuple[bool, str]:
    """Check if we need more info (e.g. no crop detected for a symptom query)."""
    crop = parsed_query.get("crop")
    issue = parsed_query.get("issue")
    symptoms = parsed_query.get("symptoms")
    
    if (issue or symptoms) and not crop:
        lang = parsed_query.get("language", "english")
        if lang == "hindi":
            return True, "कृपया अपनी फसल का नाम बताएं ताकि मैं बेहतर जानकारी दे सकूं।"
        return True, "Please specify the crop you are asking about so I can give you more accurate advice."
    
    return False, ""
