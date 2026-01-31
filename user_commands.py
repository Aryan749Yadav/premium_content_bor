"""
User-facing command handlers and menu navigation
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from user_auth import UserAuth
from menu_manager import MenuManager
from content_delivery import ContentDelivery
import config

class UserCommands:
    def __init__(self, bot):
        self.bot = bot
        self.auth = UserAuth()
        self.menu = MenuManager()
        self.delivery = ContentDelivery(bot)
    
    async def handle_start(self, message):
        """Handle /start command"""
        user_id = message.from_user.id
        
        welcome_text = (
            "🎬 **Premium Content Bot**\n\n"
            "Welcome to your exclusive content platform!\n"
            "Navigate using the buttons below to access premium content.\n\n"
            "⚠️ All content is time-limited and watermarked for security."
        )
        
        if self.auth.is_premium(user_id):
            await self.show_main_menu(message, welcome_text)
        else:
            await message.reply(
                "⛔ **Access Denied**\n\n"
                "You do not have premium access.\n"
                "Please contact the admin for subscription details."
            )
    
    async def show_main_menu(self, message, text=""):
        """Show main menu to premium users"""
        if not self.auth.is_premium(message.from_user.id):
            await message.reply("⛔ Premium access required.")
            return
        
        menu_items = self.menu.get_menu_items(parent_id=0)
        
        if not menu_items:
            keyboard = [[InlineKeyboardButton("📂 No content available", callback_data="none")]]
        else:
            keyboard = []
            row = []
            for item in menu_items:
                callback_data = f"menu_{item['item_id']}"
                
                if item['item_type'] == 'folder':
                    button_text = f"📁 {item['display_name']}"
                elif item['item_type'] == 'url':
                    button_text = f"🔗 {item['display_name']}"
                else:
                    button_text = item['display_name']
                
                row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
                
                if len(row) >= config.MAX_BUTTONS_PER_ROW:
                    keyboard.append(row)
                    row = []
            
            if row:
                keyboard.append(row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.reply(text or "📂 **Main Menu**", reply_markup=reply_markup)
    
    async def handle_callback_query(self, callback_query):
        """Handle button clicks"""
        user_id = callback_query.from_user.id
        data = callback_query.data
        
        if not self.auth.is_premium(user_id):
            await callback_query.answer("⛔ Premium access required.", show_alert=True)
            return
        
        if data.startswith("menu_"):
            item_id = int(data.split("_")[1])
            await self.handle_menu_item(user_id, item_id, callback_query)
        elif data == "back":
            await self.handle_back_button(user_id, callback_query)
        
        await callback_query.answer()
    
    async def handle_menu_item(self, user_id, item_id, callback_query):
        """Handle menu item selection"""
        item = self.menu.get_menu_item(item_id)
        
        if not item:
            await callback_query.message.edit_text("❌ Content not found.")
            return
        
        if item['item_type'] == 'folder':
            await self.show_folder(user_id, item_id, callback_query)
        elif item['item_type'] == 'button':
            await self.deliver_content(user_id, item, callback_query)
        elif item['item_type'] == 'url':
            await self.handle_url(user_id, item, callback_query)
    
    async def show_folder(self, user_id, folder_id, callback_query):
        """Show folder contents"""
        menu_items = self.menu.get_menu_items(parent_id=folder_id)
        folder_info = self.menu.get_menu_item(folder_id)
        
        keyboard = []
        row = []
        
        for item in menu_items:
            callback_data = f"menu_{item['item_id']}"
            
            if item['item_type'] == 'folder':
                button_text = f"📁 {item['display_name']}"
            elif item['item_type'] == 'url':
                button_text = f"🔗 {item['display_name']}"
            else:
                button_text = item['display_name']
            
            row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
            
            if len(row) >= config.MAX_BUTTONS_PER_ROW:
                keyboard.append(row)
                row = []
        
        if row:
            keyboard.append(row)
        
        # Add Back button if not in root
        if folder_info and folder_info['parent_id'] != 0:
            keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        folder_name = folder_info['display_name'] if folder_info else "Folder"
        
        await callback_query.message.edit_text(
            f"📂 **{folder_name}**",
            reply_markup=reply_markup
        )
    
    async def deliver_content(self, user_id, item, callback_query):
        """Deliver content from database channel"""
        content_data = item['content_data']
        
        if 'channel_id' in content_data and 'message_id' in content_data:
            channel_id = content_data['channel_id']
            message_id = content_data['message_id']
            
            success = await self.delivery.forward_content(user_id, channel_id, message_id)
            
            if success:
                await callback_query.message.reply("✅ Content delivered! (Expires in 3 hours)")
            else:
                await callback_query.message.reply("❌ Failed to deliver content.")
        else:
            await callback_query.message.reply("❌ Invalid content configuration.")
    
    async def handle_url(self, user_id, item, callback_query):
        """Handle URL content"""
        content_data = item['content_data']
        
        if 'url' in content_data:
            url = content_data['url']
            await callback_query.message.reply(f"🔗 Click here: {url}")
        else:
            await callback_query.message.reply("❌ Invalid URL configuration.")
    
    async def handle_back_button(self, user_id, callback_query):
        """Handle back button navigation"""
        # Simplified: Go to root
        await self.show_main_menu(callback_query.message, "🔙 Returned to main menu")
