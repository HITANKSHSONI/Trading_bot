import requests
import os
import pyotp
import pandas as pd
import plotly.graph_objects as go
import sys
import datetime
from dotenv import load_dotenv
import pandas_ta as ta
from dash import Dash, dcc, html
from dash.dependencies import Input, Output

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

def update_live_data(live_df, new_data):
    if new_data is not None and not new_data.empty:
        required_cols = ["date", "open", "high", "low", "close", "volume"]
        new_data = new_data.filter(items=required_cols)
        new_data = new_data.set_index("date")
        combined = pd.concat([live_df, new_data])
        # Remove duplicate timestamps, keeping the latest record
        combined = combined[~combined.index.duplicated(keep='last')]
        combined.sort_index(inplace=True)
        return combined.tail(100)  # Keep only the latest 100 records
    return live_df

def generate_chart(live_df):
    # Calculate Supertrend if there is enough data
    if not live_df.empty:
        supertrend = ta.supertrend(live_df["high"], live_df["low"], live_df["close"], length=10, multiplier=2.0)
        if supertrend is not None:
            # Remove any previous Supertrend columns and join new ones
            live_df = live_df.drop(columns=supertrend.columns, errors='ignore')
            live_df = live_df.join(supertrend)
        else:
            print("Supertrend calculation returned None.")
    
    fig = go.Figure(data=[go.Candlestick(
        x=live_df.index,
        open=live_df["open"],
        high=live_df["high"],
        low=live_df["low"],
        close=live_df["close"]
    )])
    
    if "SUPERT_10_2.0" in live_df.columns:
        fig.add_trace(go.Scatter(
            x=live_df.index,
            y=live_df["SUPERT_10_2.0"],
            mode="lines",
            name="Supertrend",
            line=dict(dash="dash", color="blue")
        ))
        
    y_min = live_df["low"].min() * 0.98
    y_max = live_df["high"].max() * 1.02
    fig.update_layout(title="Live Stock Data with Supertrend",
                      xaxis_title="Time",
                      yaxis_title="Price",
                      xaxis=dict(type="date"),
                      yaxis=dict(range=[y_min, y_max]))
    return fig

# Global DataFrame to hold combined historical and live data
global_live_df = pd.DataFrame()

# Initialize Dash app
app = Dash(__name__)
app.layout = html.Div([
    html.H1("Live Stock Data with Supertrend"),
    dcc.Graph(id="live-chart"),
    dcc.Interval(
        id="interval-component",
        interval=10 * 1000,  # Update every 10 seconds
        n_intervals=0
    )
])

# Dash callback to update the chart
@app.callback(
    Output("live-chart", "figure"),
    Input("interval-component", "n_intervals")
)
def update_chart(n):
    global global_live_df
    # If global_live_df is empty, try to load historical data first.
    if global_live_df.empty:
        hist_data = fetch_historical_stock_data()
        if hist_data is not None:
            global_live_df = hist_data
        else:
            global_live_df = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
            global_live_df.index.name = "date"
    
    # Fetch new live data and update the DataFrame
    new_live_data = fetch_live_stock_data()
    global_live_df = update_live_data(global_live_df, new_live_data)
    
    # Generate and return the updated chart
    fig = generate_chart(global_live_df)
    return fig

if __name__ == "__main__":
    login()
    app.run_server(debug=True)
