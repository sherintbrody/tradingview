# classifier.py

def classify_candle(open_price, high, low, close):
    """
    Classify a candle based on body percentage of total range.

    Body % = (|Close - Open| / (High - Low)) * 100

    > 50%  → ERC (Extended Range Candle)
    < 50%  → Base
    = 50%  → Indecisive
    """
    total_range = high - low

    if total_range == 0:
        return {
            "body_pct": 0.0,
            "classification": "Base",
            "direction": "Neutral"
        }

    body = abs(close - open_price)
    body_pct = round((body / total_range) * 100, 2)

    # Using a small tolerance for "equal to 50%"
    tolerance = 0.5  # 0.5% tolerance band around 50%

    if body_pct > 50 + tolerance:
        classification = "ERC"
    elif body_pct < 50 - tolerance:
        classification = "Base"
    else:
        classification = "Indecisive"

    # Direction
    if close > open_price:
        direction = "Bullish"
    elif close < open_price:
        direction = "Bearish"
    else:
        direction = "Neutral"

    return {
        "body_pct": body_pct,
        "classification": classification,
        "direction": direction
    }


def process_candles(candles_raw):
    """Process raw candle data and add classification."""
    processed = []
    for c in candles_raw:
        info = classify_candle(c["open"], c["high"], c["low"], c["close"])
        processed.append({
            **c,
            "body_pct": info["body_pct"],
            "classification": info["classification"],
            "direction": info["direction"]
        })
    return processed
