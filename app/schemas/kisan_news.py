from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class KisanNewsArticleRead(BaseModel):
    title: str
    description: str | None = None
    link: str
    image_url: str | None = None
    pubDate: str | None = None
    tags: list[str] = []


class KisanNewsResponse(BaseModel):
    articles: list[KisanNewsArticleRead]
    source: Literal["live", "cache", "none"]
    is_stale: bool
    refreshed_at: datetime | None = None
    message: str

