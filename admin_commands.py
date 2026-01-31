"""
Admin-only command handlers - WORKING VERSION
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from user_auth import UserAuth
from menu_manager import MenuManager
import config

class AdminCommands:
    def __init__(self, bot):
        self.bot = bot
        self.auth = UserAuth()
        self.menu = MenuManager()
        self.user_states = {}  # Track user conversation states
    
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
            await self.show_button_menu(update.message, context)
        elif command == "listmenu":
            await self.list_menu_items(update.message, context)
        elif command == "deleteitem" and len(command_parts) > 1:
            await self.delete_menu_item(update.message, context, command_parts[1])
        elif command == "quickadd" and len(command_parts) > 3:
            await self.quick_add_button(update.message, context, command_parts)
        else:
            await context.bot.send_message(
                chat_id=update.message.chat_id,
                text="❌ Unknown admin command. Use /admin button to create menu items."
            )
    
    async def add_premium_user(self, message, context, target_user_id):
        """Add user to premium list"""
        try:
            user_id = int(target_user_id)
            if self.auth.add_premium_user(user_id, message.from_user.id):
                await context.bot.send_message(
                    chat_id=message.chat_id,
                    text=f"✅ User {user_id} added to premium list."
                )
            else:
                await context.bot.send_message(
                    chat_id=message.chat_id,
                    text="❌ Failed to add user."
                )
        except ValueError:
            await context.bot.send_message(
                chat_id=message.chat_id,
                text="❌ Invalid user ID. Please provide a numeric ID."
            )
    
    async def remove_premium_user(self, message, context, target_user_id):
        """Remove user from premium list"""
        try:
            user_id = int(target_user_id)
            if self.auth.remove_premium_user(user_id):
                await context.bot.send_message(
                    chat_id=message.chat_id,
                    text=f"✅ User {user_id} removed from premium list."
                )
            else:
                await context.bot.send_message(
                    chat_id=message.chat_id,
                    text="❌ User not found or already removed."
                )
        except ValueError:
            await context.bot.send_message(
                chat_id=message.chat_id,
                text="❌ Invalid user ID."
            )
    
    async def list_premium_users(self, message, context):
        """List all premium users"""
        users = self.auth.list_premium_users()
        
        if not users:
            await context.bot.send_message(
                chat_id=message.chat_id,
                text="📭 No premium users found."
            )
            return
        
        response = "👑 **Premium Users:**\n\n"
        for user in users:
            response += f"• User ID: `{user['user_id']}`\n"
            response += f"  Added by: `{user['added_by']}`\n"
            response += f"  Date: {user['added_date']}\n\n"
        
        await context.bot.send_message(
            chat_id=message.chat_id,
            text=response
        )
    
    async def export_menu(self, message, context):
        """Export menu structure"""
        menu_json = self.menu.export_menu()
        
        # Save to file
        with open("data/menu_export.json", "w") as f:
            f.write(menu_json)
        
        # Send file to admin
        with open("data/menu_export.json", "rb") as f:
            await context.bot.send_document(
                chat_id=message.chat_id,
                document=f,
                caption="📁 Menu structure exported successfully."
            )
    
    async def show_button_menu(self, message, context):
        """Show button creation options"""
        keyboard = [
            [InlineKeyboardButton("📝 Create Database Link", callback_data="create_button")],
            [InlineKeyboardButton("🔗 Create URL Button", callback_data="create_url")],
            [InlineKeyboardButton("📁 Create Folder", callback_data="create_folder")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_create")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=message.chat_id,
            text="🛠️ **Button Creation Menu**\n\nSelect what you want to create:",
            reply_markup=reply_markup
        )
    
    async def handle_callback_query(self, update, context):
        """Handle button creation callbacks"""
        query = update.callback_query
        user_id = query.from_user.id
        data = query.data
        
        if not self.auth.is_admin(user_id):
            await query.answer("⛔ Admin only.", show_alert=True)
            return
        
        await query.answer()
        
        if data == "cancel_create":
            await query.edit_message_text("❌ Button creation cancelled.")
            return
        
        # Store user's choice
        self.user_states[user_id] = {'action': data}
        
        if data == "create_folder":
            await query.edit_message_text(
                "📁 **Creating Folder**\n\nPlease reply with:\nParent ID and Folder Name\n\nExample: `0 My Videos`"
            )
        elif data == "create_button":
            await query.edit_message_text(
                "📝 **Creating Database Link**\n\nPlease reply with:\nParent ID, Button Name, and Channel,Message\n\nExample: `0 \"Video 1\" -1003761591150,2`"
            )
        elif data == "create_url":
            await query.edit_message_text(
                "🔗 **Creating URL Button**\n\nPlease reply with:\nParent ID, Button Name, and URL\n\nExample: `0 Website https://example.com`"
            )
    
    async def handle_message_response(self, update, context):
        """Handle user's response to button creation"""
        user_id = update.message.from_user.id
        
        if user_id not in self.user_states:
            return  # Not in creation mode
        
        action = self.user_states[user_id]['action']
        user_input = update.message.text
        
        try:
            if action == "create_folder":
                parts = user_input.split(' ', 1)
                if len(parts) < 2:
                    await update.message.reply_text("❌ Format: `parent_id folder_name`")
                    return
                
                parent_id = int(parts[0])
                folder_name = parts[1]
                
                item_id = self.menu.add_menu_item(
                    parent_id=parent_id,
                    item_type='folder',
                    display_name=folder_name,
                    content_data={}
                )
                
                if item_id:
                    await update.message.reply_text(f"✅ Folder created! ID: {item_id}")
                else:
                    await update.message.reply_text("❌ Failed to create folder.")
            
            elif action == "create_button":
                # Simple parsing - assume format: "parent_id button_name channel_id,message_id"
                parts = user_input.split(' ')
                if len(parts) < 3:
                    await update.message.reply_text("❌ Format: `parent_id button_name channel_id,message_id`")
                    return
                
                parent_id = int(parts[0])
                button_name = ' '.join(parts[1:-1])  # Everything except first and last
                
                # Last part should be channel_id,message_id
                last_part = parts[-1]
                if ',' not in last_part:
                    await update.message.reply_text("❌ Last part should be: channel_id,message_id")
                    return
                
                channel_parts = last_part.split(',')
                channel_id = int(channel_parts[0])
                message_id = int(channel_parts[1])
                
                item_id = self.menu.add_menu_item(
                    parent_id=parent_id,
                    item_type='button',
                    display_name=button_name,
                    content_data={
                        'channel_id': channel_id,
                        'message_id': message_id
                    }
                )
                
                if item_id:
                    await update.message.reply_text(f"✅ Button created! ID: {item_id}")
                else:
                    await update.message.reply_text("❌ Failed to create button.")
            
            elif action == "create_url":
                parts = user_input.split(' ', 2)
                if len(parts) < 3:
                    await update.message.reply_text("❌ Format: `parent_id button_name url`")
                    return
                
                parent_id = int(parts[0])
                button_name = parts[1]
                url = parts[2]
                
                item_id = self.menu.add_menu_item(
                    parent_id=parent_id,
                    item_type='url',
                    display_name=button_name,
                    content_data={'url': url}
                )
                
                if item_id:
                    await update.message.reply_text(f"✅ URL Button created! ID: {item_id}")
                else:
                    await update.message.reply_text("❌ Failed to create URL button.")
        
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
        
        finally:
            # Clear user state
            if user_id in self.user_states:
                del self.user_states[user_id]
    
    async def list_menu_items(self, message, context):
        """List all menu items"""
        items = self.menu.get_menu_items(parent_id=0)
        
        if not items:
            await context.bot.send_message(
                chat_id=message.chat_id,
                text="📭 No menu items found."
            )
            return
        
        response = "📋 **Menu Structure:**\n\n"
        
        for item in items:
            icon = "📁" if item['item_type'] == 'folder' else "🔗" if item['item_type'] == 'url' else "📝"
            response += f"{icon} **{item['display_name']}**\n"
            response += f"  ID: `{item['item_id']}` | Type: {item['item_type']}\n"
            
            if item['item_type'] == 'folder':
                # Show sub-items
                sub_items = self.menu.get_menu_items(parent_id=item['item_id'])
                for sub in sub_items:
                    sub_icon = "🔗" if sub['item_type'] == 'url' else "📝"
                    response += f"  └─ {sub_icon} {sub['display_name']} (ID: {sub['item_id']})\n"
            
            response += "\n"
        
        await context.bot.send_message(
            chat_id=message.chat_id,
            text=response
        )
    
    async def delete_menu_item(self, message, context, item_id_str):
        """Delete a menu item"""
        try:
            item_id = int(item_id_str)
            item = self.menu.get_menu_item(item_id)
            
            if not item:
                await context.bot.send_message(
                    chat_id=message.chat_id,
                    text=f"❌ Item ID {item_id} not found."
                )
                return
            
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
    
    async def quick_add_button(self, message, context, args):
        """Quick add button: /admin quickadd parent type name data"""
        try:
            parent_id = int(args[1])
            item_type = args[2].lower()
            button_name = args[3]
            
            if item_type == 'button':
                if len(args) < 5:
                    await context.bot.send_message(
                        chat_id=message.chat_id,
                        text="❌ For buttons: /admin quickadd parent_id button name channel_id,message_id"
                    )
                    return
                
                channel_parts = args[4].split(',')
                content_data = {
                    'channel_id': int(channel_parts[0]),
                    'message_id': int(channel_parts[1])
                }
            
            elif item_type == 'url':
                if len(args) < 5:
                    await context.bot.send_message(
                        chat_id=message.chat_id,
                        text="❌ For URLs: /admin quickadd parent_id url name url_link"
                    )
                    return
                
                content_data = {'url': args[4]}
            
            elif item_type == 'folder':
                content_data = {}
            
            else:
                await context.bot.send_message(
                    chat_id=message.chat_id,
                    text="❌ Type must be: button, url, or folder"
                )
                return
            
            item_id = self.menu.add_menu_item(
                parent_id=parent_id,
                item_type=item_type,
                display_name=button_name,
                content_data=content_data
            )
            
            if item_id:
                await context.bot.send_message(
                    chat_id=message.chat_id,
                    text=f"✅ Created {item_type}: {button_name}\nID: {item_id}"
                )
            else:
                await context.bot.send_message(
                    chat_id=message.chat_id,
                    text="❌ Failed to create item."
                )
        
        except Exception as e:
            await context.bot.send_message(
                chat_id=message.chat_id,
                text=f"❌ Error: {str(e)}"
            )
