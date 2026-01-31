"""
BATCH UPLOAD SYSTEM - Upload multiple items at once
"""
import json
from menu_manager import MenuManager

class BatchUpload:
    def __init__(self):
        self.menu = MenuManager()
    
    async def upload_from_json(self, update, context, json_file):
        """Upload multiple items from JSON file"""
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            created = 0
            for item in data:
                item_id = self.menu.add_menu_item(
                    parent_id=item['parent_id'],
                    item_type=item['type'],
                    display_name=item['name'],
                    content_data=item.get('content', {})
                )
                if item_id:
                    created += 1
            
            await update.message.reply_text(f"✅ Created {created} items from file!")
        
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    def create_sample_json(self):
        """Create sample JSON for bulk upload"""
        sample = [
            {
                "parent_id": 0,
                "type": "folder",
                "name": "Course Materials",
                "content": {}
            },
            {
                "parent_id": 1,  # Inside folder ID 1
                "type": "button",
                "name": "Lesson 1",
                "content": {
                    "channel_id": -1003761591150,
                    "message_id": 2
                }
            },
            {
                "parent_id": 1,
                "type": "button",
                "name": "Lesson 2",
                "content": {
                    "channel_id": -1003761591150,
                    "message_id": 3
                }
            }
        ]
        
        with open("data/bulk_upload.json", "w") as f:
            json.dump(sample, f, indent=2)
        
        return "data/bulk_upload.json"
