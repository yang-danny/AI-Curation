from typing import Dict, List, Any
from datetime import datetime
from collections import Counter

def format_social_media_report(posts: List[Dict[str, Any]], accounts: Dict[str, List[str]]) -> str:
    """
    Format social media posts into a comprehensive Markdown report.
    
    Args:
        posts: List of formatted post dictionaries
        accounts: Dictionary of monitored accounts by platform
        
    Returns:
        Formatted Markdown report
    """
    report = f"""# Social Media Monitoring Report
*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

---

## 📊 Executive Summary

- **Total Posts Monitored**: {len(posts)}
- **Platforms Monitored**: {len(set(p['platform'] for p in posts))}
- **Accounts Tracked**: {len(set(p['account'] for p in posts))}
- **Time Period**: Last 7 days

---

## 🔥 Top Posts by Platform

"""
    
    # Group by platform
    by_platform = {}
    for post in posts:
        platform = post.get('platform', 'unknown')
        if platform not in by_platform:
            by_platform[platform] = []
        by_platform[platform].append(post)
    
    for platform, platform_posts in sorted(by_platform.items()):
        report += f"\n### {platform.title()}\n\n"
        
        # Sort by engagement (total of likes + shares + comments)
        sorted_posts = sorted(
            platform_posts,
            key=lambda p: sum(p.get('engagement', {}).values()),
            reverse=True
        )[:5]  # Top 5 per platform
        
        for i, post in enumerate(sorted_posts, 1):
            report += format_post_entry(post, index=i)
    
    # Add trending topics section
    report += "\n---\n\n## 📈 Trending Topics\n\n"
    report += generate_hashtag_analysis(posts)
    
    # Add category breakdown
    report += "\n---\n\n## 📁 Content Categories\n\n"
    report += generate_category_breakdown(posts)
    
    # Add account activity
    report += "\n---\n\n## 👥 Account Activity\n\n"
    report += generate_account_activity(posts)
    
    return report

def format_post_entry(post: Dict[str, Any], index: int = None) -> str:
    """
    Format a single post entry.
    
    Args:
        post: Post dictionary
        index: Optional index number
        
    Returns:
        Formatted post entry
    """
    prefix = f"{index}. " if index else "- "
    
    account = post.get('account', 'Unknown')
    content = post.get('content', '')[:200] + "..." if len(post.get('content', '')) > 200 else post.get('content', '')
    post_url = post.get('post_url', '#')
    timestamp = post.get('timestamp', 'Unknown date')
    
    # Format engagement
    engagement = post.get('engagement', {})
    engagement_str = f"👍 {engagement.get('likes', 0)} | 🔄 {engagement.get('shares', 0)} | 💬 {engagement.get('comments', 0)}"
    
    # Format categories
    categories = post.get('categories', [])
    categories_str = ', '.join(f"`{cat}`" for cat in categories[:3])
    
    entry = f"""{prefix}**{account}**
   - *{timestamp}*
   - {content}
   - {engagement_str}
   - Categories: {categories_str}
   - [View Post]({post_url})

"""
    return entry

def create_post_summary(post: Dict[str, Any]) -> str:
    """
    Create a concise summary of a post.
    
    Args:
        post: Post dictionary
        
    Returns:
        Concise summary string
    """
    account = post.get('account', 'Unknown')
    platform = post.get('platform', 'unknown').title()
    content = post.get('content', '')
    
    # Extract first sentence or first 100 characters
    summary = content.split('.')[0] if '.' in content else content[:100]
    
    return f"{account} on {platform}: {summary}"

def generate_hashtag_analysis(posts: List[Dict[str, Any]]) -> str:
    """
    Generate hashtag analysis from posts.
    
    Args:
        posts: List of post dictionaries
        
    Returns:
        Formatted hashtag analysis
    """
    all_hashtags = []
    for post in posts:
        all_hashtags.extend(post.get('hashtags', []))
    
    if not all_hashtags:
        return "*No hashtags found in monitored posts.*\n"
    
    # Count hashtags
    hashtag_counts = Counter(all_hashtags)
    top_hashtags = hashtag_counts.most_common(10)
    
    analysis = "**Top Hashtags:**\n\n"
    for hashtag, count in top_hashtags:
        bar = '█' * min(count, 20)  # Visual bar
        analysis += f"- #{hashtag}: {count} posts {bar}\n"
    
    return analysis + "\n"

def generate_category_breakdown(posts: List[Dict[str, Any]]) -> str:
    """
    Generate category breakdown.
    
    Args:
        posts: List of post dictionaries
        
    Returns:
        Formatted category breakdown
    """
    all_categories = []
    for post in posts:
        all_categories.extend(post.get('categories', []))
    
    if not all_categories:
        return "*No categories identified.*\n"
    
    category_counts = Counter(all_categories)
    
    breakdown = "| Category | Count | Percentage |\n"
    breakdown += "|----------|-------|------------|\n"
    
    total = len(all_categories)
    for category, count in category_counts.most_common():
        percentage = (count / total) * 100
        breakdown += f"| {category.replace('_', ' ').title()} | {count} | {percentage:.1f}% |\n"
    
    return breakdown + "\n"

def generate_account_activity(posts: List[Dict[str, Any]]) -> str:
    """
    Generate account activity summary.
    
    Args:
        posts: List of post dictionaries
        
    Returns:
        Formatted account activity
    """
    account_posts = {}
    
    for post in posts:
        account = post.get('account', 'Unknown')
        platform = post.get('platform', 'unknown')
        key = f"{account} ({platform})"
        
        if key not in account_posts:
            account_posts[key] = {
                'count': 0,
                'total_engagement': 0,
                'url': post.get('account_url', '')
            }
        
        account_posts[key]['count'] += 1
        engagement = post.get('engagement', {})
        account_posts[key]['total_engagement'] += sum(engagement.values())
    
    activity = "| Account | Platform | Posts | Total Engagement |\n"
    activity += "|---------|----------|-------|------------------|\n"
    
    # Sort by post count
    sorted_accounts = sorted(
        account_posts.items(),
        key=lambda x: x[1]['count'],
        reverse=True
    )
    
    for account_key, data in sorted_accounts:
        account_name = account_key.split(' (')[0]
        platform = account_key.split(' (')[1].rstrip(')')
        activity += f"| {account_name} | {platform.title()} | {data['count']} | {data['total_engagement']} |\n"
    
    return activity + "\n"