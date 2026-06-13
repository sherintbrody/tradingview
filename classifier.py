def classify_candle(open_price, high, low, close, avg_range=None):
    """
    Alfonso Moreno Set & Forget Classification:

    ERC (Extended Range Candle):
    - Body >= 75% of total range
    - Closes near extreme (top for bull, bottom for bear)
    - Role: Impulse (Leg-In / Leg-Out)

    Failed ERC:
    - Body <= 50% of range (long wick, failed to close at extreme)
    - BUT total candle RANGE is large/explosive (> 1.5x avg range)
    - Represents STRONG momentum that failed at close
    - Role: Impulse (Leg-In / Leg-Out) — NOT a base!

    Base / NRC (Non-Range Candle):
    - Body <= 50% of range
    - Total candle RANGE is small (low volatility, quiet candle)
    - Represents pause/consolidation
    - Role: Base ONLY

    Marubozu:
    - Body >= 95% of range
    - Almost zero wicks
    - Extreme momentum
    - Role: Strongest impulse candle

    Key insight:
    Failed ERC vs Base is separated by TOTAL RANGE SIZE
    not just body percentage alone.
    """

    total_range = high - low

    if total_range == 0:
        return {
            "body_pct": 0.0,
            "close_position_pct": 50.0,
            "upper_wick_pct": 0.0,
            "lower_wick_pct": 0.0,
            "range_vs_avg": 1.0,
            "classification": "Base",
            "structural_role": "Base",
            "direction": "Neutral",
            "is_marubozu": False,
            "is_explosive": False
        }

    body = abs(close - open_price)
    body_pct = round((body / total_range) * 100, 2)

    # Where does close sit in the full range? 0=low, 100=high
    close_position = round(((close - low) / total_range) * 100, 2)

    # Direction
    if close > open_price:
        direction = "Bullish"
    elif close < open_price:
        direction = "Bearish"
    else:
        direction = "Neutral"

    # Wick calculations
    if direction == "Bullish":
        upper_wick_pct = round(((high - close) / total_range) * 100, 2)
        lower_wick_pct = round(((open_price - low) / total_range) * 100, 2)
    else:
        upper_wick_pct = round(((high - open_price) / total_range) * 100, 2)
        lower_wick_pct = round(((close - low) / total_range) * 100, 2)

    # Range vs average (how explosive is this candle?)
    # avg_range is passed from process_candles using rolling average
    if avg_range and avg_range > 0:
        range_vs_avg = round(total_range / avg_range, 2)
    else:
        range_vs_avg = 1.0

    # Explosive candle threshold:
    # Range is 1.5x or more than the average candle range
    is_explosive = range_vs_avg >= 1.5

    # ────────────────────────────────────────────────
    # CLASSIFICATION LOGIC
    # ────────────────────────────────────────────────

    is_marubozu = False

    # 1. MARUBOZU: Body >= 95%, almost no wicks
    if body_pct >= 95:
        classification = "Marubozu"
        structural_role = "Leg-In/Leg-Out"
        is_marubozu = True

    # 2. ERC: Body >= 75%, closes near its extreme
    elif body_pct >= 75:
        # Bullish ERC: must close in top 25% of range
        # Bearish ERC: must close in bottom 25% of range
        if direction == "Bullish" and close_position >= 75:
            classification = "ERC"
            structural_role = "Leg-In/Leg-Out"
        elif direction == "Bearish" and close_position <= 25:
            classification = "ERC"
            structural_role = "Leg-In/Leg-Out"
        else:
            # Big body but didn't close at extreme → Failed ERC
            classification = "Failed ERC"
            structural_role = "Leg-In/Leg-Out"

    # 3. FAILED ERC vs BASE — both have body <= 50-75%
    # Key: separate by RANGE SIZE (explosive vs quiet)
    elif body_pct <= 50:
        if is_explosive:
            # Large range + small body = explosive move that failed
            # This is a Failed ERC (impulse, NOT a base!)
            classification = "Failed ERC"
            structural_role = "Leg-In/Leg-Out"
        else:
            # Small range + small body = quiet consolidation
            # This is a Base / NRC candle
            classification = "Base"
            structural_role = "Base"

    # 4. Body between 50-75%: borderline - check if explosive
    else:
        if is_explosive:
            classification = "Failed ERC"
            structural_role = "Leg-In/Leg-Out"
        else:
            classification = "Base"
            structural_role = "Base"

    return {
        "body_pct": body_pct,
        "close_position_pct": close_position,
        "upper_wick_pct": upper_wick_pct,
        "lower_wick_pct": lower_wick_pct,
        "range_vs_avg": range_vs_avg,
        "classification": classification,
        "structural_role": structural_role,
        "direction": direction,
        "is_marubozu": is_marubozu,
        "is_explosive": is_explosive
    }


def process_candles(candles_raw):
    """
    Process candles and classify using rolling average range.
    Uses last 10 candles rolling average to determine 'average range'.
    This lets us identify explosive vs quiet candles relatively.
    """
    if not candles_raw:
        return []

    # Calculate total ranges for all candles first
    ranges = [c["high"] - c["low"] for c in candles_raw]

    processed = []

    for i, c in enumerate(candles_raw):
        # Rolling average of last 10 candles (or however many exist)
        start = max(0, i - 10)
        window = ranges[start:i] if i > 0 else ranges[:1]
        avg_range = sum(window) / len(window) if window else ranges[i]

        info = classify_candle(
            c["open"], c["high"], c["low"], c["close"],
            avg_range=avg_range
        )

        processed.append({
            **c,
            "body_pct": info["body_pct"],
            "close_position_pct": info["close_position_pct"],
            "upper_wick_pct": info["upper_wick_pct"],
            "lower_wick_pct": info["lower_wick_pct"],
            "range_vs_avg": info["range_vs_avg"],
            "classification": info["classification"],
            "structural_role": info["structural_role"],
            "direction": info["direction"],
            "is_marubozu": info["is_marubozu"],
            "is_explosive": info["is_explosive"]
        })

    return processed
