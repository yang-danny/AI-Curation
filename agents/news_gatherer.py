import json
from datetime import datetime, timezone
from typing import List, Dict, Any

from google.adk.agents import Agent, LoopAgent
from google.adk.tools import google_search

from config import config
from utils.agent_utils import suppress_output_callback
from utils.scraping import scrape_url
from utils.validation_checkers import NewsItemsValidationChecker
import asyncio
from collections.abc import Iterable
import re
import html
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse, quote_plus

import requests
from bs4 import BeautifulSoup
def _to_state_dict(obj):
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    # Common “result object” patterns
    for attr in ("state", "context", "memory", "data", "payload"):
        if hasattr(obj, attr):
            val = getattr(obj, attr)
            if val is None:
                continue
            if isinstance(val, dict):
                return val
            if hasattr(val, "model_dump"):
                return val.model_dump()
            if hasattr(val, "dict"):
                return val.dict()
    # Pydantic or similar
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    # Generators/iterables (e.g., streaming)
    if isinstance(obj, Iterable) and not isinstance(obj, (str, bytes, dict)):
        last = None
        for item in obj:
            last = item
        return _to_state_dict(last)
    # Fallback: wrap as dict so downstream doesn’t crash
    return {"result": obj}

def _run_agent(agent, state: dict) -> dict:
    # Prefer synchronous live run
    if hasattr(agent, "run_live") and callable(agent.run_live):
        for kw in ("state", "initial_state", "input"):
            try:
                return _to_state_dict(agent.run_live(**{kw: state}))
            except TypeError:
                continue
    # Try async runner
    if hasattr(agent, "run_async") and callable(agent.run_async):
        for kw in ("state", "initial_state", "input"):
            try:
                return _to_state_dict(asyncio.run(agent.run_async(**{kw: state})))
            except TypeError:
                continue
    # Last-resort generic calls
    for name in ("execute", "invoke", "start", "process", "predict", "apply", "forward"):
        fn = getattr(agent, name, None)
        if callable(fn):
            try:
                return _to_state_dict(fn(state))
            except TypeError:
                for kw in ("state", "initial_state", "input"):
                    try:
                        return _to_state_dict(fn(**{kw: state}))
                    except TypeError:
                        continue
    # Direct callable
    if callable(agent):
        try:
            return _to_state_dict(agent(state))
        except TypeError:
            for kw in ("state", "initial_state", "input"):
                try:
                    return _to_state_dict(agent(**{kw: state}))
                except TypeError:
                    continue
    raise AttributeError(f"{type(agent).__name__} has no callable interface I can use.")
def _build_queries(keywords: List[str], country: str, days_back: int) -> List[str]:
    """
    Build targeted search queries to retrieve fresh content.
    """
    time_filter = f"after:{config.start_date_iso}"

    # Domain-restricted queries
    base = [
        f'("{kw}" OR "{kw} update") {time_filter} site:.{dom}'
        for kw in keywords
        for dom in config.source_domains
    ]

    # Broader queries (no domain restriction)
    broad = [
        q
        for kw in keywords
        for q in [
            f'"{kw}" {time_filter} news',
            f'"{kw}" {time_filter} policy',
            f'"{kw}" {time_filter} event',
            f'"{kw}" {time_filter} regulation',
        ]
    ]

    # Event-specific queries
    events = [
        q
        for kw in keywords
        for q in [
            f'"{kw}" conference {time_filter}',
            f'"{kw}" webinar {time_filter}',
            f'"{kw}" hearing {time_filter}',
            f'"{kw}" summit {time_filter}',
        ]
    ]

    queries = base + broad + events

    # Priority resource links (kept simple; you can parse domains if you wish)
    for link in config.resource_links:
        queries.append(f'site:{link} {time_filter}')

    # Dedupe and cap
    return list(dict.fromkeys(queries))[:50]

