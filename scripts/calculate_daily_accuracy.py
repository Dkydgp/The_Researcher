import sqlite3
from datetime import datetime
import sys
import io

# Force UTF-8 for Windows consoles/logs
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append('.')
from src.utils.filter_companies import INDICES

# Ticker mapping
TICKER_MAP = {
    "Reliance Industries": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "Infosys": "INFY.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "Bharti Airtel": "BHARTIARTL.NS",
    "ITC": "ITC.NS",
    "Wipro": "WIPRO.NS",
    "HCL Technologies": "HCLTECH.NS",
    "Bajaj Finance": "BAJFINANCE.NS"
}

def calculate_cumulative_accuracy():
    """Calculate cumulative accuracy from ALL historical predictions"""
    
    pred_conn = sqlite3.connect("predictions.db")
    pred_conn.row_factory = sqlite3.Row
    
    market_conn = sqlite3.connect("stock_market.db")
    market_conn.row_factory = sqlite3.Row
    
    # Get ALL daily predictions (cumulative)
    predictions = pred_conn.execute("SELECT * FROM daily_predictions ORDER BY prediction_date").fetchall()
    
    total_predictions = 0
    sentiment_correct = 0
    price_correct = 0
    confidence_stats = {
        "high": {"correct": 0, "total": 0},
        "medium": {"correct": 0, "total": 0},
        "low": {"correct": 0, "total": 0}
    }
    
    for pred in predictions:
        symbol = pred["symbol"]
        pred_date = pred["prediction_date"]
        
        # Skip indices
        if symbol in INDICES:
            continue
        
        short_name = symbol.split(' ')[0]
        ticker = TICKER_MAP.get(symbol, f"{short_name}.NS")
        
        # Get actual market data
        price_row = market_conn.execute(
            "SELECT open, close FROM stock_daily_prices WHERE symbol = ? AND date = ?",
            (ticker, pred_date)
        ).fetchone()
        
        if not price_row or not price_row["close"] or not price_row["open"]:
            continue
        
        total_predictions += 1
        
        # Calculate accuracy
        actual_move = ((price_row["close"] - price_row["open"]) / price_row["open"] * 100)
        predicted_move = float(pred["predicted_move"]) if pred["predicted_move"] else 0
        
        # Sentiment accuracy
        predicted_direction = "UP" if predicted_move >= 0 else "DOWN"
        actual_direction = "UP" if actual_move >= 0 else "DOWN"
        if predicted_direction == actual_direction:
            sentiment_correct += 1
        
        # Price accuracy (within 0.5% tolerance)
        if abs(predicted_move - actual_move) <= 0.5:
            price_correct += 1
        
        # Confidence correlation
        conf_score = int(pred["confidence_score"]) if pred["confidence_score"] else 5
        if conf_score >= 7:
            conf_level = "high"
        elif conf_score >= 5:
            conf_level = "medium"
        else:
            conf_level = "low"
        
        confidence_stats[conf_level]["total"] += 1
        if predicted_direction == actual_direction:
            confidence_stats[conf_level]["correct"] += 1
    
    # Calculate percentages
    sentiment_accuracy = (sentiment_correct / total_predictions * 100) if total_predictions > 0 else 0
    price_accuracy = (price_correct / total_predictions * 100) if total_predictions > 0 else 0
    
    high_conf_acc = (confidence_stats["high"]["correct"] / confidence_stats["high"]["total"] * 100) if confidence_stats["high"]["total"] > 0 else 0
    medium_conf_acc = (confidence_stats["medium"]["correct"] / confidence_stats["medium"]["total"] * 100) if confidence_stats["medium"]["total"] > 0 else 0
    low_conf_acc = (confidence_stats["low"]["correct"] / confidence_stats["low"]["total"] * 100) if confidence_stats["low"]["total"] > 0 else 0
    
    # Store in database
    today = datetime.now().strftime("%Y-%m-%d")
    
    try:
        pred_conn.execute('''
            INSERT OR REPLACE INTO daily_accuracy_metrics 
            (date, timeframe, sentiment_accuracy, price_accuracy, total_predictions,
             high_conf_accuracy, medium_conf_accuracy, low_conf_accuracy)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (today, 'DAILY', round(sentiment_accuracy, 1), round(price_accuracy, 1), 
              total_predictions, round(high_conf_acc, 1), round(medium_conf_acc, 1), round(low_conf_acc, 1)))
        
        pred_conn.commit()
        
        print(f"✅ Cumulative Accuracy Updated for {today}")
        print(f"   Sentiment: {sentiment_accuracy:.1f}%")
        print(f"   Price: {price_accuracy:.1f}%")
        print(f"   Total Predictions: {total_predictions}")
        print(f"   High Conf: {high_conf_acc:.1f}%")
        print(f"   Medium Conf: {medium_conf_acc:.1f}%")
        print(f"   Low Conf: {low_conf_acc:.1f}%")
        
    except Exception as e:
        print(f"❌ Error storing metrics: {e}")
    
    pred_conn.close()
    market_conn.close()

if __name__ == "__main__":
    calculate_cumulative_accuracy()
