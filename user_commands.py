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
    
    async def handle_start(self, update, context):
        """Handle /start command"""
        user_id = update.message.from_user.id
        
        welcome_text = (
            "🎬 **Premium Content Bot**\n\n"
            "Welcome to your exclusive content platform!\n"
            "Navigate using the buttons below to access premium content.\n\n"
            "⚠️ All content is time-limited and watermarked for security."
        )
        
        if self.auth.is_premium(user_id):
            await self.show_main_menu(update.message, context, welcome_text)
        else:
            await context.bot.send_message(
                chat_id=update.message.chat_id,
                text="⛔ **Access Denied**\n\nYou do not have premium access.\nPlease contact the admin for subscription details."
            )
    
    async def show_main_menu(self, message, context, text=""):
        """Show main menu to premium users"""
        if not self.auth.is_premium(message.from_user.id):
            await context.bot.send_message(
                chat_id=message.chat_id,
                text="⛔ Premium access required."
            )
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
        await context.bot.send_message(
            chat_id=message.chat_id,
            text=text or "📂 **Main Menu**",
            reply_markup=reply_markup
        )
    
    async def handle_callback_query(self, update, context):
        """Handle button clicks"""
        callback_query = update.callback_query
        user_id = callback_query.from_user.id
        data = callback_query.data
        
        if not self.auth.is_premium(user_id):
            await callback_query.answer("⛔ Premium access required.", show_alert=True)
            return
        
        if data.startswith("menu_"):
            item_id = int(data.split("_")[1])
            await self.handle_menu_item(user_id, item_id, callback_query, context)
        elif data == "back":
            await self.handle_back_button(user_id, callback_query, context)
        
        await callback_query.answer()
    
    async def handle_menu_item(self, user_id, item_id, callback_query, context):
        """Handle menu item selection"""
        item = self.menu.get_menu_item(item_id)
        
        if not item:
            await callback_query.edit_message_text("❌ Content not found.")
            return
        
        if item['item_type'] == 'folder':
            await self.show_folder(user_id, item_id, callback_query, context)
        elif item['item_type'] == 'button':
            await self.deliver_content(user_id, item, callback_query, context)
        elif item['item_type'] == 'url':
            await self.handle_url(user_id, item, callback_query, context)
    
    async def show_folder(self, user_id, folder_id, callback_query, context):
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
        
        await callback_query.edit_message_text(
            f"📂 **{folder_name}**",
            reply_markup=reply_markup
        )
    
    async def deliver_content(self, user_id, item, callback_query, context):
        """Deliver content from database channel"""
        content_data = item['content_data']
        
        if 'channel_id' in content_data and 'message_id' in content_data:
            channel_id = content_data['channel_id']
            message_id = content_data['message_id']
            
            success = await self.delivery.forward_content(user_id, channel_id, message_id)
            
            if success:
                await context.bot.send_message(
                    chat_id=callback_query.message.chat_id,
                    text="✅ Content delivered! (Expires in 3 hours)"
                )
            else:
                await context.bot.send_message(
                    chat_id=callback_query.message.chat_id,
                    text="❌ Failed to deliver content."
                )
        else:
            await context.bot.send_message(
                chat_id=callback_query.message.chat_id,
                text="❌ Invalid content configuration."
            )
    
    async def handle_url(self, user_id, item, callback_query, context):
        """Handle URL content"""
        content_data = item['content_data']
        
        if 'url' in content_data:
            url = content_data['url']
            await context.bot.send_message(
                chat_id=callback_query.message.chat_id,
                text=f"🔗 Click here: {url}"
            )
        else:
            await context.bot.send_message(
                chat_id=callback_query.message.chat_id,
                text="❌ Invalid URL configuration."
            )
    
    async def handle_back_button(self, user_id, callback_query, context):
        """Handle back button navigation"""
        await self.show_main_menu(callback_query.message, context, "🔙 Returned to main menu")
