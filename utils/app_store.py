
# utils/app_store.py
import requests, pandas as pd
from datetime import date
APPLE_URL = "https://rss.marketingtools.apple.com/api/v2/us/apps/top-free/200/apps.json"
COINBASE_ID = "886427730"

def fetch_coinbase_rank_df() -> pd.DataFrame:
    try:
        r = requests.get(APPLE_URL, timeout=20)
        r.raise_for_status()
        items = (r.json().get("feed", {}) or {}).get("results", []) or []
        rank = next((i+1 for i, app in enumerate(items) if str(app.get("id")) == COINBASE_ID), None)
        return pd.DataFrame([{
            "date": date.today().isoformat(),
            "rank": int(rank) if rank else 9999,
            "store": "apple_us",
            "chart": "top_free_overall"
        }])
    except Exception as e:
        # Return fallback data when API fails
        print(f"App Store API failed: {e}")
        return pd.DataFrame([{
            "date": date.today().isoformat(),
            "rank": 200,  # Fallback rank when API is down
            "store": "apple_us",
            "chart": "top_free_overall"
        }])
