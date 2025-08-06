"""Utility functions for TeleScout."""

from datetime import datetime


def format_datetime(dt: datetime) -> str:
    """
    Format datetime to human-readable format like '5th August 2025 5:59PM'.
    
    Args:
        dt: datetime object to format
        
    Returns:
        Formatted datetime string
    """
    # Get day with ordinal suffix
    day = dt.day
    if 10 <= day <= 13:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    
    # Format the full date
    return dt.strftime(f"{day}{suffix} %B %Y %I:%M%p")


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f} hours"
    else:
        days = seconds / 86400
        return f"{days:.1f} days"


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length with optional suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix