from pinecone import Pinecone
from typing import List, Dict, Any, Optional
from .gemini import gemini_client
from app.core.config import settings

_pc = None


def get_pinecone_index():
    global _pc
    if not _pc:
        if not settings.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY is not set")
        _pc = Pinecone(api_key=settings.pinecone_api_key)

    if not settings.pinecone_index_name:
        raise ValueError("PINECONE_INDEX_NAME is not set")

    return _pc.Index(settings.pinecone_index_name)


def build_filter(parsed_query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    crop = (parsed_query.get("crop") or "").strip()
    if not crop:
        return None

    return {
        "crop": {"$eq": crop.lower()}
    }


def _get_value(match: Any, key: str, default: Any = None) -> Any:
    if isinstance(match, dict):
        return match.get(key, default)
    return getattr(match, key, default)


def _normalize_matches(matches: List[Any], min_score: float = 0.15) -> List[Dict[str, Any]]:
    documents = []
    for match in matches:
        metadata = _get_value(match, "metadata", {}) or {}
        score = _get_value(match, "score", 0) or 0
        text = metadata.get("text") or metadata.get("content") or metadata.get("chunk") or ""

        if not text.strip():
            continue
        if score and score < min_score:
            continue

        documents.append(
            {
                "id": _get_value(match, "id", ""),
                "score": score,
                "text": text,
                "metadata": metadata,
            }
        )

    return documents


async def retrieve_documents(query: str, parsed_query: Dict[str, Any], top_k: int = 4) -> List[Dict[str, Any]]:
    try:
        vector = await gemini_client.generate_embedding(query)
        if not vector:
            print("Ask Sathi retrieval skipped: empty embedding.")
            return []

        index = get_pinecone_index()
        filter_dict = build_filter(parsed_query)

        results = index.query(
            vector=vector,
            top_k=top_k,
            namespace=settings.pinecone_namespace,
            include_metadata=True,
            filter=filter_dict,
        )
        matches = getattr(results, "matches", []) or []

        if not matches and filter_dict:
            results = index.query(
                vector=vector,
                top_k=top_k,
                namespace=settings.pinecone_namespace,
                include_metadata=True,
            )
            matches = getattr(results, "matches", []) or []

        return _normalize_matches(matches)
    except Exception as e:
        print(f"Ask Sathi retrieval unavailable: {e}")
        return []
