from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import json
import os
import logging
from datetime import datetime
import pyotp
from dotenv import load_dotenv
import threading
import time
import pandas as pd
import numpy as np
import pandas_ta as ta
import sys

# Fix UnicodeEncodeError for Windows
sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading.log'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)
# Update CORS configuration to explicitly allow all methods
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Angel One API Configuration
ANGEL_API_URL = "https://apiconnect.angelone.in"
API_KEY = os.getenv("ANGELONE_API_KEY")
CLIENT_ID = os.getenv("ANGELONE_CLIENT_ID")
PASSWORD = os.getenv("ANGELONE_MPIN")
TOTP_SECRET = os.getenv("ANGELONE_TOTP_SECRET")

# Global variables
ACCESS_TOKEN = None
active_bots = {}  # Store active trading bots: {symbol_token: bot_instance}

class TradingBot:
    def __init__(self, symbol_token, exchange, quantity=1, order_type="MARKET", product_type="INTRADAY", 
                 duration="DAY", stop_loss=0, supertrend_length=10, supertrend_factor=3):
        self.symbol_token = symbol_token
        self.exchange = exchange
        self.quantity = int(quantity)
        self.order_type = order_type
        self.product_type = product_type
        self.duration = duration
        self.stop_loss = float(stop_loss) if stop_loss else 0
        
        # Supertrend parameters
        self.supertrend_length = int(supertrend_length)
        self.supertrend_factor = float(supertrend_factor)
        
        # Trading state
        self.active_position = None
        self.entry_price = None
        self.sl_price = None
        self.tp_price = None
        self.is_running = False
        self.live_df = pd.DataFrame()
        
        # Create a thread for running the bot
        self.thread = None
    
    def start(self):
        """Start the trading bot in a separate thread."""
        if self.is_running:
            logging.info(f"Bot for {self.symbol_token} is already running")
            return False
        
        self.is_running = True
        logging.info(f"Starting trading bot for {self.symbol_token}")
        
        # Fetch historical data first
        historical_df = self.fetch_historical_stock_data()
        if historical_df is not None and not historical_df.empty:
            self.live_df = historical_df.copy()
            self.live_df = self.calculate_supertrend(self.live_df)
            logging.info(f"Initialized with {len(self.live_df)} historical candles")
        
        # Start the trading thread
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()
        
        return True
    
    def stop(self):
        """Stop the trading bot."""
        self.is_running = False
        logging.info(f"Stopping trading bot for {self.symbol_token}")
        
        # Close any open positions
        if self.active_position == "long":
            self.execute_sell_order()
        elif self.active_position == "short":
            self.execute_buy_order()
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        
        return True
    
    def run(self):
        """Main bot loop - runs in a separate thread."""
        logging.info(f"Bot {self.symbol_token} thread started")
        
        try:
            while self.is_running:
                # Check if market is open (9:15 AM to 3:30 PM, Monday to Friday)
                now = datetime.now()
                market_open = (
                    now.weekday() < 5 and  # Monday to Friday
                    (now.hour > 9 or (now.hour == 9 and now.minute >= 15)) and  # After 9:15 AM
                    (now.hour < 15 or (now.hour == 15 and now.minute <= 30))  # Before 3:30 PM
                )
                
                if not market_open:
                    logging.info(f"Market is closed. Bot {self.symbol_token} waiting...")
                    time.sleep(60)  # Check every minute
                    continue
                
                # Fetch latest live data
                new_data = self.fetch_live_stock_data()
                
                # Update dataset
                if new_data is not None and not new_data.empty:
                    self.live_df = self.update_live_data(self.live_df, new_data)
                    
                    # Recalculate Supertrend with updated data
                    self.live_df = self.calculate_supertrend(self.live_df)
                    
                    # Apply trading strategy based on Supertrend signals
                    self.apply_trading_strategy()
                
                # Wait before next update
                time.sleep(60)  # Update every minute
                
        except Exception as e:
            logging.error(f"Error in bot {self.symbol_token} thread: {str(e)}", exc_info=True)
            self.is_running = False
    
    def fetch_historical_stock_data(self):
        """Fetch historical stock data for initial analysis."""
        today = datetime.now()
        
        # Check if today is Monday (0 = Monday in Python's datetime)
        if today.weekday() == 0:
            # If Monday, get Friday's data (3 days ago)
            past_day = today - pd.Timedelta(days=3)
        else:
            # Otherwise get previous day's data
            past_day = today - pd.Timedelta(days=1)
        
        from_date = past_day.strftime("%Y-%m-%d 09:15")
        to_date = past_day.strftime("%Y-%m-%d 15:30")
        
        logging.info(f"📅 Fetching historical data for {self.symbol_token} from {from_date} to {to_date}")
        
        payload = {
            "exchange": self.exchange,
            "symboltoken": self.symbol_token,
            "interval": "FIFTEEN_MINUTE",
            "fromdate": from_date,
            "todate": to_date
        }
        
        try:
            url = f"{ANGEL_API_URL}/rest/secure/angelbroking/historical/v1/getCandleData"
            response = requests.post(url, json=payload, headers=get_headers())
            
            response_data = response.json()
            
            if "data" in response_data and response_data["data"]:
                df = pd.DataFrame(response_data["data"], columns=["date", "open", "high", "low", "close", "volume"])
                df["date"] = pd.to_datetime(df["date"])
                
                # Filter data to include only market working hours (09:15 to 15:30)
                df["time"] = df["date"].dt.time
                df = df[(df["time"] >= datetime.strptime("09:15", "%H:%M").time()) & 
                        (df["time"] <= datetime.strptime("15:30", "%H:%M").time())]
                df = df.drop(columns=["time"])
                
                df.set_index("date", inplace=True)
                logging.info(f"✅ Historical Data for {self.symbol_token} Fetched Successfully! ({len(df)} candles)")
                return df
            else:
                logging.error(f"❌ API returned no historical data for {self.symbol_token}!")
                return None
        except Exception as e:
            logging.error(f"❌ Failed to fetch historical data for {self.symbol_token}: {str(e)}")
            return None
    
    def fetch_live_stock_data(self):
        """Fetch current live market data."""
        url = f"{ANGEL_API_URL}/rest/secure/angelbroking/market/v1/quote/"
        payload = {"mode": "FULL", "exchangeTokens": {self.exchange: [self.symbol_token]}}
        
        try:
            response = requests.post(url, json=payload, headers=get_headers())
            response_data = response.json()
            
            if "data" in response_data:
                market_data = response_data["data"].get("fetched", [])
                if market_data:
                    # Convert the data to a dataframe
                    current_time = pd.Timestamp.now(tz='Asia/Kolkata')
                    live_data = {
                        "date": current_time,
                        "open": float(market_data[0].get("open", 0)),
                        "high": float(market_data[0].get("high", 0)),
                        "low": float(market_data[0].get("low", 0)),
                        "close": float(market_data[0].get("ltp", 0)),  # Using LTP as close
                        "volume": int(market_data[0].get("totalTradedVolume", 0))
                    }
                    
                    # Create a dataframe with a single row
                    df = pd.DataFrame([live_data])
                    df.set_index("date", inplace=True)
                    
                    logging.info(f"✅ Live data for {self.symbol_token} fetched successfully")
                    return df
        except Exception as e:
            logging.error(f"❌ Failed to fetch live data for {self.symbol_token}: {str(e)}")
        
        return None
    
    def update_live_data(self, live_df, new_data):
        """Update the live data with new data points."""
        if new_data is not None and not new_data.empty:
            if live_df is None or live_df.empty:
                combined = new_data
            else:
                # Round timestamps to the nearest 15 minutes for OHLC consolidation
                new_time = new_data.index[0]
                rounded_time = pd.Timestamp(
                    year=new_time.year, 
                    month=new_time.month,
                    day=new_time.day,
                    hour=new_time.hour,
                    minute=(new_time.minute // 15) * 15,
                    tz=new_time.tz
                )
                
                # Check if we need to update the last candle or create a new one
                if not live_df.empty and live_df.index[-1].floor('15min') == rounded_time.floor('15min'):
                    # Update the last candle
                    last_idx = live_df.index[-1]
                    live_df.at[last_idx, 'high'] = max(live_df.at[last_idx, 'high'], new_data['high'].values[0])
                    live_df.at[last_idx, 'low'] = min(live_df.at[last_idx, 'low'], new_data['low'].values[0])
                    live_df.at[last_idx, 'close'] = new_data['close'].values[0]
                    live_df.at[last_idx, 'volume'] += new_data['volume'].values[0]
                    combined = live_df
                else:
                    # Add a new candle
                    new_data.index = [rounded_time]
                    combined = pd.concat([live_df, new_data])
            
            # Keep only the latest 100 records
            return combined.tail(100)
        
        return live_df if live_df is not None else pd.DataFrame()
    
    def calculate_supertrend(self, df):
        """Calculate Supertrend indicator values."""
        if df is None or df.empty:
            logging.error(f"❌ No data available for Supertrend calculation for {self.symbol_token}")
            return df
        
        # Make a copy to avoid modifying the original
        df_copy = df.copy()
        
        # Ensure all required columns exist and are numeric
        required_cols = ["open", "high", "low", "close", "volume"]
        for col in required_cols:
            if col not in df_copy.columns:
                logging.error(f"❌ Missing column: {col} for Supertrend calculation for {self.symbol_token}")
                return df_copy
            df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')
        
        # Drop rows with NaN values
        df_copy = df_copy.dropna(subset=required_cols)
        
        if len(df_copy) < 10:  # Minimum length for Supertrend calculation
            logging.error(f"❌ Not enough data points for Supertrend calculation for {self.symbol_token}")
            return df_copy
        
        try:
            # Calculate Supertrend using pandas_ta
            st_length = self.supertrend_length
            st_factor = self.supertrend_factor
            supertrend = ta.supertrend(df_copy['high'], df_copy['low'], df_copy['close'], 
                                      length=st_length, multiplier=st_factor)
            
            if supertrend is not None:
                df_copy = pd.concat([df_copy, supertrend], axis=1)
                
                # Generate buy/sell signals using explicit alignment
                st_col = f"SUPERT_{st_length}_{st_factor}"
                close_series, supertrend_series = df_copy['close'].align(df_copy[st_col], axis=0, copy=False)
                df_copy['signal'] = np.where(close_series > supertrend_series, 'buy', 'sell')
                
                # Detect signal changes (from buy to sell or sell to buy)
                df_copy['signal_change'] = (df_copy['signal'] != df_copy['signal'].shift(1)) & (df_copy['signal'].shift(1).notna())
                
                logging.info(f"✅ Supertrend calculated successfully for {self.symbol_token}")
            else:
                logging.error(f"❌ Supertrend calculation returned None for {self.symbol_token}")
        except Exception as e:
            logging.error(f"❌ Error calculating Supertrend for {self.symbol_token}: {e}")
        
        return df_copy
    
    def apply_trading_strategy(self):
        """Apply the Supertrend trading strategy to the live data."""
        df = self.live_df
        
        if df is None or df.empty or 'signal' not in df.columns:
            logging.error(f"❌ No data available for strategy application for {self.symbol_token}")
            return
        
        # Get the latest candle
        latest_candle = df.iloc[-1]
        current_signal = latest_candle['signal']
        signal_changed = latest_candle.get('signal_change', False)