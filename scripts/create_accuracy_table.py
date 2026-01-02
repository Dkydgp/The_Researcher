import sqlite3
import os

# Database path
DB_PATH = "predictions.db"

def create_accuracy_table():
    """Create table to store daily cumulative accuracy metrics"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create table for daily accuracy snapshots
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_accuracy_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            timeframe TEXT NOT NULL,
            sentiment_accuracy REAL,
            price_accuracy REAL,
            total_predictions INTEGER,
            high_conf_accuracy REAL,
            medium_conf_accuracy REAL,
            low_conf_accuracy REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Created daily_accuracy_metrics table successfully!")

if __name__ == "__main__":
    create_accuracy_table()
