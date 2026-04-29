from typing import List, Dict, Any
from . import gemini, pinecone, prompts, processors

GENERIC_CONTEXT_TOPICS = {
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


def build_fallback(language: str) -> Dict[str, Any]:
    if language == "hindi":
        return {
            "type": "answer",
            "response": "मैं अभी जवाब तैयार नहीं कर पा रहा हूं। कृपया थोड़ी देर बाद फिर कोशिश करें।",
            "language": language,
        }
    return {
        "type": "answer",
        "response": "I am having trouble preparing an answer right now. Please try again in a moment.",
        "language": language,
    }


def format_context(documents: List[Dict[str, Any]]) -> str:
    formatted = []
    for i, doc in enumerate(documents):
        meta = doc.get("metadata", {})
        crop = meta.get("crop", "unknown")
        issue = meta.get("disease") or meta.get("issue") or "unknown"
        text = doc.get("text", "")
        formatted.append(f"Document {i + 1}\nCrop: {crop}\nIssue: {issue}\nText: {text}")
    return "\n\n".join(formatted)


def looks_like_refusal(response: str) -> bool:
    normalized = (response or "").lower()
    refusal_phrases = [
        "no information",
        "not given in the documents",
        "not provided in the documents",
        "documents do not contain",
        "documents provided",
        "given documents do not",
        "provided documents do not",
        "provided context does not",
        "context does not contain",
        "insufficient information",
        "specific information regarding",
        "दस्तावेज",
        "जानकारी नहीं",
        "पर्याप्त जानकारी नहीं",
    ]
    return any(phrase in normalized for phrase in refusal_phrases)


def _terms(value: str) -> List[str]:
    return [
        part.strip().lower()
        for part in (value or "").replace(",", " ").replace("/", " ").split()
        if len(part.strip()) >= 4
    ]


def documents_look_relevant(documents: List[Dict[str, Any]], parsed_query: Dict[str, Any]) -> bool:
    crop = (parsed_query.get("crop") or "").strip().lower()
    issue = (parsed_query.get("issue") or "").strip().lower()
    intent = (parsed_query.get("intent") or "").strip().lower()
    issue_terms = _terms(parsed_query.get("issue") or "")
    symptom_terms = _terms(parsed_query.get("symptoms") or "")

    if not crop and (issue in GENERIC_CONTEXT_TOPICS or intent in GENERIC_CONTEXT_TOPICS):
        return False

    if not crop and not issue_terms and not symptom_terms:
        return False

    for doc in documents:
        meta = doc.get("metadata", {})
        haystack = " ".join(
            str(value)
            for value in [
                meta.get("crop", ""),
                meta.get("disease", ""),
                meta.get("issue", ""),
                doc.get("text", ""),
            ]
        ).lower()

        crop_matches = bool(crop and crop in haystack)
        issue_matches = any(term in haystack for term in issue_terms + symptom_terms)

        if crop_matches or issue_matches:
            return True

    return False


async def generate_general_advice(parsed_query: Dict[str, Any], normalized_query: str, language: str) -> str:
    prompt = prompts.build_general_advice_prompt(
        crop=parsed_query.get("crop"),
        issue=parsed_query.get("issue"),
        question=normalized_query,
        language=language,
    )
    return await gemini.gemini_client.generate_text(prompt)


async def _answer_with_general_advice(
    parsed_query: Dict[str, Any],
    normalized_query: str,
    language: str,
) -> Dict[str, Any]:
    advice = await generate_general_advice(parsed_query, normalized_query, language)
    return {
        "type": "answer",
        "response": advice or build_fallback(language)["response"],
        "language": language,
    }


async def process_ask_sathi_query(query: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
    response_language = "english"
    normalized_text = query
    parsed_query: Dict[str, Any] = {"crop": "", "issue": "", "symptoms": "", "intent": "", "language": response_language}

    print(f"Ask Sathi query received: {query[:80]}")

    try:
        standalone_query = await processors.resolve_history(history, query)
        print(f"Ask Sathi history resolved: {standalone_query[:80]}")

        lang_data = await processors.process_language(standalone_query)
        normalized_text = lang_data.get("normalized_text") or standalone_query
        response_language = lang_data.get("original_language") or "english"
        print(f"Ask Sathi language: {response_language}")

        parsed_query = await processors.parse_query(normalized_text, response_language)
        print(f"Ask Sathi parsed query: {parsed_query}")

        needs_clari, clari_msg = processors.needs_clarification(parsed_query)
        if needs_clari:
            return {
                "type": "clarification",
                "response": clari_msg,
                "language": response_language,
            }

        documents = await pinecone.retrieve_documents(normalized_text, parsed_query)
        print(f"Ask Sathi retrieved documents: {len(documents)}")

        if not documents or not documents_look_relevant(documents, parsed_query):
            print("Ask Sathi using general advice because context is missing or weak.")
            return await _answer_with_general_advice(parsed_query, normalized_text, response_language)

        context = format_context(documents)
        prompt = prompts.build_answer_prompt(context, normalized_text, response_language)
        response = await gemini.gemini_client.generate_text(prompt)

        if not response or looks_like_refusal(response):
            print("Ask Sathi context answer was empty/refusal; using general advice.")
            return await _answer_with_general_advice(parsed_query, normalized_text, response_language)

        return {
            "type": "answer",
            "response": response,
            "language": response_language,
        }

    except Exception as e:
        print(f"Ask Sathi pipeline failed; attempting general advice fallback: {e}")
        try:
            return await _answer_with_general_advice(parsed_query, normalized_text, response_language)
        except Exception as fallback_error:
            print(f"Ask Sathi fallback failed: {fallback_error}")
            return build_fallback(response_language)
