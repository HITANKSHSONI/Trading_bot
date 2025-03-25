from flask import Flask, request, jsonify
import threading
from Live_trading_with_Supertrend_ultra_final_lite import topgun

app = Flask(__name__)

@app.route("/apply_supertrend", methods=["POST"])
def apply_supertrend():
    """API endpoint to trigger the Supertrend calculation."""
    data = request.json

    # Extract data from the frontend payload
    trading_symbol = data.get("tradingsymbol")  # Match exact key from frontend
    symbol_token = data.get("symboltoken")      # Match exact key from frontend
    exchange = data.get("exchange")
    quantity = data.get("quantity")

    # Validate required fields
    if not all([trading_symbol, symbol_token, exchange, quantity]):
        return jsonify({"error": "Missing required parameters"}), 400

    # Run the trading script in a separate thread
    thread = threading.Thread(target=topgun, args=(trading_symbol, symbol_token, exchange, quantity))
    thread.start()

    return jsonify({"message": "Supertrend strategy applied successfully", "trading_symbol": trading_symbol, "symbol_token": symbol_token})

if __name__ == "__main__":
    app.run(debug=True, port=5000)