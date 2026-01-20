import json
import os
from config.settings import USER_DATA_FILE, PENDING_AUTH_FILE
from datetime import datetime

class DataManager:
    """Manages persistent storage of user data"""
    
    def __init__(self):
        self._ensure_data_directory()
        self.user_data = self.load_data(USER_DATA_FILE)
        self.pending_auth = self.load_data(PENDING_AUTH_FILE)
    
    def _ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        os.makedirs('data', exist_ok=True)
    
    def load_data(self, filename):
        """Load data from JSON file"""
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        return {}
    
    def save_data(self, data, filename):
        """Save data to JSON file"""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    def link_user(self, discord_id, cf_handle):
        """Link Discord ID with Codeforces handle"""
        self.user_data[str(discord_id)] = cf_handle
        self.save_data(self.user_data, USER_DATA_FILE)
    
    def get_cf_handle(self, discord_id):
        """Get Codeforces handle for Discord ID"""
        return self.user_data.get(str(discord_id))
    
    def add_pending_auth(self, discord_id, cf_handle, problem_id):
        """Add pending authentication request"""
        self.pending_auth[str(discord_id)] = {
            'cf_handle': cf_handle,
            'problem_id': problem_id,
            'timestamp': datetime.now().isoformat()
        }
        self.save_data(self.pending_auth, PENDING_AUTH_FILE)
    
    def get_pending_auth(self, discord_id):
        """Get pending authentication request"""
        return self.pending_auth.get(str(discord_id))
    
    def remove_pending_auth(self, discord_id):
        """Remove pending authentication request"""
        if str(discord_id) in self.pending_auth:
            del self.pending_auth[str(discord_id)]
            self.save_data(self.pending_auth, PENDING_AUTH_FILE)
