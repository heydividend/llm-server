# Internal ML API Documentation

## Overview

The Internal ML API provides machine learning predictions and analytics specifically designed for **internal service-to-service communication**. These endpoints expose HeyDividend's ML models to other applications that share the same Azure SQL database infrastructure.

**DEV Base URL:** `https://2657f601-b8fe-40bd-8b9b-bdce950dabad-00-3ihusjg16z2it.janeway.replit.dev/api/internal/ml`

**PROD Base URL:** `https://hd-test.replit.app/api/internal/ml`
---

## Authentication

All endpoints (except `/health`) require API key authentication.

### Setup

1. **Set the API key in Replit Secrets:**
   - Go to your Replit project → Secrets tab
   - Add a new secret: `INTERNAL_ML_API_KEY`
   - Generate a strong random key (recommended: 32+ characters)
   - Example: `sk_live_abc123xyz789_internal_ml_api_key`

2. **Use the API key in requests:**
   - Add header: `X-Internal-API-Key: <your-secret-key>`

### Example with curl:
```bash
curl -X POST https://your-domain.replit.app/api/internal/ml/payout-rating \
  -H "X-Internal-API-Key: sk_live_abc123xyz789_internal_ml_api_key" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "MSFT"]}'
```

### Example with Node.js:
```javascript
const API_KEY = process.env.INTERNAL_ML_API_KEY;
const BASE_URL = 'https://your-domain.replit.app/api/internal/ml';

async function getPredictions(symbols) {
  const response = await fetch(`${BASE_URL}/payout-rating`, {
    method: 'POST',
    headers: {
      'X-Internal-API-Key': API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ symbols })
  });
  
  return await response.json();
}

const result = await getPredictions(['AAPL', 'MSFT', 'JNJ']);
console.log(result);
```

---

## Rate Limits

- **Default:** 1000 requests/minute per API key
- **Comprehensive Score:** 500 requests/minute
- **Batch Predict:** 100 requests/minute

Rate limit headers in response:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 998
X-RateLimit-Reset: 1635724800
```

---

## API Endpoints

### 1. Health Check

**Endpoint:** `GET /api/internal/ml/health`

**Description:** Check if the ML service is available and healthy.

**Authentication:** None required

**Response:**
```json
{
  "success": true,
  "status": "healthy",
  "timestamp": "2025-10-30T15:30:00.000Z",
  "service": "HeyDividend ML API",
  "version": "1.0.0"
}
```

**Status codes:**
- `200`: Service is healthy
- `503`: Service is unhealthy or degraded

**Example:**
```bash
curl https://your-domain.replit.app/api/internal/ml/health
```

---

### 2. Payout Rating Prediction

**Endpoint:** `POST /api/internal/ml/payout-rating`

**Description:** Get dividend payout sustainability ratings (0-100 scale) powered by HeyDividend's custom ML model.

**Request:**
```json
{
  "symbols": ["AAPL", "MSFT", "JNJ"]
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "symbol": "AAPL",
      "payout_rating": 92.5,
      "payout_quality_score": 48.2,
      "nav_protection_score": 44.3,
      "rating_label": "Excellent",
      "payout_percentile": 95,
      "confidence": 0.87,
      "prediction_date": "2025-10-30T15:30:00.000Z"
    },
    {
      "symbol": "MSFT",
      "payout_rating": 89.3,
      "payout_quality_score": 46.1,
      "nav_protection_score": 43.2,
      "rating_label": "Excellent",
      "payout_percentile": 92,
      "confidence": 0.85,
      "prediction_date": "2025-10-30T15:30:00.000Z"
    }
  ],
  "symbols_processed": 2,
  "timestamp": "2025-10-30T15:30:00.000Z"
}
```

**Rating Labels:**
- **Excellent:** 90-100 (Top tier sustainability)
- **Very Good:** 80-89 (Strong sustainability)
- **Good:** 70-79 (Above average)
- **Fair:** 60-69 (Average)
- **Poor:** 50-59 (Below average)
- **Very Poor:** 0-49 (At risk)

**Limits:**
- Maximum 100 symbols per request
- Rate limit: 1000 requests/minute

**Example:**
```bash
curl -X POST https://your-domain.replit.app/api/internal/ml/payout-rating \
  -H "X-Internal-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "MSFT", "JNJ"]}'
