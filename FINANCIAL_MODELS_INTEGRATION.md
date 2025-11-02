# Financial Models Integration Guide

How to integrate Harvey's Portfolio and Watchlist Projection Engine into the backend.

## Quick Start

### 1. Add to Harvey Backend (main.py)

```python
from financial_models.api.endpoints import router as financial_router

# Add after existing routers
app.include_router(financial_router)
```

### 2. Environment Variables

Ensure `.env` has:
```bash
INTERNAL_ML_API_KEY=your_internal_api_key_here
SQLSERVER_HOST=your-server.database.windows.net
SQLSERVER_DB=HeyDividend-Main-DB
SQLSERVER_USER=your-user
SQLSERVER_PASSWORD=your-password
```

### 3. Install Dependencies

```bash
pip install pymssql
```

## Available Endpoints

All endpoints require `X-Internal-API-Key` header for authentication.

### Portfolio Projection
**POST** `/api/financial/portfolio/projection`

Projects dividend income over 1/3/5/10 years using historical growth rates.

```json
{
  "user_id": "optional_user_id",
  "years": 10
}
```

**Use Case**: "Show me my projected dividend income over the next 10 years"

---

### Watchlist Analysis
**POST** `/api/financial/watchlist/analyze`

Analyzes watchlist stocks and shows potential income with given investment.

```json
{
  "user_id": "optional_user_id",
  "investment_amount": 10000
}
```

**Use Case**: "If I invest $10,000 in my watchlist, how much income would I generate?"

---

### Optimal Allocation
**POST** `/api/financial/watchlist/optimal-allocation`

Calculates optimal stock allocation to achieve target monthly income.

```json
{
  "user_id": "optional_user_id",
  "target_monthly_income": 1000,
  "total_capital": 100000
}
```

**Use Case**: "I want $1,000/month in dividends. How should I allocate $100,000?"

---

### Stock Sustainability
**POST** `/api/financial/sustainability/stock`

Analyzes dividend sustainability for a single stock (A-F grade).

```json
{
  "ticker": "AAPL"
}
```

**Use Case**: "How sustainable is Apple's dividend?"

---

### Portfolio Sustainability
**POST** `/api/financial/sustainability/portfolio`

Analyzes dividend sustainability of entire portfolio.

```json
{
  "user_id": "optional_user_id"
}
```

**Use Case**: "Rate my portfolio's dividend sustainability"

---

### Cash Flow Sensitivity
**POST** `/api/financial/cashflow/sensitivity`

Stress tests portfolio with dividend cut scenarios.

```json
{
  "user_id": "optional_user_id",
  "custom_scenarios": null
}
```

**Use Case**: "How would my income change if dividends were cut 20%?"

---

## Integration with Harvey's LLM

### Hybrid Approach

Financial models provide **computed data** → Harvey's LLM interprets for users

Example flow:
1. User asks: "How much income will I generate in 5 years?"
2. Harvey calls `/api/financial/portfolio/projection`
3. Financial engine computes: `$45,234 annual income in year 5`
4. Harvey's LLM responds: "Based on your current holdings and historical growth rates, you'll generate approximately $45,200 in annual dividend income by 2030. That's $3,770 per month - enough to cover your grocery budget with room to spare! 🎯"

### Integration Pattern

```python
# In Harvey's query handler
async def handle_portfolio_projection_query(user_id: str):
    # Call financial model
    response = await financial_api_client.post(
        "/api/financial/portfolio/projection",
        json={"user_id": user_id, "years": 10},
        headers={"X-Internal-API-Key": INTERNAL_ML_API_KEY}
    )
    
    projections = response.json()
    
    # Pass to LLM for interpretation
    llm_context = f"""
    User's portfolio analysis:
    - Current income: ${projections['current_annual_income']}/year
    - 5-year projection: ${projections['projections'][5]['annual_income']}/year
    - 10-year projection: ${projections['projections'][10]['annual_income']}/year
    - Growth rate: {projections['growth_assumptions']['avg_growth_rate_pct']}%
    
    Interpret these results in a helpful, conversational way for the user.
    """
    
    return await llm_chat(llm_context, user_query)
```

