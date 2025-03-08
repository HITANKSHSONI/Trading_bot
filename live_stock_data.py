import requests
import os
import pyotp
import pandas as pd
import plotly.graph_objects as go
import sys
import datetime
import time
from dotenv import load_dotenv
import pandas_ta as ta  # Import pandas_ta

# ✅ Fix UnicodeEncodeError for Windows
sys.stdout.reconfigure(encoding='utf-8')

# 🎯 Load environment variables from .env file
load_dotenv()

# Angel One API credentials
API_KEY = os.getenv("ANGELONE_API_KEY")
CLIENT_ID = os.getenv("ANGELONE_CLIENT_ID")
PASSWORD = os.getenv("ANGELONE_MPIN")
TOTP_SECRET = os.getenv("ANGELONE_TOTP_SECRET")

# API Headers
headers = {
    "Content-type": "application/json",
    "X-PrivateKey": API_KEY,
    "X-UserType": "USER",
    "X-SourceID": "WEB"
}

# ✅ Login Function
def login():
    url = "https://apiconnect.angelone.in/rest/auth/angelbroking/user/v1/loginByPassword"
    payload = {
        "clientcode": CLIENT_ID,
        "password": PASSWORD,
        "totp": pyotp.TOTP(TOTP_SECRET).now()
    }
    response = requests.post(url, json=payload, headers=headers)
    response_data = response.json()
    
    if response_data.get("status"):
        print("✅ Login successful!")
        auth_token = response_data["data"]["jwtToken"]
        headers["Authorization"] = f"Bearer {auth_token}"
    else:
        print("❌ Login failed!", response_data.get("message"))
        exit()

# ✅ Fetch Historical Data
def fetch_historical_stock_data(symbol_token="3045", exchange="NSE"):
    today = datetime.datetime.now()
    last_week_start = today - datetime.timedelta(days=7)
    last_week_end = today - datetime.timedelta(days=1)

    from_date = last_week_start.strftime("%Y-%m-%d 09:15")
    to_date = last_week_end.strftime("%Y-%m-%d 15:30")

    payload = {
        "exchange": exchange,
        "symboltoken": symbol_token,
        "interval": "FIFTEEN_MINUTE",
        "fromdate": from_date,
        "todate": to_date
    }

    url = "https://apiconnect.angelone.in/rest/secure/angelbroking/historical/v1/getCandleData"
    response = requests.post(url, json=payload, headers=headers)
    response_data = response.json()
    
    if "data" in response_data and response_data["data"]:
        df = pd.DataFrame(response_data["data"], columns=["date", "open", "high", "low", "close", "volume"])
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        return df
    else:
        print("❌ API returned no historical data!")
        return None

# ✅ Fetch Live Data
def fetch_live_stock_data(symbol="RELIANCE", exchange="NSE"):
    url = "https://apiconnect.angelone.in/rest/secure/angelbroking/market/v1/quote/"
    payload = {"mode": "FULL", "exchangeTokens": {exchange: ["3045"]}}
    response = requests.post(url, json=payload, headers=headers)
    
    try:
        response_data = response.json()
        if "data" in response_data:
            market_data = response_data["data"].get("fetched", [])
            if market_data:
                df = pd.DataFrame(market_data)
                df.rename(columns={"exchFeedTime": "date"}, inplace=True)
                df["date"] = pd.to_datetime(df["date"])
                return df
    except Exception as e:
        print("❌ Failed to fetch live data:", str(e))
    
    return None

# ✅ Append Live Data to DataFrame
def update_live_data(live_df, new_data):
    if new_data is not None:
        live_df = pd.concat([live_df, new_data]).drop_duplicates().reset_index(drop=True)
        live_df.sort_values("date", inplace=True)
        return live_df.tail(100)  # Keep only latest 100 records
    return live_df

# ✅ Plot Candlestick Chart with Supertrend
def plot_live_chart(df):
    fig = go.Figure(data=[go.Candlestick(
        x=df.index, open=df["open"], high=df["high"], low=df["low"], close=df["close"]
    )])
    
    if "SUPERT_10_2.0" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["SUPERT_10_2.0"], mode="lines", name="Supertrend", line=dict(dash="dash", color="blue")
        ))
    
    fig.update_layout(title="Live Stock Data with Supertrend",
                      xaxis_title="Time",
                      yaxis_title="Price",
                      xaxis=dict(type="date"))
    
    fig.show()

# ✅ Main Function
def main():
    login()
    live_df = fetch_historical_stock_data()
    if live_df is None:
        live_df = pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])  # Empty DF

    while True:
        new_data = fetch_live_stock_data()
        live_df = update_live_data(live_df, new_data)

        if not live_df.empty:
            supertrend = ta.supertrend(live_df['high'], live_df['low'], live_df['close'], length=10, multiplier=2.0)
            live_df = pd.concat([live_df, supertrend], axis=1)
            plot_live_chart(live_df)

        time.sleep(10)  # Fetch data every 10 seconds

if __name__ == "__main__":
    main()