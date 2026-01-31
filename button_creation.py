"""
Simpler button creation via commands
"""
from menu_manager import MenuManager
from utils import parse_telegram_link

class SimpleButtonCreator:
    def __init__(self):
        self.menu = MenuManager()
    
    async def create_button_simple(self, update, context):
        """Create button via command arguments"""
        args = context.args
        
        if len(args) < 3:
            await update.message.reply_text(
                "❌ Usage: `/addbutton [parent_id] [name] [type] [content]`\n\n"
                "Example 1 (Database Link):\n"
                "`/addbutton 0 \"Video 1\" button -1001234567890,42`\n\n"
                "Example 2 (URL):\n"
                "`/addbutton 0 \"Website\" url https://example.com`\n\n"
                "Example 3 (Folder):\n"
                "`/addbutton 0 \"Videos\" folder`"
            )
            return
        
        try:
            parent_id = int(args[0])
            name = args[1]
            item_type = args[2].lower()
            
            content_data = {}
            
            if item_type == 'button' and len(args) > 3:
                # Parse channel_id,message_id
                content_parts = args[3].split(',')
                content_data = {
                    'channel_id': int(content_parts[0]),
                    'message_id': int(content_parts[1])
                }
            elif item_type == 'url' and len(args) > 3:
                content_data = {'url': args[3]}
            elif item_type == 'folder':
                content_data = {}
            else:
                await update.message.reply_text("❌ Invalid content for type.")
                return
            
            item_id = self.menu.add_menu_item(
                parent_id=parent_id,
                item_type=item_type,
                display_name=name,
                content_data=content_data
            )
            
            if item_id:
                await update.message.reply_text(f"✅ Created item with ID: {item_id}")
            else:
                await update.message.reply_text("❌ Failed to create item.")
        
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
