"""
Premium user authentication and management
"""
from database import Database
import config

class UserAuth:
    def __init__(self):
        self.db = Database()
    
    def is_premium(self, user_id):
        """Check if user has premium access"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT is_active FROM premium_users WHERE user_id = ?",
            (user_id,)
        )
        result = cursor.fetchone()
        conn.close()
        
        return result is not None and result[0] == 1
    
    def is_admin(self, user_id):
        """Check if user is admin"""
        return user_id in config.ADMIN_IDS
    
    def add_premium_user(self, user_id, added_by):
        """Add user to premium list"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO premium_users (user_id, added_by, is_active)
                VALUES (?, ?, 1)
            ''', (user_id, added_by))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding premium user: {e}")
            return False
        finally:
            conn.close()
    
    def remove_premium_user(self, user_id):
        """Remove user from premium list"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "UPDATE premium_users SET is_active = 0 WHERE user_id = ?",
                (user_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error removing premium user: {e}")
            return False
        finally:
            conn.close()
    
    def list_premium_users(self):
        """Get all active premium users"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT user_id, added_by, added_date FROM premium_users WHERE is_active = 1"
        )
        users = cursor.fetchall()
        conn.close()
        
        return users
