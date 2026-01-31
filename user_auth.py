cat > user_auth.py << 'EOF'
"""
Premium user authentication and management
"""
from database import MongoDB
import config

class UserAuth:
    def __init__(self):
        self.db = MongoDB()
    
    def is_premium(self, user_id):
        """Check if user has premium access"""
        return self.db.is_premium(user_id)
    
    def is_admin(self, user_id):
        """Check if user is admin"""
        return user_id in config.ADMIN_IDS
    
    def add_premium_user(self, user_id, added_by):
        """Add user to premium list"""
        return self.db.add_premium_user(user_id, added_by)
    
    def remove_premium_user(self, user_id):
        """Remove user from premium list"""
        return self.db.remove_premium_user(user_id)
    
    def list_premium_users(self):
        """Get all active premium users"""
        return self.db.list_premium_users()
EOF
