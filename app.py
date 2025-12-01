import time
from flask import Flask, render_template, request
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
    """Load the appropriate predictor based on selected dataset."""
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
    except Exception as e:
        print(f"⚠ Error loading predictor for {domain}: {e}")
        predictor = None


# Load default dataset
load_predictor("healthcare")

# Global counters
stats = {"hits": 0, "misses": 0, "total": 0, "avg_latency": 0}


@app.route("/set_dataset", methods=["POST"])
def set_dataset():
    """Switch datasets safely without breaking AES keys."""
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

    # ⭐ SAFE cache clearing — DO NOT flush complete Redis
    try:
        for key in secure_cache.client.scan_iter("*"):
            k = key.decode()

            if k.startswith(("HLC_", "hea_", "ACC_", "ban_", "ECM_", "eco_")):
                secure_cache.client.delete(key)

        print(f"🧹 Cleared dataset-specific cache for {selected}")

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

        # ---------------------------------------------------
        # CACHE HIT
        # ---------------------------------------------------
        if cached_data:
            status = "✅ Cache Hit (Decrypted Data)"

            # FIX: prevent KeyError by supporting predicted preload entries
            result = cached_data.get(
                "result",
                f"(Cached entity: {cached_data.get('entity_id')})"
            )

            stats["hits"] += 1

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

        # ---------------------------------------------------
        # CACHE MISS
        # ---------------------------------------------------
        else:
            status = "❌ Cache Miss — Fetching from Database..."
            data = {"query": query, "result": f"Fetched data for {query}"}
            secure_cache.set_secure_cache(query, data)
            result = data["result"]
            stats["misses"] += 1

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

        latency = round((time.time() - start_time) * 1000, 2)
        stats["total"] += 1
        stats["avg_latency"] = round(
            (stats["avg_latency"] * (stats["total"] - 1) + latency) / stats["total"],
            2
        )

    return render_template(
        "index.html",
        result=result,
        status=status,
        stats=stats,
        latency=latency,
        predicted_items=predicted_items,
        current_dataset=current_dataset
    )


if __name__ == "__main__":
    app.run(debug=True)
