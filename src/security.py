"""Security utilities for TeleScout."""

import os
import stat
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def secure_session_files():
    """Set secure permissions on session files."""
    session_files = list(Path('.').glob('*.session*'))
    
    if not session_files:
        return
    
    logger.info("Securing session file permissions...")
    
    for session_file in session_files:
        try:
            # Set read/write for owner only (600)
            session_file.chmod(stat.S_IRUSR | stat.S_IWUSR)
            logger.debug(f"Set secure permissions on {session_file}")
        except Exception as e:
            logger.warning(f"Could not secure permissions for {session_file}: {e}")


def check_config_permissions():
    """Check if config files have secure permissions."""
    config_files = ['config.yaml', '.env']
    warnings = []
    
    for config_file in config_files:
        if not os.path.exists(config_file):
            continue
            
        file_stat = os.stat(config_file)
        mode = stat.filemode(file_stat.st_mode)
        
        # Check if file is readable by others
        if file_stat.st_mode & (stat.S_IRGRP | stat.S_IROTH):
            warnings.append(f"⚠️  {config_file} is readable by others ({mode})")
        
        # Check if file is writable by others
        if file_stat.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            warnings.append(f"⚠️  {config_file} is writable by others ({mode})")
    
    if warnings:
        logger.warning("Security warning - sensitive files have insecure permissions:")
        for warning in warnings:
            logger.warning(warning)
        logger.info("Run: chmod 600 config.yaml .env  # to fix permissions")


def sanitize_user_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent injection attacks."""
    if not isinstance(text, str):
        return str(text)[:max_length]
    
    # Remove potential control characters
    sanitized = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    
    # Truncate to max length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def validate_telegram_credentials(api_id: str, api_hash: str, phone: str) -> list:
    """Validate Telegram credentials format and return security warnings."""
    warnings = []
    
    # Check API ID format
    try:
        int(api_id)
    except ValueError:
        warnings.append("API ID should be a number")
    
    # Check API hash format  
    if not isinstance(api_hash, str) or len(api_hash) != 32:
        warnings.append("API hash should be a 32-character string")
    
    # Check phone format
    if not phone.startswith('+') or len(phone) < 10:
        warnings.append("Phone number should start with + and be at least 10 characters")
    
    # Check for placeholder values
    if str(api_id) == 'YOUR_API_ID_HERE' or api_id == 'your_api_id_here':
        warnings.append("API ID is still set to placeholder value")
    
    if api_hash == 'YOUR_API_HASH_HERE' or api_hash == 'your_api_hash_here':
        warnings.append("API hash is still set to placeholder value")
    
    return warnings