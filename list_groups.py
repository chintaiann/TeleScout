#!/usr/bin/env python3
"""Helper script to list your groups and their IDs."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import load_config
from src.logger import setup_logging
from telethon import TelegramClient
from telethon.tl.types import Chat, Channel

async def list_groups():
    """List all groups you're a member of."""
    setup_logging("INFO", False)
    
    config = load_config()
    client = TelegramClient(
        config.telegram.session_name,
        config.telegram.api_id,
        config.telegram.api_hash
    )
    
    try:
        await client.start(phone=config.telegram.phone_number)
        
        print("\n📋 Your Groups and Channels:")
        print("=" * 60)
        
        async for dialog in client.iter_dialogs():
            entity = dialog.entity
            
            # Check if it's a group or channel
            if isinstance(entity, (Chat, Channel)):
                entity_type = "Channel" if getattr(entity, 'broadcast', False) else "Group"
                
                # Get title
                title = getattr(entity, 'title', 'Unknown')
                
                # Get username if available
                username = getattr(entity, 'username', None)
                username_str = f"@{username}" if username else "No username"
                
                print(f"\n{entity_type}: {title}")
                print(f"  ID: {entity.id}")
                print(f"  Username: {username_str}")
                print(f"  Config format: {entity.id}")
        
        print("\n" + "=" * 60)
        print("💡 Copy the ID from 'Config format' line for the group you want to use")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(list_groups())