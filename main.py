#!/usr/bin/env python3
"""
TeleScout - Telegram Channel Monitor

A tool to monitor Telegram channels for specific keywords and forward matching messages.
"""

import asyncio
import argparse
import signal
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import load_config
from src.telegram_client import TeleScoutClient
from src.logger import setup_logging
from src.security import check_config_permissions, validate_telegram_credentials

import logging

logger = logging.getLogger(__name__)


def signal_handler(signum, frame):
    """Handle interrupt signals gracefully."""
    logger.info("Received interrupt signal, shutting down...")
    sys.exit(0)


async def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description="TeleScout - Telegram Channel Monitor")
    parser.add_argument(
        "--config", 
        default="config.yaml", 
        help="Path to configuration file (default: config.yaml)"
    )
    parser.add_argument(
        "--log-level", 
        choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
        default="INFO",
        help="Logging level (default: INFO)"
    )
    parser.add_argument(
        "--no-log-file", 
        action="store_true",
        help="Disable logging to file"
    )
    parser.add_argument(
        "--scan-only", 
        action="store_true",
        help="Only scan historical messages, don't start real-time monitoring"
    )
    parser.add_argument(
        "--no-historical", 
        action="store_true",
        help="Skip historical message scan, only do real-time monitoring"
    )
    parser.add_argument(
        "--gui", 
        action="store_true",
        help="Launch GUI interface instead of command line mode"
    )
    
    args = parser.parse_args()
    
    # Launch GUI if requested
    if args.gui:
        from src.gui import launch_gui
        launch_gui()
        return
    
    # Set up logging
    setup_logging(args.log_level, not args.no_log_file)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Security: Check file permissions
        check_config_permissions()
        
        # Load configuration
        logger.info("Loading configuration...")
        config = load_config(args.config)
        
        # Security: Validate credentials
        credential_warnings = validate_telegram_credentials(
            str(config.telegram.api_id),
            config.telegram.api_hash,
            config.telegram.phone_number
        )
        
        if credential_warnings:
            logger.error("Configuration security issues found:")
            for warning in credential_warnings:
                logger.error(f"  - {warning}")
            sys.exit(1)
        
        logger.info(f"Monitoring {len(config.channels)} channels for {len(config.keywords)} keywords")
        
        # Initialize client
        client = TeleScoutClient(config)
        
        # Start client
        await client.start()
        
        try:
            # Scan historical messages if requested
            if not args.no_historical:
                await client.scan_historical_messages()
            
            # Start real-time monitoring if not scan-only mode
            if not args.scan_only:
                await client.start_monitoring()
            else:
                logger.info("Scan-only mode: historical scan complete, exiting")
        
        finally:
            await client.stop()
    
    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        logger.info("Please copy config.example.yaml to config.yaml and configure it")
        sys.exit(1)
    
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())