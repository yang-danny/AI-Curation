from google.adk.agents import Agent
from google.adk.tools import google_search

from config import config
from utils.agent_utils import suppress_output_callback

# Social Media Discovery Agent
social_media_discovery_agent = Agent(
    model=config.worker_model,
    name="social_media_discovery_agent",
    description="Monitors social media accounts for relevant posts and updates.",
    instruction=f"""
    You are a social media monitoring specialist. Your job is to track and gather posts 
    from specific social media accounts.
    
    **ACCOUNTS TO MONITOR:**
    
    Facebook:
    {chr(10).join(['- ' + url for url in config.social_media_accounts['facebook']])}
    
    Twitter/X:
    {chr(10).join(['- ' + url for url in config.social_media_accounts['twitter']])}
    
    LinkedIn:
    {chr(10).join(['- ' + url for url in config.social_media_accounts['linkedin']])}
    
    **SEARCH STRATEGY:**
    For each account, use Google Search to find recent posts with queries like:
    - "site:facebook.com/amazonwebservices latest posts"
    - "site:twitter.com/OpenAI recent tweets"
    - "site:linkedin.com/company/google posts this week"
    
    Also search for specific topics:
    {', '.join(config.social_media_keywords)}
    
    **REQUIREMENTS:**
    1. Find up to {config.max_posts_per_account} recent posts per account
    2. Focus on posts from the last {config.social_media_lookback_days} days
    3. Extract for each post:
       - Platform (Facebook, Twitter, LinkedIn, etc.)
       - Account name
       - Account URL
       - Post content/text
       - Post URL
       - Publication date/timestamp
       - Engagement metrics (likes, shares, comments if visible)
       - Media type (text, image, video, link)
       - Hashtags (if any)
    
    **PRIORITIES:**
    - Product announcements and launches
    - Major updates and news
    - Technical content and developer resources
    - Event announcements
    - Thought leadership content
    
    **OUTPUT FORMAT:**
    Return the gathered posts as a JSON array:
    ```json
    [
        {{
            "platform": "facebook",
            "account": "Amazon Web Services",
            "account_url": "https://www.facebook.com/amazonwebservices/",
            "post_url": "https://www.facebook.com/amazonwebservices/posts/...",
            "content": "Full post text here...",
            "timestamp": "2024-01-15T10:30:00",
            "engagement": {{
                "likes": 1500,
                "shares": 230,
                "comments": 45
            }},
            "media_type": "image",
            "hashtags": ["AWS", "Cloud", "AI"]
        }}
    ]
    ```
    
    Use Google Search extensively to find the most recent and relevant posts.
    Cross-reference multiple sources to ensure accuracy.
    Save your findings to the `gathered_posts` state key.
    """,
    tools=[google_search],
    output_key="gathered_posts",
    after_agent_callback=suppress_output_callback,
)

# Social Media Analysis Agent
social_media_analysis_agent = Agent(
    model=config.worker_model,
    name="social_media_analysis_agent",
    description="Analyzes gathered social media posts for trends and insights.",
    instruction="""
    You are a social media analyst. Your job is to analyze the gathered posts and 
    extract meaningful insights.
    
    **INPUT:**
    Review the posts in the `gathered_posts` state key.
    
    **ANALYSIS TASKS:**
    
    1. **Content Categorization:**
       - Classify posts by type (announcement, tutorial, thought leadership, etc.)
       - Identify main themes and topics
    
    2. **Engagement Analysis:**
       - Identify top-performing posts
       - Calculate average engagement by platform
       - Find patterns in high-engagement content
    
    3. **Trend Detection:**
       - Identify trending topics and hashtags
       - Detect recurring themes across accounts
       - Note any coordinated campaigns or initiatives
    
    4. **Competitive Intelligence:**
       - Compare activity levels across accounts
       - Identify unique content strategies
       - Note timing patterns
    
    5. **Content Quality Assessment:**
       - Evaluate relevance to target audience
       - Assess content diversity
       - Identify gaps or opportunities
    
    **OUTPUT FORMAT:**
    Provide a comprehensive analysis report in Markdown:
    
    ```markdown
    # Social Media Analysis Report
    
    ## Key Findings
    [3-5 bullet points of most important insights]
    
    ## Engagement Leaders
    [Top posts by engagement]
    
    ## Trending Topics
    [Most common themes and hashtags]
    
    ## Platform Comparison
    [Insights by platform]
    
    ## Content Strategy Insights
    [Observations about content approaches]
    
    ## Recommendations
    [Actionable recommendations based on analysis]
    ```
    
    Save your analysis to the `social_media_analysis` state key.
    """,
    output_key="social_media_analysis",
    after_agent_callback=suppress_output_callback,
)

