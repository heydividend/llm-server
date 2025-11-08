# Harvey Agentic RAG Enrichment System Documentation

## Overview
The Harvey RAG (Retrieval-Augmented Generation) Enrichment System is an intelligent multi-source data orchestration platform that enhances dividend analysis through parallel data retrieval, intelligent reranking, and self-evaluation loops.

## Architecture

### Core Components

1. **Query Analyzer**
   - Parses user intent (buy/sell/analyze/screen)
   - Extracts stock tickers automatically
   - Rewrites queries for optimal retrieval
   - Determines required data sources
   - Calculates query confidence score

2. **Multi-Source Retrieval Orchestrator**
   - **Azure SQL Database**: ML predictions, dividend history, payout ratings
   - **Yahoo Finance API**: Real-time prices, yields, P/E ratios (FREE)
   - **Massive.com API**: Social sentiment, trending metrics (requires API key)
   - **Dividend Intelligence**: Daily news scans and alerts
   - Executes all queries in parallel for optimal performance

3. **Intelligent Reranker**
   - Scores results based on multiple factors:
     - Safety rating (40% weight for buy recommendations)
     - Dividend yield (25% weight)
     - Market sentiment (15% weight)
     - Value metrics (10% weight)
     - Price momentum (10% weight)
   - Adjusts weights based on query intent

4. **Compliance Manager**
   - Automatically inserts disclaimers for buy/sell recommendations
   - Tracks data sources for transparency
   - Ensures regulatory compliance
   - Maintains audit trail

5. **Self-Evaluation Loop**
   - Validates data freshness (<24 hours)
   - Checks response completeness
   - Ensures disclaimer presence when required
   - Retries with modified strategy if confidence is low
   - Maximum 2 retry attempts

## Deployment Details

### Service Configuration
- **Port**: 8002 (internal only)
- **Workers**: 2
- **Service**: `harvey-rag.service` (systemd)
- **Auto-restart**: Enabled
- **Location**: `/home/azureuser/harvey/harvey_rag_enrichment_system.py`

### API Endpoints

#### 1. Health Check
```
GET /health
Response: {"status": "healthy", "service": "Harvey RAG Enrichment System"}
```

#### 2. Analyze Query (Main Endpoint)
```
POST /v1/rag/analyze
Headers: X-API-Key: {HARVEY_AI_API_KEY}
Body: {
    "query": "What dividend stocks should I buy?",
    "include_raw_data": false
}
Response: {
    "success": true,
    "recommendation": "...",
    "confidence": 0.85,
    "data_sources": ["Harvey ML Models", "Yahoo Finance"],
    "disclaimer": "..."
}
```

#### 3. Cache Statistics
```
GET /v1/rag/cache-stats
Headers: X-API-Key: {HARVEY_AI_API_KEY}
Response: {
    "yahoo_cache_size": 10,
    "massive_cache_size": 5,
    "cache_ttl": {...}
}
```

## Data Flow Example

```
User Query: "Best high-yield dividend stocks to buy"
    ↓
[Query Analysis]
  • Intent: BUY_RECOMMENDATION
  • Tickers: [] (screening query)
  • Sources: [database, yahoo, massive, ml_service]
  • Confidence: 0.75
    ↓
[Parallel Retrieval]
  ├── Database: Top A+ rated stocks
  ├── Yahoo: Real-time yields & prices
  ├── Massive: Sentiment scores
  └── ML Service: Payout predictions
    ↓
[Data Fusion & Normalization]
  • Merge by ticker symbol
  • Calculate composite scores
  • Track data provenance
    ↓
[Intelligent Reranking]
  • Apply intent-specific weights
  • Score: Safety(40%) + Yield(25%) + Sentiment(15%)
  • Sort by total score
    ↓
[Compliance Check]
  • Add BUY disclaimer
  • Include source attribution
  • Timestamp response
    ↓
[Self-Evaluation]
  • Data fresh? ✓
  • Disclaimer present? ✓
  • Confidence > 0.6? ✓
    ↓
[Return Response]
```

## Integration with Harvey API

### Usage in Harvey Chat
```python
from app.services.rag_integration import rag_service

# In your chat handler
async def enhance_response_with_rag(query: str):
    # Set API key
    rag_service.set_api_key(os.getenv('HARVEY_AI_API_KEY'))
    
    # Get enhanced analysis
    rag_result = await rag_service.analyze_query(query)
    
    if rag_result.get('success'):
        # Use the recommendation in response
        return rag_result['recommendation']
    else:
        # Fallback to standard response
        return generate_standard_response(query)
```

