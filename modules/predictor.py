# predictor.py
import pandas as pd
from collections import Counter, defaultdict

class Predictor:
    """
    A simple, domain-agnostic Predictor that:
      - Loads your dataset CSV (healthcare / banking / e-commerce)
      - Learns global popularity of entity_id
      - Learns co-occurrence patterns (A → B → C)
      - Predicts next likely queries
      - Preloads predicted items into your cache
    """

    def __init__(self, dataset_path):
        self.df = pd.read_csv(dataset_path, parse_dates=['timestamp'])
        self.df.sort_values("timestamp", inplace=True)

        # Build per-session sequences for co-occurrence
        self.sessions = self._build_sessions()
        self.co_map = self._build_cooccurrence()

    # ----------------------------
    # INTERNAL HELPERS
    # ----------------------------
    def _build_sessions(self):
        sessions = defaultdict(list)
        for _, row in self.df.iterrows():
            sessions[row["session_id"]].append(row["entity_id"])
        return sessions

    def _build_cooccurrence(self):
        co = defaultdict(Counter)
        for sid, seq in self.sessions.items():
            for i in range(len(seq)-1):
                cur = seq[i]
                nxt = seq[i+1]
                co[cur][nxt] += 1
        return co

    # ----------------------------
    # PUBLIC METHODS
    # ----------------------------

    def top_k_popular(self, k=5):
        """Return global top-k most popular entity IDs."""
        freq = Counter(self.df["entity_id"])
        return [e for e, _ in freq.most_common(k)]

    def predict_next(self, recent_entity, k=3):
        """Predict next likely entity after recent_entity."""
        if recent_entity in self.co_map and len(self.co_map[recent_entity]) > 0:
            next_items = self.co_map[recent_entity].most_common(k)
            return [x for x, _ in next_items]

        # fallback → global popularity
        global_top = self.top_k_popular(k+1)
        return [g for g in global_top if g != recent_entity][:k]

    def preload_predictions(self, cache_setter, mode="global", recent=None, top_k=3, expiry=300):
        """
        Preload predicted items into the secure cache.
        cache_setter must accept: set(key, value, expiry)
        """
        if mode == "global":
            preds = self.top_k_popular(top_k)
        elif mode == "recent" and recent is not None:
            preds = self.predict_next(recent, k=top_k)
        else:
            raise ValueError("Invalid mode or missing recent query")

        domain_value = self.df["domain"].iloc[0]

        for entity in preds:
            value = {"entity_id": entity, "domain": domain_value}
            cache_setter(entity, value, expiry)

        return preds
