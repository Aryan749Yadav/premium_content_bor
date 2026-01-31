"""
Database initialization and connection management
"""
import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path="data/database.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Premium users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS premium_users (
                user_id INTEGER PRIMARY KEY,
                added_by INTEGER,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Menu structure table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS menu_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER DEFAULT 0,
                item_type TEXT CHECK(item_type IN ('button', 'folder', 'url')),
                display_name TEXT,
                content_data TEXT,  -- JSON string
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES menu_items(item_id)
            )
        ''')
        
        # Access logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item_id INTEGER,
                access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message_id INTEGER,  -- Telegram message ID of forwarded content
                scheduled_deletion TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES premium_users(user_id),
                FOREIGN KEY (item_id) REFERENCES menu_items(item_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
