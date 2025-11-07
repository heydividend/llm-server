# ML Integration Documentation for Harvey

## Overview
Harvey integrates with ML prediction services to provide enhanced dividend insights through scheduled ML models that run on Azure VM. This document explains how ML predictions are integrated into chat responses.

## Architecture

```
User Query → Harvey API → ML Integration Service → ML Scheduler Endpoints → Azure ML Models
                ↓
         Enhanced Response with ML Insights
```

## ML Scheduler Integration

### 1. Payout Rating Predictions
**Schedule:** Daily at 1:00 AM UTC  
**Purpose:** Generates A+/A/B/C dividend safety ratings  

#### Usage in Chat Responses:
```python
# When user asks about dividend safety/sustainability
from app.services.ml_integration import get_ml_integration

ml_integration = get_ml_integration()
ratings = await ml_integration.get_scheduled_payout_ratings(
    symbols=["AAPL", "JNJ", "KO"],
    force_refresh=False  # Uses cached daily predictions
)
```

**Response Enhancement Example:**
```
User: "Is Apple's dividend safe?"

Harvey: "Based on my analysis, Apple (AAPL) has strong dividend sustainability...

🤖 ML-Powered Dividend Safety Rating:
AAPL: A+ (95% confidence)
Analysis: Strong payout ratio of 15%, consistent free cash flow generation, 
and robust earnings growth support dividend sustainability.
```

### 2. Dividend Calendar Predictions  
**Schedule:** Sunday at 2:00 AM UTC  
**Purpose:** Predicts next dividend payment dates and amounts

#### Usage in Chat Responses:
```python
# When user asks about upcoming dividends
calendar = await ml_integration.get_dividend_calendar_predictions(
    symbols=["MSFT", "T", "VZ"],
    months_ahead=6
)
```

**Response Enhancement Example:**
```
User: "When will Microsoft pay its next dividend?"

Harvey: "Microsoft typically pays quarterly dividends...

📅 ML-Predicted Dividend Dates:
MSFT:
• Next Ex-Date: February 15, 2025
• Payment Date: March 14, 2025  
• Estimated Amount: $0.75
• Confidence: 92%
```

### 3. ML Training Status
**Schedule:** Sunday at 3:00 AM UTC  
**Purpose:** Retrains all 5 ML models (dividend predictions, payout ratings, yield forecasting, growth analysis, cut risk)

#### Usage for System Health:
```python
# Check ML model training status
training_status = await ml_integration.get_ml_training_status()
```

## Integration Points in Harvey's Chat

### 1. AI Controller Enhancement (`app/controllers/ai_controller.py`)

The AI controller automatically enhances responses with ML predictions when relevant:

```python
async def chat_completions(request: Request):
    # Process base chat response
    base_response = await process_chat(user_message)
    
    # Enhance with ML predictions if dividend-related
    if contains_dividend_keywords(user_message):
        ml_integration = get_ml_integration()
        
        # Extract tickers from conversation
        tickers = extract_tickers(user_message)
        
        # Get ML predictions
        if "safety" in user_message or "rating" in user_message:
            ratings = await ml_integration.get_scheduled_payout_ratings(tickers)
            base_response = enhance_with_ratings(base_response, ratings)
            
        if "when" in user_message or "calendar" in user_message:
            calendar = await ml_integration.get_dividend_calendar_predictions(tickers)
            base_response = enhance_with_calendar(base_response, calendar)
    
    return base_response
```

### 2. Comprehensive ML Intelligence

For detailed stock analysis, Harvey combines multiple ML predictions:

```python
# Get comprehensive ML intelligence for a stock
intelligence = await ml_integration.get_dividend_intelligence("JNJ")

# Returns:
{
    "symbol": "JNJ",
    "ml_available": true,
    "score": {
        "score": 92,
        "grade": "A+",
        "factors": {...}
    },
    "predictions": {
        "growth_rate": 5.2,
        "yield_12m": 2.8
    },
    "cluster_info": {
        "cluster": "Healthcare Dividend Aristocrats",
        "characteristics": {...}
    },
    "similar_stocks": ["PFE", "MRK", "ABT"],
    "insights": {...}
}
```

## ML-Enhanced Response Patterns

