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

# Fix UnicodeEncodeError for Windows
sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables from .env file
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
        df.set_index("date", inplace=True)
        print("✅ Historical data fetched successfully:")
        print(df.tail())
        return df
    else:
        print("❌ API returned no historical data!")
        return None

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
                if df["date"].dt.tz is None:
                    df["date"] = df["date"].dt.tz_localize("Asia/Kolkata")
                required_cols = ["date", "open", "high", "low", "close", "volume"]
                df = df.filter(items=required_cols)
                print("✅ Live data fetched successfully:")
                print(df.tail())
                return df
    except Exception as e:
        print("❌ Failed to fetch live data:", str(e))
    
    return None

def update_live_data(live_df, new_data):
    if new_data is not None and not new_data.empty:
        required_cols = ["date", "open", "high", "low", "close", "volume"]
        new_data = new_data.filter(items=required_cols).set_index("date")
        if live_df.empty:
            combined = new_data
        else:
            combined = pd.concat([live_df, new_data])
            combined = combined[~combined.index.duplicated(keep='last')]
            combined.sort_index(inplace=True)
        return combined.tail(100)  # Keep only the latest 100 records
    return live_df

def create_figure(live_df):
    # Create a FigureWidget for candlestick and Supertrend
    fig = go.FigureWidget(data=[go.Candlestick(
        x=live_df.index,
        open=live_df["open"],
        high=live_df["high"],
        low=live_df["low"],
        close=live_df["close"],
        name="Candlestick"
    )])
    
    if "SUPERT_10_2.0" in live_df.columns:
        fig.add_scatter(x=live_df.index, y=live_df["SUPERT_10_2.0"],
                        mode="lines", name="Supertrend",
                        line=dict(dash="dash", color="blue"))
    
    y_min = live_df["low"].min() * 0.98
    y_max = live_df["high"].max() * 1.02
    fig.update_layout(title="Live Stock Data with Supertrend",
                      xaxis_title="Time",
                      yaxis_title="Price",
                      xaxis=dict(type="date"),
                      yaxis=dict(range=[y_min, y_max]))
    return fig

def update_figure(fig, live_df):
    # Update the candlestick trace (trace 0)
    fig.data[0].x = live_df.index
    fig.data[0].open = live_df["open"]
    fig.data[0].high = live_df["high"]
    fig.data[0].low = live_df["low"]
    fig.data[0].close = live_df["close"]
    
    # Update or add the Supertrend trace (if available)
    if "SUPERT_10_2.0" in live_df.columns:
        if len(fig.data) > 1:
            fig.data[1].x = live_df.index
            fig.data[1].y = live_df["SUPERT_10_2.0"]
        else:
            fig.add_scatter(x=live_df.index, y=live_df["SUPERT_10_2.0"],
                            mode="lines", name="Supertrend",
                            line=dict(dash="dash", color="blue"))
    else:
        # If Supertrend is not available and a trace exists, remove it.
        if len(fig.data) > 1:
            fig.data = tuple([fig.data[0]])
    
    y_min = live_df["low"].min() * 0.98
    y_max = live_df["high"].max() * 1.02
    fig.update_layout(yaxis=dict(range=[y_min, y_max]))

def main():
    login()
    live_df = fetch_historical_stock_data()
    if live_df is None:
        live_df = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        live_df.index.name = "date"
    
    # Calculate initial Supertrend and join with live_df
    supertrend = ta.supertrend(live_df['high'], live_df['low'], live_df['close'], length=10, multiplier=2.0)
    live_df = live_df.join(supertrend)
    
    # Create the FigureWidget once and display it
    fig = create_figure(live_df)
    fig.show()  # Opens the graph once
    
    while True:
        new_data = fetch_live_stock_data()
        live_df = update_live_data(live_df, new_data)
        
        if not live_df.empty:
            # Recalculate Supertrend, drop any old Supertrend columns, and join the new ones
            supertrend = ta.supertrend(live_df['high'], live_df['low'], live_df['close'], length=10, multiplier=2.0)
            live_df = live_df.drop(columns=supertrend.columns, errors='ignore')
            live_df = live_df.join(supertrend)
            print("✅ Updated Live Data:")
            print(live_df.tail())
            
            update_figure(fig, live_df)
        
        time.sleep(10)  # Fetch data every 10 seconds

if __name__ == "__main__":
    main()
