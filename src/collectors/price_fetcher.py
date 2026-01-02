import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
import os
from src.analysis.technical_indicators import TechnicalIndicators

# Top 10 Nifty Stocks + Indices
STOCKS = [
    # Original 5
    "RELIANCE.NS", 
    "TCS.NS",
    "HDFCBANK.NS", 
    "INFY.NS", 
    "ICICIBANK.NS",
    # New 5 stocks
    "BHARTIARTL.NS",  # Bharti Airtel
    "ITC.NS",          # ITC
    "WIPRO.NS",        # Wipro
    "HCLTECH.NS",      # HCL Technologies
    "BAJFINANCE.NS",   # Bajaj Finance
    # Indices
    "^NSEI",           # NIFTY 50
    "^BSESN"           # SENSEX
]

class PriceFetcher:
    def __init__(self, db_path="stock_market.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_daily_prices (
                symbol TEXT,
                date TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                PRIMARY KEY (symbol, date)
            )
        ''')
        
        # Create technical indicators table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS technical_indicators (
                symbol TEXT,
                date TEXT,
                rsi REAL,
                macd REAL,
                macd_signal REAL,
                macd_histogram REAL,
                bb_upper REAL,
                bb_middle REAL,
                bb_lower REAL,
                volume_ma REAL,
                volume_ratio REAL,
                PRIMARY KEY (symbol, date)
            )
        ''')
        conn.commit()
        conn.close()

    def fetch_today_prices(self):
        print(f"\nFetching prices for {len(STOCKS)} items (stocks + indices)...")
        for symbol in STOCKS:
            try:
                ticker = yf.Ticker(symbol)
                # Get last 1 day data
                data = ticker.history(period="1d")
                if not data.empty:
                    row = data.iloc[-1]
                    date_str = data.index[-1].strftime('%Y-%m-%d')
                    self._save_to_db(symbol, date_str, row['Open'], row['High'], row['Low'], row['Close'], int(row['Volume']))
                    print(f"  {symbol}: Close {row['Close']:.2f}")
                else:
                    print(f"  No data found for {symbol}")
            except Exception as e:
                print(f"  ❌ Error fetching {symbol}: {e}")

    def fetch_historical_prices(self, days=30):
        print(f"\nFetching last {days} days of historical prices...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        for symbol in STOCKS:
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(start=start_date.strftime('%Y-%m-%d'), end=(end_date + timedelta(days=1)).strftime('%Y-%m-%d'))
                if not data.empty:
                    count = 0
                    for index, row in data.iterrows():
                        date_str = index.strftime('%Y-%m-%d')
                        self._save_to_db(symbol, date_str, row['Open'], row['High'], row['Low'], row['Close'], int(row['Volume']))
                        count += 1
                    print(f"  {symbol}: Saved {count} rows")
            except Exception as e:
                print(f"  ❌ Error fetching {symbol}: {e}")

    def _save_to_db(self, symbol, date, open_p, high, low, close_p, volume):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO stock_daily_prices (symbol, date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (symbol, date, open_p, high, low, close_p, volume))
        conn.commit()
        conn.close()

    def calculate_technical_indicators(self):
        """Calculate and store technical indicators for all stocks"""
        print("\nCalculating technical indicators...")
        conn = sqlite3.connect(self.db_path)
        
        for symbol in STOCKS:
            # Get last 60 days of price data for calculations
            query = f"SELECT date, close, volume FROM stock_daily_prices WHERE symbol = '{symbol}' ORDER BY date DESC LIMIT 60"
            df = pd.read_sql_query(query, conn)
            
            if len(df) < 20:  # Need minimum data
                print(f"  ⚠ {symbol}: Insufficient data for indicators")
                continue
            
            # Reverse to chronological order
            df = df.iloc[::-1].reset_index(drop=True)
            
            prices = df['close']
            volumes = df['volume']
            latest_date = df['date'].iloc[-1]
            latest_price = prices.iloc[-1]
            
            # Calculate indicators
            rsi = TechnicalIndicators.calculate_rsi(prices)
            macd, macd_signal, macd_hist = TechnicalIndicators.calculate_macd(prices)
            bb_upper, bb_middle, bb_lower = TechnicalIndicators.calculate_bollinger_bands(prices)
            vol_ma, vol_ratio = TechnicalIndicators.calculate_volume_indicators(volumes)
            
            # Save to database
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO technical_indicators 
                (symbol, date, rsi, macd, macd_signal, macd_histogram, 
                 bb_upper, bb_middle, bb_lower, volume_ma, volume_ratio)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (symbol, latest_date, rsi, macd, macd_signal, macd_hist,
                  bb_upper, bb_middle, bb_lower, vol_ma, vol_ratio))
            
            # Show indicator status
            rsi_sig = TechnicalIndicators.get_rsi_signal(rsi)
            macd_sig = TechnicalIndicators.get_macd_signal(macd, macd_signal)
            bb_pos = TechnicalIndicators.get_bb_position(latest_price, bb_upper, bb_middle, bb_lower)
            
            print(f"  ✓ {symbol}: RSI={rsi:.1f if rsi else 'N/A'} ({rsi_sig}), "
                  f"MACD={macd_sig}, BB Position={bb_pos:.0f if bb_pos else 'N/A'}%")
        
        conn.commit()
        conn.close()
        print("✓ Technical indicators calculated and saved")

if __name__ == "__main__":
    fetcher = PriceFetcher()
    # Fetch last 30 days to start with
    fetcher.fetch_historical_prices(days=30)
    # Then ensure today is captured
    fetcher.fetch_today_prices()
    # Calculate technical indicators
    fetcher.calculate_technical_indicators()
