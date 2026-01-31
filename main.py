"""
Main bot application - Entry point
"""
import asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from telegram import Update
import config
from user_commands import UserCommands
from admin_commands import AdminCommands, BUTTON_NAME, BUTTON_TYPE, BUTTON_CONTENT, BUTTON_PARENT
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
        
        # Admin button creation conversation handler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("admin", self.handle_admin_start)],
            states={
                BUTTON_PARENT: [
                    CallbackQueryHandler(self.admin_commands.button_parent_callback, pattern="^(parent_|cancel)")
                ],
                BUTTON_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.admin_commands.button_name)
                ],
                BUTTON_TYPE: [
                    CallbackQueryHandler(self.admin_commands.button_type_callback, pattern="^(type_|cancel)")
                ],
                BUTTON_CONTENT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.admin_commands.button_content)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.admin_commands.cancel)],
        )
        
        self.application.add_handler(conv_handler)
        
        # Callback query handler for button clicks (user navigation)
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Message handler for regular messages
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def handle_start(self, update: Update, context):
        """Handle /start command"""
        await self.user_commands.handle_start(update, context)
    
    async def handle_admin(self, update: Update, context):
        """Handle /admin command with arguments"""
        command_parts = context.args
        await self.admin_commands.handle_admin_command(update, context, command_parts)
    
    async def handle_admin_start(self, update: Update, context):
        """Handle /admin command to start conversation"""
        command_parts = context.args
        
        # If no arguments, start button creation
        if not command_parts:
            return await self.admin_commands.start_button_creation(update, context)
        else:
            # Handle other admin commands
            return await self.admin_commands.handle_admin_command(update, context, command_parts)
    
    async def handle_callback(self, update: Update, context):
        """Handle inline keyboard button clicks"""
        await self.user_commands.handle_callback_query(update, context)
    
    async def handle_message(self, update: Update, context):
        """Handle regular messages"""
        # Check if it's part of admin conversation
        if update.message.text.startswith('/'):
            return
        
        # Check if user is in conversation
        user_id = update.message.from_user.id
        if hasattr(self.admin_commands, 'temp_data') and user_id in self.admin_commands.temp_data:
            # Let conversation handler deal with it
            return
        
        # Otherwise, ignore or send help
        await update.message.reply_text(
            "🤖 **Premium Content Bot**\n\n"
            "Use /start to access premium content\n"
            "Admins: Use /admin for management"
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
