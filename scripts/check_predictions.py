import sqlite3

conn = sqlite3.connect('predictions.db')
cursor = conn.cursor()

# Check ITC, Wipro, Bajaj Finance predictions
stocks = ['ITC', 'Wipro', 'Bajaj Finance']

print("Checking predictions for:", stocks)
print("=" * 60)

for stock in stocks:
    result = cursor.execute(
        'SELECT symbol, prediction_date, direction, confidence_score FROM prediction_history WHERE symbol = ? ORDER BY prediction_date DESC LIMIT 1',
        (stock,)
    ).fetchone()
    
    if result:
        print(f"\n✅ {result[0]}:")
        print(f"   Date: {result[1]}")
        print(f"   Direction: {result[2]}")
        print(f"   Confidence: {result[3]}/10")
    else:
        print(f"\n❌ {stock}: NO PREDICTIONS FOUND")

conn.close()
