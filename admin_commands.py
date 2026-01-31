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
    
    async def handle_admin_command(self, message, command_parts):
        """Route admin commands to appropriate handlers"""
        user_id = message.from_user.id
        
        if not self.auth.is_admin(user_id):
            await message.answer("⛔ This command is for admins only.")
            return
        
        command = command_parts[0].lower() if command_parts else ""
        
        if command == "add" and len(command_parts) > 1:
            await self.add_premium_user(message, command_parts[1])
        elif command == "remove" and len(command_parts) > 1:
            await self.remove_premium_user(message, command_parts[1])
        elif command == "listusers":
            await self.list_premium_users(message)
        elif command == "export":
            await self.export_menu(message)
        elif command == "button":
            await self.start_button_creation(message)
        else:
            await message.answer("❌ Unknown admin command.")
    
    async def add_premium_user(self, message, target_user_id):
        """Add user to premium list"""
        try:
            user_id = int(target_user_id)
            if self.auth.add_premium_user(user_id, message.from_user.id):
                await message.answer(f"✅ User {user_id} added to premium list.")
            else:
                await message.answer("❌ Failed to add user.")
        except ValueError:
            await message.answer("❌ Invalid user ID. Please provide a numeric ID.")
    
    async def remove_premium_user(self, message, target_user_id):
        """Remove user from premium list"""
        try:
            user_id = int(target_user_id)
            if self.auth.remove_premium_user(user_id):
                await message.answer(f"✅ User {user_id} removed from premium list.")
            else:
                await message.answer("❌ User not found or already removed.")
        except ValueError:
            await message.answer("❌ Invalid user ID.")
    
    async def list_premium_users(self, message):
        """List all premium users"""
        users = self.auth.list_premium_users()
        
        if not users:
            await message.answer("📭 No premium users found.")
            return
        
        response = "👑 **Premium Users:**\n\n"
        for user in users:
            response += f"• User ID: `{user['user_id']}`\n"
            response += f"  Added by: `{user['added_by']}`\n"
            response += f"  Date: {user['added_date']}\n\n"
        
        await message.answer(response)
    
    async def export_menu(self, message):
        """Export menu structure"""
        menu_json = self.menu.export_menu()
        
        # Save to file
        with open("data/menu_export.json", "w") as f:
            f.write(menu_json)
        
        # Send file to admin
        with open("data/menu_export.json", "rb") as f:
            await message.answer_document(
                document=f,
                caption="📁 Menu structure exported successfully."
            )
    
    async def start_button_creation(self, message):
        """Start the button creation process"""
        # This would initiate a conversation flow
        # For simplicity, showing basic response
        await message.answer(
            "🔄 Button creation process started.\n"
            "Please send:\n"
            "1. Button name\n"
            "2. Content type (link/url/folder)\n"
            "3. Content data\n\n"
            "Or use /cancel to abort."
        )
