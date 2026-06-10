# oanda_client.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OANDA_API_KEY")
ACCOUNT_ID = os.getenv("OANDA_ACCOUNT_ID")
BASE_URL = os.getenv("OANDA_API_URL", "https://api-fxpractice.oanda.com")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

TIMEFRAME_MAP = {
    "Daily": "D",
    "Weekly": "W",
    "Monthly": "M"
}


def fetch_candles(instrument: str, granularity_label: str, count: int = 50):
    """
    Fetch candles from OANDA API.
    granularity_label: 'Daily', 'Weekly', or 'Monthly'
    """
    granularity = TIMEFRAME_MAP.get(granularity_label, "D")
    url = f"{BASE_URL}/v3/instruments/{instrument}/candles"

    params = {
        "granularity": granularity,
        "count": count,
        "price": "M"  # mid prices
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

        candles = []
        for c in data.get("candles", []):
            if not c["complete"]:
                continue
            mid = c["mid"]
            candles.append({
                "time": c["time"][:10],  # date only
                "open": float(mid["o"]),
                "high": float(mid["h"]),
                "low": float(mid["l"]),
                "close": float(mid["c"]),
                "volume": int(c["volume"])
            })
        return candles

    except requests.exceptions.RequestException as e:
        print(f"Error fetching {instrument} {granularity_label}: {e}")
        return []
