from flask import Flask, request, jsonify
import subprocess
import threading
import os

app = Flask(__name__)

def run_trading_script(trading_symbol, symbol_token, exchange, quantity):
    """Runs the trading script with updated parameters."""
    env_vars = {
        "TRADING_SYMBOL": trading_symbol,
        "SYMBOL_TOKEN": symbol_token,
        "EXCHANGE": exchange,
        "QUANTITY": str(quantity)
    }
    
    process = subprocess.Popen(["python", "Live_trading_with_Supertrend_final.py"],
                               env={**os.environ, **env_vars},
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    stdout, stderr = process.communicate()
    print(stdout.decode())
    if stderr:
        print(stderr.decode())

@app.route("/apply_supertrend", methods=["POST"])
def apply_supertrend():
    """API endpoint to trigger the Supertrend calculation."""
    data = request.json
    
    trading_symbol = data.get("trading_symbol")
    symbol_token = data.get("symbol_token")
    exchange = data.get("exchange")
    quantity = data.get("quantity")
    
    if not all([trading_symbol, symbol_token, exchange, quantity]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    # Run the trading script in a separate thread to avoid blocking
    thread = threading.Thread(target=run_trading_script, args=(trading_symbol, symbol_token, exchange, quantity))
    thread.start()
    
    return jsonify({"message": "Supertrend strategy applied successfully"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
