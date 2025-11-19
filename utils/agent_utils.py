from typing import Any, Dict

def suppress_output_callback(agent_name: str, output: Any) -> None:
    """
    Callback function to suppress or log agent output.
    
    Args:
        agent_name: Name of the agent
        output: Output from the agent
    """
    # You can add logging here if needed
    pass

def format_news_item(news_data: Dict[str, Any]) -> str:
    """
    Format a news item into a structured string.
    
    Args:
        news_data: Dictionary containing news information
        
    Returns:
        Formatted news item as string
    """
    formatted = f"""
## {news_data.get('title', 'No Title')}

**Source:** {news_data.get('source', 'Unknown')}
**Date:** {news_data.get('date', 'Unknown')}
**URL:** {news_data.get('url', 'N/A')}

**Summary:**
{news_data.get('summary', 'No summary available')}

**Keywords:** {', '.join(news_data.get('keywords', []))}

---
"""
    return formatted

def save_to_file(content: str, filename: str, directory: str = "output/content") -> str:
    """
    Save content to a file.
    
    Args:
        content: Content to save
        filename: Name of the file
        directory: Directory to save the file in
        
    Returns:
        Path to the saved file
    """
    import os
    from datetime import datetime
    
    # Create directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)
    
    # Add timestamp to filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(directory, f"{timestamp}_{filename}")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath