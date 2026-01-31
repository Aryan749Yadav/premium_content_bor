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
        
        # Callback query handlers
        # Admin callbacks (button creation)
        self.application.add_handler(CallbackQueryHandler(self.handle_admin_callback, pattern="^(create_|cancel_)"))
        # User callbacks (menu navigation) - catch all other callbacks
        self.application.add_handler(CallbackQueryHandler(self.handle_user_callback))
        
        # Message handler for all text messages (for button creation responses)
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def handle_start(self, update: Update, context):
        """Handle /start command"""
        await self.user_commands.handle_start(update, context)
    
    async def handle_admin(self, update: Update, context):
        """Handle /admin command"""
        command_parts = context.args
        await self.admin_commands.handle_admin_command(update, context, command_parts)
    
    async def handle_admin_callback(self, update: Update, context):
        """Handle admin callback queries (button creation menu)"""
        await self.admin_commands.handle_callback_query(update, context)
    
    async def handle_user_callback(self, update: Update, context):
        """Handle user callback queries (menu navigation)"""
        # First check if it's an admin callback (should have been caught already)
        query = update.callback_query
        data = query.data
        
        if data.startswith("create_") or data.startswith("cancel_"):
            # This should have been handled by admin callback handler
            return
        
        # Otherwise, it's a user menu navigation callback
        await self.user_commands.handle_callback_query(update, context)
    
    async def handle_message(self, update: Update, context):
        """Handle regular text messages"""
        # Check if it's a response to button creation
        user_id = update.message.from_user.id
        
        # If user is in button creation state, handle it
        if hasattr(self.admin_commands, 'user_states') and user_id in self.admin_commands.user_states:
            await self.admin_commands.handle_message_response(update, context)
            return
        
        # Otherwise, check if it's admin trying to use quick commands
        text = update.message.text
        
        # Check for quick add pattern without command
        if text and ' ' in text and len(text.split()) >= 3:
            # Could be a quick add attempt, forward to admin commands
            pass
        
        # Default response for other messages
        if not text.startswith('/'):
            await update.message.reply_text(
                "🤖 **Premium Content Bot**\n\n"
                "Use /start to access premium content\n"
                "Admins: Use /admin for management commands"
            )
    
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
