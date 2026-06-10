# app.py
from flask import Flask, render_template, request, jsonify
from oanda_client import fetch_candles
from classifier import process_candles

app = Flask(__name__)

# Default instruments - user can modify this list
# REPLACE WITH (new):
DEFAULT_INSTRUMENTS = [
    "XAU_USD",
    "US30_USD",
    "NAS100_USD",
    "EUR_USD",
    "GBP_USD",
    "GBP_JPY",
    "USD_JPY",
    "AUD_USD"
]

TIMEFRAMES = ["Daily", "Weekly", "Monthly"]


@app.route("/")
def dashboard():
    return render_template("dashboard.html",
                           default_instruments=DEFAULT_INSTRUMENTS,
                           timeframes=TIMEFRAMES)


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """
    Expects JSON: {
        "instruments": ["EUR_USD", "GBP_USD", ...],
        "candle_count": 30
    }
    Returns classified candle data for all instruments across all timeframes.
    """
    data = request.get_json()
    instruments = data.get("instruments", DEFAULT_INSTRUMENTS)
    candle_count = data.get("candle_count", 30)

    results = {}

    for instrument in instruments:
        results[instrument] = {}
        for tf in TIMEFRAMES:
            raw = fetch_candles(instrument, tf, count=candle_count)
            classified = process_candles(raw)
            results[instrument][tf] = classified

    return jsonify(results)


@app.route("/api/summary", methods=["POST"])
def summary():
    """
    Returns a summary: latest candle classification for each instrument/timeframe.
    """
    data = request.get_json()
    instruments = data.get("instruments", DEFAULT_INSTRUMENTS)

    summary_data = []

    for instrument in instruments:
        row = {"instrument": instrument}
        for tf in TIMEFRAMES:
            raw = fetch_candles(instrument, tf, count=5)
            classified = process_candles(raw)
            if classified:
                latest = classified[-1]
                row[tf] = {
                    "classification": latest["classification"],
                    "body_pct": latest["body_pct"],
                    "direction": latest["direction"],
                    "close": latest["close"]
                }
            else:
                row[tf] = {
                    "classification": "N/A",
                    "body_pct": 0,
                    "direction": "N/A",
                    "close": 0
                }
        summary_data.append(row)

    return jsonify(summary_data)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
