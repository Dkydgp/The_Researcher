pip3 install -r requirements.txt
# The Researcher: Autonomous Stock Market Analysis System
**White Paper**
**Date:** December 2025

---

## 1. Executive Summary
**The Researcher** is an advanced autonomous agent designed to democratize high-level financial analysis for the Indian Stock Market. By leveraging state-of-the-art Large Language Models (LLMs) specifically Google's Gemini Pro/Flash, the system synthesizes complex market data—technical indicators, fundamental metrics, and news sentiment—into actionable, human-readable investment insights.

Unlike traditional algorithmic trading systems that rely solely on quantitative metrics, **The Researcher** mimics the reasoning process of a human analyst, providing not just "Buy/Sell" signals but detailed rationales, confidence scores, and specific price targets across multiple timeframes (Daily, Weekly, Monthly).

---

## 2. Problem Statement
Retail investors in the Indian market often face "Analysis Paralysis":
1.  **Data Overload**: Tracking price action, news, and technicals for multiple stocks is impossible for an individual.
2.  **Lack of Expertise**: interpreting complex indicators (RSI, Bollinger Bands, MACD) requires years of experience.
3.  **Emotional Bias**: Human decisions are often clouded by fear or greed.

## 3. The Solution: The Researcher
**The Researcher** acts as a 24/7 AI Equities Analyst. It creates a standardized, objective analysis pipeline that:
*   Aggregates data from diverse sources.
*   Applies "Chain-of-Thought" reasoning to weigh conflicting signals.
*   Delivers clear, graded analyses (High/Medium/Low Confidence).

---

## 4. Technical Architecture

### 4.1. Data Layer (The Senses)
The system ingests data from three primary streams:
*   **Market Data**: Historical and Real-time price data (Open, High, Low, Close, Volume) via `yfinance` APIs (or similar providers).
*   **Technical Intelligence**: Automated calculation of key indicators:
    *   *Trend*: SMA-50, SMA-200.
    *   *Momentum*: RSI (Relative Strength Index).
    *   *Volatility*: Bollinger Bands.
*   **Sentiment Engine**: A dedicated `NewsFetcher` module scours financial news to gauge market mood (Bullish/Bearish/Neutral).

### 4.2. Intelligence Layer (The Brain)
At the core is the `AnalysisAgent` (Python), powered by **Google Gemini**.
*   **Prompt Engineering**: The system uses sophisticated, structured prompts that force the AI to:
    1.  Analyze the 'Big Picture' (Global Market Context).
    2.  Evaluate Technical Strength.
    3.  Assess News Impact.
    4.  Synthesize a Verdict.
*   **Multi-Timeframe Logic**:
    *   **Daily**: Focuses on Intraday volatility and immediate support/resistance (1-2 days).
    *   **Weekly**: Analyzes Swing Trading setups (1-2 weeks).
    *   **Monthly**: Evaluates macro trends and Positional setups (1-4 weeks).

### 4.3. Application Layer (The Interface)
*   **Backend**: `FastAPI` (Python) serves as the high-performance REST API, handling requests and serving the frontend.
*   **Database**: `SQLite` ensures lightweight but robust storage of all historical analyses and market data.
*   **Frontend**: A modern, responsive Web Dashboard built with Vanilla JavaScript and CSS.
    *   **Features**: Confidence Gauges, Probability Bars, Live Price Updates (simulated via API), and a Historical Analysis Archive.

---

## 5. Workflow Algorithm

1.  **Trigger**: The Analysis Pipeline initiates (Cron job or Manual).
2.  **Context Loading**: System fetches the latest NIFTY 50 and SENSEX performance to understand market direction.
3.  **Symbol Iteration**: For each target stock (e.g., TCS, HDFC Bank):
    *   Fetch Data -> Calculate Indicators -> Fetch News.
4.  **LLM Inference**: Data is formatted into a prompt and sent to Gemini.
    *   *Constraint*: The agent must output strictly formatted JSON including `direction`, `target_price`, `rationale`, and `confidence_score`.
5.  **Validation**: The output is parsed. If the AI hallucinates invalid JSON, the system retries automatically.
6.  **Storage**: Valid analyses are saved with a timestamp and `target_date`.
7.  **Presentation**: The Dashboard serves these analyses to the user immediately.

---

## 6. Key Features
*   **Archive & Accountability**: Every analysis is stored. Users can view past Daily/Weekly/Monthly analyses to verify the AI's accuracy against actual market outcomes.
*   **Robustness**: The system includes self-healing mechanisms (Retries on API failure, cache busting for frontend updates).
*   **Scalability**: Designed to easily expand from 12 stocks to 50+ by simply updating the ticker map.

---

## 7. Conclusion
## 7. Conclusion
**The Researcher** represents the next step in personal finance tools—moving away from static charts to dynamic, intelligent conversation about the market. It empowers users with institutional-grade reasoning in a simple, accessible dashboard.
