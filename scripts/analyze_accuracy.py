import sqlite3
import pandas as pd
from datetime import datetime

# Connect to database
conn = sqlite3.connect('predictions.db')

# Get all verified predictions (with actual prices)
query = """
SELECT 
    symbol, 
    prediction_date, 
    direction, 
    predicted_move, 
    open_price, 
    close_price, 
    confidence_score,
    rationale
FROM prediction_history 
WHERE open_price IS NOT NULL AND close_price IS NOT NULL
ORDER BY prediction_date DESC
"""

df = pd.read_sql_query(query, conn)

# Calculate actual movement and accuracy
results = []
for idx, row in df.iterrows():
    if row['open_price'] and row['open_price'] != 0:
        actual_move = ((row['close_price'] - row['open_price']) / row['open_price']) * 100
    else:
        actual_move = 0
    
    actual_dir = 'UP' if actual_move > 0.2 else ('DOWN' if actual_move < -0.2 else 'NEUTRAL')
    
    # Check if prediction was correct
    is_correct = (row['direction'] == actual_dir)
    
    results.append({
        'Symbol': row['symbol'],
        'Date': row['prediction_date'],
        'Predicted': f"{row['direction']} ({row['predicted_move']:+.2f}%)",
        'Actual': f"{actual_dir} ({actual_move:+.2f}%)",
        'Correct': '✅' if is_correct else '❌',
        'Confidence': f"{row['confidence_score']}/10"
    })

results_df = pd.DataFrame(results)

print("\n" + "="*80)
print("📊 PREDICTION ACCURACY ANALYSIS")
print("="*80)

# Overall accuracy
total = len(results_df)
correct = (results_df['Correct'] == '✅').sum()
accuracy = (correct / total * 100) if total > 0 else 0

print(f"\n🎯 OVERALL PERFORMANCE:")
print(f"   Total Verified Predictions: {total}")
print(f"   Correct Predictions: {correct}")
print(f"   Accuracy Rate: {accuracy:.1f}%")

# Accuracy by stock
print(f"\n📈 ACCURACY BY STOCK:")
for symbol in results_df['Symbol'].unique():
    stock_df = results_df[results_df['Symbol'] == symbol]
    stock_correct = (stock_df['Correct'] == '✅').sum()
    stock_total = len(stock_df)
    stock_acc = (stock_correct / stock_total * 100) if stock_total > 0 else 0
    print(f"   {symbol}: {stock_correct}/{stock_total} ({stock_acc:.1f}%)")

# Show recent predictions
print(f"\n📋 DETAILED RESULTS (Most Recent):")
print(results_df.head(10).to_string(index=False))

conn.close()
