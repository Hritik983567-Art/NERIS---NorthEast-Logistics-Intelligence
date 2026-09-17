import hashlib
import re
import html
from typing import Optional, Dict, Any
from app.services.news.base import NERISNewsArticle
from app.services.news.relevance import (
    infer_location,
    infer_category,
    infer_severity,
    calculate_relevance_score,
    parse_pub_date_timestamp
)

def sanitize_text(text: Optional[str], max_length: int = 1000) -> str:
    if not text:
        return ""
    # Strip HTML tags
    clean = re.sub(r'<[^>]+>', ' ', str(text))
    # Unescape HTML entities
    clean = html.unescape(clean)
    # Replace non-breaking space and replacement character artifacts
    clean = clean.replace('\xa0', ' ').replace('\ufffd', ' ').replace('&nbsp;', ' ')
    # Normalize multiple spaces and newlines
    clean = re.sub(r'\s+', ' ', clean).strip()
    if len(clean) > max_length:
        clean = clean[:max_length - 3] + "..."
    return clean

def sanitize_url(url: Optional[str]) -> str:
    if not url:
        return "#"
    clean_url = str(url).strip()
    if clean_url.startswith("http://") or clean_url.startswith("https://"):
        return clean_url
    return "#"

def generate_stable_article_id(source: str, source_url: str, title: str, published_at: str) -> str:
    canonical = f"{source.strip().lower()}|{source_url.strip().lower()}|{title.strip().lower()}"
    digest = hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:12]
    return f"neris-news-{digest}"

def normalize_article_record(
    title: str,
    summary: str,
    source: str,
    source_url: str,
    published_at: str,
    retrieved_at: str,
    location: Optional[str] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    image_url: Optional[str] = None,
    is_demo: bool = False,
    original_language: Optional[str] = "en",
    title_native: Optional[str] = None,
    summary_native: Optional[str] = None
) -> NERISNewsArticle:
    clean_title = sanitize_text(title, max_length=200)
    clean_summary = sanitize_text(summary, max_length=800)
    clean_source = sanitize_text(source, max_length=100) or "Verified News Agency"
    valid_source_url = sanitize_url(source_url)
    
    clean_title_native = sanitize_text(title_native, max_length=200) if title_native else clean_title
    clean_summary_native = sanitize_text(summary_native, max_length=800) if summary_native else clean_summary

    if len(clean_summary) < 15:
        clean_summary = f"Regional disaster & logistics update published by {clean_source} regarding {clean_title}."
    if len(clean_summary_native) < 15:
        clean_summary_native = clean_summary
    
    # Infer location dynamically from text content first, falling back to topic default location
    inferred_loc = infer_location(clean_title + " " + clean_summary, fallback_location=location)
    inferred_cat = category or infer_category(clean_title, clean_summary)
    inferred_sev = severity or infer_severity(clean_title, clean_summary)
    
    article_id = generate_stable_article_id(clean_source, valid_source_url, clean_title, published_at)
    pub_timestamp = parse_pub_date_timestamp(published_at)
    
    rel_score, rel_breakdown = calculate_relevance_score(
        clean_title,
        clean_summary,
        inferred_loc,
        inferred_sev,
        published_at
    )
    
    return NERISNewsArticle(
        id=article_id,
        title=clean_title,
        summary=clean_summary,
        category=inferred_cat,
        source=clean_source,
        source_url=valid_source_url,
        published_at=published_at,
        published_timestamp=pub_timestamp,
        retrieved_at=retrieved_at,
        location=inferred_loc,
        severity=inferred_sev,
        image_url=image_url,
        relevance_score=rel_score,
        relevance_breakdown=rel_breakdown,
        is_demo=is_demo,
        verification_status="UNVERIFIED_EXTERNAL_ARTICLE",
        is_unverified=True,
        original_language=original_language or "en",
        title_native=clean_title_native,
        summary_native=clean_summary_native,
        original_content=clean_summary
    )
