from modules.cache_manager import CacheManager

cache = CacheManager()

# Simulate caching a user query result
data = {"user": "U1", "query": "patient_record_A", "result": "Record details here"}
cache.set_cache("query1", data, expiry=60)

# Retrieve it
cached_data = cache.get_cache("query1")
print("Retrieved:", cached_data)

# Delete it
cache.delete_cache("query1")

# Clear all cache
# cache.clear_cache()
