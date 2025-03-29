import requests
import os
import pyotp
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
import datetime
import time
from dotenv import load_dotenv
import pandas_ta as ta

def topgun(trading_symbol, symbol_token, exchange, quantity):
    # Fix UnicodeEncodeError for Windows
    sys.stdout.reconfigure(encoding='utf-8')

    # Load environment variables from .env file
    load_dotenv()

    # Trading Performance Tracking Class
    class TradingPerformance:
        def __init__(self):
            self.total_trades = 0
            self.winning_trades = 0
            self.losing_trades = 0
            self.total_profit = 0.0
            self.total_loss = 0.0
            self.net_profit = 0.0

        def record_trade(self, trade_profit):
            """
            Record trade performance metrics
            :param trade_profit: Profit/loss from the trade
            """
            self.total_trades += 1
            if trade_profit > 0:
                self.winning_trades += 1
                self.total_profit += trade_profit
            elif trade_profit < 0:
                self.losing_trades += 1
                self.total_loss += abs(trade_profit)
            
            self.net_profit += trade_profit

        def print_performance(self):
            """
            Print detailed trading performance summary
            """
            print("\n===== Trading Performance =====")
            print(f"Total Trades: {self.total_trades}")
            print(f"Winning Trades: {self.winning_trades}")
            print(f"Losing Trades: {self.losing_trades}")
            print(f"Total Profit: ₹{self.total_profit:.2f}")
            print(f"Total Loss: ₹{self.total_loss:.2f}")
            print(f"Net Profit: ₹{self.net_profit:.2f}")
            print(f"Win Rate: {(self.winning_trades/self.total_trades*100):.2f}%")
            print("==============================")

    # Initialize API credentials
    API_KEY = os.getenv("ANGELONE_API_KEY")
    CLIENT_ID = os.getenv("ANGELONE_CLIENT_ID")
    PASSWORD = os.getenv("ANGELONE_MPIN")
    TOTP_SECRET = os.getenv("ANGELONE_TOTP_SECRET")

    # Global trading variables
    auth_token = None
    headers = None
    duration = "DAY"
    active_position = None
    entry_price = None
    stop_loss = None
    take_profit = None
    performance = TradingPerformance()
    trade_quantity = quantity

    # Candle size configuration
    CANDLE_SIZE = "ONE_MINUTE"  # Options: "ONE_MINUTE", "FIVE_MINUTE", "FIFTEEN_MINUTE", "THIRTY_MINUTE", "ONE_HOUR", "ONE_DAY"

    # Map candle size to minutes for calculations
    CANDLE_SIZE_MINUTES = {
        "ONE_MINUTE": 1,
        "FIVE_MINUTE": 5,
        "FIFTEEN_MINUTE": 15,
        "THIRTY_MINUTE": 30,
        "ONE_HOUR": 60,
        "ONE_DAY": 1440
    }

    def login_to_angel_one():
        """
        Login to Angel One API
        :return: Boolean indicating login success
        """
        nonlocal auth_token, headers
        
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
                return True
            else:
                print("❌ Login failed.")
                return False
        except Exception as e:
            print(f"⚠ Login error: {str(e)}")
            return False

    def execute_buy_order(trading_symbol, quantity, current_price):
        """
        Execute buy order and manage position tracking
        :param trading_symbol: Stock symbol
        :param quantity: Number of shares to buy
        :param current_price: Current market price
        :return: Boolean indicating order success
        """
        nonlocal active_position, entry_price

        # Simulate or execute buy order
        url = "https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/placeOrder"
        
        payload = {
            "exchange": exchange,
            "tradingsymbol": trading_symbol,
            "symboltoken": symbol_token,
            "quantity": quantity,
            "transactiontype": "BUY",
            "duration": duration,
            "ordertype": "MARKET",
            "producttype": "INTRADAY",
            "variety": "NORMAL"
        }

        # Simulating order execution
        entry_price = current_price
        active_position = "long"
        print(f"🟢 Buy Order Executed at ₹{entry_price}")
        return True

    def execute_sell_order(trading_symbol, quantity, current_price):
        """
        Execute sell order, calculate profit/loss, and manage position tracking
        :param trading_symbol: Stock symbol
        :param quantity: Number of shares to sell
        :param current_price: Current market price
        :return: Boolean indicating order success
        """
        nonlocal active_position, entry_price, performance

        # Calculate trade profit/loss
        if active_position == "long":
            trade_profit = (current_price - entry_price) * quantity
            performance.record_trade(trade_profit)
            print(f"💰 Trade Profit/Loss: ₹{trade_profit:.2f}")
            performance.print_performance()
        
        # Simulate or execute sell order
        url = "https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/placeOrder"
        
        payload = {
            "exchange": exchange,
            "tradingsymbol": trading_symbol,
            "symboltoken": symbol_token,
            "quantity": quantity,
            "transactiontype": "SELL",
            "duration": duration,
            "ordertype": "MARKET",
            "producttype": "INTRADAY",
            "variety": "NORMAL"
        }

        # Simulating order execution
        print(f"🔴 Sell Order Executed at ₹{current_price}")
        active_position = None
        return True

    def fetch_historical_stock_data(symbol_token, exchange):
        """
        Fetch historical stock data from Angel One API
        :param symbol_token: Unique stock token
        :param exchange: Stock exchange
        :return: DataFrame with historical stock data
        """
        global CANDLE_SIZE
        
        now = datetime.datetime.now()
        today = now.date()
        current_time = now.time()
        
        # Determine market hours and trading date
        market_open = datetime.time(9, 15)
        market_close = datetime.time(15, 30)
        market_is_open = (now.weekday() < 5) and (market_open <= current_time <= market_close)
        
        # Determine the most recent or current trading day
        if market_is_open:
            trading_date = today
            from_date = today.strftime("%Y-%m-%d") + " 09:15"
            to_date = now.strftime("%Y-%m-%d %H:%M")
        else:
            # Logic to find the most recent trading day
            days_to_subtract = 1 if now.weekday() < 5 else 2
            trading_date = today - datetime.timedelta(days=days_to_subtract)
            from_date = trading_date.strftime("%Y-%m-%d") + " 09:15"
            to_date = trading_date.strftime("%Y-%m-%d") + " 15:30"
        
        payload = {
            "exchange": exchange,
            "symboltoken": symbol_token,
            "interval": CANDLE_SIZE,
            "fromdate": from_date,
            "todate": to_date
        }
        
        url = "https://apiconnect.angelone.in/rest/secure/angelbroking/historical/v1/getCandleData"
        response = requests.post(url, json=payload, headers=headers)
        
        try:
            response_data = response.json()
        except Exception as e:
            print(f"❌ Failed to parse API response: {str(e)}")
            return None
        
        if "data" in response_data and response_data["data"]:
            df = pd.DataFrame(response_data["data"], columns=["date", "open", "high", "low", "close", "volume"])
            df["date"] = pd.to_datetime(df["date"])
            
            # Filter data to include only market working hours
            df["time"] = df["date"].dt.time
            df = df[(df["time"] >= datetime.time(9, 15)) & (df["time"] <= datetime.time(15, 30))]
            df = df.drop(columns=["time"])
            
            df.set_index("date", inplace=True)
            return df
        else:
            print("❌ API returned no historical data!")
            return None

    def fetch_live_stock_data(symbol_token, exchange):
        """
        Fetch live stock data from Angel One API
        :param symbol_token: Unique stock token
        :param exchange: Stock exchange
        :return: DataFrame with live stock data
        """
        url = "https://apiconnect.angelone.in/rest/secure/angelbroking/market/v1/quote/"
        payload = {"mode": "FULL", "exchangeTokens": {exchange: [symbol_token]}}
        
        try:
            response = requests.post(url, json=payload, headers=headers)
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
                        "close": float(market_data[0].get("ltp", 0)),
                        "volume": int(market_data[0].get("totalTradedVolume", 0))
                    }
                    
                    # Create a dataframe with a single row
                    df = pd.DataFrame([live_data])
                    df.set_index("date", inplace=True)
                    
                    return df
        except Exception as e:
            print(f"❌ Failed to fetch live data: {str(e)}")
        
        return None

    def update_live_data(live_df, new_data):
        """
        Update live data DataFrame with new candle data
        :param live_df: Existing live data DataFrame
        :param new_data: New data to be added
        :return: Updated DataFrame
        """
        global CANDLE_SIZE, CANDLE_SIZE_MINUTES
        
        if new_data is not None and not new_data.empty:
            if live_df is None or live_df.empty:
                combined = new_data
            else:
                # Get minutes for current candle size
                minutes_to_round = CANDLE_SIZE_MINUTES.get(CANDLE_SIZE, 15)
                
                # Round timestamps to the interval specified by CANDLE_SIZE
                new_time = new_data.index[0]
                rounded_time = pd.Timestamp(
                    year=new_time.year, 
                    month=new_time.month,
                    day=new_time.day,
                    hour=new_time.hour,
                    minute=(new_time.minute // minutes_to_round) * minutes_to_round,
                    tz=new_time.tz
                )
                
                # Update or add new candle logic
                if not live_df.empty:
                    last_candle_time = live_df.index[-1]
                    last_candle_floor = last_candle_time.floor(f"{minutes_to_round}min")
                    rounded_time_floor = rounded_time.floor(f"{minutes_to_round}min")
                    
                    if last_candle_floor == rounded_time_floor:
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
                else:
                    # Add a new candle
                    new_data.index = [rounded_time]
                    combined = new_data
            
            # Sort index and keep latest 100 records
            combined = combined.sort_index().tail(100)
            return combined
        
        return live_df if live_df is not None else pd.DataFrame()

    def calculate_supertrend(df):
        """
        Calculate Supertrend indicator for trading signals
        :param df: Input DataFrame with price data
        :return: DataFrame with Supertrend indicator and signals
        """
        if df is None or df.empty:
            return None
        
        # Ensure data is numeric and drop NaN values
        df_copy = df.copy()
        required_cols = ["open", "high", "low", "close", "volume"]
        for col in required_cols:
            df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')
        df_copy = df_copy.dropna(subset=required_cols)
        
        if len(df_copy) < 10:
            return df_copy
        
        try:
            # Calculate Supertrend using pandas_ta
            supertrend = ta.supertrend(df_copy['high'], df_copy['low'], df_copy['close'], length=10, multiplier=2.0)
            if supertrend is not None:
                # Remove existing supertrend columns
                df_copy = df_copy[[col for col in df_copy.columns if not col.startswith('SUPERT_')]]
                
                # Join the supertrend dataframe
                df_copy = pd.concat([df_copy, supertrend], axis=1)
                
                # Align series and create signal columns
                close_series = df_copy['close']
                supertrend_series = df_copy["SUPERT_10_2.0"]
                close_series, supertrend_series = close_series.align(supertrend_series, join='inner')
                
                # Generate buy/sell signals
                df_copy['signal'] = np.where(close_series > supertrend_series, 'buy', 'sell')
                df_copy['signal_change'] = (df_copy['signal'] != df_copy['signal'].shift(1)) & (df_copy['signal'].shift(1).notna())
            else:
                print("❌ Supertrend calculation failed")
        except Exception as e:
            print(f"❌ Supertrend calculation error: {e}")
        
        return df_copy

    def apply_trading_strategy(df, trading_symbol, quantity=1):
        """
        Apply trading strategy based on Supertrend signals
        :param df: DataFrame with price and indicator data
        :param trading_symbol: Stock symbol
        :param quantity: Number of shares to trade
        """
        nonlocal active_position, entry_price, stop_loss, take_profit

        if df is None or df.empty or 'signal' not in df.columns:
            return
        
        # Get the latest candle
        latest_candle = df.iloc[-1]
        current_signal = latest_candle['signal']
        signal_changed = latest_candle.get('signal_change', False)
        current_price = latest_candle['close']
        
        # Signal-based trading logic
        if signal_changed:
            # Close existing positions
            if active_position == "long":
                execute_sell_order(trading_symbol, quantity, current_price)
            elif active_position == "short":
                execute_buy_order(trading_symbol, quantity, current_price)
            
            # Open new positions
            if current_signal == 'buy' and active_position is None:
                execute_buy_order(trading_symbol, quantity, current_price)
                
                # Stop loss and take profit calculations
                stop_loss = df['low'].iloc[-3:].min() if len(df) >= 3 else current_price * 0.98
                risk = current_price - stop_loss
                take_profit = current_price + (2 * risk)
                
            elif current_signal == 'sell' and active_position is None:
                execute_sell_order(trading_symbol, quantity, current_price)
                
                # Stop loss and take profit calculations
                stop_loss = df['high'].iloc[-3:].max() if len(df) >= 3 else current_price * 1.02
                risk = stop_loss - current_price
                take_profit = current_price - (2 * risk)
        
        # Manage existing positions
        elif active_position is not None:
            if active_position == "long":
                # Stop loss checks
                if latest_candle['low'] <= stop_loss:
                    execute_sell_order(trading_symbol, quantity, stop_loss)
                # Take profit checks
                elif latest_candle['high'] >= take_profit:
                    execute_sell_order(trading_symbol, quantity, take_profit)
            
            elif active_position == "short":
                # Stop loss checks
                if latest_candle['high'] >= stop_loss:
                    execute_buy_order(trading_symbol, quantity, stop_loss)
                # Take profit checks
                elif latest_candle['low'] <= take_profit:
                    execute_buy_order(trading_symbol, quantity, take_profit)

    def main():
        """
        Main trading function to execute live trading strategy
        """
        # Login to Angel One
        if not login_to_angel_one():
            print("Exiting due to login failure")
            return
        
        # Fetch initial historical data
        historical_df = fetch_historical_stock_data(symbol_token, exchange)
        
        # Initialize live data
        live_df = historical_df.copy() if historical_df is not None else pd.DataFrame()
        
        # Calculate initial Supertrend
        if not live_df.empty:
            live_df = calculate_supertrend(live_df)
        
        # Trading loop
        try:
            while True:
                # Fetch latest live data
                new_data = fetch_live_stock_data(symbol_token, exchange)
                
                if new_data is not None and not new_data.empty:
                    # Update live dataset
                    live_df = update_live_data(live_df, new_data)
                    
                    # Recalculate Supertrend
                    if not live_df.empty:
                        live_df = calculate_supertrend(live_df)
                        
                        if 'SUPERT_10_2.0' in live_df.columns:
                            # Apply trading strategy
                            apply_trading_strategy(live_df, trading_symbol, quantity)
                
                # Wait before next update
                time.sleep(60)
                
        except KeyboardInterrupt:
            print("\nTrading session ended by user.")
        except Exception as e:
            print(f"⚠ Error in trading loop: {str(e)}")
        finally:
            print("Trading session ended.")

    # Execute the main trading function
    main()

if __name__ == "__main__":
    topgun("SUZLON", "12018", "NSE", 1)