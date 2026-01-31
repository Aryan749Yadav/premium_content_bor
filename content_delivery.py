"""
Content forwarding and automatic deletion system
"""
import asyncio
from datetime import datetime, timedelta
from database import Database
import config

class ContentDelivery:
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
    
    async def forward_content(self, user_id, channel_id, message_id):
        """Forward content from database channel to user"""
        try:
            # Forward the message
            forwarded_msg = await self.bot.forward_message(
                chat_id=user_id,
                from_chat_id=channel_id,
                message_id=message_id
            )
            
            # Log the access
            self.log_access(user_id, forwarded_msg.message_id)
            
            # Schedule deletion
            await self.schedule_deletion(user_id, forwarded_msg.message_id)
            
            return True
        except Exception as e:
            print(f"Error forwarding content: {e}")
            return False
    
    def log_access(self, user_id, message_id):
        """Log user access for tracking"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        deletion_time = datetime.now() + timedelta(seconds=config.CONTENT_EXPIRY_TIME)
        
        cursor.execute('''
            INSERT INTO access_logs (user_id, message_id, scheduled_deletion)
            VALUES (?, ?, ?)
        ''', (user_id, message_id, deletion_time))
        
        conn.commit()
        conn.close()
    
    async def schedule_deletion(self, user_id, message_id):
        """Schedule message deletion after expiry time"""
        await asyncio.sleep(config.CONTENT_EXPIRY_TIME)
        
        try:
            await self.bot.delete_message(chat_id=user_id, message_id=message_id)
            print(f"Deleted message {message_id} for user {user_id}")
        except Exception as e:
            print(f"Error deleting message: {e}")
    
    async def cleanup_expired_content(self):
        """Clean up expired content from database"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT log_id, user_id, message_id FROM access_logs WHERE scheduled_deletion <= datetime('now')"
        )
        
        expired_logs = cursor.fetchall()
        
        for log_id, user_id, message_id in expired_logs:
            try:
                await self.bot.delete_message(chat_id=user_id, message_id=message_id)
            except Exception as e:
                print(f"Error in cleanup for message {message_id}: {e}")
            
            # Remove from logs
            cursor.execute("DELETE FROM access_logs WHERE log_id = ?", (log_id,))
        
        conn.commit()
        conn.close()
