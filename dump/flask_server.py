from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Store selected stock details
selected_stock = {"symboltoken": None, "quantity": None}

@app.route('/start_bot', methods=['POST'])
def start_bot():
    """Receive stock selection from frontend, including quantity."""
    global selected_stock

    data = request.get_json()
    if not data or "symboltoken" not in data or "quantity" not in data:
        return jsonify({"success": False, "message": "Missing stock token or quantity"}), 400

    selected_stock["symboltoken"] = data["symboltoken"]
    selected_stock["quantity"] = int(data["quantity"])  # Convert to integer

    return jsonify({"success": True, "message": f"Bot started with {selected_stock['symboltoken']} and quantity {selected_stock['quantity']}!"})

@app.route('/get_selected_stock', methods=['GET'])
def get_selected_stock():
    """Provide selected stock details to the backend."""
    return jsonify(selected_stock)

if __name__ == '__main__':
    app.run( port=5000, host="0.0.0.0")
