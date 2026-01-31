"""
Menu structure management for MongoDB
"""
import json
from database import MongoDB
from bson import json_util

class MenuManager:
    def __init__(self):
        self.db = MongoDB()
        self.next_item_id = self._get_next_item_id()
    
    def _get_next_item_id(self):
        """Get next available item ID"""
        last_item = self.db.db.menu_items.find_one(
            {},
            sort=[("item_id", -1)]
        )
        return (last_item["item_id"] + 1) if last_item else 1
    
    def add_menu_item(self, parent_id, item_type, display_name, content_data):
        """Add new menu item"""
        item_data = {
            "item_id": self.next_item_id,
            "parent_id": parent_id,
            "item_type": item_type,
            "display_name": display_name,
            "content_data": content_data,
            "sort_order": self._get_next_sort_order(parent_id),
            "created_at": datetime.now()
        }
        
        result = self.db.add_menu_item(item_data)
        if result:
            self.next_item_id += 1
            return item_data["item_id"]
        return None
    
    def _get_next_sort_order(self, parent_id):
        """Get next sort order for parent folder"""
        items = self.db.get_menu_items(parent_id)
        return len(items) + 1
    
    def get_menu_items(self, parent_id=0):
        """Get all items in a folder"""
        return self.db.get_menu_items(parent_id)
    
    def get_menu_item(self, item_id):
        """Get specific menu item"""
        return self.db.get_menu_item(item_id)
    
    def delete_menu_item(self, item_id):
        """Delete menu item"""
        return self.db.delete_menu_item(item_id)
    
    def export_menu(self):
        """Export entire menu structure to JSON"""
        all_items = list(self.db.db.menu_items.find({}, {"_id": 0}))
        return json.dumps(all_items, default=json_util.default, indent=2)
    
    def import_menu(self, menu_json):
        """Import menu structure from JSON"""
        try:
            menu_data = json.loads(menu_json)
            
            # Clear existing menu
            self.db.db.menu_items.delete_many({})
            
            # Insert new items
            if menu_data:
                self.db.db.menu_items.insert_many(menu_data)
            
            # Update next_item_id
            self.next_item_id = self._get_next_item_id()
            
            return True
        except Exception as e:
            print(f"Error importing menu: {e}")
            return False
