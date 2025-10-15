import redis

try:
    # Connect to Redis running in Docker
    r = redis.Redis(host='localhost', port=6379, db=0)
    
    # Test setting and getting a key
    r.set('test_key', 'Hello from Docker Redis!')
    value = r.get('test_key')
    
    print("✅ Connection successful! Redis returned:", value.decode())
except Exception as e:
    print("❌ Connection failed:", e)
