import sqlite3
import pandas as pd
from datetime import datetime

# Connect to predictions database
conn = sqlite3.connect('predictions.db')
cursor = conn.cursor()

print("="*80)
print("STOCK PREDICTION ACCURACY ANALYSIS REPORT")
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# Overall accuracy
cursor.execute('''
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN was_correct = 1 THEN 1 ELSE 0 END) as correct,
        AVG(confidence_score) as avg_confidence
    FROM prediction_history 
    WHERE was_correct IS NOT NULL
''')
result = cursor.fetchone()
total, correct, avg_conf = result
accuracy = (correct/total*100) if total > 0 else 0

print(f"\n1. OVERALL STATISTICS:")
print(f"   Total Predictions Evaluated: {total}")
print(f"   Correct Predictions: {correct}")
print(f"   Wrong Predictions: {total - correct}")
print(f"   ACCURACY: {accuracy:.1f}%  <-- THIS IS THE PROBLEM!")
print(f"   Average Confidence: {avg_conf:.1f}/10")

# Accuracy by symbol
print(f"\n2. ACCURACY BY SYMBOL:")
print(f"   {'-'*70}")
cursor.execute('''
    SELECT 
        symbol,
        COUNT(*) as total,
        SUM(CASE WHEN was_correct = 1 THEN 1 ELSE 0 END) as correct,
        AVG(confidence_score) as avg_conf
    FROM prediction_history 
    WHERE was_correct IS NOT NULL
    GROUP BY symbol
    ORDER BY total DESC
''')
for row in cursor.fetchall():
    symbol, total, correct, avg_conf = row
    acc = (correct/total*100) if total > 0 else 0
    status = "✓" if acc >= 50 else "✗"
    print(f"   {status} {symbol:15} {correct}/{total} correct ({acc:5.1f}%)  Avg Conf: {avg_conf:.1f}/10")

# Accuracy by direction
print(f"\n3. ACCURACY BY PREDICTED DIRECTION:")
print(f"   {'-'*70}")
cursor.execute('''
    SELECT 
        direction,
        COUNT(*) as total,
        SUM(CASE WHEN was_correct = 1 THEN 1 ELSE 0 END) as correct,
        AVG(confidence_score) as avg_conf
    FROM prediction_history 
    WHERE was_correct IS NOT NULL
    GROUP BY direction
''')
for row in cursor.fetchall():
    direction, total, correct, avg_conf = row
    acc = (correct/total*100) if total > 0 else 0
    print(f"   {direction:10} {correct:2}/{total:2} correct ({acc:5.1f}%)  Avg Conf: {avg_conf:.1f}/10")

# Recent predictions with details
print(f"\n4. RECENT PREDICTION FAILURES (Last 10):")
print(f"   {'-'*70}")
cursor.execute('''
    SELECT 
        symbol, direction, 
        predicted_move, 
        open_price, close_price,
        confidence_score, was_correct, rationale,
        prediction_date
    FROM prediction_history 
    WHERE was_correct IS NOT NULL
    ORDER BY id DESC
    LIMIT 10
''')

for i, row in enumerate(cursor.fetchall(), 1):
    symbol, pred_dir, pred_move, open_p, close_p, conf, correct, rationale, pred_date = row
    
    # Calculate actual move
    if open_p and open_p != 0:
        actual_move = ((close_p - open_p) / open_p) * 100
    else:
        actual_move = 0
    
    # Determine actual direction
    if actual_move > 0.2:
        actual_dir = 'UP'
    elif actual_move < -0.2:
        actual_dir = 'DOWN'
    else:
        actual_dir = 'NEUTRAL'
    
    status = "✓ CORRECT" if correct else "✗ WRONG"
    print(f"\n   {i}. {symbol} ({pred_date}) - {status}")
    print(f"      Predicted: {pred_dir} ({pred_move:.2f}%)")
    print(f"      Actual:    {actual_dir} ({actual_move:.2f}%)")
    print(f"      Confidence: {conf}/10")
    if rationale:
        print(f"      Rationale: {rationale[:80]}...")

# Analysis of errors
print(f"\n5. ERROR ANALYSIS:")
print(f"   {'-'*70}")
cursor.execute('''
    SELECT 
        symbol, direction, predicted_move, open_price, close_price
    FROM prediction_history 
    WHERE was_correct = 0
''')

wrong_predictions = cursor.fetchall()
if wrong_predictions:
    print(f"   Total Wrong Predictions: {len(wrong_predictions)}")
    
    # Analyze magnitude of errors
    errors = []
    for row in wrong_predictions:
        symbol, pred_dir, pred_move, open_p, close_p = row
        if open_p and open_p != 0:
            actual_move = ((close_p - open_p) / open_p) * 100
            error = abs(pred_move - actual_move)
            errors.append(error)
    
    if errors:
        avg_error = sum(errors) / len(errors)
        max_error = max(errors)
        print(f"   Average Prediction Error: {avg_error:.2f}%")
        print(f"   Maximum Prediction Error: {max_error:.2f}%")

print(f"\n{'='*80}")
print("RECOMMENDATIONS FOR IMPROVEMENT:")
print(f"{'='*80}")
print("""
1. ACCURACY IS TOO LOW (28.6%)
   - Current model is barely better than random guessing
   - Need to improve data quality and analysis methodology

2. POSSIBLE ISSUES:
   a) Insufficient historical data for training
   b) Over-reliance on technical indicators without context
   c) News sentiment analysis may not be accurate
   d) Market regime changes not properly accounted for
   e) Gemini AI prompts may need refinement

3. SUGGESTED IMPROVEMENTS:
   a) Add more historical data (at least 1-2 years)
   b) Implement ensemble methods (combine multiple signals)
   c) Add sector-specific analysis
   d) Improve news sentiment scoring
   e) Add market regime detection (bull/bear/sideways)
   f) Implement risk management filters
   g) Use more sophisticated technical analysis
   h) Add fundamental analysis weight
   i) Implement backtesting before live predictions
   j) Add confidence calibration based on past performance

4. IMMEDIATE ACTIONS:
   - Review and improve AI prompts for better reasoning
   - Add more data sources (FII/DII data, sector trends)
   - Implement stricter validation before saving predictions
   - Add ensemble voting (multiple models/timeframes)
""")

conn.close()
