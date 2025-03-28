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
print(API_KEY)
# Global variables
auth_token = None
headers = None
trading_symbol = "HFCL-EQ"
symbol_token = "21951"  # SBIN by default
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
    "X-PrivateKey": API_KEY,
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
        'X-PrivateKey': API_KEY,
        'Accept': 'application/json',
        'X-SourceID': 'WEB',
        'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
        'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
        'X-MACAddress': 'MAC_ADDRESS',
        'X-UserType': 'USER',
        'Authorization': 'Bearer eyJhbGciOiJIUzUxMiJ9.eyJ1c2VybmFtZSI6Ikg3NjQ5MyIsInJvbGVzIjowLCJ1c2VydHlwZSI6IlVTRVIiLCJ0b2tlbiI6ImV5SmhiR2NpT2lKU1V6STFOaUlzSW5SNWNDSTZJa3BYVkNKOS5leUoxYzJWeVgzUjVjR1VpT2lKamJHbGxiblFpTENKMGIydGxibDkwZVhCbElqb2lkSEpoWkdWZllXTmpaWE56WDNSdmEyVnVJaXdpWjIxZmFXUWlPallzSW5OdmRYSmpaU0k2SWpNaUxDSmtaWFpwWTJWZmFXUWlPaUppTm1RMVpXWTFPUzAyTldGbUxUTTJObVV0WWpFd05DMDBNV05tT1RsaU9XUTVaR1FpTENKcmFXUWlPaUowY21Ga1pWOXJaWGxmZGpJaUxDSnZiVzVsYldGdVlXZGxjbWxrSWpvMkxDSndjbTlrZFdOMGN5STZleUprWlcxaGRDSTZleUp6ZEdGMGRYTWlPaUpoWTNScGRtVWlmU3dpYldZaU9uc2ljM1JoZEhWeklqb2lZV04wYVhabEluMTlMQ0pwYzNNaU9pSjBjbUZrWlY5c2IyZHBibDl6WlhKMmFXTmxJaXdpYzNWaUlqb2lTRGMyTkRreklpd2laWGh3SWpveE56UXpNak01T0RJeExDSnVZbVlpT2pFM05ETXhOVE15TkRFc0ltbGhkQ0k2TVRjME16RTFNekkwTVN3aWFuUnBJam9pWVRaa05EUTNOelF0T1dKa01DMDBPVFppTFdJMU1HTXRNakU0WWpBMk1UUXlNVGMxSWl3aVZHOXJaVzRpT2lJaWZRLkt4RmRmUEpxY3JaRXVfeGxvejladVZZTmstMU9KNEJIaWJGNHEycVhHTS1uVzZwQUpXRHE3TFpFOXIwdTRRbVVBSXZITURpRmRyV1N4dG9qd0Q4WW1sZDh4ekVzUTlNRHh6VnpyazVGblhpYmwwVlNwVm9OYlRHcXJlRGhsT3VadldKaTJvbTYya0c5MUJlNEd4Z1d6R1ptSEVkdjJOY2RHTnFmWjVfWmJMYyIsIkFQSS1LRVkiOiJ0a1NSVG1XRiIsImlhdCI6MTc0MzE1MzQyMSwiZXhwIjoxNzQzMjM5ODIxfQ.zL5GnaCfpSCJaOo150Zs7vT-URU1t9tlVS1yYFM57Of3Ed6dcALpb_HfMN3n8Fc6geZT5dezALwh1p0qKUn9tA',
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