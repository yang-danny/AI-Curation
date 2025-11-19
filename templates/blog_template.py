from datetime import datetime
from typing import Dict

class BlogTemplate:
    """Templates for blog post generation"""
    
    @staticmethod
    def get_structure_prompt() -> str:
        """Get blog post structure guidelines"""
        return """
        **Blog Post Structure:**
        
        1. **Title** (60-80 characters, SEO-friendly)
           - Clear and compelling
           - Include primary keyword
           - Promise value to reader
        
        2. **Meta Description** (150-160 characters)
           - Summarize the post
           - Include call-to-action
        
        3. **Introduction** (100-150 words)
           - Hook the reader
           - State the main topic/problem
           - Preview what they'll learn
        
        4. **Main Content** (organized in sections)
           - Use H2 and H3 headings
           - 2-4 main sections
           - Each section 150-300 words
           - Include examples, data, or quotes
           - Use bullet points and lists
        
        5. **Key Takeaways** (3-5 bullet points)
           - Summarize main insights
           - Action items when applicable
        
        6. **Conclusion** (50-100 words)
           - Reinforce main message
           - Look forward/broader implications
        
        7. **Call-to-Action**
           - Encourage engagement
           - Link to related content or resources
        
        8. **Metadata**
           - Tags/categories
           - Related topics
           - Publication date
        """
    
    @staticmethod
    def get_template(title: str = "", author: str = "Editorial Team") -> str:
        """Get a blog post template"""
        date = datetime.now().strftime("%Y-%m-%d")
        
        return f"""---
title: "{title}"
date: {date}
author: {author}
tags: []
categories: []
description: ""
---

# {title}

*Published on {date} by {author}*

## Introduction

[Hook and introduction here]

## [Main Section 1]

[Content here]

## [Main Section 2]

[Content here]

## Key Takeaways

- [Takeaway 1]
- [Takeaway 2]
- [Takeaway 3]

## Conclusion

[Conclusion here]

---

**What do you think?** [Call to action]

**Related Reading:**
- [Link 1]
- [Link 2]
"""

class SummaryTemplate:
    """Templates for news summaries"""
    
    @staticmethod
    def get_structure_prompt() -> str:
        """Get summary structure guidelines"""
        return """
        **News Summary Structure:**
        
        1. **Headline** (10-15 words)
           - Capture the key news
           - Action-oriented when possible
        
        2. **Summary** (50-100 words)
           - Who, what, when, where, why
           - Most important information first
           - Clear and concise
        
        3. **Key Points** (3-5 bullets)
           - Main details
           - Impact or significance
           - Related developments
        
        4. **Source & Link**
           - Original source
           - Publication date
           - Link to full article
        
        5. **Our Take** (optional, 30-50 words)
           - Brief analysis or context
           - Why it matters to our audience
        """
    
    @staticmethod
    def get_template() -> str:
        """Get a summary template"""
        return """## [Headline]

**Summary:** [Brief overview]

**Key Points:**
- [Point 1]
- [Point 2]
- [Point 3]

**Source:** [Source name] | [Date] | [Link]

**Our Take:** [Optional analysis]

---
"""

class SocialUpdateTemplate:
    """Templates for social media updates"""
    
    @staticmethod
    def get_platform_guidelines() -> Dict[str, str]:
        """Get platform-specific guidelines"""
        return {
            "twitter": """
                - 280 characters max
                - 1-2 hashtags
                - Include link
                - Engaging hook
            """,
            "linkedin": """
                - 150-300 characters ideal
                - Professional tone
                - Industry insights
                - Question or discussion prompt
            """,
            "facebook": """
                - 40-80 characters optimal
                - Visual/emotional appeal
                - Clear call-to-action
                - Link in first comment
            """
        }