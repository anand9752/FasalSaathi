from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from app.services.ask_sathi.pipeline import process_ask_sathi_query

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class AskSathiRequest(BaseModel):
    query: str
    history: Optional[List[Dict[str, str]]] = Field(default_factory=list)

class AskSathiResponse(BaseModel):
    type: str
    response: str
    language: str

@router.post("/ask-sathi", response_model=AskSathiResponse)
async def ask_sathi(request: AskSathiRequest):
    try:
        result = await process_ask_sathi_query(request.query, request.history or [])
        return AskSathiResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