## Query Classification

Add to Harvey's query classifier:

```python
FINANCIAL_MODEL_KEYWORDS = [
    "portfolio projection", "project income", "future dividend",
    "watchlist analysis", "what if invest", "income potential",
    "dividend sustainability", "cut risk", "safe dividend",
    "stress test", "sensitivity", "dividend cut scenario"
]

def classify_query(query: str):
    query_lower = query.lower()
    
    if any(kw in query_lower for kw in FINANCIAL_MODEL_KEYWORDS):
        return "financial_model"
    # ... existing classification logic
```

## Example Responses

### Portfolio Projection
**User**: "How much dividend income will I make in 10 years?"

**Harvey**: 
> Based on your current portfolio and historical dividend growth rates, here's your income projection:
> 
> **Current Income**: $12,450/year ($1,038/month)
> 
> **10-Year Projection**: $24,789/year ($2,066/month)
> 
> This assumes an average dividend growth rate of 7.2% per year based on your holdings' historical performance. Your top income generators are JNJ, PG, and KO, which have shown consistent dividend growth over the past decade.

### Watchlist Analysis
**User**: "If I invest $50,000 in my watchlist, how much income would I get?"

**Harvey**:
> If you invested $50,000 in your watchlist stocks, here's what you could generate:
> 
> **Projected Annual Income**: $2,340 ($195/month)
> **Average Portfolio Yield**: 4.68%
> 
> **Top Picks** (highest sustainability):
> 1. JNJ - 15% allocation, $585/year, Grade A
> 2. PG - 15% allocation, $468/year, Grade A
> 3. KO - 12% allocation, $390/year, Grade B
> 
> This allocation prioritizes dividend sustainability while maintaining sector diversification.

### Sustainability Analysis
**User**: "How safe is Apple's dividend?"

**Harvey**:
> **AAPL Dividend Sustainability: Grade A (87.5/100)**
> 
> ✅ **Payout Ratio**: 15% (Excellent - plenty of room for growth)
> ✅ **Growth Rate**: 8.2% annually over 10 years (Very Good)
> ✅ **Consistency**: 95/100 (Reliable quarterly payments)
> ⚠️ **Cut Risk**: 12.5/100 (Very Low)
> 
> **Recommendation**: Strong Buy - Apple's dividend is highly sustainable with excellent growth potential.

### Cash Flow Sensitivity
**User**: "What if there's a recession and dividends get cut?"

**Harvey**:
> I ran stress tests on your portfolio income. Here's how you'd fare:
> 
> **Mild Recession (10% cut)**: $11,205/year (down $1,245 or 10%)
> **Moderate Recession (20% cut)**: $9,960/year (down $2,490 or 20%)
> **Severe Recession (40% cut)**: $7,470/year (down $4,980 or 40%)
> 
> **Income Stability Score**: 72/100 (Good)
> 
> ⚠️ Your portfolio is 35% concentrated in Technology sector. Consider diversifying to reduce sensitivity to sector-specific downturns.
> 
> 💡 **Recommendation**: Build a cash reserve equal to 6-12 months of dividend income as a safety buffer.

## Testing

```bash
# Test portfolio projection
curl -X POST http://localhost:8000/api/financial/portfolio/projection \
  -H "X-Internal-API-Key: ${INTERNAL_ML_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"years": 10}'

# Expected: JSON with projections for years 1,3,5,10
```

## Performance

- **Latency**: ~200-500ms per endpoint (depends on portfolio size)
- **Database Queries**: 2-5 queries per request
- **Recommended**: Add connection pooling for production traffic

## Security

✅ **Secure**: API key required via environment variable
✅ **Fail-fast**: Startup fails if `INTERNAL_ML_API_KEY` is missing
✅ **No hardcoded secrets**: All credentials from environment

## Next Steps

1. Add financial model router to Harvey backend
2. Update query classifier to route to financial models
3. Test with sample user portfolios
4. Integrate LLM interpretation layer
5. Deploy to production
