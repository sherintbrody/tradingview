from flask import Flask, render_template, request, jsonify, send_from_directory
from oanda_client import fetch_candles
from classifier import process_candles
import os

app = Flask(__name__)

DEFAULT_INSTRUMENTS = [
    "XAU_USD",
    "US30_USD",
    "NAS100_USD",
    "SPX500_USD",
    "EUR_USD",
    "GBP_USD",
    "GBP_JPY",
    "EUR_JPY",
    "AUD_JPY",
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
    return {"status": "ok"}, 200


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        app.root_path,
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon"
    )


@app.route("/favicon-16x16.png")
def favicon16():
    return send_from_directory(
        app.root_path,
        "favicon-16x16.png",
        mimetype="image/png"
    )


@app.route("/favicon-32x32.png")
def favicon32():
    return send_from_directory(
        app.root_path,
        "favicon-32x32.png",
        mimetype="image/png"
    )


@app.route("/apple-touch-icon.png")
def apple_touch():
    return send_from_directory(
        app.root_path,
        "apple-touch-icon.png",
        mimetype="image/png"
    )


@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    instruments = data.get("instruments", DEFAULT_INSTRUMENTS)
    candle_count = min(data.get("candle_count", 50), 200)

    results = {}
    for instrument in instruments[:10]:
        results[instrument] = {}
        for tf in TIMEFRAMES:
            raw = fetch_candles(instrument, tf, count=candle_count + 15)
            classified = process_candles(raw)
            results[instrument][tf] = (
                classified[-candle_count:]
                if len(classified) > candle_count
                else classified
            )

    return jsonify(results)


@app.route("/api/summary", methods=["POST"])
def summary():
    data = request.get_json()
    instruments = data.get("instruments", DEFAULT_INSTRUMENTS)

    summary_data = []
    for instrument in instruments[:10]:
        row = {"instrument": instrument}
        for tf in TIMEFRAMES:
            raw = fetch_candles(instrument, tf, count=20)
            classified = process_candles(raw)
            if classified:
                latest = classified[-1]
                row[tf] = {
                    "classification":     latest["classification"],
                    "structural_role":    latest["structural_role"],
                    "body_pct":           latest["body_pct"],
                    "close_position_pct": latest["close_position_pct"],
                    "range_vs_avg":       latest["range_vs_avg"],
                    "direction":          latest["direction"],
                    "close":              latest["close"],
                    "is_marubozu":        latest["is_marubozu"],
                    "is_explosive":       latest["is_explosive"]
                }
            else:
                row[tf] = {
                    "classification": "N/A", "structural_role": "N/A",
                    "body_pct": 0, "close_position_pct": 0,
                    "range_vs_avg": 0, "direction": "N/A",
                    "close": 0, "is_marubozu": False, "is_explosive": False
                }
        summary_data.append(row)

    return jsonify(summary_data)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
