"""
Content forwarding and automatic deletion system
"""
import asyncio
from datetime import datetime, timedelta
from database import MongoDB
import config

class ContentDelivery:
    def __init__(self, bot):
        self.bot = bot
        self.db = MongoDB()
    
    async def forward_content(self, user_id, channel_id, message_id):
        """Forward content from database channel to user"""
        try:
            # Forward the message
            forwarded_msg = await self.bot.forward_message(
                chat_id=user_id,
                from_chat_id=channel_id,
                message_id=message_id
            )
            
            # Schedule deletion
            deletion_time = datetime.now() + timedelta(seconds=config.CONTENT_EXPIRY_TIME)
            
            # Log the access (no item_id in this case, use -1)
            self.db.log_access(user_id, -1, forwarded_msg.message_id, deletion_time)
            
            # Schedule deletion
            await self.schedule_deletion(user_id, forwarded_msg.message_id, deletion_time)
            
            return True
        except Exception as e:
            print(f"Error forwarding content: {e}")
            return False
    
    async def schedule_deletion(self, user_id, message_id, deletion_time):
        """Schedule message deletion after expiry time"""
        wait_time = (deletion_time - datetime.now()).total_seconds()
        if wait_time > 0:
            await asyncio.sleep(wait_time)
        
        try:
            await self.bot.delete_message(chat_id=user_id, message_id=message_id)
            print(f"Deleted message {message_id} for user {user_id}")
        except Exception as e:
            print(f"Error deleting message: {e}")
    
    async def cleanup_expired_content(self):
        """Clean up expired content from database"""
        expired_logs = self.db.get_expired_logs()
        
        for log in expired_logs:
            user_id = log.get("user_id")
            message_id = log.get("message_id")
            
            if user_id and message_id:
                try:
                    await self.bot.delete_message(chat_id=user_id, message_id=message_id)
                except Exception as e:
                    print(f"Error in cleanup for message {message_id}: {e}")
            
            # Remove from logs
            self.db.delete_log(log["_id"])
