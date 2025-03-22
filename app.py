from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import json
import os
import logging
from datetime import datetime
import pyotp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading.log'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)
# Update CORS configuration to explicitly allow all methods
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Angel One API Configuration
ANGEL_API_URL = "https://apiconnect.angelone.in"
API_KEY = os.getenv("ANGELONE_API_KEY")
CLIENT_ID = os.getenv("ANGELONE_CLIENT_ID")
PASSWORD = os.getenv("ANGELONE_MPIN")
TOTP_SECRET = os.getenv("ANGELONE_TOTP_SECRET")

# Global variable for access token
ACCESS_TOKEN = None

def login_to_angel_one():
    global ACCESS_TOKEN
    try:
        # API endpoint for login
        url = f"{ANGEL_API_URL}/rest/auth/angelbroking/user/v1/loginByPassword"
        
        # Headers
        headers = {
            "Content-type": "application/json",
            "X-ClientLocalIP": "127.0.0.1",
            "X-ClientPublicIP": "127.0.0.1",
            "X-MACAddress": "00:00:00:00:00:00",
            "Accept": "application/json",
            "X-PrivateKey": API_KEY,
            "X-UserType": "USER",
            "X-SourceID": "WEB"
        }
        
        # Generate TOTP
        totp = pyotp.TOTP(TOTP_SECRET).now()
        
        # Request body for login
        payload = {
            "clientcode": CLIENT_ID,
            "password": PASSWORD,
            "totp": totp
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()
        
        if response_data.get("status"):
            ACCESS_TOKEN = response_data["data"]["jwtToken"]
            logging.info("✅ Login successful!")
            return True
        else:
            logging.error(f"❌ Login failed: {response_data.get('message')}")
            return False
            
    except Exception as e:
        logging.error(f"⚠ Login error: {str(e)}")
        return False

def get_headers():
    if not ACCESS_TOKEN:
        if not login_to_angel_one():
            raise Exception("Failed to obtain access token")
    
    return {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-UserType': 'USER',
        'X-SourceID': 'WEB',
        'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
        'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
        'X-MACAddress': 'MAC_ADDRESS',
        'X-PrivateKey': API_KEY
    }

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/place_order', methods=['POST', 'OPTIONS'])
def place_order():
    # Handle preflight request
    if request.method == 'OPTIONS':
        return '', 204

    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'message': 'Content-Type must be application/json'
            }), 400

        order_data = request.get_json()
        logging.info(f"Received order data: {json.dumps(order_data, indent=2)}")
        
        # Validate required fields
        required_fields = ['tradingsymbol', 'symboltoken', 'transactiontype', 'quantity']
        missing_fields = [field for field in required_fields if field not in order_data]
        if missing_fields:
            return jsonify({
                'success': False,
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400

        # Add default values for optional fields
        order_data.setdefault('variety', 'NORMAL')
        order_data.setdefault('exchange', 'NSE')
        order_data.setdefault('ordertype', 'MARKET')
        order_data.setdefault('producttype', 'INTRADAY')
        order_data.setdefault('duration', 'DAY')
        order_data.setdefault('stoploss', '0')

        # First attempt to place order
        response = requests.post(
            f"{ANGEL_API_URL}/rest/secure/angelbroking/order/v1/placeOrder",
            headers=get_headers(),
            json=order_data
        )
        
        response_data = response.json()
        logging.info(f"API Response: {json.dumps(response_data, indent=2)}")

        # If token expired, try to login again and retry the order
        if response_data.get("errorcode") == "AB2001":
            logging.info("Token expired, attempting to refresh...")
            if login_to_angel_one():
                response = requests.post(
                    f"{ANGEL_API_URL}/rest/secure/angelbroking/order/v1/placeOrder",
                    headers=get_headers(),
                    json=order_data
                )
                response_data = response.json()
                logging.info(f"API Response after token refresh: {json.dumps(response_data, indent=2)}")

        # Handle final response
        if response_data.get("status"):
            return jsonify({
                'success': True,
                'message': 'Order placed successfully',
                'data': response_data
            })
        else:
            error_message = response_data.get("message", "Unknown error")
            error_code = response_data.get("errorcode", "")
            return jsonify({
                'success': False,
                'message': f'Failed to place order: {error_message} (Code: {error_code})',
                'error': response_data
            }), 400

    except Exception as e:
        logging.error(f"Error in place_order: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

if __name__ == '__main__':
    # Initial login attempt
    if not login_to_angel_one():
        logging.error("Failed to login during startup")
    
    logging.info("Starting Flask server...")
    app.run(debug=True, port=8000, host='0.0.0.0') 