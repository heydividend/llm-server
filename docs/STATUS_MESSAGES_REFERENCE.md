# Harvey AI - Context-Aware Status Messages Reference

## Overview

Harvey AI displays intelligent, context-aware status messages during streaming responses. The system automatically detects query intent and shows the most relevant status message to users.

## 📊 Status Message Categories

### 🏆 Dividend Aristocrats/Kings/Champions
- **Queries:** "dividend aristocrats", "dividend kings", "dividend champions"
- **Messages:**
  - "Finding dividend aristocrats..."
  - "Finding dividend kings..."
  - "Finding dividend champions..."

### ⏰ Timing & Calendar
- **Queries:** "ex-dividend", "when pay", "monthly payers", "quarterly"
- **Messages:**
  - "Finding ex-dividend dates..."
  - "Checking payment schedules..."
  - "Finding monthly payers..."
  - "Checking payment frequencies..."

### 🛡️ Dividend Safety & Risk
- **Queries:** "dividend safety", "cut risk", "sustainable", "coverage"
- **Messages:**
  - "Evaluating dividend safety..."
  - "Assessing cut risk..."
  - "Evaluating dividend sustainability..."
  - "Checking coverage ratios..."

### 🤖 Harvey AI & ML Features
- **Queries:** "predict", "forecast", "score", "backtest", "ai", "model"
- **Messages:**
  - "Running ML models..."
  - "Calculating AI scores..."
  - "Generating ratings..."
  - "Running backtests..."
  - "Processing with Harvey AI..."

### 💼 Portfolio & Strategy
- **Queries:** "rebalance", "optimize", "allocation", "diversify", "risk"
- **Messages:**
  - "Balancing portfolio..."
  - "Optimizing allocations..."
  - "Scanning portfolios..."
  - "Assessing diversification..."
  - "Assessing risk levels..."
  - "Analyzing volatility..."
  - "Reviewing positions..."
  - "Reviewing holdings..."

### 🔍 Comparison & Screening
- **Queries:** "compare", "vs", "screen", "filter", "find stocks"
- **Messages:**
  - "Comparing options..."
  - "Comparing alternatives..."
  - "Screening stocks..."
  - "Filtering results..."
  - "Searching for stocks..."
  - "Searching database..."

### 💰 Income Planning
- **Queries:** "income ladder", "monthly income", "passive income", "retirement income"
- **Messages:**
  - "Building income ladder..."
  - "Calculating monthly income..."
  - "Planning passive income..."
  - "Projecting retirement income..."
  - "Calculating income projections..."

### 💵 Valuation & Analysis
- **Queries:** "overvalued", "fair value", "P/E ratio", "intrinsic value"
- **Messages:**
  - "Evaluating valuation..."
  - "Calculating fair value..."
  - "Checking valuation metrics..."
  - "Analyzing price targets..."
  - "Calculating intrinsic value..."

### 📚 Research & Due Diligence
- **Queries:** "research", "due diligence", "deep dive", "analyze"
- **Messages:**
  - "Conducting research..."
  - "Performing due diligence..."
  - "Conducting deep analysis..."
  - "Analyzing data..."
  - "Running analysis..."

### 📈 Performance & Returns
- **Queries:** "performance", "return", "total return", "outperform", "track record"
- **Messages:**
  - "Analyzing performance..."
  - "Calculating returns..."
  - "Calculating total returns..."
  - "Calculating dividend returns..."
  - "Comparing performance..."
  - "Reviewing track record..."

### 🏭 Sectors & Industries
- **Queries:** "energy", "utilities", "healthcare", "technology", "financial"
- **Messages:**
  - "Scanning energy sector..."
  - "Scanning utilities..."
  - "Scanning healthcare sector..."
  - "Scanning tech sector..."
  - "Reviewing financials..."
  - "Scanning consumer sector..."
  - "Scanning sectors..."
  - "Reviewing industries..."
  - "Analyzing sector rotation..."

### 🌍 International & Geography
- **Queries:** "Canadian", "European", "international", "global"
- **Messages:**
  - "Scanning Canadian markets..."
  - "Scanning European markets..."
  - "Scanning global markets..."
  - "Scanning international stocks..."
  - "Scanning international markets..."

### 📊 Growth vs Income
- **Queries:** "growth stock", "dividend growth", "income stock"
- **Messages:**
  - "Analyzing growth stocks..."
  - "Analyzing growth potential..."
  - "Analyzing dividend growth..."
  - "Calculating growth rates..."
  - "Finding income stocks..."

### 📉 Specific Financial Metrics
- **Queries:** "payout ratio", "yield", "earnings", "revenue", "debt", "cash flow"
- **Messages:**
  - "Evaluating payout ratios..."
  - "Checking yields..."
  - "Checking distributions..."
  - "Calculating dividends..."
  - "Checking earnings..."
  - "Analyzing revenue..."
  - "Analyzing debt levels..."
  - "Checking cash flows..."
  - "Analyzing dividend reinvestment..." (DRIP)

