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

    print(f"📅 Fetching data from {from_date} to {to_date}")

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

        print(f"✅ Historical Data Fetched Successfully! ({len(df)} candles)")
        return df
    else:
        print("❌ API returned no data!")
        return None

# Fetch Data for the last week
df = fetch_historical_stock_data()

if df is None or df.empty:
    print("⚠ No historical data available!")
    exit()

# Forward Fill Missing Data
df.ffill(inplace=True)

# 🎯 Calculate Supertrend Indicator using pandas_ta
supertrend = ta.supertrend(df['high'], df['low'], df['close'], length=10, multiplier=2.0)
df = pd.concat([df, supertrend], axis=1)

# Generate red/green signals based on Supertrend and closing price
df['signal'] = np.where(df['close'] > df["SUPERT_10_2.0"], 'green', 'red')

# 🎯 Plot the Entire Week's Data with Supertrend and Signal Markers
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
    
    # Add Supertrend line trace
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["SUPERT_10_2.0"],
        mode="lines",
        name="Supertrend",
        line=dict(dash="dash")
    ))
    
    # Add signal markers: green for buy, red for sell
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["close"],
        mode='markers',
        marker=dict(
             color=[ 'green' if s == 'green' else 'red' for s in df['signal'] ],
             size=8,
             symbol='circle'
        ),
        name='Signals'
    ))
    
    # Calculate y-axis range with some padding
    y_min = df["low"].min() * 0.98
    y_max = df["high"].max() * 1.02

    fig.update_layout(
        title="Weekly Stock Data with Supertrend and Signals (Intraday: 9:15 to 15:30)",
        xaxis_title="Date/Time",
        yaxis_title="Price",
        yaxis=dict(range=[y_min, y_max])
    )
    
    # Use rangebreaks to remove non-trading hours and weekends
    fig.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]),
            dict(bounds=[15.5, 9.25], pattern="hour")
        ]
    )
    
    fig.show()

# Show the plot
plot_weekly_data_single_graph(df)

# ───────────────────────────────────────────────
# BUY/SELL LOGIC (Backtesting with 1:2 Risk-to-Reward Ratio)
# ───────────────────────────────────────────────

# Helper function to simulate trade execution (for backtesting)
def execute_trade(action, symbol_token, quantity, price, time):
    if action == "buy":
        print(f"Executing Buy Order for {symbol_token}, Quantity: {quantity}, Price: {price}, Time: {time}")
    elif action == "sell":
        print(f"Executing Sell Order for {symbol_token}, Quantity: {quantity}, Price: {price}, Time: {time}")

# Backtesting function with 1:2 risk-to-reward ratio integrated
def apply_stop_loss_take_profit(df, symbol_token="3045", quantity=1):
    position = None    # 'long' or 'short'
    entry_price = None
    stop_loss = None
    take_profit = None
    total_profit_loss = 0

    # Start loop from index 3 to ensure we have 3 candles for SL calculation
    for i in range(3, len(df)):
        current_candle = df.iloc[i]
        supertrend_line = current_candle['SUPERT_10_2.0']
        
        # Generate signal: green if close > supertrend (buy), red if below (sell)
        signal = "green" if current_candle['close'] > supertrend_line else "red"

        if position is None:
            # No open position: open new trade based on signal
            if signal == "green":
                entry_price = current_candle['close']
                # For long positions, use the lowest low of last 3 candles as stop loss
                last_3_candles_low = df['low'].iloc[i-3:i].min()
                stop_loss = last_3_candles_low
                risk = entry_price - stop_loss
                take_profit = entry_price + 2 * risk  # 1:2 risk-to-reward ratio
                position = "long"
                execute_trade("buy", symbol_token, quantity, entry_price, current_candle.name)
                print(f"📈 New Buy Position at {entry_price}, Stop Loss: {stop_loss}, Take Profit: {take_profit} at {current_candle.name}")
            elif signal == "red":
                entry_price = current_candle['close']
                # For short positions, use the highest high of last 3 candles as stop loss
                last_3_candles_high = df['high'].iloc[i-3:i].max()
                stop_loss = last_3_candles_high
                risk = stop_loss - entry_price
                take_profit = entry_price - 2 * risk  # 1:2 risk-to-reward ratio
                position = "short"
                execute_trade("sell", symbol_token, quantity, entry_price, current_candle.name)
                print(f"📉 New Sell Position at {entry_price}, Stop Loss: {stop_loss}, Take Profit: {take_profit} at {current_candle.name}")
        else:
            # Position is open, check for exit conditions
            if position == "long":
                # Check if take profit is reached
                if current_candle['close'] >= take_profit:
                    execute_trade("sell", symbol_token, quantity, current_candle['close'], current_candle.name)
                    profit = (current_candle['close'] - entry_price) * quantity
                    total_profit_loss += profit
                    print(f"💰 Take Profit hit on Buy at {current_candle['close']} (Profit: {profit}) at {current_candle.name}")
                    position = None
                    entry_price = None
                # Check if stop loss is hit
                elif current_candle['low'] <= stop_loss:
                    execute_trade("sell", symbol_token, quantity, stop_loss, current_candle.name)
                    loss = (stop_loss - entry_price) * quantity
                    total_profit_loss += loss
                    print(f"❌ Stop Loss hit on Buy at {stop_loss} (Loss: {loss}) at {current_candle.name}")
                    position = None
                    entry_price = None
            elif position == "short":
                # For short positions, take profit if price falls to target
                if current_candle['close'] <= take_profit:
                    execute_trade("buy", symbol_token, quantity, current_candle['close'], current_candle.name)
                    profit = (entry_price - current_candle['close']) * quantity
                    total_profit_loss += profit
                    print(f"💰 Take Profit hit on Sell at {current_candle['close']} (Profit: {profit}) at {current_candle.name}")
                    position = None
                    entry_price = None
                # Check stop loss for short positions
                elif current_candle['high'] >= stop_loss:
                    execute_trade("buy", symbol_token, quantity, stop_loss, current_candle.name)
                    loss = (entry_price - stop_loss) * quantity
                    total_profit_loss += loss
                    print(f"❌ Stop Loss hit on Sell at {stop_loss} (Loss: {loss}) at {current_candle.name}")
                    position = None
                    entry_price = None

    print(f"Total Profit/Loss for the session: {total_profit_loss}")

# ───────────────────────────────────────────────
# Execute Backtesting Strategy
# ───────────────────────────────────────────────
print("\n=== Backtesting Buy/Sell Strategy with 1:2 Risk-to-Reward Ratio ===")
apply_stop_loss_take_profit(df)
