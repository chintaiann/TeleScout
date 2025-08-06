"""Keyword matching functionality for TeleScout."""

import re
from typing import List, Optional


class KeywordMatcher:
    """Handles keyword matching in messages."""
    
    def __init__(self, keywords: List[str]):
        """Initialize with a list of keywords to match."""
        self.keywords = [kw.lower().strip() for kw in keywords]
        
        # Pre-compile regex patterns for better performance
        self.patterns = []
        for keyword in self.keywords:
            # Escape special regex characters and create word boundary pattern
            escaped = re.escape(keyword)
            pattern = re.compile(rf'\b{escaped}\b', re.IGNORECASE | re.UNICODE)
            self.patterns.append((keyword, pattern))
    
    def find_matches(self, text: str) -> List[str]:
        """
        Find all matching keywords in the given text.
        
        Args:
            text: The text to search in
            
        Returns:
            List of matched keywords
        """
        if not text:
            return []
        
        matches = []
        text_lower = text.lower()
        
        for keyword, pattern in self.patterns:
            if pattern.search(text):
                matches.append(keyword)
        
        return matches
    
    def has_match(self, text: str) -> bool:
        """
        Check if text contains any of the keywords.
        
        Args:
            text: The text to search in
            
        Returns:
            True if any keyword is found, False otherwise
        """
        if not text:
            return False
        
        for _, pattern in self.patterns:
            if pattern.search(text):
                return True
        
        return False
    
    def get_match_summary(self, text: str) -> Optional[str]:
        """
        Get a summary of matches found in the text.
        
        Args:
            text: The text to search in
            
        Returns:
            Summary string of matches, or None if no matches
        """
        matches = self.find_matches(text)
        if not matches:
            return None
        
        if len(matches) == 1:
            return f"Keyword matched: '{matches[0]}'"
        else:
            keywords_list = ', '.join(f"'{m}'" for m in matches[:3])
            extra_count = f" (+{len(matches)-3} more)" if len(matches) > 3 else ""
            return f"Keywords matched: {keywords_list}{extra_count}"