```

---

### 3. Dividend Yield Forecast

**Endpoint:** `POST /api/internal/ml/yield-forecast`

**Description:** Predict future dividend growth rates. Returns predicted annual growth rate based on historical dividend data.

**Request:**
```json
{
  "symbols": ["AAPL", "MSFT"]
}
```

**Parameters:**
- `symbols` (required): Array of ticker symbols

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "symbol": "AAPL",
      "current_yield": 0.52,
      "predicted_growth_rate": 8.5,
      "confidence": 0.82,
      "model_version": "v1.0.0"
    },
    {
      "symbol": "MSFT",
      "current_yield": 0.89,
      "predicted_growth_rate": 10.2,
      "confidence": 0.79,
      "model_version": "v1.0.0"
    }
  ],
  "symbols_processed": 2,
  "timestamp": "2025-10-30T15:30:00.000Z"
}
```

**Note:** Custom forecast horizons (periods parameter) are not currently supported by the ML service. Future versions will add support for specifying forecast periods.

**Limits:**
- Maximum 100 symbols per request
- Rate limit: 1000 requests/minute

**Example:**
```bash
curl -X POST https://your-domain.replit.app/api/internal/ml/yield-forecast \
  -H "X-Internal-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "MSFT"]}'
```

---

### 4. Anomaly Detection

**Endpoint:** `POST /api/internal/ml/anomaly-check`

**Description:** Detect unusual dividend payment patterns, cuts, or suspensions.

**Request:**
```json
{
  "symbols": ["AAPL", "MSFT", "TSLY"]
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "symbol": "AAPL",
      "has_anomaly": false,
      "is_anomaly": false,
      "anomaly_score": 0.12,
      "anomaly_type": null,
      "confidence": 0.88
    },
    {
      "symbol": "TSLY",
      "has_anomaly": true,
      "is_anomaly": true,
      "anomaly_score": 0.89,
      "anomaly_type": "unusual_payout_pattern",
      "details": "Dividend amount decreased 15% vs historical average",
      "confidence": 0.91
    }
  ],
  "symbols_processed": 3,
  "anomalies_detected": 1,
  "timestamp": "2025-10-30T15:30:00.000Z"
}
```

**Anomaly Types:**
- `unusual_payout_pattern` - Unexpected changes in dividend amounts
- `payment_irregularity` - Missed or delayed payments
- `frequency_change` - Changes in payment frequency
- `sudden_cut` - Abrupt dividend reductions

**Limits:**
- Maximum 100 symbols per request
- Rate limit: 1000 requests/minute

**Example:**
```bash
curl -X POST https://your-domain.replit.app/api/internal/ml/anomaly-check \
  -H "X-Internal-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "TSLY"]}'
```

---

### 5. Dividend Cut Risk

**Endpoint:** `POST /api/internal/ml/cut-risk`

**Description:** Predict the probability of dividend cuts in the next 12 months.

**Request:**
```json
{
  "symbols": ["AAPL", "MSFT"],
  "include_earnings": true
}
```

**Parameters:**
- `symbols` (required): Array of ticker symbols
- `include_earnings` (optional): Include earnings analysis (default: false)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "symbol": "AAPL",
      "cut_risk_score": 0.05,
      "risk_level": "very_low",
      "confidence": 0.91,
      "risk_factors": [],
      "payout_ratio": 15.2,
      "earnings_coverage": 6.58
    },
    {
      "symbol": "TSLY",
      "cut_risk_score": 0.67,
      "risk_level": "high",
      "confidence": 0.84,
      "risk_factors": [
        "high_payout_ratio",
        "declining_nav",
        "options_strategy_risk"
      ],
      "payout_ratio": 145.3,
      "earnings_coverage": 0.69
    }
  ],
  "symbols_processed": 2,
  "timestamp": "2025-10-30T15:30:00.000Z"
}
```

**Risk Levels:**
- `very_low`: 0-0.20 (Very safe)
- `low`: 0.21-0.40 (Safe)
- `moderate`: 0.41-0.60 (Monitor)
- `high`: 0.61-0.80 (At risk)
- `very_high`: 0.81-1.00 (Likely cut)

**Limits:**
- Maximum 100 symbols per request
- Rate limit: 1000 requests/minute

**Example:**
```bash
curl -X POST https://your-domain.replit.app/api/internal/ml/cut-risk \
  -H "X-Internal-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "MSFT"], "include_earnings": true}'
