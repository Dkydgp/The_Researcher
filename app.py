from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import sqlite3
import pandas as pd
import subprocess
import os
import json
from datetime import datetime
from src.core.prediction_agent import PredictionAgent
from src.utils.filter_companies import TOP_5_NIFTY, INDICES

# Ticker mapping for stocks that don't use their display name
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

app = FastAPI()

# Ensure static directory exists
if not os.path.exists("static"):
    os.makedirs("static")

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# NEW: moved all HTML routes to bottom of file for better organization

# ========== UTILITY FUNCTIONS ==========
@app.get("/api/latest")
async def get_latest_data():
    """Fetch latest predictions (today) and market data"""
    try:
        results = []
        # Main DB for current prices/fundamentals
        main_conn = sqlite3.connect("stock_market.db")
        main_conn.row_factory = sqlite3.Row
        
        # Pred DB for AI analysis
        pred_conn = sqlite3.connect("predictions.db")
        pred_conn.row_factory = sqlite3.Row
        
        from datetime import date
        
        today = date.today().isoformat()
        
        # Process INDICES FIRST, then stocks
        ordered_symbols = list(INDICES.keys()) + list(TOP_5_NIFTY.keys())
        
        for symbol in ordered_symbols:
            short_name = symbol.split(' ')[0]
            is_index = symbol in INDICES
            
            # 1. Get MOST RECENT Prediction (not necessarily today)
            pred_row = pred_conn.execute(
                "SELECT * FROM prediction_history WHERE symbol = ? ORDER BY prediction_date DESC, id DESC LIMIT 1", 
                (symbol,)
            ).fetchone()

            prediction = {}
            if pred_row:
                prediction = {
                    "direction": pred_row["direction"],
                    "predicted_percentage_move": pred_row["predicted_move"],
                    "confidence_score": pred_row["confidence_score"],
                    "rationale": pred_row["rationale"],
                    "timestamp": pred_row["created_at"],
                    "date": pred_row["prediction_date"]
                }
            else:
                prediction = {
                    "direction": "PENDING",
                    "predicted_percentage_move": 0,
                    "confidence_score": 0,
                    "rationale": "AI analysis pending. Please run pipeline."
                }

            # 2. Get latest price (Live/End of Day)
            if is_index:
                # For indices, use the exact ticker
                ticker = INDICES[symbol]["ticker"]
                price_data = pd.read_sql_query(f"SELECT * FROM stock_daily_prices WHERE symbol = '{ticker}' ORDER BY date DESC LIMIT 1", main_conn)
            else:
                # For stocks, use the ticker map
                ticker = TICKER_MAP.get(symbol, f"{short_name}.NS")
                price_data = pd.read_sql_query(f"SELECT * FROM stock_daily_prices WHERE symbol = '{ticker}' ORDER BY date DESC LIMIT 1", main_conn)
            
            # 3. Fundamentals (SKIP for indices)
            if is_index:
                fund_data = pd.DataFrame()  # Empty for indices
            else:
                fund_data = pd.read_sql_query(f"SELECT * FROM stock_fundamentals WHERE symbol LIKE '{short_name}%' ORDER BY date DESC LIMIT 1", main_conn)
            
            results.append({
                "symbol": symbol,
                "short_name": short_name,
                "is_index": is_index,
                "price": price_data.to_dict('records')[0] if not price_data.empty else {},
                "fundamentals": fund_data.to_dict('records')[0] if not fund_data.empty else {},
                "prediction": prediction
            })
        
        # Get market context
        market_context_data = pd.read_sql_query("SELECT * FROM market_context ORDER BY date DESC LIMIT 1", main_conn)
        market_context = {}
        if not market_context_data.empty:
            mc = market_context_data.to_dict('records')[0]
            market_context = {
                'sp500_close': mc.get('sp500_close'),
                'sp500_change': mc.get('sp500_change'),
                'crude_oil': mc.get('crude_oil'),
                'usd_inr': mc.get('usd_inr'),
                'nifty_trend': mc.get('nifty_trend'),
                'volatility_regime': mc.get('volatility_regime')
            }
        
        main_conn.close()
        pred_conn.close()
            
        return {
            "status": "success",
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "market_context": market_context,
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history/dates")
async def get_history_dates(timeframe: str = "DAILY"):
    """Get list of dates we have predictions for (filtered by timeframe)"""
    try:
        table_map = {
            "DAILY": "daily_predictions",
            "WEEKLY": "weekly_predictions",
            "MONTHLY": "monthly_predictions"
        }
        table_name = table_map.get(timeframe.upper(), "daily_predictions")
        
        conn = sqlite3.connect("predictions.db")
        cursor = conn.cursor()
        
        # Check if table exists first
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            conn.close()
            return {"dates": []}

        cursor.execute(f"SELECT DISTINCT prediction_date FROM {table_name} ORDER BY prediction_date DESC")
        dates = [row[0] for row in cursor.fetchall()]
        conn.close()
        return {"dates": dates}
    except Exception as e:
        return {"dates": []} # Return empty if DB doesn't exist yet

@app.get("/api/history/{date_str}")
async def get_history_by_date(date_str: str, timeframe: str = "DAILY"):
    """Get predictions for a specific date and timeframe"""
    try:
        table_map = {
            "DAILY": "daily_predictions",
            "WEEKLY": "weekly_predictions",
            "MONTHLY": "monthly_predictions"
        }
        table_name = table_map.get(timeframe.upper(), "daily_predictions")

        conn = sqlite3.connect("predictions.db")
        conn.row_factory = sqlite3.Row
        
        # Check if table exists
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            conn.close()
            return {"date": date_str, "data": []}

        rows = conn.execute(f"SELECT * FROM {table_name} WHERE prediction_date = ?", (date_str,)).fetchall()
        
        # Get actual prices for context (using daily close as approx reference)
        # For weekly/monthly, ideally we'd get that specific period's close, but daily close of that date is a fine reference point
        main_conn = sqlite3.connect("stock_market.db")
        main_conn.row_factory = sqlite3.Row
        
        results = []
        for row in rows:
            symbol = row["symbol"]
            short_name = symbol.split(' ')[0]
            is_index = symbol in INDICES
            ticker = INDICES[symbol]["ticker"] if is_index else TICKER_MAP.get(symbol, f"{short_name}.NS")
            
            # Get EOD price for that date (Archive Verification)
            price_row = main_conn.execute(
                "SELECT open, close FROM stock_daily_prices WHERE symbol = ? AND date = ?", 
                (ticker, date_str)
            ).fetchone()

            market_data = {
                "open": price_row["open"] if price_row else None,
                "close": price_row["close"] if price_row else None
            }
            
            # Map fields based on timeframe (normalizing response)
            prediction_data = {
                "direction": row["direction"],
                "confidence_score": row["confidence_score"],
                "rationale": row["rationale"],
                "target_date": row["target_date"] if "target_date" in row.keys() else None
            }
            
            # Add specific fields
            if timeframe == "DAILY":
                prediction_data["predicted_move"] = row["predicted_move"]
            elif timeframe == "WEEKLY":
                 prediction_data["week_high_target"] = row["week_high_target"]
                 prediction_data["week_low_target"] = row["week_low_target"]
            elif timeframe == "MONTHLY":
                 prediction_data["month_high_target"] = row["month_high_target"]
                 prediction_data["month_low_target"] = row["month_low_target"]

            results.append({
                "symbol": symbol,
                "prediction": prediction_data,
                "market_data": market_data
            })
            
        conn.close()
        main_conn.close()
        
        return {"date": date_str, "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/archive/metrics")
async def get_archive_metrics(timeframe: str = "DAILY", start_date: str = None, end_date: str = None):
    """Calculate performance metrics for archive predictions"""
    try:
        table_map = {
            "DAILY": "daily_predictions",
            "WEEKLY": "weekly_predictions",
            "MONTHLY": "monthly_predictions"
        }
        table_name = table_map.get(timeframe.upper(), "daily_predictions")
        
        conn = sqlite3.connect("predictions.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            conn.close()
            return {
                "overall_accuracy": {"sentiment_accuracy": 0, "price_accuracy": 0, "total_predictions": 0},
                "top_performers": [],
                "bottom_performers": [],
                "confidence_correlation": {}
            }
        
        # Build query with optional date filtering
        date_filter = ""
        params = []
        if start_date and end_date:
            date_filter = " WHERE prediction_date BETWEEN ? AND ?"
            params = [start_date, end_date]
        elif start_date:
            date_filter = " WHERE prediction_date >= ?"
            params = [start_date]
        elif end_date:
            date_filter = " WHERE prediction_date <= ?"
            params = [end_date]
        
        # Get all predictions with market data
        query = f"SELECT * FROM {table_name}{date_filter} ORDER BY prediction_date DESC"
        predictions = cursor.execute(query, params).fetchall()
        
        # Get market data
        main_conn = sqlite3.connect("stock_market.db")
        main_conn.row_factory = sqlite3.Row
        
        total_predictions = 0
        sentiment_correct = 0
        price_correct = 0
        stock_stats = {}
        confidence_stats = {"high": {"correct": 0, "total": 0}, "medium": {"correct": 0, "total": 0}, "low": {"correct": 0, "total": 0}}
        
        for pred in predictions:
            symbol = pred["symbol"]
            pred_date = pred["prediction_date"]
            short_name = symbol.split(' ')[0]
            is_index = symbol in INDICES
            
            # Skip indices (NIFTY 50, SENSEX)
            if is_index:
                continue
            
            ticker = TICKER_MAP.get(symbol, f"{short_name}.NS")
            
            # Get actual market data
            price_row = main_conn.execute(
                "SELECT open, close FROM stock_daily_prices WHERE symbol = ? AND date = ?",
                (ticker, pred_date)
            ).fetchone()
            
            if not price_row or not price_row["close"] or not price_row["open"]:
                continue
            
            total_predictions += 1
            
            # Initialize stock stats
            if symbol not in stock_stats:
                stock_stats[symbol] = {"correct": 0, "total": 0}
            stock_stats[symbol]["total"] += 1
            
            # Calculate accuracy for DAILY timeframe
            if timeframe == "DAILY":
                actual_move = ((price_row["close"] - price_row["open"]) / price_row["open"] * 100)
                predicted_move = float(pred["predicted_move"]) if pred["predicted_move"] else 0
                
                # Sentiment accuracy
                predicted_direction = "UP" if predicted_move >= 0 else "DOWN"
                actual_direction = "UP" if actual_move >= 0 else "DOWN"
                if predicted_direction == actual_direction:
                    sentiment_correct += 1
                    stock_stats[symbol]["correct"] += 1
                
                # Price accuracy (within 0.5% tolerance)
                if abs(predicted_move - actual_move) <= 0.5:
                    price_correct += 1
            else:
                # For weekly/monthly, use simple direction check
                if pred["direction"] == "UP" and price_row["close"] > price_row["open"]:
                    sentiment_correct += 1
                    stock_stats[symbol]["correct"] += 1
                elif pred["direction"] == "DOWN" and price_row["close"] < price_row["open"]:
                    sentiment_correct += 1
                    stock_stats[symbol]["correct"] += 1
            
            # Confidence correlation
            conf_score = int(pred["confidence_score"]) if pred["confidence_score"] else 5
            if conf_score >= 7:
                conf_level = "high"
            elif conf_score >= 5:
                conf_level = "medium"
            else:
                conf_level = "low"
            
            confidence_stats[conf_level]["total"] += 1
            if predicted_direction == actual_direction if timeframe == "DAILY" else (pred["direction"] == "UP" and price_row["close"] > price_row["open"]) or (pred["direction"] == "DOWN" and price_row["close"] < price_row["open"]):
                confidence_stats[conf_level]["correct"] += 1
        
        conn.close()
        main_conn.close()
        
        # Calculate percentages
        sentiment_accuracy = (sentiment_correct / total_predictions * 100) if total_predictions > 0 else 0
        price_accuracy = (price_correct / total_predictions * 100) if total_predictions > 0 else 0
        
        # Calculate confidence correlation
        confidence_correlation = {
            "high_confidence_accuracy": (confidence_stats["high"]["correct"] / confidence_stats["high"]["total"] * 100) if confidence_stats["high"]["total"] > 0 else 0,
            "medium_confidence_accuracy": (confidence_stats["medium"]["correct"] / confidence_stats["medium"]["total"] * 100) if confidence_stats["medium"]["total"] > 0 else 0,
            "low_confidence_accuracy": (confidence_stats["low"]["correct"] / confidence_stats["low"]["total"] * 100) if confidence_stats["low"]["total"] > 0 else 0
        }
        
        return {
            "overall_accuracy": {
                "sentiment_accuracy": round(sentiment_accuracy, 1),
                "price_accuracy": round(price_accuracy, 1),
                "total_predictions": total_predictions
            },
            "confidence_correlation": confidence_correlation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/refresh")
async def refresh_pipeline():
    """Trigger the full data pipeline"""
    try:
        # Run run_pipeline.py as a subprocess
        process = subprocess.Popen(["python", "run_pipeline.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return {"status": "started", "message": "Pipeline execution started in background"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/accuracy/latest")
async def get_latest_accuracy():
    """Get latest cumulative accuracy metrics from database"""
    try:
        conn = sqlite3.connect("predictions.db")
        conn.row_factory = sqlite3.Row
        
        # Get most recent entry
        row = conn.execute(
            "SELECT * FROM daily_accuracy_metrics WHERE timeframe = 'DAILY' ORDER BY date DESC LIMIT 1"
        ).fetchone()
        
        conn.close()
        
        if row:
            return {
                "date": row["date"],
                "sentiment_accuracy": row["sentiment_accuracy"],
                "price_accuracy": row["price_accuracy"],
                "total_predictions": row["total_predictions"],
                "high_conf_accuracy": row["high_conf_accuracy"],
                "medium_conf_accuracy": row["medium_conf_accuracy"],
                "low_conf_accuracy": row["low_conf_accuracy"]
            }
        else:
            return {
                "date": None,
                "sentiment_accuracy": 0,
                "price_accuracy": 0,
                "total_predictions": 0,
                "high_conf_accuracy": 0,
                "medium_conf_accuracy": 0,
                "low_conf_accuracy": 0
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== HTML ROUTES ==========

@app.get("/")
@app.get("/home")
async def home():
    """Home/Landing page"""
    return FileResponse("static/home.html")

@app.get("/daily")
async def index():
    """Daily predictions view"""
    return FileResponse("static/daily.html")

@app.get("/weekly")
async def weekly_page():
    """Serve weekly predictions page"""
    return FileResponse("static/weekly.html")

@app.get("/monthly")
async def monthly_page():
    """Serve monthly predictions page"""
    return FileResponse("static/monthly.html")

@app.get("/archive")
async def archive_page():
    """Serve archive page"""
    return FileResponse("static/archive.html")

@app.get("/api/predictions/daily")
async def get_daily_predictions():
    """Fetch latest daily predictions"""
    try:
        conn = sqlite3.connect("predictions.db")
        conn.row_factory = sqlite3.Row
        main_conn = sqlite3.connect("stock_market.db")
        
        results = []
        ordered_symbols = list(INDICES.keys()) + list(TOP_5_NIFTY.keys())
        
        for symbol in ordered_symbols:
            # Get daily prediction
            pred_row = conn.execute(
                "SELECT * FROM daily_predictions WHERE symbol = ? ORDER BY prediction_date DESC LIMIT 1",
                (symbol,)
            ).fetchone()
            
            if pred_row:
                # Get latest price
                short_name = symbol.split(' ')[0]
                is_index = symbol in INDICES
                ticker = INDICES[symbol]["ticker"] if is_index else TICKER_MAP.get(symbol, f"{short_name}.NS")
                price_data = pd.read_sql_query(f"SELECT * FROM stock_daily_prices WHERE symbol = '{ticker}' ORDER BY date DESC LIMIT 1", main_conn)
                
                results.append({
                    "symbol": symbol,
                    "timeframe": "DAILY",
                    "current_price": float(price_data['close'].iloc[0]) if not price_data.empty else None,
                    "prediction": {
                        "direction": pred_row["direction"],
                        "confidence_score": pred_row["confidence_score"],
                        "probability": pred_row["probability"],
                        "predicted_move": pred_row["predicted_move"],
                        "target_price_min": pred_row["target_price_min"],
                        "target_price_max": pred_row["target_price_max"],
                        "risk_level": pred_row["risk_level"],
                        "rationale": pred_row["rationale"],
                        "target_date": pred_row["target_date"]
                    }
                })
        
        conn.close()
        main_conn.close()
        return {"predictions": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/predictions/weekly")
async def get_weekly_predictions():
    """Fetch latest weekly predictions"""
    try:
        conn = sqlite3.connect("predictions.db")
        conn.row_factory = sqlite3.Row
        main_conn = sqlite3.connect("stock_market.db")
        
        results = []
        ordered_symbols = list(INDICES.keys()) + list(TOP_5_NIFTY.keys())
        
        for symbol in ordered_symbols:
            pred_row = conn.execute(
                "SELECT * FROM weekly_predictions WHERE symbol = ? ORDER BY prediction_date DESC LIMIT 1",
                (symbol,)
            ).fetchone()
            
            if pred_row:
                short_name = symbol.split(' ')[0]
                is_index = symbol in INDICES
                ticker = INDICES[symbol]["ticker"] if is_index else TICKER_MAP.get(symbol, f"{short_name}.NS")
                price_data = pd.read_sql_query(f"SELECT * FROM stock_daily_prices WHERE symbol = '{ticker}' ORDER BY date DESC LIMIT 1", main_conn)
                
                results.append({
                    "symbol": symbol,
                    "timeframe": "WEEKLY",
                    "current_price": float(price_data['close'].iloc[0]) if not price_data.empty else None,
                    "prediction": {
                        "direction": pred_row["direction"],
                        "confidence_score": pred_row["confidence_score"],
                        "probability": pred_row["probability"],
                        "predicted_move": pred_row["predicted_move"],
                        "week_high_target": pred_row["week_high_target"],
                        "week_low_target": pred_row["week_low_target"],
                        "trend_strength": pred_row["trend_strength"],
                        "trend_strength": pred_row["trend_strength"],
                        "rationale": pred_row["rationale"],
                        "target_date": pred_row["target_date"]
                    }
                })
        
        conn.close()
        main_conn.close()
        return {"predictions": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/predictions/monthly")
async def get_monthly_predictions():
    """Fetch latest monthly predictions"""
    try:
        conn = sqlite3.connect("predictions.db")
        conn.row_factory = sqlite3.Row
        main_conn = sqlite3.connect("stock_market.db")
        
        results = []
        ordered_symbols = list(INDICES.keys()) + list(TOP_5_NIFTY.keys())
        
        for symbol in ordered_symbols:
            pred_row = conn.execute(
                "SELECT * FROM monthly_predictions WHERE symbol = ? ORDER BY prediction_date DESC LIMIT 1",
                (symbol,)
            ).fetchone()
            
            if pred_row:
                short_name = symbol.split(' ')[0]
                is_index = symbol in INDICES
                ticker = INDICES[symbol]["ticker"] if is_index else TICKER_MAP.get(symbol, f"{short_name}.NS")
                price_data = pd.read_sql_query(f"SELECT * FROM stock_daily_prices WHERE symbol = '{ticker}' ORDER BY date DESC LIMIT 1", main_conn)
                
                results.append({
                    "symbol": symbol,
                    "timeframe": "MONTHLY",
                    "current_price": float(price_data['close'].iloc[0]) if not price_data.empty else None,
                    "prediction": {
                        "direction": pred_row["direction"],
                        "confidence_score": pred_row["confidence_score"],
                        "probability": pred_row["probability"],
                        "predicted_move": pred_row["predicted_move"],
                        "month_high_target": pred_row["month_high_target"],
                        "month_low_target": pred_row["month_low_target"],
                        "fundamental_rating": pred_row["fundamental_rating"],
                        "fundamental_rating": pred_row["fundamental_rating"],
                        "rationale": pred_row["rationale"],
                        "target_date": pred_row["target_date"]
                    }
                })
        
        conn.close()
        main_conn.close()
        return {"predictions": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/blog")
async def blog():
    """Blog/Insights page"""
    return FileResponse("static/blog.html")

@app.get("/article/jio-report")
async def jio_report():
    """Jio Financial Report Article"""
    return FileResponse("static/article_jio.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
