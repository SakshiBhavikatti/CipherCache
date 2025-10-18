Just open a terminal and run this once:

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

docker run --name redis-cache -p 6379:6379 -d redis

You’ll see something like:

Unable to find image 'redis:latest' locally
latest: Pulling from library/redis...
Status: Downloaded newer image for redis:latest
<container-id>

✅ Done! Redis is now running.

You can check:

docker ps

It’ll show something like:

CONTAINER ID   IMAGE   COMMAND     PORTS        NAMES
abcd1234       redis   "redis..."  0.0.0.0:6379 redis-cache

If you ever want to stop it:

docker stop redis-cache

To start it again:

docker start redis-cache

python test_redis.py

python test_cache_manager.py

python test_encryptor.py

python app.py
