import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration settings for AI-Curation project"""
    
    # Model configuration
    worker_model = os.getenv("WORKER_MODEL")
    # Search configuration
    search_keywords = [
        "AI technology news",
        "machine learning breakthroughs",
        "artificial intelligence events",
        "tech industry updates"
    ]
    
    # Resource links for news sources
    resource_links = [
        "https://techcrunch.com",
        "https://www.theverge.com",
        "https://venturebeat.com",
        "https://www.artificialintelligence-news.com"
    ]
    social_media_accounts = {
        "facebook": [
            "https://www.facebook.com/amazonwebservices/",
            "https://www.facebook.com/openai",
            "https://www.facebook.com/Google/",
            "https://www.facebook.com/Microsoft/",
            "https://www.facebook.com/nvidia/",
        ],
        "twitter": [
            "https://twitter.com/awscloud",
            "https://twitter.com/OpenAI",
            "https://twitter.com/Google",
            "https://twitter.com/Microsoft",
            "https://twitter.com/nvidia",
        ],
        "linkedin": [
            "https://www.linkedin.com/company/amazon-web-services/",
            "https://www.linkedin.com/company/openai/",
            "https://www.linkedin.com/company/google/",
            "https://www.linkedin.com/company/microsoft/",
            "https://www.linkedin.com/company/nvidia/",
        ]
    }
    
    # Social media search keywords
    social_media_keywords = [
        "AI announcement",
        "product launch",
        "new feature",
        "technology update",
        "developer tools",
        "cloud computing",
    ]
    max_posts_per_account = int(os.getenv("MAX_POSTS_PER_ACCOUNT", "5"))
    social_media_lookback_days = int(os.getenv("SOCIAL_MEDIA_LOOKBACK_DAYS", "7"))
    # Agent configuration
    max_news_items = int(os.getenv("MAX_NEWS_ITEMS", "5"))
    search_interval_hours = int(os.getenv("SEARCH_INTERVAL_HOURS", "24"))
    
   # Content Generation Configuration
    brand_name = os.getenv("BRAND_NAME", "Tech Advocacy Group")
    brand_tagline = os.getenv("BRAND_TAGLINE", "Championing Innovation and Technology")
    
    # Brand voice attributes
    brand_voice = {
        "tone": os.getenv("BRAND_TONE", "professional, enthusiastic, informative"),
        "style": os.getenv("BRAND_STYLE", "clear, engaging, authoritative"),
        "perspective": os.getenv("BRAND_PERSPECTIVE", "first-person plural (we/our)"),
        "avoid": "jargon without explanation, overly promotional language, clickbait",
    }
    
    # Target audience
    target_audience = {
        "primary": "Technology professionals, developers, IT decision-makers",
        "secondary": "Tech enthusiasts, students, industry observers",
        "knowledge_level": "intermediate to advanced",
    }
    
    # Content generation settings
    summary_length = os.getenv("SUMMARY_LENGTH", "medium")  # short, medium, long
    blog_post_length = os.getenv("BLOG_POST_LENGTH", "medium")  # 500-1000 words
    include_seo = os.getenv("INCLUDE_SEO", "true").lower() == "true"
    include_cta = os.getenv("INCLUDE_CTA", "true").lower() == "true"
    
    # Content templates
    content_types = [
        "news_summary",      # Brief news summaries
        "blog_post",         # Full blog articles
        "social_update",     # Social media posts
        "newsletter",        # Newsletter content
        "press_release",     # Press release style
    ]
    
    default_content_type = os.getenv("DEFAULT_CONTENT_TYPE", "blog_post")
     # Supervisor Agent Configuration
    max_retries = int(os.getenv("MAX_RETRIES", "3"))
    retry_delay = int(os.getenv("RETRY_DELAY", "5"))  # seconds
    enable_parallel_execution = os.getenv("ENABLE_PARALLEL", "false").lower() == "true"
    
    # Workflow configuration
    workflow_steps = [
        "news_gathering",
        "social_media_monitoring",
        "content_generation",
    ]
    
    required_steps = os.getenv("REQUIRED_STEPS", "news_gathering,content_generation").split(",")
    optional_steps = ["social_media_monitoring"]
    
    # Workflow behavior
    continue_on_failure = os.getenv("CONTINUE_ON_FAILURE", "true").lower() == "true"
    save_intermediate_results = os.getenv("SAVE_INTERMEDIATE", "true").lower() == "true"
    
    # Output configuration
    output_format = "markdown"
    output_directory = "output"
    content_output_directory = "output"
    workflow_logs_directory = "output/logs"
    
    
    
    # Google API configuration (if needed)
    google_api_key = os.getenv("GOOGLE_API_KEY", "")

config = Config()