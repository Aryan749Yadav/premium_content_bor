"""
Utility functions and helpers
"""
import logging
from datetime import datetime

def setup_logging():
    """Configure logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/bot.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def parse_telegram_link(link):
    """
    Parse Telegram channel link to extract channel ID and message ID
    Format: https://t.me/c/channel_id/message_id
    """
    try:
        parts = link.split('/')
        if len(parts) >= 2:
            # Extract channel ID (negative for channels)
            channel_part = parts[-2]
            message_id = int(parts[-1])
            
            # Convert to integer channel ID
            if channel_part.startswith('100'):
                channel_id = int(channel_part)
                # Make it negative for private channels
                if channel_id > 0:
                    channel_id = -channel_id
            else:
                channel_id = int(channel_part)
            
            return channel_id, message_id
    except Exception as e:
        print(f"Error parsing link: {e}")
    
    return None, None

def format_user_info(user):
    """Format user information for logging"""
    return f"ID: {user.id}, Username: @{user.username}, Name: {user.first_name} {user.last_name or ''}"
