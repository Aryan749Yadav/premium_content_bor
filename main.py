"""
Main bot application - Entry point
"""
import asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram import Update
import config
from user_commands import UserCommands
from admin_commands import AdminCommands
from utils import setup_logging
from content_delivery import ContentDelivery

# Setup logging
logger = setup_logging()

class PremiumContentBot:
    def __init__(self):
        self.application = Application.builder().token(config.BOT_TOKEN).build()
        
        # Initialize handlers
        self.user_commands = UserCommands(self.application.bot)
        self.admin_commands = AdminCommands(self.application.bot)
        self.content_delivery = ContentDelivery(self.application.bot)
        
        # Add handlers
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup all command and callback handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.handle_start))
        self.application.add_handler(CommandHandler("admin", self.handle_admin))
        
        # Callback query handler for button clicks
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Message handler for admin button creation (simplified)
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def handle_start(self, update: Update, context):
        """Handle /start command"""
        await self.user_commands.handle_start(update, context)
    
    async def handle_admin(self, update: Update, context):
        """Handle /admin command"""
        command_parts = context.args
        await self.admin_commands.handle_admin_command(update, context, command_parts)
    
    async def handle_callback(self, update: Update, context):
        """Handle inline keyboard button clicks"""
        await self.user_commands.handle_callback_query(update, context)
    
    async def handle_message(self, update: Update, context):
        """Handle regular messages (for admin flows)"""
        pass
    
    async def cleanup_task(self):
        """Periodic cleanup task"""
        while True:
            try:
                await self.content_delivery.cleanup_expired_content()
                await asyncio.sleep(config.CLEANUP_INTERVAL)
            except Exception as e:
                logger.error(f"Cleanup task error: {e}")
    
    def run(self):
        """Start the bot"""
        logger.info("Starting Premium Content Bot...")
        
        # Start cleanup task
        loop = asyncio.get_event_loop()
        loop.create_task(self.cleanup_task())
        
        # Start bot
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    bot = PremiumContentBot()
    bot.run()