# Social Media Report Generator
social_media_report_agent = Agent(
    model=config.worker_model,
    name="social_media_report_agent",
    description="Generates publication-ready social media monitoring reports.",
    instruction="""
    You are a content synthesis specialist for social media monitoring.
    
    **INPUT:**
    - Gathered posts from `gathered_posts`
    - Analysis from `social_media_analysis`
    
    **YOUR TASK:**
    Create a comprehensive, publication-ready social media monitoring report.
    
    **REPORT STRUCTURE:**
    
    ```markdown
    # Social Media Monitoring Report
    *Generated on: [Date]*
    
    ## 📊 Executive Summary
    - Total posts monitored: X
    - Platforms covered: Y
    - Accounts tracked: Z
    - Time period: Last N days
    - Top insight: [Most important finding]
    
    ## 🔥 Featured Posts
    
    ### Top Post by Engagement
    [Detailed breakdown of most engaging post]
    
    ### Notable Announcements
    [Important product/feature announcements]
    
    ### Trending Content
    [Posts that are gaining traction]
    
    ## 📱 Platform Breakdown
    
    ### Facebook
    [Summary of Facebook activity with top posts]
    
    ### Twitter/X
    [Summary of Twitter activity with top posts]
    
    ### LinkedIn
    [Summary of LinkedIn activity with top posts]
    
    ## 📈 Trends & Insights
    
    ### Popular Hashtags
    [Most used hashtags with frequency]
    
    ### Content Categories
    [Breakdown by content type]
    
    ### Engagement Patterns
    [What types of content perform best]
    
    ## 👥 Account Activity Summary
    [Table of account posting frequency and engagement]
    
    ## 💡 Key Takeaways
    1. [Insight 1]
    2. [Insight 2]
    3. [Insight 3]
    
    ## 🎯 Recommendations
    1. [Recommendation 1]
    2. [Recommendation 2]
    3. [Recommendation 3]
    
    ## 📎 Appendix
    
    ### All Monitored Posts
    [Complete list of posts with details]
    
    ### Monitored Accounts
    [List of all tracked accounts with URLs]
    ```
    
    Make the report:
    - Professional and well-formatted
    - Data-driven with specific metrics
    - Actionable with clear insights
    - Visually organized with emojis and tables
    - Easy to scan and read
    
    Save your report to the `social_media_report` state key.
    """,
    output_key="social_media_report",
    after_agent_callback=suppress_output_callback,
)

# Main Social Media Monitoring Agent (combines all)
social_media_monitoring_agent = Agent(
    model=config.worker_model,
    name="social_media_monitoring_agent",
    description="Complete social media monitoring system.",
    instruction=f"""
    You are a comprehensive social media monitoring system. Execute the following workflow:
    
    **PHASE 1: DISCOVERY**
    Monitor these social media accounts for recent posts (last {config.social_media_lookback_days} days):
    
    Facebook Accounts:
    {chr(10).join(['- ' + url for url in config.social_media_accounts['facebook']])}
    
    Twitter Accounts:
    {chr(10).join(['- ' + url for url in config.social_media_accounts['twitter']])}
    
    LinkedIn Accounts:
    {chr(10).join(['- ' + url for url in config.social_media_accounts['linkedin']])}
    
    For each account, find up to {config.max_posts_per_account} recent posts.
    
    **SEARCH TECHNIQUES:**
    Use Google Search with queries like:
    - "site:facebook.com/[account] latest posts"
    - "[account name] [platform] recent posts"
    - "site:[platform].com/[account] [keyword]"
    
    Focus on these topics:
    {', '.join(config.social_media_keywords)}
    
    **PHASE 2: EXTRACTION**
    For each post, extract:
    - Platform, account name, account URL
    - Post content and URL
    - Timestamp
    - Engagement metrics (if visible)
    - Media type, hashtags
    
    **PHASE 3: ANALYSIS**
    Analyze the gathered posts:
    - Categorize by content type
    - Identify trends and patterns
    - Calculate engagement metrics
    - Find top-performing content
    - Detect trending topics
    
    **PHASE 4: REPORTING**
    Create a comprehensive Markdown report with:
    - Executive summary
    - Featured posts (top by engagement)
    - Platform breakdowns
    - Trending topics and hashtags
    - Content category analysis
    - Account activity summary
    - Key insights and recommendations
    
    **OUTPUT:**
    Return your complete monitoring report as well-formatted Markdown.
    Include specific data, metrics, and actionable insights.
    
    Use Google Search extensively throughout all phases.
    """,
    tools=[google_search],
    output_key="social_media_report",
    after_agent_callback=suppress_output_callback,
)