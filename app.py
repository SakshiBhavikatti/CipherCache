import time
from flask import Flask, render_template, request
from modules.secure_cache_manager import SecureCacheManager

app = Flask(__name__)
secure_cache = SecureCacheManager()

# Global counters
stats = {"hits": 0, "misses": 0, "total": 0, "avg_latency": 0}

@app.route("/", methods=["GET", "POST"])
def index():
    result = ""
    status = ""
    latency = 0

    if request.method == "POST":
        query = request.form.get("query")

        start_time = time.time()  # start timer
        cached_data = secure_cache.get_secure_cache(query)

        if cached_data:
            status = "✅ Cache Hit (Decrypted Data)"
            result = cached_data["result"]
            stats["hits"] += 1
        else:
            status = "❌ Cache Miss — Fetching from Database..."
            # Simulated data fetch
            data = {"query": query, "result": f"Fetched data for {query}"}
            secure_cache.set_secure_cache(query, data)
            result = data["result"]
            stats["misses"] += 1

        latency = round((time.time() - start_time) * 1000, 2)
        stats["total"] += 1
        # Update average latency
        stats["avg_latency"] = round(
            (stats["avg_latency"] * (stats["total"] - 1) + latency) / stats["total"], 2
        )

    return render_template(
        "index.html",
        result=result,
        status=status,
        stats=stats,
        latency=latency,
    )

if __name__ == "__main__":
    app.run(debug=True)
