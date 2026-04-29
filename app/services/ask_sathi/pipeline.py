from typing import List, Dict, Any, Optional
from . import gemini, pinecone, prompts, processors

def build_fallback(language: str) -> Dict[str, Any]:
    if language == "hindi":
        return {
            "type": "answer",
            "response": "मेरे पास अभी पर्याप्त जानकारी नहीं है। कृपया समस्या के बारे में और विवरण दीजिए।",
            "language": language,
        }
    return {
        "type": "answer",
        "response": "I do not have enough information right now. Please provide more details about the problem.",
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
    normalized = response.lower()
    refusal_phrases = [
        "no information",
        "not given in the documents",
        "not provided in the documents",
        "given documents do not",
        "provided context does not",
        "insufficient information",
        "दस्तावेज़ों में",
        "जानकारी नहीं दी गई",
        "पर्याप्त जानकारी नहीं",
    ]
    return any(phrase in normalized for phrase in refusal_phrases)

async def generate_general_advice(parsed_query: Dict[str, Any], normalized_query: str, language: str) -> str:
    prompt = prompts.build_general_advice_prompt(
        crop=parsed_query.get("crop"),
        issue=parsed_query.get("issue"),
        question=normalized_query,
        language=language
    )
    return await gemini.gemini_client.generate_text(prompt)

async def process_ask_sathi_query(query: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
    response_language = "english"
    try:
        # 1. Resolve history
        standalone_query = await processors.resolve_history(history, query)
        
        # 2. Normalize language
        lang_data = await processors.process_language(standalone_query)
        normalized_text = lang_data["normalized_text"]
        response_language = lang_data["original_language"]
        
        # 3. Parse query
        parsed_query = await processors.parse_query(normalized_text, response_language)
        
        # 4. Check for clarification
        needs_clari, clari_msg = processors.needs_clarification(parsed_query)
        if needs_clari:
            return {
                "type": "clarification",
                "response": clari_msg,
                "language": response_language
            }
        
        # 5. Retrieve documents
        documents = await pinecone.retrieve_documents(normalized_text, parsed_query)
        
        # 6. Generate answer
        if not documents:
            advice = await generate_general_advice(parsed_query, normalized_text, response_language)
            return {
                "type": "answer",
                "response": advice or build_fallback(response_language)["response"],
                "language": response_language
            }
        
        context = format_context(documents)
        prompt = prompts.build_answer_prompt(context, normalized_text, response_language)
        response = await gemini.gemini_client.generate_text(prompt)
        
        # 7. Fallback if response is a refusal
        if looks_like_refusal(response):
            response = await generate_general_advice(parsed_query, normalized_text, response_language)
            
        return {
            "type": "answer",
            "response": response or build_fallback(response_language)["response"],
            "language": response_language
        }
        
    except Exception as e:
        print(f"Error in Ask Sathi pipeline: {e}")
        return build_fallback(response_language)
