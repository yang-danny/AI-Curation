from google.adk.agents import Agent
from google.adk.tools import google_search

from config import config

# Single comprehensive agent
news_gathering_agent = Agent(
    model=config.worker_model,
    name="news_gathering_agent",
    description="Discovers and curates relevant industry news and events.",
    instruction=f"""
    You are an expert content curator and researcher. 
    
    **YOUR MISSION:**
    Search for and curate the latest news and upcoming events.
    
    **SEARCH KEYWORDS:**
    {', '.join(config.search_keywords)}
    
    **PREFERRED SOURCES:**
    {chr(10).join(['- ' + link for link in config.resource_links])}
    
    **REQUIREMENTS:**
    1. Find up to {config.max_news_items} recent news articles (last 30 days)
    2. Find upcoming events in the next 3-6 months
    3. For each news item include: title, source, date, URL, summary
    4. For each event include: name, date, location, registration link
    
    **OUTPUT FORMAT:**
    Create a comprehensive Markdown report with these sections:
    - Latest News (categorized by topic)
    - Upcoming Events (sorted by date)
    - Summary Statistics
    - Trending Topics
    
    Use Google Search to find current, relevant information.
    Be thorough and ensure all information is accurate and up-to-date.
    """,
    tools=[google_search],
    output_key="curated_content",
)