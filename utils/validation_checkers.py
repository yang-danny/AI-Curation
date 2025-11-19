from google.adk.agents import Agent
from config import config
from utils.agent_utils import suppress_output_callback

class NewsValidationChecker(Agent):
    """Validates that news content meets quality standards"""
    
    def __init__(self, name: str = "news_validation_checker"):
        super().__init__(
            model=config.worker_model,
            name=name,
            description="Validates gathered news content for quality and relevance.",
            instruction="""
            You are a content quality validator. Your job is to review gathered news content and ensure it meets the following criteria:
            
            1. **Relevance**: The content must be related to the specified industry/topics
            2. **Recency**: The content should be recent (within the last 30 days preferred)
            3. **Credibility**: Sources should be reputable and trustworthy
            4. **Completeness**: Each news item should have a title, source, date, URL, and summary
            5. **Uniqueness**: Avoid duplicate or near-duplicate content
            
            Review the news content in the `gathered_news` state key.
            
            If the content passes validation, output "VALID" and provide a brief quality report.
            If the content fails validation, output "INVALID" and explain what needs to be improved.
            
            Your output should be in the following format:
            ```
            STATUS: [VALID/INVALID]
            QUALITY_SCORE: [1-10]
            REPORT: [Your assessment]
            RECOMMENDATIONS: [Any suggestions for improvement]
            ```
            """,
            output_key="validation_result",
            after_agent_callback=suppress_output_callback,
        )

class EventValidationChecker(Agent):
    """Validates that event information is complete and accurate"""
    
    def __init__(self, name: str = "event_validation_checker"):
        super().__init__(
            model=config.worker_model,
            name=name,
            description="Validates gathered event information.",
            instruction="""
            You are an event information validator. Review the gathered event data and ensure:
            
            1. **Essential Information**: Event name, date/time, location (or virtual link), and description
            2. **Future Events**: Events should be upcoming, not past events
            3. **Relevance**: Events should match the industry focus
            4. **Registration Details**: If available, include registration links and deadlines
            
            Review the events in the `gathered_events` state key.
            
            Output format:
            ```
            STATUS: [VALID/INVALID]
            EVENTS_COUNT: [Number of valid events]
            ISSUES: [Any problems found]
            ```
            """,
            output_key="event_validation_result",
            after_agent_callback=suppress_output_callback,
        )

class SocialMediaValidationChecker(Agent):
    """Validates social media posts for quality and relevance"""
    
    def __init__(self, name: str = "social_media_validation_checker"):
        super().__init__(
            model=config.worker_model,
            name=name,
            description="Validates gathered social media posts.",
            instruction="""
            You are a social media content validator. Review the gathered posts and ensure:
            
            1. **Authenticity**: Posts should be from verified/official accounts
            2. **Recency**: Posts should be recent (within specified lookback period)
            3. **Completeness**: Each post should have platform, account, content, URL, and timestamp
            4. **Relevance**: Content should be relevant to monitoring objectives
            5. **Data Quality**: Engagement metrics and metadata should be present
            6. **No Spam**: Filter out promotional spam or irrelevant content
            
            Review the posts in the `gathered_posts` state key.
            
            Output format:
            ```
            STATUS: [VALID/INVALID]
            QUALITY_SCORE: [1-10]
            TOTAL_POSTS: [Number]
            VALID_POSTS: [Number]
            ISSUES: [Any problems found]
            RECOMMENDATIONS: [Suggestions for improvement]
            ```
            """,
            output_key="social_media_validation_result",
            after_agent_callback=suppress_output_callback,
        )
        # ... (keep existing validators)

class ContentQualityChecker(Agent):
    """Validates generated content for quality and brand consistency"""
    
    def __init__(self, name: str = "content_quality_checker"):
        super().__init__(
            model=config.worker_model,
            name=name,
            description="Validates generated content for quality, accuracy, and brand consistency.",
            instruction=f"""
            You are a content quality assurance specialist for {config.brand_name}.
            
            **YOUR TASK:**
            Review generated content and validate it meets our quality standards.
            
            **REVIEW CRITERIA:**
            
            1. **Brand Voice (Weight: 25%)**
               - Tone matches: {config.brand_voice['tone']}
               - Style matches: {config.brand_voice['style']}
               - Perspective: {config.brand_voice['perspective']}
               - Avoids: {config.brand_voice['avoid']}
            
            2. **Technical Quality (Weight: 25%)**
               - Grammar and spelling correct
               - Proper punctuation
               - No typos or errors
               - Consistent formatting
            
            3. **Content Value (Weight: 25%)**
               - Provides clear value to audience
               - Accurate and factual
               - Well-researched
               - Original insights included
            
            4. **Structure & Readability (Weight: 15%)**
               - Clear headings and sections
               - Scannable with bullets/lists
               - Appropriate length
               - Logical flow
            
            5. **SEO & Engagement (Weight: 10%)**
               - Compelling title
               - Good meta description
               - Effective CTAs
               - Relevant links
            
            **REVIEW PROCESS:**
            1. Read through all generated content
            2. Score each criterion (1-10)
            3. Calculate weighted overall score
            4. Identify specific issues
            5. Provide actionable feedback
            
            Review content from the `generated_content` state key.
            
            **OUTPUT FORMAT:**
            ```
            STATUS: [APPROVED/NEEDS_REVISION/REJECTED]
            OVERALL_SCORE: [1-10]
            
            SCORES BY CRITERIA:
            - Brand Voice: [1-10]
            - Technical Quality: [1-10]
            - Content Value: [1-10]
            - Structure & Readability: [1-10]
            - SEO & Engagement: [1-10]
            
            STRENGTHS:
            - [Strength 1]
            - [Strength 2]
            
            ISSUES FOUND:
            - [Issue 1]
            - [Issue 2]
            
            RECOMMENDATIONS:
            - [Recommendation 1]
            - [Recommendation 2]
            
            APPROVAL NOTES:
            [Overall assessment and any special notes]
            ```
            """,
            output_key="content_validation_result",
            after_agent_callback=suppress_output_callback,
        )