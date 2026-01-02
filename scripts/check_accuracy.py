import sqlite3

conn = sqlite3.connect('predictions.db')
cursor = conn.execute("""
SELECT 
    symbol, 
    prediction_date, 
    direction, 
    predicted_move, 
    open_price, 
    close_price, 
    confidence_score
FROM prediction_history 
WHERE open_price IS NOT NULL AND close_price IS NOT NULL
ORDER BY prediction_date DESC
""")

results = cursor.fetchall()

print("\n" + "="*80)
print("PREDICTION ACCURACY ANALYSIS")
print("="*80)

total = 0
correct = 0
by_stock = {}

for row in results:
    symbol, pred_date, direction, pred_move, open_p, close_p, confidence = row
    
    # Calculate actual movement
    if open_p and open_p != 0:
        actual_move = ((close_p - open_p) / open_p) * 100
    else:
        continue
    
    # Determine actual direction
    if actual_move > 0.2:
        actual_dir = 'UP'
    elif actual_move < -0.2:
        actual_dir = 'DOWN'
    else:
        actual_dir = 'NEUTRAL'
    
    # Check if correct
    is_correct = (direction == actual_dir)
    
    total += 1
    if is_correct:
        correct += 1
    
    # Track by stock
    if symbol not in by_stock:
        by_stock[symbol] = {'total': 0, 'correct': 0}
    by_stock[symbol]['total'] += 1
    if is_correct:
        by_stock[symbol]['correct'] += 1
    
    # Print individual result
    status = "CORRECT" if is_correct else "WRONG"
    print(f"\n{pred_date} | {symbol}")
    print(f"  Predicted: {direction} ({pred_move:+.2f}%) | Confidence: {confidence}/10")
    print(f"  Actual: {actual_dir} ({actual_move:+.2f}%)")
    print(f"  Result: {status}")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"Total Verified Predictions: {total}")
print(f"Correct Predictions: {correct}")
if total > 0:
    print(f"Overall Accuracy: {(correct/total*100):.1f}%")

print(f"\nAccuracy by Stock:")
for stock, stats in by_stock.items():
    acc = (stats['correct']/stats['total']*100) if stats['total'] > 0 else 0
    print(f"  {stock}: {stats['correct']}/{stats['total']} ({acc:.1f}%)")

conn.close()
