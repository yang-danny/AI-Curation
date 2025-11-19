from config import config

class BrandVoice:
    """Brand voice and style guidelines"""
    
    VOICE_GUIDELINES = f"""
    **Brand Name:** {config.brand_name}
    **Tagline:** {config.brand_tagline}
    
    **Brand Voice Attributes:**
    - Tone: {config.brand_voice['tone']}
    - Style: {config.brand_voice['style']}
    - Perspective: {config.brand_voice['perspective']}
    
    **Target Audience:**
    - Primary: {config.target_audience['primary']}
    - Secondary: {config.target_audience['secondary']}
    - Knowledge Level: {config.target_audience['knowledge_level']}
    
    **Writing Guidelines:**
    1. Use clear, accessible language while maintaining technical accuracy
    2. Write in an enthusiastic but professional tone
    3. Focus on how technology impacts and benefits our community
    4. Include practical examples and real-world applications
    5. Maintain credibility through proper citations and sources
    6. Use active voice and strong verbs
    7. Break complex topics into digestible sections
    8. Include relevant technical details without overwhelming readers
    
    **Avoid:**
    - {config.brand_voice['avoid']}
    - Unsubstantiated claims or hype
    - Overly technical jargon without context
    - Passive voice when active is clearer
    
    **Content Structure Preferences:**
    - Start with a compelling hook or key insight
    - Use descriptive headings and subheadings
    - Include bullet points for easy scanning
    - Add relevant links and resources
    - End with clear takeaways or call-to-action
    """
    
    @staticmethod
    def get_voice_prompt() -> str:
        """Get the brand voice prompt for content generation"""
        return BrandVoice.VOICE_GUIDELINES
    
    @staticmethod
    def get_editing_guidelines() -> str:
        """Get guidelines for content editing and refinement"""
        return """
        **Editing Checklist:**
        1. ✓ Tone matches brand voice
        2. ✓ Technical accuracy verified
        3. ✓ Clear and scannable structure
        4. ✓ Proper grammar and punctuation
        5. ✓ Links and citations included
        6. ✓ SEO-friendly headings (if applicable)
        7. ✓ Call-to-action included (if applicable)
        8. ✓ Accessible to target audience
        9. ✓ No spelling errors or typos
        10. ✓ Consistent formatting
        """