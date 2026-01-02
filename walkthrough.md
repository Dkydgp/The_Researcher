# The Researcher: Project Walkthrough

## 1. Overview
**The Researcher** is an autonomous stock analysis agent that provides institutional-grade insights for the Indian Market. We have successfully upgraded the system to use **3 Distinct Trading Frameworks** for better accuracy and realism.

## 2. Key Features Implemented

### 🧠 Distinct AI Logic
| Timeframe | Framework | Key Inputs | Target Range |
| :--- | :--- | :--- | :--- |
| **DAILY** | **Day Trading** | Intraday patterns, Momentum, RSI | **0.1% - 3.0%** (Strict Realism) |
| **WEEKLY** | **Swing Trading** | Weekly Candles, Trend Strength, Sector Rotation | 3% - 8% |
| **MONTHLY** | **Position Trading** | Fundamentals (P/E, ROCE), Macro Economics | 5% - 15% |

### 🛠️ Robust Pipeline (`retry_predictions.py`)
- **Problem**: API Rate Limits (Error 429) caused missing stocks.
- **Solution**: A dedicated script that:
    - Iterates through all 12 target stocks/indices.
    - Automatically retries on failure.
    - **Adaptive Delay**: Sleeps 45s between requests to respect strict free-tier limits.
    - **Model**: Optimized to use `gemini-2.0-flash-lite` (or Pro if upgraded).

### 📰 News & Social Integration
- **News Impact**: Full articles are fed to the AI to auto-detect "Earnings Surprises" or "Regulatory Shocks".
- **Social Sentiment**: The system searches for "retail frenzy" (Reddit/Twitter keywords) to adjust confidence scores for meme stocks.

## 3. How to Run

### Option A: Free Tier (Slow & Steady)
Run the pipeline and let it run in the background ~25 mins/day.
```powershell
python retry_predictions.py
```

### Option B: Paid Tier (Fast)
Upgrade to Pay-as-you-go (~$0.50/month).
Then reduce the sleep timer in `retry_predictions.py` to 1 second:
```python
# line 40
time.sleep(1) 
```

## 4. Verification
Check the dashboard at: `http://localhost:8000`
You should see:
- Distinct predictions for "Daily", "Weekly", "Monthly".
- **Dedicated Archive**: View historical accuracy at `http://localhost:8000/archive`.
- Realism constraints applied (no more wild 10% daily predictions).
