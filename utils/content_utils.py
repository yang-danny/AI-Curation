from typing import Dict, List, Any
import re

def count_words(text: str) -> int:
    """Count words in text"""
    return len(text.split())

def estimate_reading_time(text: str, words_per_minute: int = 200) -> int:
    """Estimate reading time in minutes"""
    word_count = count_words(text)
    return max(1, round(word_count / words_per_minute))

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract potential keywords from text"""
    # Remove common words (simple approach)
    common_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
        'those', 'it', 'its', 'as', 'we', 'our', 'their'
    }
    
    # Extract words
    words = re.findall(r'\b[a-z]{4,}\b', text.lower())
    
    # Filter and count
    from collections import Counter
    filtered_words = [w for w in words if w not in common_words]
    keyword_counts = Counter(filtered_words)
    
    return [word for word, count in keyword_counts.most_common(max_keywords)]

def generate_seo_metadata(title: str, content: str) -> Dict[str, str]:
    """Generate SEO metadata from content"""
    # Extract first paragraph for description
    paragraphs = content.split('\n\n')
    first_para = paragraphs[0] if paragraphs else content[:160]
    
    # Clean and truncate description
    description = re.sub(r'[#*`\[\]]', '', first_para)
    description = ' '.join(description.split())[:155] + "..."
    
    # Extract keywords
    keywords = extract_keywords(content, max_keywords=10)
    
    return {
        'title': title[:60],
        'description': description,
        'keywords': ', '.join(keywords[:5]),
        'og_title': title,
        'og_description': description,
    }

def format_markdown(content: str) -> str:
    """Clean and format markdown content"""
    # Remove excessive blank lines
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # Ensure proper spacing around headings
    content = re.sub(r'([^\n])\n(#{1,6} )', r'\1\n\n\2', content)
    content = re.sub(r'(#{1,6} .+)\n([^\n])', r'\1\n\n\2', content)
    
    # Ensure proper list formatting
    content = re.sub(r'([^\n])\n([*-] )', r'\1\n\n\2', content)
    
    return content.strip()

def add_table_of_contents(content: str) -> str:
    """Generate and add table of contents to content"""
    # Extract headings
    headings = re.findall(r'^(#{2,3}) (.+)$', content, re.MULTILINE)
    
    if not headings:
        return content
    
    toc = "\n## Table of Contents\n\n"
    
    for level, title in headings:
        indent = "  " * (len(level) - 2)
        anchor = title.lower().replace(' ', '-').replace('[^a-z0-9-]', '')
        toc += f"{indent}- [{title}](#{anchor})\n"
    
    toc += "\n---\n\n"
    
    # Insert TOC after first heading
    parts = content.split('\n', 1)
    if len(parts) == 2:
        return parts[0] + '\n\n' + toc + parts[1]
    return toc + content

def split_into_sections(content: str) -> List[Dict[str, str]]:
    """Split content into sections based on headings"""
    sections = []
    current_section = {"heading": "Introduction", "content": ""}
    
    lines = content.split('\n')
    
    for line in lines:
        heading_match = re.match(r'^(#{1,6}) (.+)$', line)
        
        if heading_match:
            if current_section["content"]:
                sections.append(current_section)
            
            level = len(heading_match.group(1))
            title = heading_match.group(2)
            current_section = {
                "heading": title,
                "level": level,
                "content": ""
            }
        else:
            current_section["content"] += line + '\n'
    
    if current_section["content"]:
        sections.append(current_section)
    
    return sections

def add_call_to_action(content: str, cta_type: str = "engagement") -> str:
    """Add call-to-action to content"""
    ctas = {
        "engagement": """
---

**💬 Join the Conversation**

What are your thoughts on this? Share your perspective in the comments below or reach out to us on social media.
""",
        "newsletter": """
---

**📧 Stay Updated**

Subscribe to our newsletter to receive the latest tech insights and industry updates delivered to your inbox.

[Subscribe Now](#)
""",
        "resources": """
---

**📚 Learn More**

Explore our resource library for in-depth guides, tutorials, and case studies on this topic.

[View Resources](#)
""",
        "share": """
---

**🔗 Share This Article**

Found this helpful? Share it with your network to spread the knowledge!
"""
    }
    
    return content + "\n" + ctas.get(cta_type, ctas["engagement"])

def validate_content_quality(content: str) -> Dict[str, Any]:
    """Validate content quality and provide feedback"""
    issues = []
    warnings = []
    
    word_count = count_words(content)
    
    # Check length
    if word_count < 300:
        warnings.append("Content is quite short (< 300 words)")
    elif word_count > 2000:
        warnings.append("Content is quite long (> 2000 words) - consider breaking into series")
    
    # Check headings
    headings = re.findall(r'^#{1,6} .+$', content, re.MULTILINE)
    if len(headings) < 2:
        warnings.append("Consider adding more headings for better structure")
    
    # Check for links
    links = re.findall(r'\[.+\]\(.+\)', content)
    if len(links) < 2:
        warnings.append("Consider adding more links to sources or related content")
    
    # Check for lists
    lists = re.findall(r'^[*-] .+$', content, re.MULTILINE)
    if len(lists) < 3:
        warnings.append("Consider using bullet points for better readability")
    
    # Check paragraph length
    paragraphs = [p for p in content.split('\n\n') if p.strip() and not p.strip().startswith('#')]
    long_paragraphs = [p for p in paragraphs if count_words(p) > 150]
    if long_paragraphs:
        warnings.append(f"{len(long_paragraphs)} paragraphs are quite long (> 150 words)")
    
    return {
        'valid': len(issues) == 0,
        'word_count': word_count,
        'reading_time': estimate_reading_time(content),
        'heading_count': len(headings),
        'link_count': len(links),
        'issues': issues,
        'warnings': warnings,
    }