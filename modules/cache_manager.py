import redis
import json
import time

class CacheManager:
    def __init__(self, host='localhost', port=6379, db=0):
        try:
            self.client = redis.Redis(host=host, port=port, db=db)
            self.client.ping()
            print("✅ Connected to Redis cache successfully.")
        except Exception as e:
            print("❌ Failed to connect to Redis:", e)
            self.client = None

    def set_cache(self, key, value, expiry=None):
        """Store data in cache (optionally set expiry in seconds)"""
        if self.client:
            self.client.set(key, value)
            if expiry:
                self.client.expire(key, expiry)
            print(f"✅ Cached key '{key}' successfully.")
        else:
            print("⚠️ Redis not connected.")

    def get_cache(self, key):
        """Retrieve data from cache"""
        if self.client:
            value = self.client.get(key)
            if value:
                print(f"📦 Cache hit for key '{key}'.")
                return value
            else:
                print(f"🚫 Cache miss for key '{key}'.")
                return None
        else:
            print("⚠️ Redis not connected.")
            return None

    def delete_cache(self, key):
        """Delete a key from cache"""
        if self.client:
            self.client.delete(key)
            print(f"🗑️ Deleted cache key '{key}'.")
        else:
            print("⚠️ Redis not connected.")

    def clear_cache(self):
        """Clear all cache data"""
        if self.client:
            self.client.flushdb()
            print("🧹 Cleared all cache data.")
        else:
            print("⚠️ Redis not connected.")