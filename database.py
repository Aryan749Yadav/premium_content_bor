cat > database.py << 'EOF'
"""
MongoDB database operations
"""
from pymongo import MongoClient
from datetime import datetime
import config

class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None
        self.connect()
    
    def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(config.MONGODB_URI)
            self.db = self.client[config.DATABASE_NAME]
            print("✅ Connected to MongoDB")
            self.init_collections()
        except Exception as e:
            print(f"❌ MongoDB connection error: {e}")
            raise
    
    def init_collections(self):
        """Initialize collections with indexes"""
        # Premium users collection
        self.db.premium_users.create_index("user_id", unique=True)
        
        # Menu items collection
        self.db.menu_items.create_index("item_id", unique=True)
        self.db.menu_items.create_index("parent_id")
        
        # Access logs collection
        self.db.access_logs.create_index("scheduled_deletion")
        self.db.access_logs.create_index([("user_id", 1), ("access_time", -1)])
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
    
    # Premium Users Methods
    def add_premium_user(self, user_id, added_by):
        """Add user to premium list"""
        try:
            user_data = {
                "user_id": user_id,
                "added_by": added_by,
                "added_date": datetime.now(),
                "is_active": True
            }
            result = self.db.premium_users.update_one(
                {"user_id": user_id},
                {"$set": user_data},
                upsert=True
            )
            return result.acknowledged
        except Exception as e:
            print(f"Error adding premium user: {e}")
            return False
    
    def remove_premium_user(self, user_id):
        """Remove user from premium list"""
        try:
            result = self.db.premium_users.update_one(
                {"user_id": user_id},
                {"$set": {"is_active": False}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error removing premium user: {e}")
            return False
    
    def is_premium(self, user_id):
        """Check if user has premium access"""
        user = self.db.premium_users.find_one({
            "user_id": user_id,
            "is_active": True
        })
        return user is not None
    
    def list_premium_users(self):
        """Get all active premium users"""
        users = list(self.db.premium_users.find(
            {"is_active": True},
            {"_id": 0, "user_id": 1, "added_by": 1, "added_date": 1}
        ))
        return users
    
    # Menu Items Methods
    def add_menu_item(self, item_data):
        """Add new menu item"""
        try:
            result = self.db.menu_items.insert_one(item_data)
            return result.inserted_id
        except Exception as e:
            print(f"Error adding menu item: {e}")
            return None
    
    def get_menu_items(self, parent_id=0):
        """Get all items in a folder"""
        items = list(self.db.menu_items.find(
            {"parent_id": parent_id},
            {"_id": 0}
        ).sort("sort_order", 1))
        return items
    
    def get_menu_item(self, item_id):
        """Get specific menu item"""
        item = self.db.menu_items.find_one(
            {"item_id": item_id},
            {"_id": 0}
        )
        return item
    
    def update_menu_item(self, item_id, update_data):
        """Update menu item"""
        result = self.db.menu_items.update_one(
            {"item_id": item_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    def delete_menu_item(self, item_id):
        """Delete menu item"""
        result = self.db.menu_items.delete_one({"item_id": item_id})
        return result.deleted_count > 0
    
    # Access Logs Methods
    def log_access(self, user_id, item_id, message_id, scheduled_deletion):
        """Log user access"""
        log_data = {
            "user_id": user_id,
            "item_id": item_id,
            "message_id": message_id,
            "access_time": datetime.now(),
            "scheduled_deletion": scheduled_deletion
        }
        self.db.access_logs.insert_one(log_data)
    
    def get_expired_logs(self):
        """Get expired access logs"""
        expired = list(self.db.access_logs.find({
            "scheduled_deletion": {"$lte": datetime.now()}
        }))
        return expired
    
    def delete_log(self, log_id):
        """Delete access log"""
        self.db.access_logs.delete_one({"_id": log_id})
EOF
