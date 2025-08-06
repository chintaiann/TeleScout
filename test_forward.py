#!/usr/bin/env python3
"""Test script to verify message forwarding works."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import load_config
from src.telegram_client import TeleScoutClient
from src.logger import setup_logging

async def test_forward():
    """Test if forwarding works by sending a test message."""
    setup_logging("DEBUG", False)
    
    config = load_config()
    client = TeleScoutClient(config)
    
    try:
        await client.start()
        
        # Send a test message
        test_message = "🧪 **TeleScout Test Message**\n\nThis is a test to verify forwarding is working correctly.\nTimestamp: " + str(asyncio.get_event_loop().time())
        
        sent_message = await client.client.send_message(client.target_user, test_message)
        print(f"✅ Test message sent successfully! Message ID: {sent_message.id}")
        print(f"📱 Check your Telegram 'Saved Messages' for the test message")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    finally:
        await client.stop()

if __name__ == "__main__":
    asyncio.run(test_forward())