"""
Admin-only command handlers
"""
from user_auth import UserAuth
from menu_manager import MenuManager
import config

class AdminCommands:
    def __init__(self, bot):
        self.bot = bot
        self.auth = UserAuth()
        self.menu = MenuManager()
    
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
            await self.start_button_creation(update.message, context)
        else:
            await context.bot.send_message(
                chat_id=update.message.chat_id,
                text="❌ Unknown admin command."
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
    
    async def start_button_creation(self, message, context):
        """Start the button creation process"""
        await context.bot.send_message(
            chat_id=message.chat_id,
            text="🔄 Button creation process started.\nPlease send:\n1. Button name\n2. Content type (link/url/folder)\n3. Content data\n\nOr use /cancel to abort."
        )