news_researcher = Agent(
    model=config.worker_model,
    name="news_researcher",
    description="Discovers relevant industry news and events for advocacy.",
    instruction=f"""
You are the News Gathering Agent for {config.org_name}.
Your task:
- Use Google Search to find fresh, high-signal articles, press releases, regulatory updates, and events.
- Focus on the past {config.days_back} days.
- Prioritize high-quality sources, official sites, and reputable organizations.
- Suggested sources and hubs:
  {chr(10).join(f"- {u}" for u in config.resource_links)}
- Event calendars to consider:
  {chr(10).join(f"- {u}" for u in config.event_calendars)}
- Core topics/keywords:
  {", ".join(config.keywords)}

Guidelines:
- Only include items relevant to these topics and to advocacy or policy implications.
- Prefer English content (language: {config.language}).
- Return up to {config.max_results} top items.

Output format:
Return a JSON array where each element is an object:
{{
  "title": str,
  "url": str,
  "source": str,                   # domain or publisher
  "summary": str,                  # 2-3 sentence summary from the result snippet or page signals
  "type": "news"|"event"|"press_release"|"report",
  "published_at": str|null,        # ISO 8601 if known
  "topics": [str],                 # tags inferred from keywords
  "relevance_reason": str,         # why this matters for advocacy/policy
  "event_start": str|null,         # ISO 8601 if type=event
  "event_location": str|null,
  "author": str|null
}}

Notes:
- Be precise and avoid duplicates.
- If metadata is missing in search results, leave as null; the pipeline will enrich later.
- Do not include commentary. Only output the JSON array to the `news_items` key.
""",
    tools=[google_search],
    output_key="news_items",
    after_agent_callback=suppress_output_callback,
)

robust_news_gatherer = LoopAgent(
    name="robust_news_gatherer",
    description="Finds news and validates structure.",
    sub_agents=[
        news_researcher,
        NewsItemsValidationChecker(name="news_items_validator", model=config.worker_model),
    ],
    max_iterations=3,
    after_agent_callback=suppress_output_callback,
)
def _domain(url: str) -> str | None:
    try:
        return urlparse(url).netloc.lower().split(":")[0]
    except Exception:
        return None

