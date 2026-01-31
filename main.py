"""
Main bot with SIMPLE ADMIN interface
"""
import asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram import Update
import config
from user_commands import UserCommands
from simple_admin import SimpleAdmin  # Changed from admin_commands
from utils import setup_logging
from content_delivery import ContentDelivery

# Setup logging
logger = setup_logging()

class PremiumContentBot:
    def __init__(self):
        self.application = Application.builder().token(config.BOT_TOKEN).build()
        
        # Initialize handlers
        self.user_commands = UserCommands(self.application.bot)
        self.simple_admin = SimpleAdmin(self.application.bot)  # Changed
        self.content_delivery = ContentDelivery(self.application.bot)
        
        # Add handlers
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup all command and callback handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.handle_start))
        self.application.add_handler(CommandHandler("admin", self.handle_admin))
        
        # Admin callback handlers (for simple admin interface)
        self.application.add_handler(CallbackQueryHandler(self.handle_admin_callback, 
                                                        pattern="^(admin_|create_|select_|add_|setup_|folder_|view_)"))
        
        # User callback handlers (menu navigation)
        self.application.add_handler(CallbackQueryHandler(self.handle_user_callback))
        
        # Message handler for responses
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def handle_start(self, update: Update, context):
        """Handle /start command"""
        await self.user_commands.handle_start(update, context)
    
    async def handle_admin(self, update: Update, context):
        """Handle /admin command"""
        command_parts = context.args
        await self.simple_admin.handle_admin_command(update, context, command_parts)
    
    async def handle_admin_callback(self, update: Update, context):
        """Handle admin interface callbacks"""
        await self.simple_admin.handle_callback(update, context)
    
    async def handle_user_callback(self, update: Update, context):
        """Handle user menu navigation"""
        await self.user_commands.handle_callback_query(update, context)
    
    async def handle_message(self, update: Update, context):
        """Handle text messages"""
        # First check if it's a response to admin actions
        await self.simple_admin.handle_message_response(update, context)
    
    async def cleanup_task(self):
        """Periodic cleanup"""
        while True:
            try:
                await self.content_delivery.cleanup_expired_content()
                await asyncio.sleep(config.CLEANUP_INTERVAL)
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    def run(self):
        """Start bot"""
        logger.info("Starting Premium Content Bot...")
        
        loop = asyncio.get_event_loop()
        loop.create_task(self.cleanup_task())
        
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    bot = PremiumContentBot()
    bot.run()
