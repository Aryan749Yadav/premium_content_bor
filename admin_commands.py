"""
Admin-only command handlers - SIMPLE WORKING VERSION
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
                text="❌ Unknown admin command.\n\n"
                     "📋 **Available Commands:**\n"
                     "• `/admin add [user_id]` - Add premium user\n"
                     "• `/admin remove [user_id]` - Remove premium user\n"
                     "• `/admin listusers` - List all premium users\n"
                     "• `/admin button` - Create new menu items\n"
                     "• `/admin listmenu` - Show menu structure\n"
                     "• `/admin deleteitem [id]` - Delete menu item\n"
                     "• `/admin export` - Export menu\n"
                     "• `/admin quickadd [parent] [type] [name] [data]` - Quick add\n\n"
                     "📝 **Quick Add Format:**\n"
                     "`/admin quickadd 0 folder Videos`\n"
                     "`/admin quickadd 1 button \"Video 1\" -1003761591150,2`\n"
                     "`/admin quickadd 0 url Website https://example.com`"
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
            text="🛠️ **Button Creation Menu**\n\n"
                 "Select what you want to create:",
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
                "📁 **Creating Folder**\n\n"
                "Please reply with:\n"
                "1. Parent folder ID (0 for root)\n"
                "2. Folder name\n\n"
                "Example: `0 My Videos`"
            )
        elif data == "create_button":
            await query.edit_message_text(
                "📝 **Creating Database Link**\n\n"
                "Please reply with:\n"
                "1. Parent folder ID (0 for root)\n"
                "2. Button name\n"
                "3. Channel ID,Message ID\n\n"
                "Example: `0 \"Video 1\" -1003761591150,2`\n\n"
                "💡 Get Channel ID & Message ID by forwarding\n"
                "a message from your database channel to\n"
                "@username_to_id_bot"
            )
        elif data == "create_url":
            await query.edit_message_text(
                "🔗 **Creating URL Button**\n\n"
                "Please reply with:\n"
                "1. Parent folder ID (0 for root)\n"
                "2. Button name\n"
                "3. URL\n\n"
                "Example: `0 Website https://example.com`"
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
                    await update.message.reply_text(
                        f"✅ Folder created!\n"
                        f"• Name: {folder_name}\n"
                        f"• Parent ID: {parent_id}\n"
                        f"• Item ID: {item_id}"
                    )
                else:
                    await update.message.reply_text("❌ Failed to create folder.")
            
            elif action == "create_button":
                # Parse: "parent_id "button name" channel_id,message_id"
                try:
                    # Find the last comma for channel,message
                    last_comma = user_input.rfind(',')
                    if last_comma == -1:
                        raise ValueError("No comma found")
                    
                    # Get channel_id,message_id
                    channel_data = user_input[last_comma+1:]
                    channel_parts = channel_data.split(',')
                    if len(channel_parts) != 2:
                        raise ValueError("Invalid channel,message format")
                    
                    channel_id = int(channel_parts[0])
                    message_id = int(channel_parts[1])
                    
                    # Get the rest for parent and name
                    rest = user_input[:last_comma].strip()
                    
                    # Find where name ends (could have quotes)
                    if rest.count('"') >= 2:
                        # Name is in quotes
                        first_quote = rest.find('"')
                        last_quote = rest.rfind('"')
                        parent_part = rest[:first_quote].strip()
                        button_name = rest[first_quote+1:last_quote]
                    else:
                        # Name is not in quotes
                        parts = rest.rsplit(' ', 1)
                        if len(parts) < 2:
                            raise ValueError("Invalid format")
                        parent_part = parts[0]
                        button_name = parts[1]
                    
                    parent_id = int(parent_part)
                    
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
                        await update.message.reply_text(
                            f"✅ Database Link created!\n"
                            f"• Name: {button_name}\n"
                            f"• Parent ID: {parent_id}\n"
                            f"• Channel: {channel_id}\n"
                            f"• Message: {message_id}\n"
                            f"• Item ID: {item_id}"
                        )
                    else:
                        await update.message.reply_text("❌ Failed to create button.")
                
                except Exception as e:
                    await update.message.reply_text(
                        f"❌ Error parsing: {str(e)}\n\n"
                        "Correct format:\n"
                        "`0 \"Video Name\" -1003761591150,2`\n"
                        "or\n"
                        "`0 VideoName -1003761591150,2`"
                    )
            
            elif action == "create_url":
                parts = user_input.split(' ', 2)
                if len(parts) < 3:
                    await update.message.reply_text("❌ Format: `parent_id name url`")
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
                    await update.message.reply_text(
                        f"✅ URL Button created!\n"
                        f"• Name: {button_name}\n"
                        f"• Parent ID: {parent_id}\n"
                        f"• URL: {url}\n"
                        f"• Item ID: {item_id}"
                    )
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
                text="📭 No menu items found. Create some with `/admin button`"
            )
            return
        
        response = "📋 **Menu Structure:**\n\n"
        
        def build_tree(parent_id=0, level=0):
            nonlocal response
            items = self.menu.get_menu_items(parent_id=parent_id)
            
            for item in items:
                indent = "  " * level
                icon = "📁" if item['item_type'] == 'folder' else "🔗" if item['item_type'] == 'url' else "📝"
                response += f"{indent}{icon} **{item['display_name']}**\n"
                response += f"{indent}  ID: `{item['item_id']}` | Type: {item['item_type']}\n"
                
                if item['item_type'] == 'button' and 'content_data' in item:
                    cd = item['content_data']
                    if 'channel_id' in cd and 'message_id' in cd:
                        response += f"{indent}  Channel: {cd['channel_id']}, Msg: {cd['message_id']}\n"
                elif item['item_type'] == 'url' and 'content_data' in item:
                    cd = item['content_data']
                    if 'url' in cd:
                        response += f"{indent}  URL: {cd['url'][:50]}...\n"
                
                # Recursively show folder contents
                if item['item_type'] == 'folder':
                    build_tree(item['item_id'], level + 1)
        
        build_tree()
        
        response += "\n💡 **Commands:**\n"
        response += "• `/admin deleteitem [id]` - Delete an item\n"
        response += "• `/admin button` - Create new items\n"
        response += "• `/admin quickadd` - Quick add (see help)"
        
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
        if len(args) < 4:
            await context.bot.send_message(
                chat_id=message.chat_id,
                text="❌ Usage: `/admin quickadd parent_id type name data`\n\n"
                     "Examples:\n"
                     "• `/admin quickadd 0 folder Videos`\n"
                     "• `/admin quickadd 1 button \"Video 1\" -1003761591150,2`\n"
                     "• `/admin quickadd 0 url Website https://example.com`"
            )
            return
        
        try:
            parent_id = int(args[1])
            item_type = args[2].lower()
            button_name = args[3]
            
            content_data = {}
            
            if item_type == 'button':
                if len(args) < 5:
                    await context.bot.send_message(
                        chat_id=message.chat_id,
                        text="❌ For buttons, provide: parent_id button name channel_id,message_id"
                    )
                    return
                
                channel_parts = args[4].split(',')
                if len(channel_parts) != 2:
                    await context.bot.send_message(
                        chat_id=message.chat_id,
                        text="❌ Channel data format: -1003761591150,2"
                    )
                    return
                
                content_data = {
                    'channel_id': int(channel_parts[0]),
                    'message_id': int(channel_parts[1])
                }
            
            elif item_type == 'url':
                if len(args) < 5:
                    await context.bot.send_message(
                        chat_id=message.chat_id,
                        text="❌ For URLs, provide: parent_id url name url_link"
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
