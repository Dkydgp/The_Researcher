import sqlite3
import json

try:
    conn = sqlite3.connect('predictions.db')
    cursor = conn.cursor()
    cursor.execute("SELECT prediction_json FROM prediction_history WHERE symbol LIKE '%Reliance%' ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    if row:
        with open('latest_pred.json', 'w', encoding='utf-8') as f:
            f.write(row[0])
        print("Done.")
    else:
        print("No predictions found.")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