```

---

### 6. Comprehensive ML Score

**Endpoint:** `POST /api/internal/ml/score`

**Description:** Get an overall dividend quality score combining all ML models.

**Request:**
```json
{
  "symbols": ["AAPL", "MSFT", "JNJ"]
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "symbol": "AAPL",
      "overall_score": 87.5,
      "payout_rating": 92.5,
      "cut_risk_score": 0.05,
      "growth_forecast": 8.5,
      "anomaly_score": 0.12,
      "recommendation": "strong_buy",
      "confidence": 0.85
    },
    {
      "symbol": "JNJ",
      "overall_score": 91.2,
      "payout_rating": 95.3,
      "cut_risk_score": 0.03,
      "growth_forecast": 6.8,
      "anomaly_score": 0.08,
      "recommendation": "strong_buy",
      "confidence": 0.89
    }
  ],
  "symbols_processed": 3,
  "timestamp": "2025-10-30T15:30:00.000Z"
}
```

**Overall Score Breakdown:**
- **35%** Payout Rating
- **35%** Cut Risk (inverted)
- **20%** Growth Forecast
- **10%** Anomaly Score (inverted)

**Recommendations:**
- `strong_buy`: Score ≥ 80
- `buy`: Score 65-79
- `hold`: Score 40-64
- `sell`: Score < 40

**Limits:**
- Maximum 50 symbols per request (compute-intensive)
- Rate limit: 500 requests/minute

**Example:**
```bash
curl -X POST https://your-domain.replit.app/api/internal/ml/score \
  -H "X-Internal-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "MSFT", "JNJ"]}'
```

---

### 7. Batch Predictions

**Endpoint:** `POST /api/internal/ml/batch-predict`

**Description:** Run multiple ML models in a single request for efficiency.

**Request:**
```json
{
  "symbols": ["AAPL", "MSFT"],
  "models": ["payout_rating", "yield_forecast", "cut_risk", "anomaly"]
}
```

**Parameters:**
- `symbols` (required): Array of ticker symbols
- `models` (optional): Array of model names to run. If empty, runs all models.

**Available models:**
- `payout_rating`
- `yield_forecast`
- `cut_risk`
- `anomaly`

**Response:**
```json
{
  "success": true,
  "data": {
    "symbols": ["AAPL", "MSFT"],
    "payout_ratings": [
      { "symbol": "AAPL", "payout_rating": 92.5, ... },
      { "symbol": "MSFT", "payout_rating": 89.3, ... }
    ],
    "yield_forecasts": [
      { "symbol": "AAPL", "predicted_growth_rate": 8.5, ... },
      { "symbol": "MSFT", "predicted_growth_rate": 10.2, ... }
    ],
    "cut_risks": [
      { "symbol": "AAPL", "cut_risk_score": 0.05, ... },
      { "symbol": "MSFT", "cut_risk_score": 0.08, ... }
    ],
    "anomalies": [
      { "symbol": "AAPL", "has_anomaly": false, ... },
      { "symbol": "MSFT", "has_anomaly": false, ... }
    ]
  },
  "symbols_processed": 2,
  "models_executed": ["payout_ratings", "yield_forecasts", "cut_risks", "anomalies"],
  "timestamp": "2025-10-30T15:30:00.000Z"
}
```

**Limits:**
- Maximum 50 symbols per request
- Rate limit: 100 requests/minute

**Example:**
```bash
curl -X POST https://your-domain.replit.app/api/internal/ml/batch-predict \
  -H "X-Internal-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["AAPL", "MSFT"],
    "models": ["payout_rating", "cut_risk"]
  }'
