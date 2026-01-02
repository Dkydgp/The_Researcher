# Self-Learning Mechanism: How the AI Improves

The system uses a **Closed-Loop Feedback System** to verify predictions, calculate accuracy, and automatically adjust future confidence levels.

## 1. The Feedback Loop Process

The self-learning process consists of 3 automatic steps that run every day:

### Step 1: Verification (`evaluate_predictions`)
- The system checks yesterday's predictions against today's actual market open/close prices.
- It determines if the direction was correct (UP/DOWN/NEUTRAL).
- It calculates the **Error Margin** (difference between predicted % move and actual % move).

### Step 2: Performance Scoring (`_update_performance_metrics`)
- It calculates a **Rolling Accuracy Score** for each stock (based on last 10 predictions).
- It tracks two key metrics:
  - **Win Rate**: % of correct directions.
  - **Accuracy Score**: Weighted score (70% for direction, 30% for magnitude precision).

### Step 3: Strategy Adjustment (`get_confidence_adjustment`)
The system **automatically penalizes or boosts** the AI's confidence for the next prediction based on recent performance:

| Recent Accuracy (Last 10) | Evaluation | Action Taken |
|---------------------------|------------|--------------|
| **> 70%** | High Performance | **Boost Confidence (+1 to +2)** |
| **50% - 70%** | Average | **No Change** |
| **< 50%** | Poor Performance | **Penalize Confidence (-1 to -2)** |

**Example:**
If the AI has been wrong about `HDFC Bank` 3 times in a row, the `accuracy_rate` drops below 50%. The system calculates a negative adjustment (e.g., -1.5).
Next time the AI predicts "High Confidence Buy (8/10)", the system automatically downgrades it to "Moderate Buy (6.5/10)" before showing it to you.

## 2. Historical Scenario Matching

The system also uses **Case-Based Reasoning**:
1. Before making a prediction, it looks at the last 2 years of data.
2. It finds days with **similar technical conditions** (e.g., "RSI > 70 AND High Volume").
3. It checks what actually happened next in those specific past cases.
4. It presents this data to the AI: *"In the last 5 similar scenarios, the stock fell 4 times."*
5. This forces the AI to learn from historical patterns specific to that stock.

## 3. Strategy Correction (Dynamic Signal Weighting) - ✅ ACTIVE

The system now actively adjusts its strategy for each stock:

1.  **Tracking**: It records the accuracy of specific indicators (RSI, MACD, Volume) for each stock.
2.  **Dynamic Prompting**: Before asking the AI for a prediction, it injects specific advice based on past data.

**Example of how the Prompt changes automatically:**

> **STRATEGY ADVICE FOR TCS:**
> - **TRUST VOLUME**: High accuracy (80%) for this stock.
> - **IGNORE RSI**: Low accuracy (35%) for this stock recently.

This forces the AI to **adapt its reasoning** to the specific personality of each stock, rather than using a generic "one-size-fits-all" strategy.
