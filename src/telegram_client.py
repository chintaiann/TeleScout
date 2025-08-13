"""Telegram client functionality for TeleScout."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, AsyncGenerator
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from telethon.tl.types import Message, User, Channel

from .config import Config
from .keyword_matcher import KeywordMatcher
from .rate_limiter import RateLimiter
from .security import secure_session_files
from .utils import format_datetime

logger = logging.getLogger(__name__)


class TeleScoutClient:
    """Main Telegram client for monitoring channels."""
    
    def __init__(self, config: Config):
        """Initialize the TeleScout client."""
        self.config = config
        self.keyword_matcher = KeywordMatcher(config.keywords)
        self.rate_limiter = RateLimiter(
            config.max_messages_per_hour,
            config.max_messages_per_channel_per_hour
        )
        self.client = TelegramClient(
            config.telegram.session_name,
            config.telegram.api_id,
            config.telegram.api_hash
        )
        self.target_user = None
        self.monitored_channels = []
        self._last_forward_time = {}
        self._forwarded_messages = set()  # Track message IDs to prevent duplicates
        self._max_tracked_messages = 10000  # Limit memory usage
        self.on_message_forwarded = None  # Callback for when messages are forwarded
    
    async def start(self):
        """Start the Telegram client and authenticate."""
        logger.info("Starting TeleScout client...")
        
        await self.client.start(phone=self.config.telegram.phone_number)
        
        # Handle 2FA if needed
        if not await self.client.is_user_authorized():
            try:
                await self.client.send_code_request(self.config.telegram.phone_number)
                code = input("Enter the code you received: ")
                await self.client.sign_in(self.config.telegram.phone_number, code)
            except SessionPasswordNeededError:
                password = input("Enter your 2FA password: ")
                await self.client.sign_in(password=password)
        
        # Get target user/group
        try:
            self.target_user = await self.client.get_entity(self.config.forward_to_user_id)
            
            # Get display name based on entity type
            if hasattr(self.target_user, 'first_name'):
                display_name = self.target_user.first_name
                entity_type = "User"
            elif hasattr(self.target_user, 'title'):
                display_name = self.target_user.title
                entity_type = "Group/Channel"
            else:
                display_name = str(self.target_user.id)
                entity_type = "Entity"
            
            logger.info(f"Target {entity_type.lower()} found: {display_name} (ID: {self.target_user.id})")
            
            # Verify this is actually you by getting your own info
            me = await self.client.get_me()
            logger.info(f"Authenticated as: {me.first_name} (ID: {me.id})")
            
            if self.target_user.id == me.id:
                logger.info("✓ Target is yourself - messages will be sent to 'Saved Messages'")
            else:
                logger.info(f"✓ Target is {entity_type.lower()} '{display_name}' - messages will be sent there")
                
        except Exception as e:
            logger.error(f"Could not find target entity with ID {self.config.forward_to_user_id}: {e}")
            raise
        
        # Resolve channel entities
        await self._resolve_channels()
        
        # Security: Secure session files after authentication
        secure_session_files()
        
        logger.info("TeleScout client started successfully!")
    
    async def _resolve_channels(self):
        """Resolve channel usernames/IDs to entities."""
        self.monitored_channels = []
        
        for channel_identifier in self.config.channels:
            try:
                entity = await self.client.get_entity(channel_identifier)
                self.monitored_channels.append(entity)
                
                if hasattr(entity, 'title'):
                    logger.info(f"Monitoring channel: {entity.title} ({channel_identifier})")
                else:
                    logger.info(f"Monitoring channel: {channel_identifier}")
                    
            except Exception as e:
                logger.error(f"Could not resolve channel {channel_identifier}: {e}")
        
        if not self.monitored_channels:
            raise ValueError("No valid channels found to monitor")
    
    async def scan_historical_messages(self):
        """Scan historical messages in monitored channels."""
        if not self.config.time_window_hours:
            logger.info("No time window specified, skipping historical scan")
            return
        
        logger.info(f"Scanning historical messages from last {self.config.time_window_hours} hours...")
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=self.config.time_window_hours)
        logger.debug(f"Cutoff time: {format_datetime(cutoff_time)}")
        total_processed = 0
        total_matched = 0
        
        for channel in self.monitored_channels:
            channel_processed = 0
            channel_matched = 0
            
            try:
                async for message in self.client.iter_messages(
                    channel,
                    offset_date=cutoff_time,
                    reverse=True
                ):
                    if message.date < cutoff_time:
                        continue
                    
                    channel_processed += 1
                    
                    if await self._process_message(message, is_historical=True):
                        channel_matched += 1
                        await asyncio.sleep(self.config.forward_delay)
                
                channel_name = getattr(channel, 'title', str(channel.id))
                logger.info(f"Channel {channel_name}: {channel_processed} messages processed, {channel_matched} matches")
                
                total_processed += channel_processed
                total_matched += channel_matched
                
            except Exception as e:
                logger.error(f"Error scanning historical messages for {channel}: {e}")
        
        logger.info(f"Historical scan complete: {total_processed} messages processed, {total_matched} matches")
    
    async def start_monitoring(self):
        """Start real-time monitoring of channels."""
        logger.info("Starting real-time monitoring...")
        
        @self.client.on(events.NewMessage(chats=self.monitored_channels))
        async def handle_new_message(event):
            await self._process_message(event.message, is_historical=False)
        
        logger.info("Real-time monitoring active. Press Ctrl+C to stop.")
        
        try:
            await self.client.run_until_disconnected()
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
    
    async def _process_message(self, message: Message, is_historical: bool = False) -> bool:
        """
        Process a message and forward if it matches keywords.
        
        Returns:
            True if message was forwarded, False otherwise
        """
        if not message.text:
            return False
        
        # Check for keyword matches
        if not self.keyword_matcher.has_match(message.text):
            return False
        
        # Prevent duplicate forwards - check if we've already forwarded this message
        # Extract channel ID for both deduplication and rate limiting
        channel_id = message.peer_id.channel_id if hasattr(message.peer_id, 'channel_id') else None
        # For deduplication, we need a hashable identifier
        dedup_id = (channel_id, message.id)
        if dedup_id in self._forwarded_messages:
            logger.debug(f"Message already forwarded (Channel: {channel_id}, ID: {message.id}), skipping duplicate")
            return False
        
        # Security: Check message length
        if len(message.text) > self.config.max_message_length:
            logger.warning(f"Message too long ({len(message.text)} chars), truncating to {self.config.max_message_length}")
            # We'll truncate in the forwarding function
        
        # Rate limiting check (reuse the channel_id from above)
        current_time = datetime.now(timezone.utc)
        
        # Security: Check rate limits before processing
        if not self.rate_limiter.can_send_message(channel_id):
            logger.warning("Rate limit exceeded, skipping message forward")
            return False
        
        if channel_id in self._last_forward_time:
            time_since_last = (current_time - self._last_forward_time[channel_id]).total_seconds()
            if time_since_last < self.config.forward_delay:
                logger.debug(f"Basic rate limiting: skipping message (last forward {time_since_last:.1f}s ago)")
                return False
        
        try:
            await self._forward_message(message, is_historical)
            self._last_forward_time[channel_id] = current_time
            
            # Mark message as forwarded to prevent duplicates
            self._forwarded_messages.add(dedup_id)
            
            # Memory management: Limit the size of tracked messages
            if len(self._forwarded_messages) > self._max_tracked_messages:
                # Remove oldest half of entries (approximate)
                messages_list = list(self._forwarded_messages)
                self._forwarded_messages = set(messages_list[-self._max_tracked_messages//2:])
                logger.debug(f"Cleaned forwarded messages cache, now tracking {len(self._forwarded_messages)} messages")
            
            # Security: Record message in rate limiter
            self.rate_limiter.record_message(channel_id)
            
            # Call callback if provided (for GUI updates)
            if self.on_message_forwarded:
                self.on_message_forwarded()
            
            return True
        except FloodWaitError as e:
            logger.warning(f"Flood wait error: waiting {e.seconds} seconds")
            await asyncio.sleep(e.seconds)
            return False
        except Exception as e:
            logger.error(f"Error forwarding message: {e}")
            return False
    
    async def _forward_message(self, message: Message, is_historical: bool):
        """Forward a matching message to the target user."""
        # Get channel info
        channel = await self.client.get_entity(message.peer_id)
        channel_name = getattr(channel, 'title', 'Unknown Channel')
        
        # Get match summary
        match_summary = self.keyword_matcher.get_match_summary(message.text)
        
        # Format time in a more readable way
        formatted_time = format_datetime(message.date)
        
        # Create header
        header = f"🎯 **TeleScout Match**\n"
        header += f"📺 **Channel:** {channel_name}\n"
        header += f"⏰ **Time:** {formatted_time}\n"
        header += f"🔍 **{match_summary}**\n"
        
        if is_historical:
            header += "📚 **Historical message**\n"
        
        header += f"{'='*50}\n\n"
        
        # Security: Truncate message if too long
        message_text = message.text
        if len(message_text) > self.config.max_message_length:
            truncated_length = self.config.max_message_length - len(header) - 100  # Leave room for truncation notice
            if truncated_length > 0:
                message_text = message_text[:truncated_length] + "\n\n[Message truncated for security]"
            else:
                message_text = "[Message too long, content hidden for security]"
        
        # Combine header with original message
        full_message = header + message_text
        
        # Debug logging
        logger.debug(f"Attempting to send message to user ID: {self.target_user.id}")
        logger.debug(f"Target user info: {self.target_user}")
        logger.debug(f"Message length: {len(full_message)} chars")
        
        try:
            # Forward the message
            sent_message = await self.client.send_message(self.target_user, full_message)
            logger.info(f"Successfully forwarded message from {channel_name}: {match_summary}")
            logger.debug(f"Sent message ID: {sent_message.id}")
        except Exception as e:
            logger.error(f"Failed to forward message: {e}")
            raise
    
    async def stop(self):
        """Stop the client and clean up."""
        logger.info("Stopping TeleScout client...")
        await self.client.disconnect()