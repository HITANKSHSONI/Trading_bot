import requests
import os
import numpy as np
import pyotp
import pandas as pd
import pandas_ta as ta  
import plotly.graph_objects as go
import sys
import datetime
from dotenv import load_dotenv

# ✅ Fix UnicodeEncodeError for Windows
sys.stdout.reconfigure(encoding='utf-8')

# 🎯 Load environment variables from .env file
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
    response = requests.post(url, json=payload, headers=headers)
    response_data = response.json()

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

# 🎯 Fetch Historical Stock Data from Angel One API (Only Market Hours)
def fetch_historical_stock_data(symbol_token="3045", exchange="NSE"):
    today = datetime.datetime.now()
    last_week_start = today - datetime.timedelta(days=7)
    last_week_end = today - datetime.timedelta(days=1)

    from_date = last_week_start.strftime("%Y-%m-%d 09:15")  # Market opens at 09:15 AM IST
    to_date = last_week_end.strftime("%Y-%m-%d 15:30")  # Market closes at 03:30 PM IST

    payload = {
        "exchange": exchange,
        "symboltoken": symbol_token,
        "interval": "FIFTEEN_MINUTE",
        "fromdate": from_date,
        "todate": to_date
    }

    url = "https://apiconnect.angelone.in/rest/secure/angelbroking/historical/v1/getCandleData"
    response = requests.post(url, json=payload, headers=headers)

    try:
        response_data = response.json()
    except Exception as e:
        print("❌ Failed to parse API response:", str(e))
        return None

    if "data" in response_data and response_data["data"]:
        df = pd.DataFrame(response_data["data"], columns=["date", "open", "high", "low", "close", "volume"])
        df["date"] = pd.to_datetime(df["date"])
        
        # ✅ Fix: Extract time separately and filter correctly
        df["time"] = df["date"].dt.time  # Extract time separately
        df = df[(df["time"] >= datetime.time(9, 15)) & (df["time"] <= datetime.time(15, 30))]
        df = df.drop(columns=["time"])  # Drop extra column after filtering

        # ✅ Fix: Use index for weekday filtering
        df.set_index("date", inplace=True)
        df = df[~df.index.weekday.isin([5, 6])]  # Remove Saturday (5) & Sunday (6)

        print("✅ Historical Data Fetched Successfully!")
        return df
    else:
        print("❌ API returned no data!")
        return None

# Fetch Data
df = fetch_historical_stock_data()

if df is None or df.empty:
    print("⚠ No historical data available!")
    exit()

# 🎯 Apply Supertrend using `pandas_ta`
def apply_supertrend(df, period=7, multiplier=3):
    df = df.copy()  # Avoid modifying original DataFrame

    # ✅ Apply Supertrend Indicator from `pandas_ta`
    supertrend = df.ta.supertrend(length=period, multiplier=multiplier)

    # ✅ Add Supertrend columns to DataFrame
    df["supertrend"] = supertrend["SUPERT_7_3.0"]  # Supertrend value
    df["supertrend_direction"] = supertrend["SUPERTd_7_3.0"]  # Direction (+1 for uptrend, -1 for downtrend)

    return df

# Apply Supertrend
df = apply_supertrend(df)

# 🎯 Plot Historical Data with Supertrend (Market Hours Only)
def plot_historical_stock_data(df):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df["open"], high=df["high"], low=df["low"], close=df["close"], name="Candlestick"))

    # Supertrend Line
    fig.add_trace(go.Scatter(x=df.index, y=df["supertrend"], mode="lines", name="Supertrend", line=dict(color="orange", width=2)))

    # Trend Markers
    colors = df["supertrend_direction"].map({1: "green", -1: "red"})
    fig.add_trace(go.Scatter(x=df.index, y=df["close"], mode="markers", name="Trend", marker=dict(color=colors, size=5)))

    fig.update_layout(
        title="Historical Stock Data with Supertrend (Market Hours Only)",
        xaxis_title="Date",
        yaxis_title="Price",
        xaxis=dict(rangeslider=dict(visible=True), type="date"),
        yaxis=dict(fixedrange=False)
    )

    fig.show()

# Show Plot
plot_historical_stock_data(df)
