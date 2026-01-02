import sqlite3
import pandas as pd
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.vector_db import VectorDB

def prepare_dataset(db_path="stock_market.db", output_file="training_data.csv"):
    print("Preparing training dataset...")
    
    # 1. Load Prices
    conn = sqlite3.connect(db_path)
    prices_df = pd.read_sql_query("SELECT * FROM stock_daily_prices", conn)
    
    # 2. Load Fundamentals
    fundamentals_df = pd.read_sql_query("SELECT * FROM stock_fundamentals", conn)
    
    # 3. Load news from Vector DB (Filtered Collection)
    import chromadb
    from chromadb.config import Settings
    from src.utils.config import config
    
    client = chromadb.PersistentClient(
        path=config.CHROMA_DB_PATH,
        settings=Settings(anonymized_telemetry=False)
    )
    
    try:
        collection = client.get_collection("top10_nifty_news")
    except:
        print("⚠ Filtered collection 'top10_nifty_news' not found. Run filter_companies.py first.")
        return
        
    all_news = collection.get(include=['documents', 'metadatas', 'embeddings'])
    
    news_list = []
    if all_news['ids']:
        for i in range(len(all_news['ids'])):
            metadata = all_news['metadatas'][i]
            news_list.append({
                'symbol': metadata.get('company', 'General'),
                'date': metadata.get('published_date', '').split(' ')[0],
                'title': metadata.get('title', ''),
                'source': metadata.get('source', ''),
                'text': all_news['documents'][i]
            })
    
    news_df = pd.DataFrame(news_list)
    
    if news_df.empty:
        print("⚠ No news data found in vector database.")
        return

    # Normalize symbols for joining
    def normalize_symbol(s):
        if not s: return "GENERAL"
        s = s.upper()
        if "RELIANCE" in s: return "RELIANCE"
        if "TCS" in s: return "TCS"
        if "HDFC" in s: return "HDFCBANK"
        if "INFY" in s or "INFOSYS" in s: return "INFY"
        if "ICICI" in s: return "ICICIBANK"
        return s.split('.')[0].split(' ')[0]

    news_df['join_symbol'] = news_df['symbol'].apply(normalize_symbol)
    
    # Prices in DB are like 'RELIANCE.NS'
    prices_df['join_symbol'] = prices_df['symbol'].apply(lambda x: x.split('.')[0])
    
    # Fundamentals in DB are like 'RELIANCE'
    fundamentals_df['join_symbol'] = fundamentals_df['symbol']

    # 4. Join Data
    print(f"News unique dates: {news_df['date'].unique().tolist()[:5]}")
    print(f"Prices unique dates: {prices_df['date'].unique().tolist()[:5]}")
    
    # Match news with the price of that day
    merged_df = pd.merge(news_df, prices_df, on=['join_symbol', 'date'], how='inner')
    print(f"Merged news + prices shape: {merged_df.shape}")
    
    # Match with latest fundamentals (most recent for that symbol)
    # For simplicity, we just join by symbol since fundamentals don't change daily
    fundamentals_latest = fundamentals_df.sort_values('date').groupby('join_symbol').tail(1)
    final_df = pd.merge(merged_df, fundamentals_latest, on='join_symbol', suffixes=('', '_fund'), how='left')

    # 5. Calculate "Next Day Return" as a target (if available)
    # This requires looking up the price of the next trading day
    print("Calculating targets...")
    prices_df = prices_df.sort_values(['join_symbol', 'date'])
    prices_df['next_day_close'] = prices_df.groupby('join_symbol')['close'].shift(-1)
    prices_df['return_label'] = (prices_df['next_day_close'] > prices_df['close']).astype(int)
    
    # Update final_df with return target
    final_df = pd.merge(final_df, prices_df[['join_symbol', 'date', 'return_label']], on=['join_symbol', 'date'], how='left')

    # 6. Save
    final_df.to_csv(output_file, index=False)
    print(f"✓ Dataset saved to {output_file}")
    print(f"  Rows: {len(final_df)}")
    print(f"  Columns: {final_df.columns.tolist()}")

if __name__ == "__main__":
    prepare_dataset()
