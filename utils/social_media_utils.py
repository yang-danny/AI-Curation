from typing import Dict, List, Any
from urllib.parse import urlparse
import re
from datetime import datetime, timedelta

def extract_platform_from_url(url: str) -> str:
    """
    Extract the social media platform from a URL.
    
    Args:
        url: Social media profile URL
        
    Returns:
        Platform name (facebook, twitter, linkedin, etc.)
    """
    url_lower = url.lower()
    
    if 'facebook.com' in url_lower or 'fb.com' in url_lower:
        return 'facebook'
    elif 'twitter.com' in url_lower or 'x.com' in url_lower:
        return 'twitter'
    elif 'linkedin.com' in url_lower:
        return 'linkedin'
    elif 'instagram.com' in url_lower:
        return 'instagram'
    elif 'youtube.com' in url_lower:
        return 'youtube'
    else:
        return 'unknown'

def extract_account_name(url: str) -> str:
    """
    Extract the account name from a social media URL.
    
    Args:
        url: Social media profile URL
        
    Returns:
        Account name or handle
    """
    try:
        # Remove trailing slashes
        url = url.rstrip('/')
        
        # Parse URL
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        
        if not path_parts:
            return parsed.netloc
        
        # For most social media, the account name is the last part
        # Handle special cases
        if 'linkedin.com/company/' in url:
            # LinkedIn company pages
            return path_parts[-1] if path_parts else 'unknown'
        elif 'facebook.com' in url or 'twitter.com' in url or 'x.com' in url:
            return path_parts[0] if path_parts else 'unknown'
        else:
            return path_parts[-1] if path_parts else 'unknown'
            
    except Exception as e:
        return 'unknown'

def categorize_post_content(content: str) -> List[str]:
    """
    Categorize post content based on keywords and content analysis.
    
    Args:
        content: Post content text
        
    Returns:
        List of categories
    """
    categories = []
    content_lower = content.lower()
    
    # Define category keywords
    category_keywords = {
        'product_launch': ['launch', 'introducing', 'new product', 'release', 'unveil'],
        'announcement': ['announce', 'announcement', 'news', 'update'],
        'tutorial': ['how to', 'tutorial', 'guide', 'learn', 'step by step'],
        'event': ['event', 'conference', 'webinar', 'workshop', 'summit'],
        'case_study': ['case study', 'success story', 'customer story'],
        'technical': ['api', 'sdk', 'code', 'developer', 'technical', 'programming'],
        'community': ['community', 'join us', 'follow', 'subscribe'],
        'thought_leadership': ['future', 'trends', 'innovation', 'vision', 'perspective'],
    }
    
    for category, keywords in category_keywords.items():
        if any(keyword in content_lower for keyword in keywords):
            categories.append(category)
    
    return categories if categories else ['general']

def extract_engagement_metrics(post_data: Dict[str, Any]) -> Dict[str, int]:
    """
    Extract engagement metrics from post data.
    
    Args:
        post_data: Dictionary containing post information
        
    Returns:
        Dictionary with engagement metrics
    """
    metrics = {
        'likes': 0,
        'shares': 0,
        'comments': 0,
        'views': 0,
    }
    
    # Try to extract from various possible fields
    text = str(post_data).lower()
    
    # Simple pattern matching (this would be more sophisticated with actual data)
    patterns = {
        'likes': r'(\d+)\s*likes?',
        'shares': r'(\d+)\s*shares?',
        'comments': r'(\d+)\s*comments?',
        'views': r'(\d+)\s*views?',
    }
    
    for metric, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            metrics[metric] = int(match.group(1))
    
    return metrics

def format_post_data(post: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format raw post data into a standardized structure.
    
    Args:
        post: Raw post data
        
    Returns:
        Formatted post dictionary
    """
    formatted = {
        'platform': post.get('platform', 'unknown'),
        'account': post.get('account', 'unknown'),
        'account_url': post.get('account_url', ''),
        'post_url': post.get('post_url', post.get('url', '')),
        'content': post.get('content', post.get('text', '')),
        'timestamp': post.get('timestamp', post.get('date', datetime.now().isoformat())),
        'categories': categorize_post_content(post.get('content', '')),
        'engagement': extract_engagement_metrics(post),
        'media_type': post.get('media_type', 'text'),
        'hashtags': extract_hashtags(post.get('content', '')),
        'mentions': extract_mentions(post.get('content', '')),
    }
    
    return formatted

def extract_hashtags(content: str) -> List[str]:
    """
    Extract hashtags from content.
    
    Args:
        content: Post content
        
    Returns:
        List of hashtags (without # symbol)
    """
    return re.findall(r'#(\w+)', content)

def extract_mentions(content: str) -> List[str]:
    """
    Extract mentions from content.
    
    Args:
        content: Post content
        
    Returns:
        List of mentions (without @ symbol)
    """
    return re.findall(r'@(\w+)', content)

def is_recent_post(timestamp: str, days: int = 7) -> bool:
    """
    Check if a post is recent (within specified days).
    
    Args:
        timestamp: Post timestamp (ISO format)
        days: Number of days to consider as recent
        
    Returns:
        True if post is recent, False otherwise
    """
    try:
        post_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        cutoff_date = datetime.now() - timedelta(days=days)
        return post_date >= cutoff_date
    except:
        return True  # If we can't parse, assume it's recent

def filter_posts_by_relevance(posts: List[Dict[str, Any]], keywords: List[str]) -> List[Dict[str, Any]]:
    """
    Filter posts by relevance based on keywords.
    
    Args:
        posts: List of post dictionaries
        keywords: List of keywords to match
        
    Returns:
        Filtered list of relevant posts
    """
    relevant_posts = []
    
    for post in posts:
        content = post.get('content', '').lower()
        
        # Check if any keyword appears in content
        if any(keyword.lower() in content for keyword in keywords):
            relevant_posts.append(post)
            continue
        
        # Check categories
        categories = post.get('categories', [])
        if any(cat in ['product_launch', 'announcement', 'technical'] for cat in categories):
            relevant_posts.append(post)
    
    return relevant_posts