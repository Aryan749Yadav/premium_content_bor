"""
Admin-only command handlers with button creation conversation
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from user_auth import UserAuth
from menu_manager import MenuManager
import config

# Conversation states
BUTTON_NAME, BUTTON_TYPE, BUTTON_CONTENT, BUTTON_PARENT = range(4)

class AdminCommands:
    def __init__(self, bot):
        self.bot = bot
        self.auth = UserAuth()
        self.menu = MenuManager()
        self.temp_data = {}  # Store temporary data during conversation
    
    async def handle_admin_command(self, update, context, command_parts):
        """Route admin commands to appropriate handlers"""
        user_id = update.message.from_user.id
        
        if not self.auth.is_admin(user_id):
            await context.bot.send_message(
                chat_id=update.message.chat_id,
                text="⛔ This command is for admins only."
            )
            return
        
        command = command_parts[0].lower() if command_parts else ""
        
        if command == "add" and len(command_parts) > 1:
            await self.add_premium_user(update.message, context, command_parts[1])
        elif command == "remove" and len(command_parts) > 1:
            await self.remove_premium_user(update.message, context, command_parts[1])
        elif command == "listusers":
            await self.list_premium_users(update.message, context)
        elif command == "export":
            await self.export_menu(update.message, context)
        elif command == "button":
            await self.start_button_creation(update, context)
        elif command == "listmenu":
            await self.list_menu_items(update.message, context)
        elif command == "deleteitem":
            await self.delete_menu_item(update.message, context, command_parts)
        else:
            await context.bot.send_message(
                chat_id=update.message.chat_id,
                text="❌ Unknown admin command.\n\nAvailable commands:\n"
                     "/admin add [user_id]\n"
                     "/admin remove [user_id]\n"
                     "/admin listusers\n"
                     "/admin export\n"
                     "/admin button\n"
                     "/admin listmenu\n"
                     "/admin deleteitem [item_id]"
            )
    
    # ... keep existing add_premium_user, remove_premium_user, list_premium_users, export_menu methods ...
    
    async def start_button_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start button creation conversation"""
        # Store user_id for this conversation
        self.temp_data[update.message.from_user.id] = {
            'step': 'name',
            'data': {}
        }
        
        # Ask for folder parent first
        keyboard = []
        menu_items = self.menu.get_menu_items(parent_id=0)
        
        # Add root option
        keyboard.append([InlineKeyboardButton("🏠 Root Level", callback_data="parent_0")])
        
        # Add existing folders
        for item in menu_items:
            if item['item_type'] == 'folder':
                keyboard.append([InlineKeyboardButton(f"📁 {item['display_name']}", callback_data=f"parent_{item['item_id']}")])
        
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📁 **Select where to add the new item:**\n"
            "Choose a folder or root level:",
            reply_markup=reply_markup
        )
        
        return BUTTON_PARENT
    
    async def button_parent_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle parent selection"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if data == "cancel":
            await query.edit_message_text("❌ Button creation cancelled.")
            return ConversationHandler.END
        
        parent_id = int(data.split("_")[1])
        
        # Store parent ID
        if user_id not in self.temp_data:
            self.temp_data[user_id] = {'step': 'name', 'data': {}}
        
        self.temp_data[user_id]['data']['parent_id'] = parent_id
        
        # Ask for button name
        await query.edit_message_text(
            "✏️ **Enter button name:**\n"
            "This will be displayed to users."
        )
        
        return BUTTON_NAME
    
    async def button_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get button name"""
        user_id = update.message.from_user.id
        button_name = update.message.text
        
        if user_id not in self.temp_data:
            self.temp_data[user_id] = {'step': 'name', 'data': {}}
        
        self.temp_data[user_id]['data']['name'] = button_name
        
        # Ask for button type
        keyboard = [
            [InlineKeyboardButton("📝 Database Link", callback_data="type_button")],
            [InlineKeyboardButton("🔗 Public URL", callback_data="type_url")],
            [InlineKeyboardButton("📁 Folder", callback_data="type_folder")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📋 **Select item type:**\n\n"
            "• 📝 Database Link: Link to content in private channel\n"
            "• 🔗 Public URL: External website link\n"
            "• 📁 Folder: Container for organizing items",
            reply_markup=reply_markup
        )
        
        return BUTTON_TYPE
    
    async def button_type_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle type selection"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if data == "cancel":
            await query.edit_message_text("❌ Button creation cancelled.")
            return ConversationHandler.END
        
        item_type = data.split("_")[1]  # button, url, or folder
        
        if user_id not in self.temp_data:
            self.temp_data[user_id] = {'step': 'name', 'data': {}}
        
        self.temp_data[user_id]['data']['type'] = item_type
        
        # Ask for content based on type
        if item_type == 'button':
            await query.edit_message_text(
                "📎 **Database Link Setup**\n\n"
                "1. Go to your database channel\n"
                "2. Forward any message to @username_to_id_bot\n"
                "3. It will reply with Channel ID and Message ID\n"
                "4. Send them in format: `channel_id,message_id`\n\n"
                "Example: `-1001234567890,42`"
            )
            return BUTTON_CONTENT
        
        elif item_type == 'url':
            await query.edit_message_text(
                "🔗 **Enter Public URL:**\n"
                "Example: https://example.com"
            )
            return BUTTON_CONTENT
        
        elif item_type == 'folder':
            # Folders don't need additional content
            await self.create_menu_item(user_id, query)
            return ConversationHandler.END
    
    async def button_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get content data"""
        user_id = update.message.from_user.id
        content_text = update.message.text
        
        if user_id not in self.temp_data:
            await update.message.reply_text("❌ Session expired. Start again with /admin button")
            return ConversationHandler.END
        
        item_type = self.temp_data[user_id]['data']['type']
        
        if item_type == 'button':
            # Parse channel_id and message_id
            try:
                parts = content_text.split(',')
                channel_id = int(parts[0].strip())
                message_id = int(parts[1].strip())
                
                self.temp_data[user_id]['data']['content'] = {
                    'channel_id': channel_id,
                    'message_id': message_id
                }
                
                await self.create_menu_item(user_id, update.message)
                
            except Exception as e:
                await update.message.reply_text(
                    f"❌ Invalid format: {e}\n"
                    "Use: `channel_id,message_id`\n"
                    "Example: `-1001234567890,42`"
                )
                return BUTTON_CONTENT
        
        elif item_type == 'url':
            self.temp_data[user_id]['data']['content'] = {
                'url': content_text
            }
            await self.create_menu_item(user_id, update.message)
        
        return ConversationHandler.END
    
    async def create_menu_item(self, user_id, update_obj):
        """Create the menu item in database"""
        data = self.temp_data[user_id]['data']
        
        try:
            item_id = self.menu.add_menu_item(
                parent_id=data['parent_id'],
                item_type=data['type'],
                display_name=data['name'],
                content_data=data.get('content', {})
            )
            
            if item_id:
                # Clean up temp data
                if user_id in self.temp_data:
                    del self.temp_data[user_id]
                
                item_type_display = {
                    'button': 'Database Link',
                    'url': 'Public URL',
                    'folder': 'Folder'
                }[data['type']]
                
                await update_obj.reply_text(
                    f"✅ **{item_type_display} created successfully!**\n\n"
                    f"• Name: {data['name']}\n"
                    f"• Type: {item_type_display}\n"
                    f"• ID: {item_id}\n\n"
                    f"Users will see this in the menu."
                )
            else:
                await update_obj.reply_text("❌ Failed to create menu item.")
        
        except Exception as e:
            await update_obj.reply_text(f"❌ Error: {str(e)}")
        
        finally:
            # Clean up temp data
            if user_id in self.temp_data:
                del self.temp_data[user_id]
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel button creation"""
        user_id = update.message.from_user.id
        if user_id in self.temp_data:
            del self.temp_data[user_id]
        
        await update.message.reply_text("❌ Button creation cancelled.")
        return ConversationHandler.END
    
    async def list_menu_items(self, message, context):
        """List all menu items"""
        # Get all items
        from database import MongoDB
        db = MongoDB()
        items = list(db.db.menu_items.find({}, {"_id": 0}).sort("parent_id", 1))
        
        if not items:
            await context.bot.send_message(
                chat_id=message.chat_id,
                text="📭 No menu items found."
            )
            return
        
        response = "📋 **Menu Structure:**\n\n"
        
        # Organize by parent
        items_by_parent = {}
        for item in items:
            parent_id = item['parent_id']
            if parent_id not in items_by_parent:
                items_by_parent[parent_id] = []
            items_by_parent[parent_id].append(item)
        
        # Display
        def display_items(parent_id=0, level=0):
            nonlocal response
            if parent_id in items_by_parent:
                for item in items_by_parent[parent_id]:
                    indent = "  " * level
                    icon = "📁" if item['item_type'] == 'folder' else "🔗" if item['item_type'] == 'url' else "📝"
                    response += f"{indent}{icon} **{item['display_name']}**\n"
                    response += f"{indent}  ID: `{item['item_id']}` | Type: {item['item_type']}\n"
                    
                    if item['item_type'] == 'folder':
                        display_items(item['item_id'], level + 1)
        
        display_items()
        
        response += "\n💡 Use `/admin deleteitem [id]` to delete an item."
        
        await context.bot.send_message(
            chat_id=message.chat_id,
            text=response
        )
    
    async def delete_menu_item(self, message, context, command_parts):
        """Delete a menu item"""
        if len(command_parts) < 2:
            await context.bot.send_message(
                chat_id=message.chat_id,
                text="❌ Usage: `/admin deleteitem [item_id]`"
            )
            return
        
        try:
            item_id = int(command_parts[1])
            
            # Check if item exists
            item = self.menu.get_menu_item(item_id)
            if not item:
                await context.bot.send_message(
                    chat_id=message.chat_id,
                    text=f"❌ Item ID {item_id} not found."
                )
                return
            
            # Delete item
            if self.menu.delete_menu_item(item_id):
                await context.bot.send_message(
                    chat_id=message.chat_id,
                    text=f"✅ Deleted: {item['display_name']} (ID: {item_id})"
                )
            else:
                await context.bot.send_message(
                    chat_id=message.chat_id,
                    text=f"❌ Failed to delete item ID {item_id}."
                )
        
        except ValueError:
            await context.bot.send_message(
                chat_id=message.chat_id,
                text="❌ Invalid item ID. Must be a number."
            )
    
    # ... keep other existing methods (add_premium_user, remove_premium_user, etc.) ...