### 📉 Market Conditions
- **Queries:** "bear market", "recession", "inflation", "interest rate", "fed"
- **Messages:**
  - "Analyzing market conditions..."
  - "Assessing recession impact..."
  - "Analyzing inflation effects..."
  - "Checking rate environment..."
  - "Analyzing Fed policy..."
  - "Analyzing markets..."

### 🏢 Asset Types
- **Queries:** "REIT", "MLP", "ETF", "mutual fund", "bond", "stock"
- **Messages:**
  - "Analyzing REITs..."
  - "Analyzing MLPs..."
  - "Reviewing ETFs..."
  - "Reviewing mutual funds..."
  - "Analyzing bonds..."
  - "Analyzing stocks..."
  - "Analyzing equities..."

### 📅 Data Operations
- **Queries:** "historical", "trending", "popular", "aggregate"
- **Messages:**
  - "Searching historical data..."
  - "Finding trending stocks..."
  - "Finding popular picks..."
  - "Aggregating sources..."
  - "Enriching with AI..."

### 📋 Lists & Categories
- **Queries:** "list", "category", "top", "best", "highest", "lowest"
- **Messages:**
  - "Building dividend lists..."
  - "Finding categories..."
  - "Finding top performers..."
  - "Finding best options..."
  - "Identifying weak performers..."
  - "Finding highest yielders..."
  - "Finding lowest volatility..."

### 💸 Tax Considerations
- **Queries:** "tax", "qualified dividend", "ROTH", "IRA", "taxable"
- **Messages:**
  - "Analyzing tax implications..."
  - "Checking dividend qualifications..."
  - "Checking tax treatment..."
  - "Analyzing tax strategies..."
  - "Analyzing retirement accounts..."
  - "Analyzing tax impact..."

### 🎯 Ticker-Specific Messages
- **Pattern:** `$TICKER` or `#TICKER`
- **Messages:**
  - "Pulling AAPL fundamentals..." (default)
  - "Checking MSFT distributions..." (if query mentions "distributions")
  - "Finding ex-dividend dates..." (if query mentions "ex-dividend")
  - "Evaluating dividend safety..." (if query mentions "safety", "cut", "suspend")

### ⚡ Quick Actions
- **Queries:** "show", "get", "what", "how", "when", "why", "explain"
- **Messages:**
  - "Retrieving data..."
  - "Fetching information..."
  - "Processing query..."
  - "Analyzing question..."
  - "Checking dates..."
  - "Investigating reasoning..."
  - "Preparing explanation..."

### 🤔 Default Fallback
- **Query:** Any unmatched query
- **Message:** "Harvey is thinking..."

## 🎯 Smart Detection Examples

| User Query | Detected Status Message |
|------------|------------------------|
| "What are the top dividend aristocrats?" | Finding dividend aristocrats... |
| "Analyze $AAPL fundamentals" | Pulling AAPL fundamentals... |
| "Check $MSFT distributions" | Checking MSFT distributions... |
| "Predict JNJ dividend growth" | Running ML models... |
| "Rebalance my portfolio" | Balancing portfolio... |
| "Build an income ladder" | Building income ladder... |
| "Is T dividend safe?" | Evaluating dividend safety... |
| "Screen for high yield" | Screening stocks... |
| "Canadian dividend stocks" | Scanning Canadian markets... |
| "Recession-proof dividends" | Assessing recession impact... |
| "Explain payout ratios" | Preparing explanation... |
| "Hello Harvey" | Harvey is thinking... |

## 🔧 Technical Details

### Priority System
Status messages are matched using **longest-first** matching to ensure specific phrases match before general terms:

```python
# Example priority:
"dividend aristocrat" (18 chars) → matches first
"aristocrat" (10 chars) → matches second
"dividend" (8 chars) → matches last
```

This ensures "dividend aristocrats" triggers "Finding dividend aristocrats..." instead of "Calculating dividends...".

### Ticker Detection
Ticker patterns (`$TICKER` or `#TICKER`) are detected first, before keyword matching:
- `$AAPL fundamentals` → "Pulling AAPL fundamentals..."
- `#MSFT distributions` → "Checking MSFT distributions..."
- `Is $T safe?` → "Evaluating dividend safety..."

### Performance
- Detection time: < 1ms
- Zero overhead on streaming
- Status message sent first in SSE stream

## 📝 Adding New Status Messages

To add new status messages, edit `app/helpers/status_message_detector.py`:

```python
STATUS_MAPPINGS = {
    # Add more specific phrases first
    "your specific phrase": "Your status message...",
    # General terms later
    "general term": "General message...",
}
```

**Best Practices:**
- Put longer, more specific phrases first in the dictionary
- Use action-oriented language ("Analyzing...", "Calculating...", "Finding...")
- Keep messages concise (2-4 words + ellipsis)
- Avoid emojis (professional, clean look)
- Test with real user queries

## 🚀 Total Status Messages

**130+ unique status messages** covering:
- ✅ All dividend-related queries
- ✅ Portfolio and strategy planning
- ✅ Market analysis and sectors
- ✅ ML/AI features
- ✅ Tax and income planning
- ✅ International markets
- ✅ Ticker-specific analysis
- ✅ And much more!

---

**Last Updated:** November 16, 2025  
**Feature Version:** 2.0  
**Status:** Production Ready
