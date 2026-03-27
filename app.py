import time
from flask import Flask, render_template, request, Response
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
from modules.secure_cache_manager import SecureCacheManager
from modules.predictor import Predictor

app = Flask(__name__)
secure_cache = SecureCacheManager()

# ---------------------------
# Dynamic Predictor Loading
# ---------------------------
predictor = None
current_dataset = "healthcare"


def load_predictor(domain):
    """Load predictor model for selected dataset."""
    global predictor
    try:
        if domain == "healthcare":
            predictor = Predictor("data/healthcare_requests.csv")
        elif domain == "banking":
            predictor = Predictor("data/banking_requests.csv")
        elif domain == "ecommerce":
            predictor = Predictor("data/ecommerce_requests.csv")
        else:
            predictor = Predictor("data/healthcare_requests.csv")  # fallback

        print(f"📌 Loaded predictor for dataset: {domain}")

    except Exception as e:
        print(f"⚠ Error loading predictor for {domain}: {e}")
        predictor = None


# Load default predictor
load_predictor("healthcare")

# ---------------------------
# Prometheus Metrics
# ---------------------------
cache_hits_metric = Counter('cache_hits_total', 'Total cache hits')
cache_misses_metric = Counter('cache_misses_total', 'Total cache misses')
total_queries_metric = Counter('total_queries', 'Total queries received')
avg_latency_metric = Gauge('avg_latency_ms', 'Average latency in milliseconds')
current_dataset_metric = Gauge('current_dataset', 'Current dataset indicator', ['dataset'])

# ✅ Initialize dataset metrics (clear old series completely)
for ds in ["healthcare", "banking", "ecommerce"]:
    current_dataset_metric.remove(ds)

current_dataset_metric.labels(dataset="healthcare").set(1)

# Global counters
stats = {"hits": 0, "misses": 0, "total": 0, "avg_latency": 0}


@app.route("/set_dataset", methods=["POST"])
def set_dataset():
    """Switch all systems to a new dataset."""
    global current_dataset

    selected = request.form.get("dataset")

    if not selected:
        return render_template(
            "index.html",
            result="",
            status="⚠ Please select a valid dataset.",
            stats=stats,
            latency=0,
            predicted_items=[],
            current_dataset=current_dataset
        )

    current_dataset = selected
    load_predictor(selected)

    # ✅ REMOVE old time series completely
    for ds in ["healthcare", "banking", "ecommerce"]:
        current_dataset_metric.remove(ds)

    # ✅ Set only active dataset
    current_dataset_metric.labels(dataset=selected).set(1)

    # ⭐ Correct Cache Clearing
    VALID_PREFIXES = ("hea_", "ban_", "eco_")

    try:
        deleted_count = 0
        for key in secure_cache.client.scan_iter("*"):
            k = key.decode()
            if k.startswith(VALID_PREFIXES):
                secure_cache.client.delete(key)
                deleted_count += 1

        print(f"🧹 Cleared {deleted_count} cache entries for dataset switch → {selected}")

    except Exception as e:
        print(f"⚠ Failed to clear dataset cache: {e}")

    return render_template(
        "index.html",
        result="",
        status=f"Dataset switched to {selected.capitalize()}",
        stats=stats,
        latency=0,
        predicted_items=[],
        current_dataset=current_dataset
    )


@app.route("/", methods=["GET", "POST"])
def index():
    result = ""
    status = ""
    latency = 0
    predicted_items = []

    if request.method == "POST":
        query = request.form.get("query").strip()
        start_time = time.time()

        cached_data = secure_cache.get_secure_cache(query)

        # CACHE HIT
        if cached_data:
            status = "✅ Cache Hit (Decrypted Data)"
            result = cached_data.get("result", f"(Cached entity: {cached_data.get('entity_id')})")
            stats["hits"] += 1
            cache_hits_metric.inc()

            if predictor:
                try:
                    predicted_items = predictor.preload_predictions(
                        secure_cache.set_secure_cache,
                        mode="recent",
                        recent=query,
                        top_k=3,
                        expiry=300
                    )
                except Exception as e:
                    print("Prediction error:", e)

        # CACHE MISS
        else:
            status = "❌ Cache Miss — Fetching from Database..."
            data = {"query": query, "result": f"Fetched data for {query}"}
            secure_cache.set_secure_cache(query, data)

            result = data["result"]
            stats["misses"] += 1
            cache_misses_metric.inc()

            if predictor:
                try:
                    predicted_items = predictor.preload_predictions(
                        secure_cache.set_secure_cache,
                        mode="global",
                        top_k=3,
                        expiry=300
                    )
                except Exception as e:
                    print("Prediction error:", e)

        # LATENCY & METRICS
        latency = round((time.time() - start_time) * 1000, 2)
        stats["total"] += 1
        total_queries_metric.inc()

        stats["avg_latency"] = round(
            (stats["avg_latency"] * (stats["total"] - 1) + latency) / stats["total"],
            2
        )

        avg_latency_metric.set(stats["avg_latency"])

    return render_template(
        "index.html",
        result=result,
        status=status,
        stats=stats,
        latency=latency,
        predicted_items=predicted_items,
        current_dataset=current_dataset
    )


# ---------------------------
# Prometheus Metrics Endpoint
# ---------------------------
@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(debug=True)