### Pattern 1: Dividend Safety Analysis
**Trigger Keywords:** safety, sustainable, cut, risk, secure  
**ML Enhancement:** Payout ratings, sustainability scores  

### Pattern 2: Payment Predictions  
**Trigger Keywords:** when, next, calendar, schedule, upcoming  
**ML Enhancement:** Dividend calendar predictions  

### Pattern 3: Portfolio Optimization
**Trigger Keywords:** optimize, improve, rebalance, diversify  
**ML Enhancement:** Portfolio scoring, cluster analysis, optimization suggestions  

### Pattern 4: Similar Stock Discovery
**Trigger Keywords:** like, similar, alternative, compare  
**ML Enhancement:** ML clustering, similarity scoring  

## Performance Optimization

### Caching Strategy
- Payout ratings: Cached for 24 hours (refreshed daily at 1 AM)
- Calendar predictions: Cached for 7 days (refreshed Sundays at 2 AM)  
- Training status: Real-time queries

### Concurrent API Calls
The ML integration service uses `asyncio.gather()` for parallel API calls:
- **Before:** 6-12 seconds (sequential)
- **After:** 2-3 seconds (concurrent)

## Testing ML Endpoints

### Test Script Location
`~/workspace/test_ml_endpoints.py`

### Quick Test Commands:
```bash
# Test health endpoint
curl http://20.81.210.213:8001/v1/ml-schedulers/health \
  -H "Authorization: Bearer hh_live_X6SPcjPD5jZhTMw69_internal_api_key"

# Test payout ratings  
curl -X POST http://20.81.210.213:8001/v1/ml-schedulers/payout-ratings \
  -H "Authorization: Bearer hh_live_X6SPcjPD5jZhTMw69_internal_api_key" \
  -H "Content-Type: application/json" \
  -d '["AAPL", "JNJ", "KO"]'

# Test dividend calendar
curl -X POST http://20.81.210.213:8001/v1/ml-schedulers/dividend-calendar \
  -H "Authorization: Bearer hh_live_X6SPcjPD5jZhTMw69_internal_api_key" \
  -H "Content-Type: application/json" \
  -d '["MSFT", "T"]'
```

## Admin Dashboard

### Access Methods:

1. **Browser URL:**
   ```
   http://20.81.210.213:8001/v1/ml-schedulers/admin/dashboard?api_key=hh_live_X6SPcjPD5jZhTMw69_internal_api_key
   ```

2. **Command Line:**
   ```bash
   curl http://20.81.210.213:8001/v1/ml-schedulers/admin/dashboard \
     -H "Authorization: Bearer hh_live_X6SPcjPD5jZhTMw69_internal_api_key" | python -m json.tool
   ```

### Dashboard Metrics:
- Total scheduler runs
- Success/failure rates
- Average processing times
- Recent execution logs
- Model performance metrics

## Configuration

### Environment Variables
```bash
# Harvey API authentication
HARVEY_AI_API_KEY=hh_live_X6SPcjPD5jZhTMw69_internal_api_key

# ML Service endpoint  
ML_API_BASE_URL=http://20.81.210.213:9000

# Internal ML API key
INTERNAL_ML_API_KEY=<ml_service_key>
```

### ML Service Endpoints
- **Harvey API:** `http://20.81.210.213:8001/v1/`
- **ML Service:** `http://20.81.210.213:9000/`
- **ML Schedulers:** `http://20.81.210.213:8001/v1/ml-schedulers/`

## Error Handling

The ML integration includes comprehensive fallbacks:
1. If ML service unavailable → Returns base response without ML enhancements
2. If specific model fails → Uses other available models
3. If all ML fails → Provides standard financial analysis

## Future Enhancements

1. **Real-time ML Updates:** WebSocket connections for live predictions
2. **Custom Model Training:** User-specific model fine-tuning
3. **Advanced Portfolio AI:** Multi-objective optimization
4. **Sentiment Integration:** News/social sentiment in ratings
5. **Risk Forecasting:** Dividend cut probability models

## Support

For issues with ML integration:
1. Check ML service health: `/v1/ml-schedulers/health`
2. Review training status: `/v1/ml-schedulers/training-status`
3. Access admin dashboard for detailed logs
4. Contact Azure VM administrator for service restarts