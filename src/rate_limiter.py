"""Rate limiting functionality for TeleScout security."""

import time
from collections import defaultdict, deque
from typing import Dict, Deque
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Security rate limiter to prevent message flooding."""
    
    def __init__(self, max_per_hour: int, max_per_channel_per_hour: int):
        """Initialize rate limiter with hourly limits."""
        self.max_per_hour = max_per_hour
        self.max_per_channel_per_hour = max_per_channel_per_hour
        
        # Track message timestamps
        self.global_messages: Deque[float] = deque()
        self.channel_messages: Dict[int, Deque[float]] = defaultdict(deque)
        
        logger.info(f"Rate limiter initialized: {max_per_hour} msgs/hour globally, "
                   f"{max_per_channel_per_hour} msgs/hour per channel")
    
    def _cleanup_old_messages(self, message_queue: Deque[float], current_time: float) -> None:
        """Remove messages older than 1 hour."""
        hour_ago = current_time - 3600  # 1 hour in seconds
        while message_queue and message_queue[0] < hour_ago:
            message_queue.popleft()
    
    def can_send_message(self, channel_id: int = None) -> bool:
        """
        Check if a message can be sent without hitting rate limits.
        
        Args:
            channel_id: Optional channel ID for per-channel limiting
            
        Returns:
            True if message can be sent, False if rate limited
        """
        current_time = time.time()
        
        # Clean up old messages
        self._cleanup_old_messages(self.global_messages, current_time)
        
        # Check global rate limit
        if len(self.global_messages) >= self.max_per_hour:
            logger.warning(f"Global rate limit exceeded: {len(self.global_messages)}/{self.max_per_hour} messages in last hour")
            return False
        
        # Check per-channel rate limit if channel_id provided
        if channel_id is not None:
            channel_queue = self.channel_messages[channel_id]
            self._cleanup_old_messages(channel_queue, current_time)
            
            if len(channel_queue) >= self.max_per_channel_per_hour:
                logger.warning(f"Channel {channel_id} rate limit exceeded: "
                             f"{len(channel_queue)}/{self.max_per_channel_per_hour} messages in last hour")
                return False
        
        return True
    
    def record_message(self, channel_id: int = None) -> None:
        """
        Record that a message was sent.
        
        Args:
            channel_id: Optional channel ID for per-channel tracking
        """
        current_time = time.time()
        
        # Record globally
        self.global_messages.append(current_time)
        
        # Record per-channel if channel_id provided
        if channel_id is not None:
            self.channel_messages[channel_id].append(current_time)
        
        logger.debug(f"Message recorded. Global: {len(self.global_messages)}, "
                    f"Channel {channel_id}: {len(self.channel_messages.get(channel_id, []))}")
    
    def get_status(self) -> dict:
        """Get current rate limiting status."""
        current_time = time.time()
        
        # Clean up old messages
        self._cleanup_old_messages(self.global_messages, current_time)
        
        # Clean up per-channel messages
        for channel_queue in self.channel_messages.values():
            self._cleanup_old_messages(channel_queue, current_time)
        
        return {
            'global_messages_last_hour': len(self.global_messages),
            'global_limit': self.max_per_hour,
            'global_remaining': max(0, self.max_per_hour - len(self.global_messages)),
            'channels_tracked': len(self.channel_messages),
            'per_channel_limit': self.max_per_channel_per_hour
        }