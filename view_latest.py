import sqlite3
import json

try:
    conn = sqlite3.connect('predictions.db')
    cursor = conn.cursor()
    # Query with NEW columns
    cursor.execute("SELECT symbol, rationale, confidence_score, key_factors, prediction_date, signals_aligned, sentiment_score FROM daily_predictions WHERE symbol LIKE '%Reliance%' ORDER BY prediction_date DESC LIMIT 1")
    row = cursor.fetchone()
    
    if row:
        print(f"Latest Prediction for: {row[0]} (Target: {row[4]})")
        print("-" * 50)
        print(f"Confidence: {row[2]}")
        print(f"Signals Aligned: {row[5]}")
        print(f"Sentiment Score: {row[6]}")
        print("-" * 20)
        print(f"Rationale: {row[1]}")
    else:
        print("No predictions found in daily_predictions table.")
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
