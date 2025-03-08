# Install dependencies if not installed: pip install requests dotenv pyotp pandas plotly
import requests
import os
import pyotp
import pandas as pd
import plotly.graph_objects as go
import sys
from dotenv import load_dotenv

# ✅ Fix UnicodeEncodeError for Windows
sys.stdout.reconfigure(encoding='utf-8')

# 🎯 Step 1: Load environment variables from .env file
load_dotenv()

# Angel One API credentials
API_KEY = os.getenv("ANGELONE_API_KEY")
CLIENT_ID = os.getenv("ANGELONE_CLIENT_ID")
PASSWORD = os.getenv("ANGELONE_MPIN")
TOTP_SECRET = os.getenv("ANGELONE_TOTP_SECRET")

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
    "clientcode": CLIENT_ID,
    "password": PASSWORD,
    "totp": pyotp.TOTP(TOTP_SECRET).now()
}

try:
    # 🔐 Make the POST request for authentication
    response = requests.post(url, json=payload, headers=headers)
    response_data = response.json()

    # ✅ Authentication Check
    if response_data.get("status"):
        print("✅ Login successful!")
        auth_token = response_data["data"]["jwtToken"]
        headers["Authorization"] = f"Bearer {auth_token}"  # Add auth token to headers
    else:
        print("❌ Login failed. Error:", response_data.get("message"))
        exit()

except Exception as e:
    print("⚠ An error occurred:", str(e))
    exit()

# 🎯 Step 2: Fetch Live Stock Data from Angel One API
def fetch_live_stock_data(symbol="RELIANCE", exchange="NSE"):
    payload = {
        "mode": "FULL",
        "exchangeTokens": {exchange: ["3045"]}  # Ensure this token is correct
    }
    
    url = "https://apiconnect.angelone.in/rest/secure/angelbroking/market/v1/quote/"
    response = requests.post(url, json=payload, headers=headers)
    
    try:
        response_data = response.json()
    except Exception as e:
        print("❌ Failed to parse API response:", str(e))
        return None
    
    # ✅ Debugging: Print API response structure
    print("📊 Raw API Response:", response_data)

    # ✅ Check if "data" key exists
    if "data" in response_data and response_data["data"]:
        try:
            market_data = response_data["data"].get("fetched", [])
            if not market_data:
                print("❌ No market data available!")
                return None

            # ✅ Convert to DataFrame
            df = pd.DataFrame(market_data)

            # ✅ Rename `exchFeedTime` to `date`
            if "exchFeedTime" in df.columns:
                df.rename(columns={"exchFeedTime": "date"}, inplace=True)

            print("✅ Market Data Fetched Successfully!")
            return df
        except Exception as e:
            print("⚠ Error while creating DataFrame:", str(e))
            return None
    else:
        print("❌ API returned no data!")
        return None

# Fetch Data
df = fetch_live_stock_data()

# ✅ Check if Data is Available
if df is None or df.empty:
    print("⚠ No data available!")
    exit()

# Convert Date Column to Pandas Datetime Format
df["date"] = pd.to_datetime(df["date"], errors="coerce")  # Handle invalid dates
df.set_index("date", inplace=True)

# 🎯 Step 3: Calculate Supertrend Indicator
def calculate_supertrend(df, multiplier=3, period=10):
    high_low = df["high"] - df["low"]
    high_close = abs(df["high"] - df["close"].shift())
    low_close = abs(df["low"] - df["close"].shift())
    tr = high_low.combine(high_close, max).combine(low_close, max)
    atr = tr.rolling(window=period).mean()

    basic_upper = (df["high"] + df["low"]) / 2 + multiplier * atr
    basic_lower = (df["high"] + df["low"]) / 2 - multiplier * atr

    supertrend = [basic_upper[0]]
    supertrend
    for i in range(1, len(df)):
        if df["close"][i] <= supertrend[-1]:
            supertrend.append(basic_upper[i])
        else:
            supertrend.append(basic_lower[i])

    return supertrend

# Forward Fill Missing Data
df.fillna(method="ffill", inplace=True)

# Calculate Supertrend
supertrend = calculate_supertrend(df)
print("Supertrend type:", type(supertrend))

# 🎯 Step 4: Plot Candlestick Chart with Supertrend
def plot_stock_data(df, supertrend):
    fig = go.Figure(data=[go.Candlestick(x=df.index,
                                         open=df["open"],
                                         high=df["high"],
                                         low=df["low"],
                                         close=df["close"])])
    
    fig.add_trace(go.Scatter(x=df.index, y=supertrend, mode="lines", name="Supertrend",
                             line=dict(dash="dash")))

    fig.update_layout(title="Reliance Industries Stock with Supertrend",
                      xaxis_title="Date",
                      yaxis_title="Price",
                      xaxis=dict(rangeslider=dict(visible=True), type="date"))
    
    fig.show()

# Show Plot
plot_stock_data(df, supertrend)
