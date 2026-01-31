"""
ULTRA SIMPLE Admin Interface - No typing required!
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from user_auth import UserAuth
from menu_manager import MenuManager
import config

class SimpleAdmin:
    def __init__(self, bot):
        self.bot = bot
        self.auth = UserAuth()
        self.menu = MenuManager()
        self.user_state = {}  # {user_id: {'step': 'waiting_for_name', 'data': {}}}
    
    async def handle_admin_command(self, update, context, command_parts):
        """Handle admin commands"""
        user_id = update.message.from_user.id
        
        if not self.auth.is_admin(user_id):
            await update.message.reply_text("⛔ Admin only.")
            return
        
        command = command_parts[0].lower() if command_parts else ""
        
        if command == "add" and len(command_parts) > 1:
            await self.add_user(update.message, context, command_parts[1])
        elif command == "remove" and len(command_parts) > 1:
            await self.remove_user(update.message, context, command_parts[1])
        elif command == "listusers":
            await self.list_users(update.message, context)
        elif command == "menu":
            await self.show_main_admin_menu(update.message, context)
        elif command == "help":
            await self.show_help(update.message, context)
        else:
            await self.show_main_admin_menu(update.message, context)
    
    async def show_main_admin_menu(self, message, context):
        """Show main admin dashboard"""
        keyboard = [
            [InlineKeyboardButton("➕ Add Premium User", callback_data="admin_adduser")],
            [InlineKeyboardButton("➖ Remove User", callback_data="admin_removeuser")],
            [InlineKeyboardButton("👥 List Users", callback_data="admin_listusers")],
            [InlineKeyboardButton("📁 Manage Content", callback_data="admin_manage")],
            [InlineKeyboardButton("🚀 Quick Setup", callback_data="admin_quick")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=message.chat_id,
            text="🎛️ **ADMIN DASHBOARD**\n\nWhat would you like to do?",
            reply_markup=reply_markup
        )
    
    async def show_help(self, message, context):
        """Show help"""
        help_text = """
🆘 **QUICK HELP**

**Basic Commands:**
`/admin menu` - Open admin dashboard
`/admin add USER_ID` - Add premium user
`/admin remove USER_ID` - Remove user
`/admin listusers` - List all users

**From Dashboard:**
• Click 📁 Manage Content - Create folders/buttons
• Click 🚀 Quick Setup - Auto-create basic structure
• Click 👥 List Users - View all premium users