## Configuration & Environment Variables

### Required
- `SQLSERVER_HOST`: Azure SQL Server hostname
- `SQLSERVER_DB`: Database name
- `SQLSERVER_USER`: Database username
- `SQLSERVER_PASSWORD`: Database password
- `HARVEY_AI_API_KEY`: API key for authentication

### Optional
- `MASSIVE_API_KEY`: For Massive.com sentiment analysis
- `OPENAI_API_KEY`: For enhanced query rewriting (future)

## Cache Configuration

| Data Type | TTL (seconds) | Purpose |
|-----------|---------------|---------|
| Quotes | 60 | Real-time price data |
| Sentiment | 300 | Social sentiment scores |
| ML Ratings | 3600 | Daily ML predictions |
| Dividends | 1800 | Dividend payment data |

## Performance Metrics

- **Latency**: 2-5 seconds average (with caching)
- **Parallel Processing**: All data sources queried simultaneously
- **Retry Logic**: Max 2 retries with strategy modification
- **Cache Hit Rate**: ~60% after warm-up

## Monitoring & Debugging

### Check Service Status
```bash
sudo systemctl status harvey-rag
```

### View Logs
```bash
sudo journalctl -u harvey-rag -f
```

### Test Endpoints
```bash
# Health check
curl http://127.0.0.1:8002/health

# Test analysis (requires API key)
curl -X POST http://127.0.0.1:8002/v1/rag/analyze \
  -H "X-API-Key: $HARVEY_AI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "analyze AAPL dividend"}'
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Verify Azure SQL credentials in environment
   - Check firewall rules allow VM IP
   - Ensure database tables exist

2. **Yahoo Finance No Data**
   - Markets may be closed
   - Ticker symbol may be invalid
   - Rate limiting (use cache)

3. **Low Confidence Scores**
   - Add more specific keywords to query
   - Ensure ML models are up-to-date
   - Check data source availability

4. **Service Won't Start**
   - Check port 8002 is available
   - Verify Python dependencies installed
   - Check systemd logs for errors

## Future Enhancements

1. **Redis Integration**: External cache for distributed scaling
2. **WebSocket Support**: Real-time streaming responses
3. **Query History**: Learn from user preferences
4. **A/B Testing**: Compare different ranking strategies
5. **Custom Embeddings**: Semantic search improvements
6. **Multi-language Support**: International markets

## Security Considerations

1. **API Key Required**: All endpoints except health check
2. **Internal Only**: Service binds to 127.0.0.1
3. **Data Sanitization**: All inputs validated
4. **Rate Limiting**: Built-in protection
5. **Audit Logging**: All requests logged

## Compliance Features

1. **Automatic Disclaimers**: Added to all buy/sell recommendations
2. **Source Attribution**: Transparent data provenance
3. **Data Freshness**: Timestamps on all responses
4. **Audit Trail**: Request/response logging
5. **Risk Grading**: Different disclaimer levels

## Example Responses

### Buy Recommendation
```markdown
📈 **BUY RECOMMENDATIONS**

Based on comprehensive analysis of safety ratings, yields, and market sentiment:

**1. JNJ** (Score: 0.92/1.00)
   • Safety Rating: A+
   • Current Price: $155.32
   • Dividend Yield: 3.15%
   • Market Sentiment: Positive
   ✓ Strong dividend safety with attractive yield

**Data Sources:** Harvey ML Models, Yahoo Finance, Massive.com
**Analysis Date:** 2025-11-08 13:30 UTC

---
*INVESTMENT DISCLAIMER: This analysis is for educational purposes only...*
```

## Maintenance

### Daily Tasks
- Monitor service health
- Check cache hit rates
- Review error logs

### Weekly Tasks
- Clear old cache entries
- Update ML model connections
- Review API usage metrics

### Monthly Tasks
- Performance optimization review
- Update ticker mappings
- Audit compliance logs

## Contact & Support

For issues or questions about the RAG Enrichment System:
- Check logs: `sudo journalctl -u harvey-rag -f`
- Service location: `/home/azureuser/harvey/`
- Configuration: `/etc/systemd/system/harvey-rag.service`

---

*Last Updated: November 8, 2025*
*Version: 1.0.0*