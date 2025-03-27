import requests
import os
import pyotp
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
import datetime
import time
from dotenv import load_dotenv
import pandas_ta as ta

# Fix UnicodeEncodeError for Windows
sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables from .env file
load_dotenv()

# Angel One API credentials
API_KEY = os.getenv("ANGELONE_API_KEY")
CLIENT_ID = os.getenv("ANGELONE_CLIENT_ID")
PASSWORD = os.getenv("ANGELONE_MPIN")
TOTP_SECRET = os.getenv("ANGELONE_TOTP_SECRET")

# Global variables
auth_token = None
headers = None
trading_symbol = "SBIN-EQ"
symbol_token = "3045"  # SBIN by default
exchange = "NSE"
quantity = 1
active_position = None
entry_price = None
stop_loss = None
take_profit = None

import requests
import os
from dotenv import load_dotenv
import pyotp

# Load environment variables from .env file
load_dotenv()

# API endpoint
url = "https://apiconnect.angelone.in/rest/auth/angelbroking/user/v1/loginByPassword"

# Headers
headers = {
    "Content-type": "application/json",
    "X-ClientLocalIP": "127.0.0.1",
    "X-ClientPublicIP": "127.0.0.1",
    "X-MACAddress": "00:00:00:00:00:00",
    "Accept": "application/json",
    "X-PrivateKey": '7Ee2qnqp',
    "X-UserType": "USER",
    "X-SourceID": "WEB"
}

# Request body
payload = {
    "clientcode": os.getenv("ANGELONE_CLIENT_ID"),
    "password": os.getenv("ANGELONE_MPIN"),
    "totp": pyotp.TOTP(os.getenv("ANGELONE_TOTP_SECRET")).now()
}

try:
    # Make the POST request
    response = requests.post(url, json=payload, headers=headers)
    response_data = response.json()

    # Check if the login was successful
    if response_data.get("status"):
        print("Login successful!")
        print("Response:", response_data)
    else:
        print("Login failed. Error:", response_data.get("message"))
except Exception as e:
    print("An error occurred:", str(e))


def execute_buy_order(symbol_token,trading_symbol, quantity, stop_loss_price=None):
    url = "https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/placeOrder"
    print(exchange)
    # Setting up order parameters
    payload = {
        "exchange": exchange,
        "tradingsymbol": trading_symbol,
        "symboltoken" : symbol_token,
        "quantity": quantity,
        "disclosedquantity": 0,
        "transactiontype": "SELL",
        "duration" : "DAY",
        "ordertype": "MARKET",
        "producttype": "INTRADAY",
        "variety": "NORMAL"
    }
    headers = {
        'X-PrivateKey': '7Ee2qnqp',
        'Accept': 'application/json',
        'X-SourceID': 'WEB',
        'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
        'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
        'X-MACAddress': 'MAC_ADDRESS',
        'X-UserType': 'USER',
        'Authorization': 'Bearer eyJhbGciOiJIUzUxMiJ9.eyJ1c2VybmFtZSI6Ikg3NjQ5MyIsInJvbGVzIjowLCJ1c2VydHlwZSI6IlVTRVIiLCJ0b2tlbiI6ImV5SmhiR2NpT2lKU1V6STFOaUlzSW5SNWNDSTZJa3BYVkNKOS5leUoxYzJWeVgzUjVjR1VpT2lKamJHbGxiblFpTENKMGIydGxibDkwZVhCbElqb2lkSEpoWkdWZllXTmpaWE56WDNSdmEyVnVJaXdpWjIxZmFXUWlPallzSW5OdmRYSmpaU0k2SWpNaUxDSmtaWFpwWTJWZmFXUWlPaUpsWVdZMVpqZGpZUzB4T0daa0xUTTJORGt0WVRkbE15MDRPRFpoWVRoa1pUTXpOVGtpTENKcmFXUWlPaUowY21Ga1pWOXJaWGxmZGpJaUxDSnZiVzVsYldGdVlXZGxjbWxrSWpvMkxDSndjbTlrZFdOMGN5STZleUprWlcxaGRDSTZleUp6ZEdGMGRYTWlPaUpoWTNScGRtVWlmU3dpYldZaU9uc2ljM1JoZEhWeklqb2lZV04wYVhabEluMTlMQ0pwYzNNaU9pSjBjbUZrWlY5c2IyZHBibDl6WlhKMmFXTmxJaXdpYzNWaUlqb2lTRGMyTkRreklpd2laWGh3SWpveE56UXlPVEl3TlRZeUxDSnVZbVlpT2pFM05ESTRNek01T0RJc0ltbGhkQ0k2TVRjME1qZ3pNems0TWl3aWFuUnBJam9pTWpNM05UY3pNbUV0TnpKaVpTMDBNalF3TFdFM09XSXRaakpoT0dOak5qSmlOelkzSWl3aVZHOXJaVzRpT2lJaWZRLmNZVWxjbFRrTm9NRm43UGFnTlNMckpadTN0SDN4cHBRSjBCcjh3c0JZNjRGUFBIVmNHdUVyRGhoSGxGN3lPYWkwdGhKRVpiMXptWnp1c1F6OXp3ZkoyRVRCRTR6M3ZoX24tV2lsdFN1MGxoYmRlME9kNzBjWk95YkJsYk9pMVFjNjh3aVM4Sl85YUZTOWZsRVJpNmhvSjAzT21WMktCNllPRGhiZzJGQl9hdyIsIkFQSS1LRVkiOiI3RWUycW5xcCIsImlhdCI6MTc0MjgzNDE2MiwiZXhwIjoxNzQyOTIwNTYyfQ.SVKypuoizgHRlVRkU2HlaiN8pzXWRybuB3bEDFc-hnJ8o36QZt5A16o63HPymYN3Y4FoyNbsDuoffkkr9Z62pg',
        'Accept': 'application/json',
        'X-SourceID': 'WEB',
        'Content-Type': 'application/json'
    }
    # If stop loss is provided, use STOPLOSS variety
    if stop_loss_price:
        payload["stoploss"] = stop_loss_price
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()
        
        if response_data.get("status"):
            print(f"✅ sell order placed successfully! Order ID: {response_data.get('data', {}).get('orderid')}")
            return True
        else:
            print(f"❌ Failed to place buy order: {response_data.get('message')}")
            return False
    except Exception as e:
        print(f"⚠ Error placing buy order: {str(e)}")
        return False
    
execute_buy_order(symbol_token,trading_symbol, quantity)