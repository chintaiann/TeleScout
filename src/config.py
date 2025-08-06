"""Configuration management for TeleScout."""

import os
import yaml
from typing import List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class TelegramConfig:
    """Telegram API configuration."""
    api_id: int
    api_hash: str
    phone_number: str
    session_name: str = "telescout_session"


@dataclass
class Config:
    """Main application configuration."""
    telegram: TelegramConfig
    forward_to_user_id: int
    channels: List[str]
    keywords: List[str]
    time_window_hours: Optional[int] = None
    forward_delay: int = 5
    max_messages_per_hour: int = 60  # Security: Limit messages per hour
    max_messages_per_channel_per_hour: int = 20  # Security: Per-channel limit
    max_message_length: int = 4000  # Security: Prevent extremely long messages


def load_config(config_path: str = "config.yaml") -> Config:
    """Load configuration from YAML file and environment variables."""
    load_dotenv()
    
    # Load from YAML file
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
    else:
        raise FileNotFoundError(f"Configuration file '{config_path}' not found. "
                              "Please copy config.example.yaml to config.yaml and configure it.")
    
    # Override with environment variables if available
    api_id = os.getenv('TELEGRAM_API_ID', config_data['telegram']['api_id'])
    api_hash = os.getenv('TELEGRAM_API_HASH', config_data['telegram']['api_hash'])
    phone_number = os.getenv('TELEGRAM_PHONE', config_data['telegram']['phone_number'])
    
    # Validate required fields
    if not api_id or api_id == 'YOUR_API_ID_HERE':
        raise ValueError("TELEGRAM_API_ID is required. Set it in .env file or config.yaml")
    if not api_hash or api_hash == 'YOUR_API_HASH_HERE':
        raise ValueError("TELEGRAM_API_HASH is required. Set it in .env file or config.yaml")
    if not phone_number or phone_number == '+1234567890':
        raise ValueError("TELEGRAM_PHONE is required. Set it in .env file or config.yaml")
    
    telegram_config = TelegramConfig(
        api_id=int(api_id),
        api_hash=str(api_hash),
        phone_number=str(phone_number),
        session_name=config_data['telegram'].get('session_name', 'telescout_session')
    )
    
    # Validate forward_to_user_id
    forward_to_user_id = config_data.get('forward_to_user_id')
    if not forward_to_user_id or forward_to_user_id == 'YOUR_USER_ID_HERE':
        raise ValueError("forward_to_user_id is required in config.yaml")
    
    # Validate channels and keywords
    channels = config_data.get('channels', [])
    if not channels:
        raise ValueError("At least one channel must be specified in config.yaml")
    
    keywords = config_data.get('keywords', [])
    if not keywords:
        raise ValueError("At least one keyword must be specified in config.yaml")
    
    # Security settings with safe defaults
    max_messages_per_hour = config_data.get('max_messages_per_hour', 60)
    max_messages_per_channel_per_hour = config_data.get('max_messages_per_channel_per_hour', 20)
    max_message_length = config_data.get('max_message_length', 4000)
    
    # Validate security limits
    if max_messages_per_hour > 200:
        raise ValueError("max_messages_per_hour cannot exceed 200 for security reasons")
    if max_messages_per_channel_per_hour > 50:
        raise ValueError("max_messages_per_channel_per_hour cannot exceed 50 for security reasons")
    if max_message_length > 10000:
        raise ValueError("max_message_length cannot exceed 10000 characters for security reasons")
    
    return Config(
        telegram=telegram_config,
        forward_to_user_id=int(forward_to_user_id),
        channels=channels,
        keywords=[kw.lower() for kw in keywords],  # Convert to lowercase for matching
        time_window_hours=config_data.get('time_window_hours'),
        forward_delay=config_data.get('forward_delay', 5),
        max_messages_per_hour=max_messages_per_hour,
        max_messages_per_channel_per_hour=max_messages_per_channel_per_hour,
        max_message_length=max_message_length
    )