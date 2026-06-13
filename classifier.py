def classify_candle(open_price, high, low, close):
    """
    Candle Classification:

    1. ERC (Extended Range Candle):
       - Body >= 80% of candle range
       - Close near high (bullish) or near low (bearish)
       - Strong directional move

    2. Base Candle:
       - Body < 50% of candle range
       - Consolidation / indecision

    3. Failed ERC:
       - Wide/explosive candle range
       - BUT body is 50% or less of range
       - Looks like ERC but fails to close high/low
       - The "50% candle"

    4. Marubozu:
       - Body >= 95% of candle range
       - Almost no wicks
       - Extreme momentum candle

    Body % = (|Close - Open| / (High - Low)) * 100
    Close Position % = where close sits in the range
    """
    total_range = high - low

    if total_range == 0:
        return {
            "body_pct": 0.0,
            "close_position_pct": 50.0,
            "classification": "Base",
            "direction": "Neutral",
            "is_marubozu": False
        }

    body = abs(close - open_price)
    body_pct = round((body / total_range) * 100, 2)

    # Where does the close sit in the range? 0% = at low, 100% = at high
    close_position = round(((close - low) / total_range) * 100, 2)

    # Direction
    if close > open_price:
        direction = "Bullish"
    elif close < open_price:
        direction = "Bearish"
    else:
        direction = "Neutral"

    # Upper and lower wick percentages
    if direction == "Bullish":
        upper_wick = high - close
        lower_wick = open_price - low
    else:
        upper_wick = high - open_price
        lower_wick = close - low

    upper_wick_pct = round((upper_wick / total_range) * 100, 2)
    lower_wick_pct = round((lower_wick / total_range) * 100, 2)

    # ─── CLASSIFICATION ─────────────────────────────
    is_marubozu = False

    # MARUBOZU: Body >= 95% of range (almost no wicks)
    if body_pct >= 95:
        classification = "Marubozu"
        is_marubozu = True

    # ERC: Body >= 80% AND close near extreme
    # Bullish ERC: close in top 80% of range
    # Bearish ERC: close in bottom 20% of range
    elif body_pct >= 80:
        if direction == "Bullish" and close_position >= 80:
            classification = "ERC"
        elif direction == "Bearish" and close_position <= 20:
            classification = "ERC"
        else:
            # Has big body but didn't close at extreme
            classification = "Failed ERC"

    # FAILED ERC: Body between 50% and 80%
    # Explosive looking candle but body doesn't dominate
    elif body_pct >= 50:
        classification = "Failed ERC"

    # BASE: Body < 50%
    else:
        classification = "Base"

    return {
        "body_pct": body_pct,
        "close_position_pct": close_position,
        "upper_wick_pct": upper_wick_pct,
        "lower_wick_pct": lower_wick_pct,
        "classification": classification,
        "direction": direction,
        "is_marubozu": is_marubozu
    }


def process_candles(candles_raw):
    """Process raw candle data and add classification."""
    processed = []
    for c in candles_raw:
        info = classify_candle(c["open"], c["high"], c["low"], c["close"])
        processed.append({
            **c,
            "body_pct": info["body_pct"],
            "close_position_pct": info["close_position_pct"],
            "upper_wick_pct": info.get("upper_wick_pct", 0),
            "lower_wick_pct": info.get("lower_wick_pct", 0),
            "classification": info["classification"],
            "direction": info["direction"],
            "is_marubozu": info["is_marubozu"]
        })
    return processed
