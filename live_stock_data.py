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
    "X-ClientLocalIP": "127.0.0.1",
    "X-ClientPublicIP": "127.0.0.1",
    "X-MACAddress": "00:00:00:00:00:00",
    "Accept": "application/json",
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

# ✅ Fetch Only Past Day's Historical Data
def fetch_historical_stock_data(symbol_token="3045", exchange="NSE"):
    today = datetime.datetime.now()
    past_day = today - datetime.timedelta(days=1)  # Fetch only yesterday's data
    from_date = past_day.strftime("%Y-%m-%d 09:15")
    to_date = past_day.strftime("%Y-%m-%d 15:30")

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
        # Historical data is already tz-aware; ensure the index is set accordingly
        df.set_index("date", inplace=True)
        print("✅ Historical data fetched successfully:")
        print(df.tail())
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
                # Convert the 'date' column to datetime and localize it to Asia/Kolkata
                df["date"] = pd.to_datetime(df["date"])
                if df["date"].dt.tz is None:
                    df["date"] = df["date"].dt.tz_localize("Asia/Kolkata")
                # Filter only the required columns
                required_cols = ["date", "open", "high", "low", "close", "volume"]
                df = df.filter(items=required_cols)
                print("✅ Live data fetched successfully:")
                print(df.tail())
                return df
    except Exception as e:
        print("❌ Failed to fetch live data:", str(e))
    
    return None

# ✅ Append Live Data to DataFrame
def update_live_data(live_df, new_data):
    if new_data is not None and not new_data.empty:
        required_cols = ["date", "open", "high", "low", "close", "volume"]
        new_data = new_data.filter(items=required_cols)
        # Reset index of live_df to merge using the 'date' column
        if not live_df.empty:
            live_df_reset = live_df.reset_index()
        else:
            live_df_reset = pd.DataFrame(columns=required_cols)
        combined = pd.concat([live_df_reset, new_data], ignore_index=True)
        combined.drop_duplicates(subset="date", inplace=True)
        combined.sort_values("date", inplace=True)
        combined.set_index("date", inplace=True)
        return combined.tail(100)  # Keep only latest 100 records
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
    
    # Calculate y-axis range with some padding
    y_min = df["low"].min() * 0.98  # 2% lower than the minimum
    y_max = df["high"].max() * 1.02  # 2% higher than the maximum

    fig.update_layout(title="Live Stock Data with Supertrend",
                      xaxis_title="Time",
                      yaxis_title="Price",
                      xaxis=dict(type="date"),
                      yaxis=dict(range=[y_min, y_max]))
    
    fig.show()

# ✅ Main Function
def main():
    login()
    live_df = fetch_historical_stock_data()
    if live_df is None:
        live_df = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    
    # Calculate initial Supertrend on historical data
    supertrend = ta.supertrend(live_df['high'], live_df['low'], live_df['close'], length=10, multiplier=2.0)
    live_df = pd.concat([live_df, supertrend], axis=1)
    plot_live_chart(live_df)
    
    while True:
        new_data = fetch_live_stock_data()
        live_df = update_live_data(live_df, new_data)

        if not live_df.empty:
            # Recalculate Supertrend with updated data
            supertrend = ta.supertrend(live_df['high'], live_df['low'], live_df['close'], length=10, multiplier=2.0)
            live_df = pd.concat([live_df.reset_index(), supertrend], axis=1).set_index("date")
            print("✅ Updated Live Data:")
            print(live_df.tail())  # Display last few rows to confirm live updates
            plot_live_chart(live_df)

        time.sleep(10)  # Fetch data every 10 seconds

if __name__ == "__main__":
    main()
