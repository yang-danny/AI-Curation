import json
import re
from datetime import datetime
from typing import Dict, Any, Optional

import requests
import trafilatura
from bs4 import BeautifulSoup

ISO_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

def _normalize_date(dt_str: Optional[str]) -> Optional[str]:
    if not dt_str:
        return None
    # Try a few formats; return ISO 8601 date or datetime
    try:
        # Already ISO?
        if ISO_DATE_RE.match(dt_str.strip()[:10]):
            return dt_str
    except Exception:
        pass

    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d %b %Y", "%b %d, %Y", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            dt = datetime.strptime(dt_str.strip(), fmt)
            return dt.isoformat()
        except Exception:
            continue
    return None

def _extract_meta_dates(soup: BeautifulSoup) -> Optional[str]:
    # Try a range of common meta tags
    meta_props = [
        ("meta", {"property": "article:published_time"}),
        ("meta", {"name": "article:published_time"}),
        ("meta", {"property": "og:updated_time"}),
        ("meta", {"property": "og:published_time"}),
        ("meta", {"name": "pubdate"}),
        ("meta", {"name": "date"}),
        ("time", {"datetime": True}),
    ]
    for tag, attrs in meta_props:
        el = soup.find(tag, attrs)
        if el:
            val = el.get("content") or el.get("datetime") or el.get("value") or el.text
            if val:
                iso = _normalize_date(val)
                if iso:
                    return iso
    return None

def _extract_meta_title(soup: BeautifulSoup) -> Optional[str]:
    og = soup.find("meta", {"property": "og:title"})
    if og and og.get("content"):
        return og["content"].strip()
    if soup.title and soup.title.text:
        return soup.title.text.strip()
    return None

def scrape_url(url: str, timeout: int = 20) -> Dict[str, Any]:
    """
    Fetches and extracts main content and metadata from a URL.
    Returns a dict with fields: text, title, published_at, authors (optional)
    """
    # Try trafilatura first (often yields good results)
    downloaded = None
    try:
        downloaded = trafilatura.fetch_url(url, timeout=timeout)
    except Exception:
        downloaded = None

    article_text = None
    article_title = None
    article_date = None
    authors = []

    if downloaded:
        try:
            extracted_json = trafilatura.extract(downloaded, output_format="json")
            if extracted_json:
                data = json.loads(extracted_json)
                article_text = (data.get("text") or "")[:10000]  # cap length
                article_title = data.get("title")
                article_date = _normalize_date(data.get("date"))
                authors = data.get("authors") or []
        except Exception:
            pass

    # If metadata missing, try a lightweight HTML parse
    if not article_title or not article_date:
        try:
            resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0 (AI-Curation Bot)"})
            if resp.ok and resp.text:
                soup = BeautifulSoup(resp.text, "lxml")
                if not article_title:
                    article_title = _extract_meta_title(soup)
                if not article_date:
                    article_date = _extract_meta_dates(soup)
        except Exception:
            pass

    return {
        "text": article_text or "",
        "title": article_title,
        "published_at": article_date,
        "authors": authors,
        "url": url,
    }