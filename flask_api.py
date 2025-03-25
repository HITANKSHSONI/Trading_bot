from flask import Flask, request, jsonify
import threading
from Live_trading_with_Supertrend_ultra_final_lite import topgun

app = Flask(__name__)

@app.route("/apply_supertrend", methods=["POST"])
def apply_supertrend():
    """API endpoint to trigger the Supertrend calculation."""
    try:
        # Ensure the request contains JSON
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        # Get JSON data
        data = request.get_json()

        # Extract data from the frontend payload
        trading_symbol = data.get("tradingsymbol")
        symbol_token = data.get("symboltoken")
        exchange = data.get("exchange", "NSE")
        quantity = data.get("quantity")

        # Validate required fields
        if not all([trading_symbol, symbol_token, quantity]):
            return jsonify({"error": "Missing required parameters"}), 400

        # Run the trading script in a separate thread
        thread = threading.Thread(target=topgun, args=(trading_symbol, symbol_token, exchange, quantity))
        thread.start()

        return jsonify({
            "message": "Supertrend strategy applied successfully", 
            "trading_symbol": trading_symbol, 
            "symbol_token": symbol_token
        }), 200

    except Exception as e:
        # Catch and log any unexpected errors
        print(f"Error in apply_supertrend: {str(e)}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

# Additional CORS and error handling (if needed)
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS if you're running frontend and backend on different ports

if __name__ == "__main__":
    app.run(debug=True, port=5000)