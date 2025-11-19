from google.adk.agents import Agent
from typing import Optional

def NewsItemsValidationChecker(name: Optional[str] = "news_items_validator", model: Optional[str] = None) -> Agent:
    """
    Returns a google.adk Agent that validates and, if needed, repairs the `news_items` JSON
    stored in the conversation/state. It should ensure a JSON array of objects with required fields.
    """
    return Agent(
        model=model or "emini-2.5-pro",
        name=name or "news_items_validator",
        description="Validates news_items JSON structure and repairs it if necessary.",
        instruction="""
You are a strict JSON validator and fixer for news items.
- Inspect the `news_items` key in the current state.
- It MUST be a JSON array of objects with at least these fields:
  ["title", "url", "source", "summary"]
- Optional fields: ["published_at", "type", "topics", "relevance_reason", "event_start", "event_location", "author"]
- Ensure dates are ISO-8601 if present.
- Remove items that are not clearly relevant or are duplicates.
- Output ONLY the corrected JSON array back to `news_items`.
""",
        output_key="news_items",
    )