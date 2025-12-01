import json
from modules.cache_manager import CacheManager
from modules.encryptor import HybridEncryptor

class SecureCacheManager:
    def __init__(self):
        self.cache = CacheManager()
        self.client = self.cache.client     # 🔥 EXPOSE REDIS CLIENT HERE
        self.encryptor = HybridEncryptor()
        print("🔐 Secure Cache Manager initialized successfully.")

    def set_secure_cache(self, key, value, expiry=None):
        """Encrypt and store data securely in cache"""
        try:
            data_str = json.dumps(value)
            encrypted_data = self.encryptor.encrypt(data_str)
            self.cache.set_cache(key, encrypted_data, expiry)
            print(f"✅ Securely cached key '{key}' with encryption.")
        except Exception as e:
            print(f"❌ Failed to secure cache for key '{key}': {e}")

    def get_secure_cache(self, key):
        """Retrieve and decrypt data from cache"""
        try:
            encrypted_data = self.cache.get_cache(key)
            if not encrypted_data:
                return None
            decrypted_data = self.encryptor.decrypt(encrypted_data)
            return json.loads(decrypted_data)
        except Exception as e:
            print(f"❌ Failed to decrypt cache for key '{key}': {e}")
            return None

    def delete_secure_cache(self, key):
        self.cache.delete_cache(key)

    def clear_secure_cache(self):
        self.cache.clear_cache()
