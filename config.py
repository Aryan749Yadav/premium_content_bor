"""
Configuration and constants for the Premium Content Bot
"""

# Bot Configuration
BOT_TOKEN = "8503320755:AAEfdX41jXqRjVk8mfBIZoqCkPCXKR7m-m4"  # Replace with your actual token
ADMIN_IDS = [8130609678]  # Your Telegram user ID(s)

# MongoDB Configuration
MONGODB_URI = "mongodb+srv://Test:aloksingh@cluster0.iomykdc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DATABASE_NAME = "premium_content_bot"

# Database channel configuration
DATABASE_CHANNEL_ID = -1003761591150  # Your private channel ID

# Time settings (in seconds)
CONTENT_EXPIRY_TIME = 3 * 60 * 60  # 3 hours
CLEANUP_INTERVAL = 300  # 5 minutes

# Bot settings
MAX_FOLDER_DEPTH = 10
MAX_BUTTONS_PER_ROW = 2