def _clean_text(text: str | None) -> str | None:
    if not text:
        return None
    # Strip HTML and collapse whitespace
    try:
        txt = BeautifulSoup(text, "lxml").get_text(" ", strip=True)
    except Exception:
        txt = re.sub(r"<[^>]+>", " ", text)
    txt = html.unescape(txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt or None

def _to_iso(dt):
    if not dt:
        return None
    try:
        return dt.isoformat()
    except Exception:
        return None

def _call_google_adk_search(query: str, k: int = 5):
    """
    Best-effort invocation of google_adk.tools.google_search across versions.
    Returns a list of result dicts or None if not callable.
    """
    tool = google_search
    candidates = []

    tried = []

    def normalize_payload(payload):
        # Try to coerce payload into a list of dicts
        if payload is None:
            return None
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in ("results", "items", "data", "output", "payload"):
                v = payload.get(key)
                if isinstance(v, list):
                    return v
            # Sometimes a single result dict
            return [payload]
        # Iterable stream
        try:
            iter(payload)
            if not isinstance(payload, (str, bytes)):
                last = None
                for item in payload:
                    last = item
                return normalize_payload(last)
        except Exception:
            pass
        return None

    # Try different call shapes
    calls = [
        (tool, {"query": query, "num_results": k}),
        (tool, {"query": query, "k": k}),
        (tool, {"input": query}),
    ]
    for meth in ("__call__", "run", "invoke", "execute", "search"):
        fn = getattr(tool, meth, None)
        if callable(fn):
            calls.extend([
                (fn, {"query": query, "num_results": k}),
                (fn, {"query": query, "k": k}),
                (fn, {"input": query}),
                (fn, {"q": query, "num_results": k}),
            ])

    for fn, kwargs in calls:
        try:
            res = fn(**kwargs)
            norm = normalize_payload(res)
            if norm:
                return norm
            tried.append((getattr(fn, "__name__", str(fn)), kwargs))
        except TypeError:
            continue
        except Exception:
            continue

    return None  # Will trigger RSS fallback

def _fetch_google_news_rss(query: str, lang: str, country: str, limit: int = 10):
    """
    Fetch results from Google News RSS for a given query.
    """
    hl = f"{lang}-{country}" if "-" not in lang else lang
    ceid = f"{country}:{lang.split('-')[0]}"
    gl = country
    url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl={hl}&gl={gl}&ceid={ceid}"

    try:
        resp = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0 (AI-Curation Bot)"})
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except Exception:
        return []

    items = []
    for item in root.findall(".//item"):
        title = _clean_text((item.findtext("title") or "").strip())
        link = (item.findtext("link") or "").strip()
        desc = _clean_text(item.findtext("description") or "")
        pub_txt = item.findtext("pubDate")
        published_at = None
        if pub_txt:
            try:
                published_at = _to_iso(parsedate_to_datetime(pub_txt))
            except Exception:
                published_at = None

        if not link or not title:
            continue

        items.append({
            "title": title,
            "url": link,
            "snippet": desc,
            "published_at": published_at,
            "source": _domain(link),
        })
        if len(items) >= limit:
            break
    return items

def _normalize_search_item(obj: dict) -> dict | None:
    """
    Normalize a single search result from either google_adk tool or RSS fallback.
    Expected keys we try: title, url/link, snippet/description, source/domain, published_at/date
    """
    if obj is None:
        return None

    def pick(d, *keys):
        for k in keys:
            if k in d and d[k]:
                return d[k]
        for k in keys:
            v = getattr(d, k, None)
            if v:
                return v
        return None

    title = _clean_text(pick(obj, "title", "name", "headline"))
    url = pick(obj, "url", "link", "href")
    snippet = _clean_text(pick(obj, "snippet", "description", "summary"))
    source = pick(obj, "source", "publisher", "domain")
    published = pick(obj, "published_at", "date", "published", "published_time", "time")

    if not url or not title:
        return None

    if not source:
        source = _domain(url)

    # Basic type inference: tag events if obvious keywords
    t = "event" if re.search(r"\b(conference|summit|webinar|hearing|workshop|meetup)\b", (title + " " + (snippet or "")).lower()) else "news"

    return {
        "title": title,
        "url": url,
        "source": source,
        "summary": snippet or "",
        "type": t,
        "published_at": published,
    }

def _infer_topics(text: str, keywords: list[str]) -> list[str]:
    text_low = text.lower()
    hits = []
    for kw in keywords:
        if kw.lower() in text_low:
            hits.append(kw)
    return sorted(set(hits))

def _validate_items_local(items: list[dict]) -> list[dict]:
    """
    Deterministic validation: ensure required fields and dedupe.
    Required: title, url, source, summary
    """
    seen = set()
    out = []
    for it in items:
        if not it:
            continue
        url = it.get("url")
        title = it.get("title")
        source = it.get("source") or _domain(url or "")
        if not (url and title and source):
            continue
        key = (url.strip(), title.strip())
        if key in seen:
            continue
        seen.add(key)
        # Ensure summary key exists
        it["summary"] = it.get("summary") or ""
        it["source"] = source
        out.append(it)
    return out

def _search_candidates(queries: list[str], per_query_k: int = 5, hard_cap: int = 80) -> list[dict]:
    """
    Runs google_adk search if available, otherwise falls back to Google News RSS.
    Returns normalized list of result dicts (may be > max_results for later filtering).
    """
    all_items = []
    seen_urls = set()
    for q in queries:
        res = _call_google_adk_search(q, k=per_query_k)
        if res is None:
            # Fallback to RSS
            res = _fetch_google_news_rss(q, config.language, config.country_focus, limit=per_query_k)

        for r in res or []:
            norm = _normalize_search_item(r)
            if not norm:
                continue
            u = norm["url"]
            if u in seen_urls:
                continue
            seen_urls.add(u)

            # Light enrichment: add topics from title/summary
            topics = _infer_topics((norm.get("title") or "") + " " + (norm.get("summary") or ""), config.keywords)
            norm["topics"] = topics
            # Simple relevance reason
            if topics:
                norm["relevance_reason"] = f"Matches topics: {', '.join(topics)}"
            else:
                norm["relevance_reason"] = "Related to advocacy/policy keywords"

            all_items.append(norm)

        if len(all_items) >= hard_cap:
            break

    # Deterministic validation
    return _validate_items_local(all_items)
    """
    Runs the news researcher agent, validates/fixes the JSON, scrapes each result,
    and returns enriched items as a list of dicts.
    """
    queries = _build_queries(config.keywords, config.country_focus, config.days_back)

    initial_state = {
        "now": datetime.utcnow().isoformat(),
        "search_context": {
            "language": config.language,
            "country": config.country_focus,
            "start_date": config.start_date_iso,
            "resource_links": config.resource_links,
            "event_calendars": config.event_calendars,
            "source_domains": config.source_domains,
            "keywords": config.keywords,
            "max_results": config.max_results,
        },
        "queries": queries,
    }

    # 1) Run discovery
    state = _run_agent(news_researcher, initial_state)

    # 2) Validate/fix JSON structure
    validator = NewsItemsValidationChecker(
        name="news_items_validator",
        model=config.worker_model
    )
    state = _run_agent(validator, state)

    # 3) Parse results
    raw_items: List[Dict[str, Any]] = []
    news_payload = state.get("news_items") if isinstance(state, dict) else state
    if isinstance(news_payload, list):
        raw_items = news_payload
    else:
        try:
            raw_items = json.loads(news_payload or "[]")
        except Exception:
            raw_items = []

    # 4) Enrich via scraping
    enriched: List[Dict[str, Any]] = []
    seen_urls = set()
    for item in raw_items:
        url = item.get("url")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)

        scraped = scrape_url(url)
        enriched_item = {
            "title": item.get("title") or scraped.get("title"),
            "url": url,
            "source": item.get("source"),
            "summary": item.get("summary"),
            "type": item.get("type") or "news",
            "published_at": item.get("published_at") or scraped.get("published_at"),
            "topics": item.get("topics") or [],
            "relevance_reason": item.get("relevance_reason"),
            "event_start": item.get("event_start"),
            "event_location": item.get("event_location"),
            "author": item.get("author") or (
                ", ".join(scraped.get("authors")) if scraped.get("authors") else None
            ),
            "scraped_text": scraped.get("text") or "",
            "scraped_title": scraped.get("title"),
        }
        enriched.append(enriched_item)

        if len(enriched) >= config.max_results:
            break

    return enriched
    # ... build initial_state as you already do ...

    # Run discovery once, then validate/repair
    state = _run_agent(robust_news_gatherer, initial_state)

    validator = NewsItemsValidationChecker(
        name="news_items_validator",
        model=config.worker_model
    )
    state = _run_agent(validator, state)

    # Parse results
    raw_items = []
    news_payload = state.get("news_items")
    if isinstance(news_payload, list):
        raw_items = news_payload
    else:
        try:
            raw_items = json.loads(news_payload or "[]")
        except Exception:
            raw_items = []

    enriched: List[Dict[str, Any]] = []
    seen_urls = set()
    for item in raw_items:
        url = item.get("url")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)

        # Scrape and enrich
        scraped = scrape_url(url)
        enriched_item = {
            "title": item.get("title") or scraped.get("title"),
            "url": url,
            "source": item.get("source"),
            "summary": item.get("summary"),
            "type": item.get("type") or "news",
            "published_at": item.get("published_at") or scraped.get("published_at"),
            "topics": item.get("topics") or [],
            "relevance_reason": item.get("relevance_reason"),
            "event_start": item.get("event_start"),
            "event_location": item.get("event_location"),
            "author": item.get("author") or (
                ", ".join(scraped.get("authors")) if scraped.get("authors") else None
            ),
            "scraped_text": scraped.get("text") or "",
            "scraped_title": scraped.get("title"),
        }
        enriched.append(enriched_item)

        if len(enriched) >= config.max_results:
            break

    return enriched
