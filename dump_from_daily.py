import sqlite3
import json

try:
    conn = sqlite3.connect('predictions.db')
    cursor = conn.cursor()
    cursor.execute("SELECT symbol, rationale, confidence_score, key_factors, prediction_date, signals_aligned, sentiment_score FROM daily_predictions WHERE symbol LIKE '%Reliance%' ORDER BY prediction_date DESC LIMIT 1")
    row = cursor.fetchone()
    
    output = {}
    if row:
        output = {
            "symbol": row[0],
            "rationale": row[1],
            "confidence": row[2],
            "key_factors": row[3],
            "target_date": row[4],
            "signals_aligned": row[5],
            "sentiment_score": row[6]
        }
        
    with open('latest_daily_pred.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=4)
        print("Done.")

    conn.close()
except Exception as e:
    print(f"Error: {e}")
