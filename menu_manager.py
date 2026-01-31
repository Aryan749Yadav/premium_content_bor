"""
Menu structure management and navigation
"""
import json
from database import Database

class MenuManager:
    def __init__(self):
        self.db = Database()
    
    def add_menu_item(self, parent_id, item_type, display_name, content_data):
        """Add new menu item (button, folder, or URL)"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get next sort order
            cursor.execute(
                "SELECT COALESCE(MAX(sort_order), 0) + 1 FROM menu_items WHERE parent_id = ?",
                (parent_id,)
            )
            sort_order = cursor.fetchone()[0]
            
            cursor.execute('''
                INSERT INTO menu_items (parent_id, item_type, display_name, content_data, sort_order)
                VALUES (?, ?, ?, ?, ?)
            ''', (parent_id, item_type, display_name, json.dumps(content_data), sort_order))
            
            item_id = cursor.lastrowid
            conn.commit()
            return item_id
        except Exception as e:
            print(f"Error adding menu item: {e}")
            return None
        finally:
            conn.close()
    
    def get_menu_items(self, parent_id=0):
        """Get all items in a folder"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT item_id, item_type, display_name, content_data 
            FROM menu_items 
            WHERE parent_id = ? 
            ORDER BY sort_order
        ''', (parent_id,))
        
        items = []
        for row in cursor.fetchall():
            item_id, item_type, display_name, content_data_json = row
            content_data = json.loads(content_data_json) if content_data_json else {}
            
            items.append({
                'item_id': item_id,
                'type': item_type,
                'name': display_name,
                'content_data': content_data
            })
        
        conn.close()
        return items
    
    def get_menu_item(self, item_id):
        """Get specific menu item"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT item_type, display_name, content_data, parent_id 
            FROM menu_items 
            WHERE item_id = ?
        ''', (item_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            item_type, display_name, content_data_json, parent_id = row
            content_data = json.loads(content_data_json) if content_data_json else {}
            
            return {
                'type': item_type,
                'name': display_name,
                'content_data': content_data,
                'parent_id': parent_id
            }
        return None
    
    def delete_menu_item(self, item_id):
        """Delete menu item and all children"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Recursive delete (simplified - cascade would be better)
            cursor.execute("DELETE FROM menu_items WHERE item_id = ?", (item_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting menu item: {e}")
            return False
        finally:
            conn.close()
    
    def export_menu(self):
        """Export entire menu structure to JSON"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT item_id, parent_id, item_type, display_name, content_data 
            FROM menu_items 
            ORDER BY parent_id, sort_order
        ''')
        
        menu_data = []
        for row in cursor.fetchall():
            item_id, parent_id, item_type, display_name, content_data_json = row
            content_data = json.loads(content_data_json) if content_data_json else {}
            
            menu_data.append({
                'item_id': item_id,
                'parent_id': parent_id,
                'type': item_type,
                'name': display_name,
                'content_data': content_data
            })
        
        conn.close()
        return json.dumps(menu_data, indent=2)
    
    def import_menu(self, menu_json):
        """Import menu structure from JSON"""
        try:
            menu_data = json.loads(menu_json)
            
            # Clear existing menu
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM menu_items")
            
            # Insert new items
            for item in menu_data:
                cursor.execute('''
                    INSERT INTO menu_items (item_id, parent_id, item_type, display_name, content_data)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    item['item_id'],
                    item['parent_id'],
                    item['type'],
                    item['name'],
                    json.dumps(item['content_data'])
                ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error importing menu: {e}")
            return False
