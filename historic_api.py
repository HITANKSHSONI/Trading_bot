import requests
import os
import pyotp
import pandas as pd
import plotly.graph_objects as go
import sys
import datetime
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

# API endpoint for login
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

# Request body for login
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
    to_date = last_week_end.strftime("%Y-%m-%d 15:30")        # Market closes at 03:30 PM IST

    payload = {
        "exchange": exchange,
        "symboltoken": symbol_token,
        "interval": "FIVE_MINUTE",
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

    print("📊 Raw API Response:", response_data)

    if "data" in response_data and response_data["data"]:
        df = pd.DataFrame(response_data["data"], columns=["date", "open", "high", "low", "close", "volume"])
        df["date"] = pd.to_datetime(df["date"])

        # Filter data to include only market working hours (09:15 to 15:30)
        df["time"] = df["date"].dt.time
        df = df[(df["time"] >= datetime.time(9, 15)) & (df["time"] <= datetime.time(15, 30))]
        df = df.drop(columns=["time"])

        # Remove weekends (if any data sneaks in)
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

# Forward Fill Missing Data
df.ffill(inplace=True)

# 🎯 Calculate Supertrend Indicator using pandas_ta
supertrend = ta.supertrend(df['high'], df['low'], df['close'], length=10, multiplier=2.0)
df = pd.concat([df, supertrend], axis=1)

# 🎯 Plot the Entire Week's Data in One Graph Using Rangebreaks with Adjusted Y-Axis
def plot_weekly_data_single_graph(df):
    fig = go.Figure()
    
    # Add candlestick trace
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name="Candlestick"
    ))
    
    # Add Supertrend line
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["SUPERT_10_2.0"],
        mode="lines",
        name="Supertrend",
        line=dict(dash="dash")
    ))
    
    # Calculate y-axis range with some padding
    y_min = df["low"].min() * 0.98  # 2% lower than the minimum
    y_max = df["high"].max() * 1.02  # 2% higher than the maximum

    fig.update_layout(
        title="Weekly Stock Data with Supertrend (Intraday: 9:15 to 15:30)",
        xaxis_title="Date/Time",
        yaxis_title="Price",
        yaxis=dict(range=[y_min, y_max])
    )
    
    # Use rangebreaks to remove non-trading hours and weekends from the x-axis
    fig.update_xaxes(
        rangebreaks=[
            # Hide weekends
            dict(bounds=["sat", "mon"]),
            # Hide hours outside trading session (using decimal hours: 9:15 = 9.25, 15:30 = 15.5)
            dict(bounds=[15.5, 9.25], pattern="hour")
        ]
    )
    
    fig.show()

# Show the plot in one graph
plot_weekly_data_single_graph(df)
