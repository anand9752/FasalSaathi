from typing import List, Dict, Any, Tuple
from .gemini import gemini_client
from . import prompts


GENERIC_ISSUES = {
    "soil",
    "soil health",
    "fertilizer",
    "fertilizer advice",
    "fertiliser",
    "fertiliser advice",
    "irrigation",
    "weather",
    "market",
    "crop advice",
    "farming",
}


async def process_language(query: str) -> Dict[str, Any]:
    """Detect language and translate to English."""
    try:
        prompt = prompts.build_language_prompt(query)
        result = await gemini_client.generate_json(prompt)
    except Exception as e:
        print(f"Language processing failed: {e}")
        result = {}

    normalized_text = result.get("normalizedText") or query
    original_language = (result.get("originalLanguage") or "english").lower()
    if original_language not in {"hindi", "english"}:
        original_language = "english"

    return {
        "normalized_text": normalized_text,
        "original_language": original_language,
    }


async def resolve_history(history: List[Dict[str, str]], query: str) -> str:
    """Turn a follow-up query into a standalone one based on history."""
    if not history:
        return query

    try:
        prompt = prompts.build_standalone_query_prompt(history, query)
        result = await gemini_client.generate_json(prompt)
    except Exception as e:
        print(f"History resolution failed: {e}")
        return query

    return result.get("standaloneQuery") or query


async def parse_query(query: str, language: str) -> Dict[str, Any]:
    """Extract crop, issue, symptoms, and intent from the query."""
    try:
        prompt = prompts.build_query_parser_prompt(query, language)
        result = await gemini_client.generate_json(prompt)
    except Exception as e:
        print(f"Query parsing failed: {e}")
        result = {}

    return {
        "crop": result.get("crop") or "",
        "issue": result.get("issue") or "",
        "symptoms": result.get("symptoms") or "",
        "intent": result.get("intent") or "",
        "language": language,
    }


def needs_clarification(parsed_query: Dict[str, Any]) -> Tuple[bool, str]:
    """Check if we need more info for symptom-specific diagnosis."""
    crop = (parsed_query.get("crop") or "").strip()
    issue = (parsed_query.get("issue") or "").strip().lower()
    symptoms = (parsed_query.get("symptoms") or "").strip()
    intent = (parsed_query.get("intent") or "").strip().lower()

    is_generic_advice = issue in GENERIC_ISSUES or intent in GENERIC_ISSUES

    if symptoms and not crop and not is_generic_advice:
        lang = parsed_query.get("language", "english")
        if lang == "hindi":
            return True, "कृपया अपनी फसल का नाम बताएं ताकि मैं बेहतर जानकारी दे सकूं।"
        return True, "Please specify the crop you are asking about so I can give you more accurate advice."

    return False, ""
