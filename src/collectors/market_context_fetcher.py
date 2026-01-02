"""
Market Context Fetcher
Fetches global market indicators: S&P 500, Crude Oil, USD/INR
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
import numpy as np

class MarketContextFetcher:
    def __init__(self, db_path="stock_market.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_context (
                date TEXT PRIMARY KEY,
                sp500_close REAL,
                sp500_change REAL,
                crude_oil REAL,
                usd_inr REAL,
                nifty_trend TEXT,
                volatility_regime TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def fetch_global_indicators(self, days=30):
        """Fetch global market indicators"""
        print("\n" + "="*60)
        print("FETCHING GLOBAL MARKET CONTEXT")
        print("="*60)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # S&P 500
        print("\nFetching S&P 500...")
        sp500 = yf.Ticker("^GSPC")
        sp500_data = sp500.history(start=start_date.strftime('%Y-%m-%d'), 
                                    end=(end_date + timedelta(days=1)).strftime('%Y-%m-%d'))
        
        # Crude Oil
        print("Fetching Crude Oil prices...")
        oil = yf.Ticker("CL=F")
        oil_data = oil.history(start=start_date.strftime('%Y-%m-%d'), 
                               end=(end_date + timedelta(days=1)).strftime('%Y-%m-%d'))
        
        # USD/INR
        print("Fetching USD/INR exchange rate...")
        usd_inr = yf.Ticker("INR=X")
        inr_data = usd_inr.history(start=start_date.strftime('%Y-%m-%d'), 
                                   end=(end_date + timedelta(days=1)).strftime('%Y-%m-%d'))
        
        # NIFTY 50 for regime detection
        print("Fetching NIFTY 50 for regime detection...")
        nifty = yf.Ticker("^NSEI")
        nifty_data = nifty.history(start=start_date.strftime('%Y-%m-%d'), 
                                   end=(end_date + timedelta(days=1)).strftime('%Y-%m-%d'))
        
        # Save to database
        self._save_market_context(sp500_data, oil_data, inr_data, nifty_data)
        
        print(f"\n✓ Saved {len(sp500_data)} days of market context")
    
    def _detect_market_regime(self, nifty_data):
        """Detect bull/bear/sideways and volatility regime"""
        if len(nifty_data) < 60:
            return "NEUTRAL", "MEDIUM"
        
        # Trend detection (3-month performance)
        recent_90d = nifty_data.tail(60)
        pct_change = ((recent_90d['Close'].iloc[-1] - recent_90d['Close'].iloc[0]) / 
                      recent_90d['Close'].iloc[0]) * 100
        
        if pct_change > 10:
            trend = "BULL"
        elif pct_change < -10:
            trend = "BEAR"
        else:
            trend = "SIDEWAYS"
        
        # Volatility detection (30-day rolling std dev)
        recent_30d = nifty_data.tail(30)
        returns = recent_30d['Close'].pct_change()
        volatility = returns.std() * 100
        
        if volatility > 2:
            vol_regime = "HIGH"
        elif volatility > 1:
            vol_regime = "MEDIUM"
        else:
            vol_regime = "LOW"
        
        return trend, vol_regime
    
    def _save_market_context(self, sp500_data, oil_data, inr_data, nifty_data):
        """Save market context to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Combine all data by date
        dates = sp500_data.index
        
        for date in dates:
            date_str = date.strftime('%Y-%m-%d')
            
            # S&P 500
            sp500_close = sp500_data.loc[date, 'Close'] if date in sp500_data.index else None
            sp500_change = ((sp500_data.loc[date, 'Close'] - sp500_data.loc[date, 'Open']) / 
                           sp500_data.loc[date, 'Open'] * 100) if date in sp500_data.index else None
            
            # Crude Oil
            oil_close = oil_data.loc[date, 'Close'] if date in oil_data.index else None
            
            # USD/INR
            usd_inr_rate = inr_data.loc[date, 'Close'] if date in inr_data.index else None
            
            # Market regime (calculate only for the latest date)
            if date == dates[-1]:
                trend, vol_regime = self._detect_market_regime(nifty_data)
            else:
                trend, vol_regime = None, None
            
            cursor.execute('''
                INSERT OR REPLACE INTO market_context 
                (date, sp500_close, sp500_change, crude_oil, usd_inr, nifty_trend, volatility_regime)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (date_str, sp500_close, sp500_change, oil_close, usd_inr_rate, trend, vol_regime))
        
        conn.commit()
        conn.close()
        
        # Print latest context
        if len(dates) > 0:
            latest = dates[-1]
            print(f"\nLatest Market Context ({latest.strftime('%Y-%m-%d')}):")
            print(f"  S&P 500: ${sp500_data.loc[latest, 'Close']:.2f}")
            print(f"  Crude Oil: ${oil_data.loc[latest, 'Close'] if latest in oil_data.index else 'N/A'}")
            print(f"  USD/INR: ₹{inr_data.loc[latest, 'Close'] if latest in inr_data.index else 'N/A'}")
            trend, vol_regime = self._detect_market_regime(nifty_data)
            print(f"  Market Trend: {trend}")
            print(f"  Volatility: {vol_regime}")
    
    def get_latest_context(self):
        """Get the most recent market context"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM market_context 
            ORDER BY date DESC LIMIT 1
        ''')
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'date': row[0],
                'sp500_close': row[1],
                'sp500_change': row[2],
                'crude_oil': row[3],
                'usd_inr': row[4],
                'nifty_trend': row[5],
                'volatility_regime': row[6]
            }
        return None

if __name__ == "__main__":
    fetcher = MarketContextFetcher()
    fetcher.fetch_global_indicators(days=30)
