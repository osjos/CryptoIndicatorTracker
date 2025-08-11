
#!/usr/bin/env python

import requests
import pandas as pd
from datetime import date

APPLE_TOP_FREE_URL = "https://rss.applemarketingtools.com/api/v2/us/apps/top-free/200/apps.json"
COINBASE_APP_ID = "886427730"  # Apple ID for Coinbase app

def fetch_coinbase_rank_row():
    """Return dict: {date, store, chart, rank} where rank is 1..200 or 9999 if not listed."""
    r = requests.get(APPLE_TOP_FREE_URL, timeout=30)
    r.raise_for_status()
    items = r.json().get("feed", {}).get("results", [])
    rank = 9999
    for i, app in enumerate(items, start=1):
        if str(app.get("id")) == COINBASE_APP_ID:
            rank = i
            break
    return {
        "date": date.today().isoformat(),
        "store": "apple_us",
        "chart": "top_free_overall",
        "rank": int(rank)
    }

def fetch_coinbase_rank_df() -> pd.DataFrame:
    """Convenience wrapper returning a single-row DataFrame."""
    return pd.DataFrame([fetch_coinbase_rank_row()])
