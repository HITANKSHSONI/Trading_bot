import requests
import os
import pyotp
import pandas as pd
import numpy as np
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
# The supertrend function returns: SUPERTd_10_2.0 (direction), SUPERT_10_2.0 (trend line), SUPERTl_10_2.0 (lower band), SUPERTh_10_2.0 (upper band)
# We only need the trend line and direction for our strategy
df['SUPERT_10_2.0'] = supertrend['SUPERT_10_2.0']  # Trend line
df['SUPERT_10_2.0_direction'] = supertrend['SUPERTd_10_2.0']  # Direction (1 for bullish, -1 for bearish)

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
    
    # Split Supertrend line by direction for coloring
    df['datetime'] = df.index  # Temporary column for plotting
    bullish = df[df['SUPERT_10_2.0_direction'] == 1]
    bearish = df[df['SUPERT_10_2.0_direction'] == -1]
    
    # Add Supertrend lines with colors
    fig.add_trace(go.Scatter(
        x=bullish['datetime'],
        y=bullish['SUPERT_10_2.0'],
        mode='lines',
        line=dict(color='green', dash='dash'),
        name='Supertrend (Bullish)'
    ))
    
    fig.add_trace(go.Scatter(
        x=bearish['datetime'],
        y=bearish['SUPERT_10_2.0'],
        mode='lines',
        line=dict(color='red', dash='dash'),
        name='Supertrend (Bearish)'
    ))
    
    # Calculate y-axis range with some padding
    y_min = min(df["low"].min(), df["SUPERT_10_2.0"].min()) * 0.98  # 2% lower
    y_max = max(df["high"].max(), df["SUPERT_10_2.0"].max()) * 1.02  # 2% higher

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
    
    df.drop('datetime', axis=1, inplace=True)  # Remove temporary column
    fig.show()

# Show the plot in one graph
plot_weekly_data_single_graph(df)

# ───────────────────────────────────────────────
# BUY/SELL LOGIC (Backtesting with Stop Loss and Take Profit)
# ───────────────────────────────────────────────

# 🎯 Helper function to check the trend direction
def check_trend_change(current_direction, previous_direction):
    return current_direction != previous_direction

# 🎯 Function to execute the trade using Angel One API (template for backtesting)
def execute_trade(action, symbol_token, quantity, price):
    if action == "buy":
        # Place buy order (backtesting: simply print)
        print(f"Executing Buy Order for {symbol_token}, Quantity: {quantity}, Price: {price}")
        # Integration with actual API would go here
    elif action == "sell":
        # Place sell order (backtesting: simply print)
        print(f"Executing Sell Order for {symbol_token}, Quantity: {quantity}, Price: {price}")
        # Integration with actual API would go here

# 🎯 Backtesting logic with Stop Loss and Take Profit
def apply_stop_loss_take_profit(df, symbol_token="3045", quantity=1):
    # Initialize positions
    position = None  # No position to start
    stop_loss = None
    entry_price = None  # Track entry price for P&L calculation
    total_profit_loss = 0  # Track total profit/loss

    # Iterate through each row of the dataframe
    for i in range(2, len(df)):  # Starting from 2 because we need at least 2 previous candles
        current_candle = df.iloc[i]
        previous_candle = df.iloc[i-1]
        
        # Get current and previous trend directions
        current_direction = current_candle['SUPERT_10_2.0_direction']
        previous_direction = previous_candle['SUPERT_10_2.0_direction']
        
        # Get the recent 3 candle lows and highs for stop loss
        last_3_candles_low = df['low'].iloc[i-3:i].min()
        last_3_candles_high = df['high'].iloc[i-3:i].max()

        # Check for trend direction change
        if check_trend_change(current_direction, previous_direction):
            # Bearish trend change
            if current_direction == -1:
                if position != "sell":
                    if position == "buy":
                        # Close buy position
                        execute_trade("sell", symbol_token, quantity, current_candle['close'])
                        total_profit_loss += (current_candle['close'] - entry_price) * quantity
                        position = None
                        entry_price = None
                        print(f"💰 Take Profit on Buy at {current_candle['close']} (Trend changed to Bearish)")
                    # Open new sell position
                    execute_trade("sell", symbol_token, quantity, current_candle['close'])
                    position = "sell"
                    entry_price = current_candle['close']
                    stop_loss = last_3_candles_high
                    print(f"📉 New Sell Position at {entry_price}, Stop Loss set to {stop_loss}")
            
            # Bullish trend change
            elif current_direction == 1:
                if position != "buy":
                    if position == "sell":
                        # Close sell position
                        execute_trade("buy", symbol_token, quantity, current_candle['close'])
                        total_profit_loss += (entry_price - current_candle['close']) * quantity
                        position = None
                        entry_price = None
                        print(f"💰 Take Profit on Sell at {current_candle['close']} (Trend changed to Bullish)")
                    # Open new buy position
                    execute_trade("buy", symbol_token, quantity, current_candle['close'])
                    position = "buy"
                    entry_price = current_candle['close']
                    stop_loss = last_3_candles_low
                    print(f"📈 New Buy Position at {entry_price}, Stop Loss set to {stop_loss}")

        # Check for stop loss hit
        if position == "buy" and current_candle['low'] <= stop_loss:
            execute_trade("sell", symbol_token, quantity, stop_loss)
            total_profit_loss += (stop_loss - entry_price) * quantity
            position = None
            entry_price = None
            print(f"❌ Stop Loss Hit on Buy at {stop_loss}, Position Closed")

        if position == "sell" and current_candle['high'] >= stop_loss:
            execute_trade("buy", symbol_token, quantity, stop_loss)
            total_profit_loss += (entry_price - stop_loss) * quantity
            position = None
            entry_price = None
            print(f"❌ Stop Loss Hit on Sell at {stop_loss}, Position Closed")

    # Print total profit/loss
    print(f"Total Profit/Loss for the session: {total_profit_loss}")

# ───────────────────────────────────────────────
# Execute the Backtesting Buy/Sell Logic on Historical Data
# ───────────────────────────────────────────────

print("\n=== Backtesting Buy/Sell Strategy ===")
apply_stop_loss_take_profit(df)
