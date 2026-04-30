from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.kisan_news import KisanNewsArticle
from app.schemas.kisan_news import KisanNewsArticleRead, KisanNewsResponse


NEWS_QUERY = "farmer OR agriculture OR kisan OR crop OR mandi OR fertilizer"
TAG_KEYWORDS = {
    "farmer": ("farmer", "farmers", "kisan"),
    "mandi": ("mandi", "market", "price", "mandis"),
    "crop": ("crop", "crops", "harvest", "sowing"),
    "fertilizer": ("fertilizer", "fertiliser", "urea", "dap"),
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _article_to_schema(article: KisanNewsArticle) -> KisanNewsArticleRead:
    return KisanNewsArticleRead(
        title=article.title,
        description=article.description,
        link=article.link,
        image_url=article.image_url,
        pubDate=article.pubDate,
        tags=article.tags or [],
    )


def _get_cached_articles(db: Session, limit: int) -> list[KisanNewsArticle]:
    return list(
        db.scalars(
            select(KisanNewsArticle)
            .order_by(KisanNewsArticle.fetched_at.desc(), KisanNewsArticle.id.asc())
            .limit(limit)
        )
    )


def _latest_cache_time(db: Session) -> datetime | None:
    article = db.scalars(
        select(KisanNewsArticle).order_by(KisanNewsArticle.fetched_at.desc()).limit(1)
    ).first()
    return _as_aware(article.fetched_at) if article else None


def _is_cache_fresh(db: Session) -> bool:
    latest = _latest_cache_time(db)
    if latest is None:
        return False
    return _utc_now() - latest < timedelta(hours=settings.newsdata_cache_ttl_hours)


def _derive_tags(title: str, description: str | None) -> list[str]:
    haystack = f"{title} {description or ''}".lower()
    tags = [tag for tag, keywords in TAG_KEYWORDS.items() if any(keyword in haystack for keyword in keywords)]
    return tags[:3] or ["agriculture"]


def _normalize_article(item: dict) -> dict | None:
    title = (item.get("title") or "").strip()
    link = (item.get("link") or "").strip()
    if not title or not link:
        return None

    description = item.get("description")
    if isinstance(description, str):
        description = description.strip() or None
    else:
        description = None

    image_url = item.get("image_url")
    if isinstance(image_url, str):
        image_url = image_url.strip() or None
    else:
        image_url = None

    pub_date = item.get("pubDate")
    if isinstance(pub_date, str):
        pub_date = pub_date.strip() or None
    else:
        pub_date = None

    return {
        "title": title,
        "description": description,
        "link": link,
        "image_url": image_url,
        "pubDate": pub_date,
        "tags": _derive_tags(title, description),
    }


def _fetch_from_newsdata(limit: int) -> list[dict] | None:
    api_key = settings.newsdata_api_key
    if not api_key:
        return None

    params = {
        "apikey": api_key,
        "q": NEWS_QUERY,
        "country": "in",
        "language": "en,hi",
        "size": limit,
    }
    try:
        response = httpx.get(settings.newsdata_base_url, params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return None

    if payload.get("status") == "error":
        return None

    normalized: list[dict] = []
    seen_links: set[str] = set()
    for item in payload.get("results", []):
        article = _normalize_article(item)
        if not article or article["link"] in seen_links:
            continue
        seen_links.add(article["link"])
        normalized.append(article)
        if len(normalized) >= limit:
            break
    return normalized


def _replace_cache(db: Session, articles: list[dict]) -> datetime:
    fetched_at = _utc_now()
    db.execute(delete(KisanNewsArticle))
    for article in articles:
        db.add(KisanNewsArticle(**article, fetched_at=fetched_at))
    db.commit()
    return fetched_at


def get_kisan_news(db: Session, limit: int = 8, force_refresh: bool = False) -> KisanNewsResponse:
    limit = max(5, min(10, limit))

    if not force_refresh and _is_cache_fresh(db):
        cached = _get_cached_articles(db, limit)
        latest = _latest_cache_time(db)
        return KisanNewsResponse(
            articles=[_article_to_schema(article) for article in cached],
            source="cache",
            is_stale=False,
            refreshed_at=latest,
            message="Fresh cached agriculture news returned.",
        )

    live_articles = _fetch_from_newsdata(limit)
    if live_articles:
        refreshed_at = _replace_cache(db, live_articles)
        cached = _get_cached_articles(db, limit)
        return KisanNewsResponse(
            articles=[_article_to_schema(article) for article in cached],
            source="live",
            is_stale=False,
            refreshed_at=refreshed_at,
            message="Latest agriculture news fetched successfully.",
        )

    cached = _get_cached_articles(db, limit)
    if cached:
        latest = _latest_cache_time(db)
        return KisanNewsResponse(
            articles=[_article_to_schema(article) for article in cached],
            source="cache",
            is_stale=True,
            refreshed_at=latest,
            message="Live news is unavailable right now, showing saved agriculture news.",
        )

    return KisanNewsResponse(
        articles=[],
        source="none",
        is_stale=True,
        refreshed_at=None,
        message="No agriculture news is available right now. Please try refreshing later.",
    )

