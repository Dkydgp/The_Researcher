import sqlite3

conn = sqlite3.connect('predictions.db')
cursor = conn.cursor()

# Get latest NIFTY and SENSEX predictions
cursor.execute('''
    SELECT symbol, direction, predicted_move, confidence_score, prediction_date 
    FROM daily_predictions 
    WHERE symbol IN ('NIFTY 50', 'SENSEX', 'Nifty 50', 'Sensex')
    ORDER BY prediction_date DESC 
    LIMIT 5
''')

print("Latest NIFTY & SENSEX Predictions:")
print("=" * 60)
for row in cursor.fetchall():
    symbol, direction, move, conf, date = row
    print(f"{symbol}: {direction} ({move}%) - Confidence: {conf} - Date: {date}")

conn.close()
