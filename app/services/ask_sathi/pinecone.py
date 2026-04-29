import os
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
    crop = parsed_query.get("crop")
    if not crop:
        return None
    
    return {
        "crop": {"$eq": crop.lower()}
    }

async def retrieve_documents(query: str, parsed_query: Dict[str, Any], top_k: int = 4) -> List[Dict[str, Any]]:
    try:
        vector = await gemini_client.generate_embedding(query)
        if not vector:
            return []
        
        index = get_pinecone_index()
        filter_dict = build_filter(parsed_query)
        
        # Search with filter
        results = index.query(
            vector=vector,
            top_k=top_k,
            namespace=settings.pinecone_namespace,
            include_metadata=True,
            filter=filter_dict
        )
        
        matches = results.get("matches", [])
        
        # Fallback to semantic-only retrieval if no filtered matches
        if not matches and filter_dict:
            results = index.query(
                vector=vector,
                top_k=top_k,
                namespace=settings.pinecone_namespace,
                include_metadata=True
            )
            matches = results.get("matches", [])
        
        return [
            {
                "id": m.get("id"),
                "score": m.get("score"),
                "text": m.get("metadata", {}).get("text", ""),
                "metadata": m.get("metadata", {})
            }
            for m in matches
        ]
    except Exception as e:
        print(f"Error retrieving documents: {e}")
        return []