def gather_news() -> List[Dict[str, Any]]:
    """
    Deterministic search + scrape flow that avoids LlmAgent invocation differences.
    - Builds queries
    - Searches via google_adk tool or RSS fallback
    - Validates locally
    - Scrapes each URL for metadata and text
    - Returns up to config.max_results enriched items
    """
    queries = _build_queries(config.keywords, config.country_focus, config.days_back)

    # Get candidates (oversample then filter)
    candidates = _search_candidates(queries, per_query_k=5, hard_cap=max(80, config.max_results * 6))

    # Time filter: keep only items within the configured window if they have a date
    try:
        cutoff = datetime.fromisoformat(config.start_date_iso)
    except Exception:
        cutoff = None

    filtered = []
    for it in candidates:
        dt_iso = it.get("published_at")
        keep = True
        if dt_iso and cutoff:
            try:
                it_dt = datetime.fromisoformat(dt_iso.replace("Z", "+00:00"))
                if it_dt.date() < cutoff.date():
                    keep = False
            except Exception:
                pass
        if keep:
            filtered.append(it)

    # Prefer items with dates, then by most recent
    def sort_key(x):
        dt = x.get("published_at")
        return (0 if dt else 1, dt or "")

    filtered.sort(key=sort_key)

    # Enrich via scraping
    enriched: List[Dict[str, Any]] = []
    seen_urls = set()
    for item in filtered:
        url = item.get("url")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)

        scraped = scrape_url(url)
        enriched_item = {
            "title": item.get("title") or scraped.get("title"),
            "url": url,
            "source": item.get("source") or _domain(url),
            "summary": item.get("summary") or (scraped.get("text")[:300] if scraped.get("text") else ""),
            "type": item.get("type") or "news",
            "published_at": item.get("published_at") or scraped.get("published_at"),
            "topics": item.get("topics") or [],
            "relevance_reason": item.get("relevance_reason"),
            "event_start": item.get("event_start"),
            "event_location": item.get("event_location"),
            "author": item.get("author") or (
                ", ".join(scraped.get("authors")) if scraped.get("authors") else None
            ),
            "scraped_text": scraped.get("text") or "",
            "scraped_title": scraped.get("title"),
        }
        enriched.append(enriched_item)
        if len(enriched) >= config.max_results:
            break

    return enriched