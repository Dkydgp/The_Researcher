import sqlite3
import pandas as pd

conn = sqlite3.connect('stock_market.db')

print("Checking index prices in database...")
print("\nSearching for ^NSEI:")
df1 = pd.read_sql_query("SELECT * FROM stock_daily_prices WHERE symbol = '^NSEI' ORDER BY date DESC LIMIT 2", conn)
print(df1)

print("\nSearching for ^BSESN:")
df2 = pd.read_sql_query("SELECT * FROM stock_daily_prices WHERE symbol = '^BSESN' ORDER BY date DESC LIMIT 2", conn)
print(df2)

print("\nAll unique symbols:")
df3 = pd.read_sql_query("SELECT DISTINCT symbol FROM stock_daily_prices ORDER BY symbol", conn)
print(df3[df3['symbol'].str.contains('\^', regex=True)])

conn.close()
