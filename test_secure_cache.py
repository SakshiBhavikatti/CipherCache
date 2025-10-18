from modules.secure_cache_manager import SecureCacheManager

secure_cache = SecureCacheManager()

# Example data
data = {
    "user_id": "U1",
    "query": "patient_record_A",
    "result": "Sensitive details about patient A"
}

# Store securely in cache
secure_cache.set_secure_cache("record_A", data, expiry=120)

# Retrieve and decrypt
retrieved = secure_cache.get_secure_cache("record_A")
print("\n🔓 Retrieved decrypted data:", retrieved)

# Delete cache
secure_cache.delete_secure_cache("record_A")
