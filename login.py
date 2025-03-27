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
    "X-PrivateKey": os.getenv("ANGELONE_API_KEY"),
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
    