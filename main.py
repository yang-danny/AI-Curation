
from datetime import datetime, timezone
from agents.news_gatherer import gather_news

def run_once():
    print("--- AI-Curation: Starting News Gathering Agent ---")
    items = gather_news()
    if not items:
        print("No news items found.")
        return

    for i, it in enumerate(items, 1):
        title = it.get("title") or "(no title)"
        src = it.get("source") or ""
        typ = it.get("type") or "news"
        date = it.get("published_at") or "unknown date"
        topics = ", ".join(it.get("topics") or [])
        url = it.get("url") or ""
        summary = (it.get("summary") or "").strip()
        if len(summary) > 240:
            summary = summary[:240].rstrip() + "..."

        print(f"{i}. {title}")
        print(f"   Source: {src} | Type: {typ} | Published: {date}")
        if typ == "event":
            ev_start = it.get("event_start") or "TBA"
            ev_loc = it.get("event_location") or "TBA"
            print(f"   Event: {ev_start} @ {ev_loc}")
        if topics:
            print(f"   Topics: {topics}")
        print(f"   URL: {url}")
        if summary:
            print(f"   Summary: {summary}")
        print()
    # Here you could push to your CMS instead of saving to file.
   
    print(f"[{datetime.now(timezone.utc).isoformat()}] Gathered {len(items)} news.")

if __name__ == "__main__":
    run_once()