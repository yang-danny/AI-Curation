import os
from dataclasses import dataclass, field
from typing import List
from datetime import datetime, timedelta, timezone

@property
def start_date_iso(self) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=self.days_back)).date().isoformat()

@dataclass
class Config:
    # Core
    org_name: str = os.getenv( "AI-Curation")
    worker_model: str = os.getenv("WORKER_MODEL", "gemini-2.5-pro")

    # Google Search (used by google-adk's google_search tool)
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")

    # Gathering controls
    days_back: int = int(os.getenv("DAYS_BACK", "14"))
    max_results: int = int(os.getenv("MAX_RESULTS", "5"))
    language: str = os.getenv("LANGUAGE", "en")
    country_focus: str = os.getenv("COUNTRY_FOCUS", "US")

    # Content targeting
    # Set these via env for your domain; defaults are sane placeholders
    keywords: List[str] = field(default_factory=lambda: [
        "AI policy", "algorithmic accountability", "data privacy",
        "AI regulation", "responsible AI", "online safety"
    ])

    # Optional: restrict to known good sources/domains if you prefer
    source_domains: List[str] = field(default_factory=lambda: [
        "gov", "edu", "org"
    ])

    # Known resource links or hubs you care about (fill with your org’s nearby ecosystem)
    resource_links: List[str] = field(default_factory=lambda: [
        "https://www.oecd.ai", 
        "https://ai.gov",
        "https://data.gov",
        "https://www.whitehouse.gov/ostp/", 
        "https://www.europa.eu", 
    ])

    # Any public event calendars you want to monitor (add yours)
    event_calendars: List[str] = field(default_factory=lambda: [
        "https://oecd.ai/en/events", 
    ])

    @property
    def start_date_iso(self) -> str:
        return (datetime.now(timezone.utc) - timedelta(days=self.days_back)).date().isoformat()

config = Config()