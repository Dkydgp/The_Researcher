# 🧠 The Researcher: Think Tank for Stock Analysis

> **Institutional-grade stock market predictions powered by a 6-pillar AI framework**

An advanced stock market prediction system that combines **Algorithmic Analysis (RSI, SMA)**, **Social Media Momentum**, **News Sentiment**, and **Financial Theories** to generate daily predictions for top NIFTY 50 stocks.

![Dashboard](https://img.shields.io/badge/Status-Live-success)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Gemini 3](https://img.shields.io/badge/AI-Google%20Gemini%203%20Pro-purple)
![Hackathon](https://img.shields.io/badge/Contest-Gemini%203%20Hackathon-FFD700)

---

> 🏆 **Submitted to Gemini 3 Hackathon**
>
> **The Researcher** leverages **Gemini 3 Pro** to solve the "Black Box" problem in financial AI.
> - **Reasoning**: Synthesizes conflicting technical & fundamental signals.
> - **Self-Learning**: Closed-loop system that adjusts confidence based on past accuracy.
> - **Long Context**: Analyzes 200+ days of history in a single pass.

---

## 🎯 Features

- **6-Pillar AI Framework**: Combines technical indicators, social sentiment, and financial theories
- **Live Dashboard**: Real-time predictions with confidence scores
- **Historical Archive**: Track prediction accuracy over time with "Predict-Verify" loop
- **Automated Daily Updates**: Scheduler runs at 7 PM IST
- **Professional UI**: Modern, dark-themed interface with performance tracking

---

## 🧠 The 6 Analytical Pillars

1. **Algorithmic Analysis**: RSI (14-day) & SMA (20-day) trend detection
2. **Social Media Momentum**: Retail investor sentiment from news database
3. **Efficient Market Hypothesis**: News absorption speed analysis
4. **Sentiment Correlation**: Historical news-price pattern matching
5. **Behavioral Finance**: Mean reversion vs momentum detection
6. **Fundamental Anchoring**: P/E, ROCE, and valuation metrics

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Google Gemini API key ([Get it here](https://makersuite.google.com/app/apikey))
- Jina AI API key (optional, for news fetching)

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd "Stock Market"

# Install dependencies
pip install -r requirements.txt

# Set up your API key
# Create a .env file or set environment variable:
export GOOGLE_API_KEY="your_gemini_api_key_here"
```

### Running the System

```bash
# 1. Run the data pipeline (first time setup)
python run_pipeline.py

# 2. Start the web dashboard
python app.py

# 3. Open your browser
# Navigate to: http://localhost:8000
```

### Enable Daily Automation

```bash
# Run the scheduler (keeps running, updates daily at 7 PM)
python scheduler.py
```

---

## 📊 Architecture

```
Stock Market/
├── app.py                    # FastAPI web server
├── main.py                   # CLI entry point
├── run_pipeline.py           # Data fetching orchestrator
├── src/
│   ├── core/
│   │   ├── prediction_agent.py   # AI prediction engine
│   │   └── vector_db.py         # Database interface
│   ├── collectors/              # Data fetchers (news, prices, etc.)
│   ├── analysis/                # Tech indicators & patterns
│   └── utils/                   # Config & helpers
├── scripts/                  # Maintenance & migration scripts
├── stock_market.db           # Market data (prices, fundamentals, news)
├── predictions.db            # AI predictions + accuracy tracking
└── static/
    ├── index.html            # Dashboard UI
    ├── style.css             # Modern dark theme
    └── script.js             # Live/Archive view logic
```

---

## 🔧 Configuration

### Tracked Stocks
Edit `src/utils/filter_companies.py` to add/remove stocks:
```python
TOP_5_NIFTY = {
    "Reliance Industries": "RELIANCE.NS",
    "TCS": "TCS.NS",
    # Add more...
}
```

### Scheduler Time
Edit `src/utils/scheduler.py`:
```python
TARGET_HOUR = 19  # Change to desired hour (24-hour format)
```

---

## 📈 How Predictions Work

1. **Data Collection**: Fetches latest news, prices (30 days), fundamentals
2. **Technical Analysis**: Calculates RSI, SMA, trend strength
3. **Social Sentiment**: Searches news DB for retail investor buzz
4. **AI Synthesis**: Gemini LLM analyzes all 6 pillars → Prediction
5. **Storage**: Saves prediction with `open_price=NULL`, `close_price=NULL`
6. **Verification**: Next day, updates with actual prices → Accuracy badge

---

## 🎨 Dashboard Views

### Live Analysis
- Current predictions for next trading day
- Confidence scores (1-10)
- AI rationale with technical + social insights

### Archive
- Historical predictions with "Actual Move" comparison
- Accuracy badges: ✅ Correct / ❌ Missed
- "Outcome Pending" for future dates

---

## 🛡️ Security Notes

⚠️ **DO NOT** commit:
- `*.db` files (contains prediction data)
- `.env` files (contains API keys)
- `*.csv` files (data exports)

The `.gitignore` is pre-configured to exclude these.

---

## 📝 License

MIT License - Feel free to use and modify for your projects!

---

## 🙏 Acknowledgments

- **Google Gemini**: LLM for multi-factor analysis
- **yfinance**: Historical price data
- **Screener.in**: Fundamental metrics
- **FastAPI**: High-performance web framework

---

## 📧 Contact

For questions or contributions, please open an issue!

---

**⭐ Star this repo if you found it useful!**