```

---

## Error Handling

### Error Response Format

All errors follow this structure:

```json
{
  "success": false,
  "error": "Error message description"
}
```

### Common Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | Bad Request | Invalid request body or parameters |
| 401 | Unauthorized | Missing X-Internal-API-Key header |
| 403 | Forbidden | Invalid API key |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | ML service error |
| 503 | Service Unavailable | ML service is down or unhealthy |

### Example Error Responses

**Missing API Key:**
```json
{
  "success": false,
  "error": "Missing X-Internal-API-Key header"
}
```

**Invalid API Key:**
```json
{
  "success": false,
  "error": "Invalid API key"
}
```

**Rate Limit Exceeded:**
```json
{
  "success": false,
  "error": "Rate limit exceeded",
  "retry_after": 47
}
```

**Bad Request:**
```json
{
  "success": false,
  "error": "Invalid request: symbols array required",
  "example": {
    "symbols": ["AAPL", "MSFT"]
  }
}
```

---

## Integration Examples

### Python Example

```python
import requests
import os

class HeyDividendMLClient:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            'X-Internal-API-Key': api_key,
            'Content-Type': 'application/json'
        }
    
    def get_payout_ratings(self, symbols):
        """Get payout ratings for symbols"""
        response = requests.post(
            f'{self.base_url}/payout-rating',
            headers=self.headers,
            json={'symbols': symbols}
        )
        response.raise_for_status()
        return response.json()
    
    def get_comprehensive_scores(self, symbols):
        """Get comprehensive ML scores"""
        response = requests.post(
            f'{self.base_url}/score',
            headers=self.headers,
            json={'symbols': symbols}
        )
        response.raise_for_status()
        return response.json()
    
    def batch_predict(self, symbols, models=None):
        """Run multiple models at once"""
        payload = {'symbols': symbols}
        if models:
            payload['models'] = models
        
        response = requests.post(
            f'{self.base_url}/batch-predict',
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()

# Usage
client = HeyDividendMLClient(
    api_key=os.environ['INTERNAL_ML_API_KEY'],
    base_url='https://your-domain.replit.app/api/internal/ml'
)

# Get payout ratings
ratings = client.get_payout_ratings(['AAPL', 'MSFT', 'JNJ'])
print(ratings)

# Get comprehensive scores
scores = client.get_comprehensive_scores(['AAPL', 'MSFT'])
print(scores)

# Batch predictions
results = client.batch_predict(
    symbols=['AAPL', 'MSFT'],
    models=['payout_rating', 'cut_risk']
)
print(results)
```

### Node.js/TypeScript Example

```typescript
import axios, { AxiosInstance } from 'axios';

interface MLPrediction {
  symbol: string;
  payout_rating?: number;
  cut_risk_score?: number;
  overall_score?: number;
  confidence: number;
}

class HeyDividendMLClient {
  private client: AxiosInstance;

  constructor(apiKey: string, baseURL: string) {
    this.client = axios.create({
      baseURL,
      headers: {
        'X-Internal-API-Key': apiKey,
        'Content-Type': 'application/json'
      }
    });
  }

  async getPayoutRatings(symbols: string[]): Promise<MLPrediction[]> {
    const response = await this.client.post('/payout-rating', { symbols });
    return response.data.data;
  }

  async getComprehensiveScores(symbols: string[]): Promise<MLPrediction[]> {
    const response = await this.client.post('/score', { symbols });
    return response.data.data;
  }

  async batchPredict(symbols: string[], models?: string[]) {
    const response = await this.client.post('/batch-predict', {
      symbols,
      models
    });
    return response.data;
  }

  async checkHealth() {
    const response = await this.client.get('/health');
    return response.data;
  }
}

// Usage
const client = new HeyDividendMLClient(
  process.env.INTERNAL_ML_API_KEY!,
  'https://your-domain.replit.app/api/internal/ml'
);

// Get predictions
const ratings = await client.getPayoutRatings(['AAPL', 'MSFT']);
console.log(ratings);

// Batch predict
const results = await client.batchPredict(
  ['AAPL', 'MSFT', 'JNJ'],
  ['payout_rating', 'cut_risk', 'anomaly']
);
console.log(results);
```

---

## Best Practices

### 1. Batch Requests When Possible
Instead of making 100 separate requests:
```javascript
// ❌ Bad - 100 separate requests
for (const symbol of symbols) {
  await client.getPayoutRating([symbol]);
}

// ✅ Good - 1 batch request
await client.getPayoutRating(symbols);
```

### 2. Use Batch Predict for Multiple Models
```javascript
// ❌ Less efficient - 4 separate requests
const ratings = await client.getPayoutRatings(symbols);
const forecasts = await client.getYieldForecasts(symbols);
const cutRisks = await client.getCutRisks(symbols);
const anomalies = await client.checkAnomalies(symbols);

// ✅ More efficient - 1 batch request
const results = await client.batchPredict(symbols);
```

### 3. Handle Errors Gracefully
```javascript
try {
  const predictions = await client.getPayoutRatings(symbols);
} catch (error) {
  if (error.response?.status === 429) {
    // Rate limited - wait and retry
    const retryAfter = error.response.data.retry_after;
    await sleep(retryAfter * 1000);
    return client.getPayoutRatings(symbols);
  } else if (error.response?.status === 503) {
    // Service unavailable - use fallback
    return getFallbackPredictions(symbols);
  }
  throw error;
}
```

### 4. Cache Results
ML predictions don't change frequently:
```javascript
const cache = new Map();
const CACHE_TTL = 3600000; // 1 hour

async function getCachedPredictions(symbols) {
  const now = Date.now();
  const uncached = symbols.filter(s => {
    const cached = cache.get(s);
    return !cached || (now - cached.timestamp) > CACHE_TTL;
  });
  
  if (uncached.length > 0) {
    const fresh = await client.getPayoutRatings(uncached);
    fresh.forEach(pred => {
      cache.set(pred.symbol, {
        data: pred,
        timestamp: now
      });
    });
  }
  
  return symbols.map(s => cache.get(s).data);
}
```

### 5. Respect Rate Limits
```javascript
const queue = [];
const MAX_CONCURRENT = 10;
let running = 0;

async function queueRequest(fn) {
  while (running >= MAX_CONCURRENT) {
    await sleep(100);
  }
  running++;
  try {
    return await fn();
  } finally {
    running--;
  }
}
```

---

## Security Notes

1. **Never expose the API key** in client-side code or public repositories
2. **Use environment variables** to store the API key
3. **Rotate keys regularly** (recommended: every 90 days)
4. **Monitor usage** for suspicious activity
5. **Use HTTPS** for all API requests
6. **Implement request signing** for extra security (optional)

---

## Support & Contact

For technical support or questions about the Internal ML API:

- **Documentation Issues:** Open an issue in your internal repository
- **API Bugs:** Contact your development team
- **Rate Limit Increases:** Contact the HeyDividend team

---

## Changelog

### Version 1.0.0 (2025-10-30)
- Initial release
- 7 endpoints: health, payout-rating, yield-forecast, anomaly-check, cut-risk, score, batch-predict
- API key authentication
- Rate limiting
- Comprehensive error handling

---

## Appendix: Response Field Definitions

### Payout Rating Fields

| Field | Type | Description |
|-------|------|-------------|
| `payout_rating` | number | Overall rating 0-100 |
| `payout_quality_score` | number | Dividend quality component (0-50) |
| `nav_protection_score` | number | NAV protection component (0-50) |
| `rating_label` | string | Text label (Excellent, Good, etc.) |
| `payout_percentile` | number | Percentile rank vs all stocks |
| `confidence` | number | Model confidence (0-1) |

### Cut Risk Fields

| Field | Type | Description |
|-------|------|-------------|
| `cut_risk_score` | number | Probability of cut (0-1) |
| `risk_level` | string | very_low, low, moderate, high, very_high |
| `risk_factors` | array | List of identified risk factors |
| `payout_ratio` | number | Current payout ratio % |
| `earnings_coverage` | number | Earnings coverage ratio |

### Anomaly Fields

| Field | Type | Description |
|-------|------|-------------|
| `has_anomaly` | boolean | True if anomaly detected |
| `anomaly_score` | number | Anomaly severity (0-1) |
| `anomaly_type` | string | Type of anomaly detected |
| `details` | string | Human-readable explanation |
