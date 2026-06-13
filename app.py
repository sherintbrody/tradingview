from flask import Flask, render_template, request, jsonify
from oanda_client import fetch_candles
from classifier import process_candles
import os

app = Flask(__name__)

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


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    instruments = data.get("instruments", DEFAULT_INSTRUMENTS)
    candle_count = min(data.get("candle_count", 30), 100)

    results = {}
    for instrument in instruments[:10]:
        results[instrument] = {}
        for tf in TIMEFRAMES:
            raw = fetch_candles(instrument, tf, count=candle_count)
            classified = process_candles(raw)
            results[instrument][tf] = classified

    return jsonify(results)


@app.route("/api/summary", methods=["POST"])
def summary():
    data = request.get_json()
    instruments = data.get("instruments", DEFAULT_INSTRUMENTS)

    summary_data = []
    for instrument in instruments[:10]:
        row = {"instrument": instrument}
        for tf in TIMEFRAMES:
            raw = fetch_candles(instrument, tf, count=5)
            classified = process_candles(raw)
            if classified:
                latest = classified[-1]
                row[tf] = {
                    "classification": latest["classification"],
                    "body_pct": latest["body_pct"],
                    "close_position_pct": latest["close_position_pct"],
                    "direction": latest["direction"],
                    "close": latest["close"],
                    "is_marubozu": latest["is_marubozu"]
                }
            else:
                row[tf] = {
                    "classification": "N/A",
                    "body_pct": 0,
                    "close_position_pct": 0,
                    "direction": "N/A",
                    "close": 0,
                    "is_marubozu": False
                }
        summary_data.append(row)

    return jsonify(summary_data)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