**No typing needed - just click buttons!**
        """
        await context.bot.send_message(chat_id=message.chat_id, text=help_text)
    
    async def show_content_manager(self, message, context):
        """Show content management interface"""
        # Get existing folders for selection
        folders = self.menu.get_menu_items(parent_id=0)
        folders = [f for f in folders if f['item_type'] == 'folder']
        
        keyboard = []
        
        # Add existing folders as options
        if folders:
            keyboard.append([InlineKeyboardButton("📁 Existing Folders:", callback_data="none")])
            for folder in folders[:5]:  # Show max 5
                btn_text = f"📂 {folder['display_name']}"
                keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"select_folder_{folder['item_id']}")])
        
        # Creation options
        keyboard.append([InlineKeyboardButton("➕ Create New Folder", callback_data="create_folder")])
        keyboard.append([InlineKeyboardButton("📝 Add Content to Folder", callback_data="add_content")])
        keyboard.append([InlineKeyboardButton("📋 View Structure", callback_data="view_structure")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_back")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=message.chat_id,
            text="📁 **CONTENT MANAGER**\n\nSelect a folder or create new:",
            reply_markup=reply_markup
        )
    
    async def show_quick_setup(self, message, context):
        """One-click setup for common structures"""
        keyboard = [
            [InlineKeyboardButton("🎓 Course Structure", callback_data="setup_course")],
            [InlineKeyboardButton("📚 Library Structure", callback_data="setup_library")],
            [InlineKeyboardButton("🎬 Video Series", callback_data="setup_videos")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=message.chat_id,
            text="🚀 **QUICK SETUP**\n\nSelect a template to auto-create:",
            reply_markup=reply_markup
        )
    
    async def handle_callback(self, update, context):
        """Handle ALL admin callbacks"""
        query = update.callback_query
        user_id = query.from_user.id
        data = query.data
        
        if not self.auth.is_admin(user_id):
            await query.answer("⛔ Admin only.", show_alert=True)
            return
        
        await query.answer()
        
        # Route to appropriate handler
        if data == "admin_back":
            await self.show_main_admin_menu(query.message, context)
        
        elif data == "admin_manage":
            await self.show_content_manager(query.message, context)
        
        elif data == "admin_quick":
            await self.show_quick_setup(query.message, context)
        
        elif data == "admin_adduser":
            await self.prompt_add_user(query, context)
        
        elif data == "admin_removeuser":
            await self.prompt_remove_user(query, context)
        
        elif data == "admin_listusers":
            await self.show_user_list(query, context)
        
        elif data == "create_folder":
            await self.prompt_create_folder(query, context)
        
        elif data == "add_content":
            await self.show_folder_selection(query, context)
        
        elif data == "view_structure":
            await self.show_menu_structure(query, context)
        
        elif data.startswith("select_folder_"):
            folder_id = int(data.split("_")[2])
            await self.show_folder_options(query, context, folder_id)
        
        elif data.startswith("setup_"):
            setup_type = data.split("_")[1]
            await self.run_quick_setup(query, context, setup_type)
        
        elif data.startswith("add_to_folder_"):
            folder_id = int(data.split("_")[3])
            await self.prompt_add_content(query, context, folder_id)
    
    async def prompt_add_user(self, query, context):
        """Prompt for user ID to add"""
        self.user_state[query.from_user.id] = {
            'action': 'add_user',
            'step': 'waiting_id'
        }
        
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="admin_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text="👤 **Add Premium User**\n\nPlease reply with the user's Telegram ID:",
            reply_markup=reply_markup
        )
    
    async def prompt_remove_user(self, query, context):
        """Prompt for user ID to remove"""
        self.user_state[query.from_user.id] = {
            'action': 'remove_user',
            'step': 'waiting_id'
        }
        
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="admin_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text="🗑️ **Remove User**\n\nPlease reply with the user's Telegram ID:",
            reply_markup=reply_markup
        )
    
    async def show_user_list(self, query, context):
        """Show list of premium users"""
        users = self.auth.list_premium_users()
        
        if not users:
            await query.edit_message_text("📭 No premium users found.")
            return
        
        text = "👑 **Premium Users:**\n\n"
        for user in users:
            text += f"• `{user['user_id']}` - Added {user['added_date'].split()[0]}\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text=text, reply_markup=reply_markup)
    
    async def prompt_create_folder(self, query, context):
        """Prompt for folder creation"""
        self.user_state[query.from_user.id] = {
            'action': 'create_folder',
            'step': 'waiting_name'
        }
        
        keyboard = [
            [InlineKeyboardButton("🏠 Root Level", callback_data="folder_parent_0")],
            [InlineKeyboardButton("❌ Cancel", callback_data="admin_manage")]
        ]
        
        # Add existing folders as parent options
        folders = self.menu.get_menu_items(parent_id=0)
        folders = [f for f in folders if f['item_type'] == 'folder']
        
        for folder in folders[:3]:  # Max 3 for simplicity
            keyboard.append([InlineKeyboardButton(f"📂 {folder['display_name']}", 
                                                callback_data=f"folder_parent_{folder['item_id']}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text="📁 **Create New Folder**\n\nSelect where to create it:",
            reply_markup=reply_markup
        )
    
    async def show_folder_selection(self, query, context):
        """Show folders to add content to"""
        folders = self.menu.get_menu_items(parent_id=0)
        folders = [f for f in folders if f['item_type'] == 'folder']
        
        if not folders:
            await query.edit_message_text("❌ No folders found. Create one first!")
            return
        
        keyboard = []
        for folder in folders:
            btn_text = f"📂 {folder['display_name']}"
            keyboard.append([InlineKeyboardButton(btn_text, 
                                                callback_data=f"add_to_folder_{folder['item_id']}")])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_manage")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text="📝 **Add Content**\n\nSelect folder to add content:",
            reply_markup=reply_markup
        )
    
    async def prompt_add_content(self, query, context, folder_id):
        """Prompt to add content to specific folder"""
        folder = self.menu.get_menu_item(folder_id)
        
        self.user_state[query.from_user.id] = {
            'action': 'add_content',
            'step': 'waiting_info',
            'folder_id': folder_id
        }
        
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="admin_manage")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=f"📝 **Add Content to: {folder['display_name']}**\n\n"
                 "Reply with:\n"
                 "1. Content name\n"
                 "2. Channel ID,Message ID\n\n"
                 "Example:\n"
                 "`Math Lesson 1\n"
                 "-1003761591150,2`",
            reply_markup=reply_markup
        )
    
    async def show_menu_structure(self, query, context):
        """Show current menu structure"""
        items = self.menu.get_menu_items(parent_id=0)
        
        if not items:
            await query.edit_message_text("📭 Menu is empty. Create some content!")
            return
        
        text = "📋 **Current Structure:**\n\n"
        
        def build_tree(parent_id=0, level=0):
            nonlocal text
            items = self.menu.get_menu_items(parent_id=parent_id)
            
            for item in items:
                indent = "  " * level
                icon = "📁" if item['item_type'] == 'folder' else "📝"
                text += f"{indent}{icon} {item['display_name']} (ID: {item['item_id']})\n"
                
                if item['item_type'] == 'folder':
                    build_tree(item['item_id'], level + 1)
        
        build_tree()
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_manage")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text=text, reply_markup=reply_markup)
    
    async def run_quick_setup(self, query, context, setup_type):
        """Auto-create common structures"""
        if setup_type == "course":
            # Create course structure
            course_id = self.menu.add_menu_item(0, 'folder', '🎓 Course', {})
            self.menu.add_menu_item(course_id, 'folder', '📚 Module 1', {})
            self.menu.add_menu_item(course_id, 'folder', '📚 Module 2', {})
            self.menu.add_menu_item(course_id, 'folder', '📚 Module 3', {})
            text = "✅ Created Course Structure!"
        
        elif setup_type == "library":
            # Create library structure
            lib_id = self.menu.add_menu_item(0, 'folder', '📚 Library', {})
            self.menu.add_menu_item(lib_id, 'folder', '📖 E-Books', {})
            self.menu.add_menu_item(lib_id, 'folder', '🎬 Videos', {})
            self.menu.add_menu_item(lib_id, 'folder', '🎵 Audio', {})
            text = "✅ Created Library Structure!"
        
        elif setup_type == "videos":
            # Create video series
            video_id = self.menu.add_menu_item(0, 'folder', '🎬 Video Series', {})
            for i in range(1, 6):
                self.menu.add_menu_item(video_id, 'folder', f'📼 Episode {i}', {})
            text = "✅ Created Video Series Structure!"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_quick")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text=text, reply_markup=reply_markup)
    
    async def handle_message_response(self, update, context):
        """Handle user's text responses"""
        user_id = update.message.from_user.id
        text = update.message.text
        
        if user_id not in self.user_state:
            return
        
        state = self.user_state[user_id]
        action = state.get('action')
        
        try:
            if action == 'add_user':
                user_id_to_add = int(text)
                if self.auth.add_premium_user(user_id_to_add, user_id):
                    await update.message.reply_text(f"✅ Added user {user_id_to_add}")
                else:
                    await update.message.reply_text("❌ Failed to add user")
            
            elif action == 'remove_user':
                user_id_to_remove = int(text)
                if self.auth.remove_premium_user(user_id_to_remove):
                    await update.message.reply_text(f"✅ Removed user {user_id_to_remove}")
                else:
                    await update.message.reply_text("❌ User not found")
            
            elif action == 'create_folder':
                if state.get('step') == 'waiting_name':
                    # User has selected parent, now asking for name
                    folder_name = text
                    parent_id = state.get('parent_id', 0)
                    
                    folder_id = self.menu.add_menu_item(
                        parent_id=parent_id,
                        item_type='folder',
                        display_name=folder_name,
                        content_data={}
                    )
                    
                    if folder_id:
                        await update.message.reply_text(f"✅ Created folder: {folder_name}")
                    else:
                        await update.message.reply_text("❌ Failed to create folder")
            
            elif action == 'add_content':
                # Parse content name and channel data
                lines = text.strip().split('\n')
                if len(lines) >= 2:
                    content_name = lines[0].strip()
                    channel_data = lines[1].strip()
                    
                    if ',' in channel_data:
                        channel_parts = channel_data.split(',')
                        channel_id = int(channel_parts[0].strip())
                        message_id = int(channel_parts[1].strip())
                        
                        folder_id = state.get('folder_id')
                        
                        button_id = self.menu.add_menu_item(
                            parent_id=folder_id,
                            item_type='button',
                            display_name=content_name,
                            content_data={
                                'channel_id': channel_id,
                                'message_id': message_id
                            }
                        )
                        
                        if button_id:
                            await update.message.reply_text(f"✅ Added content: {content_name}")
                        else:
                            await update.message.reply_text("❌ Failed to add content")
                    else:
                        await update.message.reply_text("❌ Invalid format. Use: Name\nChannel,MessageID")
                else:
                    await update.message.reply_text("❌ Need 2 lines: Name and Channel,MessageID")
        
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
        
        finally:
            # Clear state
            if user_id in self.user_state:
                del self.user_state[user_id]
    
    async def add_user(self, message, context, user_id_str):
        """Add user via command"""
        try:
            user_id = int(user_id_str)
            if self.auth.add_premium_user(user_id, message.from_user.id):
                await message.reply_text(f"✅ Added user {user_id}")
            else:
                await message.reply_text("❌ Failed to add user")
        except:
            await message.reply_text("❌ Invalid user ID")
    
    async def remove_user(self, message, context, user_id_str):
        """Remove user via command"""
        try:
            user_id = int(user_id_str)
            if self.auth.remove_premium_user(user_id):
                await message.reply_text(f"✅ Removed user {user_id}")
            else:
                await message.reply_text("❌ User not found")
        except:
            await message.reply_text("❌ Invalid user ID")
    
    async def list_users(self, message, context):
        """List users via command"""
        users = self.auth.list_premium_users()
        
        if not users:
            await message.reply_text("📭 No premium users")
            return
        
        text = "👑 **Premium Users:**\n\n"
        for user in users:
            text += f"• `{user['user_id']}`\n"
        
        await message.reply_text(text)
