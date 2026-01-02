import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import time

# Mapping for Screener.in (stripping .NS if present)
SCREENER_SYMBOLS = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]

class ScreenerFetcher:
    def __init__(self, db_path="stock_market.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_fundamentals (
                symbol TEXT,
                date TEXT,
                market_cap REAL,
                current_price REAL,
                high_low TEXT,
                stock_pe REAL,
                book_value REAL,
                dividend_yield REAL,
                roce REAL,
                roe REAL,
                face_value REAL,
                PRIMARY KEY (symbol, date)
            )
        ''')
        conn.commit()
        conn.close()

    def fetch_fundamentals(self):
        print(f"\nFetching fundamental data from Screener.in for {len(SCREENER_SYMBOLS)} stocks...")
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        for symbol in SCREENER_SYMBOLS:
            try:
                url = f"https://www.screener.in/company/{symbol}/"
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    ratios = self._parse_ratios(soup)
                    if ratios:
                        self._save_to_db(symbol, date_str, ratios)
                        print(f"  {symbol}: Market Cap ₹{ratios.get('Market Cap', 'N/A')} Cr, P/E {ratios.get('Stock P/E', 'N/A')}")
                    else:
                        print(f"  Could not parse ratios for {symbol}")
                else:
                    print(f"  Failed to fetch {symbol}: Status {response.status_code}")
                
                # Small delay to be polite
                time.sleep(1)
            except Exception as e:
                print(f"  Error fetching {symbol}: {e}")

    def _parse_ratios(self, soup):
        ratios = {}
        top_ratios = soup.find('ul', id='top-ratios')
        if not top_ratios:
            return None
        
        for li in top_ratios.find_all('li'):
            name_span = li.find('span', class_='name')
            value_span = li.find('span', class_='number')
            if name_span and value_span:
                name = name_span.text.strip()
                value = value_span.text.strip().replace(',', '')
                ratios[name] = value
        
        return ratios

    def _save_to_db(self, symbol, date, ratios):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Helper to safely convert to float
        def to_float(val):
            try:
                if not val: return None
                # Handle cases like "High / Low" which is a string
                if '/' in str(val): return str(val)
                return float(str(val).replace('%', '').strip())
            except:
                return str(val)

        cursor.execute('''
            INSERT OR REPLACE INTO stock_fundamentals (
                symbol, date, market_cap, current_price, high_low, 
                stock_pe, book_value, dividend_yield, roce, roe, face_value
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            symbol, date, 
            to_float(ratios.get('Market Cap')),
            to_float(ratios.get('Current Price')),
            ratios.get('High / Low'),
            to_float(ratios.get('Stock P/E')),
            to_float(ratios.get('Book Value')),
            to_float(ratios.get('Dividend Yield')),
            to_float(ratios.get('ROCE')),
            to_float(ratios.get('ROE')),
            to_float(ratios.get('Face Value'))
        ))
        conn.commit()
        conn.close()

if __name__ == "__main__":
    fetcher = ScreenerFetcher()
    fetcher.fetch_fundamentals()
