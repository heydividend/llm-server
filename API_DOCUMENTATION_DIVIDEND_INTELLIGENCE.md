# Harvey Dividend Intelligence System - Internal API Documentation

## Overview
The Harvey Dividend Intelligence System provides real-time monitoring and analysis of dividend-related news and announcements. All endpoints are **internal only** and require authentication via the Harvey API key.

## Base URL
```
http://127.0.0.1:9001/v1/dividend-intelligence
```

## Authentication
All endpoints require the `X-API-Key` header with the internal Harvey API key:
```
X-API-Key: <HARVEY_AI_API_KEY>
```

## Endpoints

### 1. Health Check
**GET** `/health`

Check the service status and last scan time.

**Response:**
```json
{
  "status": "healthy",
  "service": "Harvey Dividend Intelligence",
  "timestamp": "2025-11-08T12:00:00Z",
  "last_scan": "2025-11-08T11:45:00Z"
}
```

### 2. Trigger Manual Scan
**POST** `/scan`

Manually trigger a dividend intelligence scan.

**Response:**
```json
{
  "success": true,
  "results": {
    "scan_timestamp": "2025-11-08T12:00:00Z",
    "articles_found": 15,
    "top_articles": [...],
    "alerts": [...],
    "trending_tickers": {"AAPL": 3, "MSFT": 2},
    "statistics": {
      "breaking_news": 2,
      "positive_sentiment": 8,
      "negative_sentiment": 2,
      "unique_tickers": 10
    }
  }
}
```

### 3. Get Latest Intelligence
**GET** `/latest`

Retrieve the most recent scan results (cached).

**Response:**
```json
{
  "scan_timestamp": "2025-11-08T12:00:00Z",
  "articles_found": 15,
  "top_articles": [
    {
      "id": "abc123",
      "title": "Apple Increases Quarterly Dividend by 5%",
      "source": "MarketWatch",
      "url": "https://marketwatch.com/...",
      "published_at": "2025-11-08T10:00:00Z",
      "relevance_score": 8.5,
      "sentiment_score": 0.8,
      "tickers": ["AAPL"],
      "analysis": {
        "impact_level": "HIGH",
        "sentiment_interpretation": "Positive dividend development",
        "recommendation": "BUY CONSIDERATION: Potential accumulation opportunity",
        "tickers_affected": ["AAPL"],
        "requires_disclaimer": true
      },
      "is_breaking": false
    }
  ],
  "alerts": [...],
  "trending_tickers": {...}
}
```

### 4. Get Current Alerts
**GET** `/alerts`

Retrieve active dividend alerts.

**Response:**
```json
{
  "alerts": [
    {
      "priority": "HIGH",
      "title": "Microsoft Declares Special Dividend",
      "source": "Reuters",
      "url": "https://reuters.com/...",
      "analysis": {
        "impact_level": "HIGH",
        "recommendation": "BUY CONSIDERATION: Special dividend capture opportunity",
        "requires_disclaimer": true
      }
    }
  ],
  "generated_at": "2025-11-08T12:00:00Z"
}
```

### 5. Get Trending Topics
**GET** `/trending`

Get currently trending dividend-related tickers.

**Response:**
```json
{
  "trending_tickers": {
    "AAPL": 3,
    "MSFT": 2,
    "JNJ": 2,
    "KO": 1
  },
  "scan_time": "2025-11-08T12:00:00Z"
}
```

### 6. Analyze Custom Text
**POST** `/analyze-text`

Analyze any text for dividend relevance and sentiment.

**Request:**
```json
{
  "text": "Apple announced a 10% dividend increase effective next quarter"
}
```

**Response:**
```json
{
  "relevance_score": 8.0,
  "sentiment_score": 0.9,
  "tickers_found": ["AAPL"],
  "analysis": {
    "impact_level": "HIGH",
    "sentiment_interpretation": "Positive dividend development",
    "recommendation": "BUY CONSIDERATION: Potential accumulation opportunity",
    "tickers_affected": ["AAPL"],
    "requires_disclaimer": true
  }
}
```

### 7. Get Ticker-Specific Intelligence
**GET** `/ticker/<TICKER>`

Get all dividend intelligence for a specific ticker.

**Example:** `/ticker/AAPL`

**Response:**
```json
{
  "ticker": "AAPL",
  "articles": [
    {
      "title": "Apple Increases Quarterly Dividend",
      "relevance_score": 8.5,
      "sentiment_score": 0.8,
      ...
    }
  ],
  "article_count": 3,
  "is_trending": true
}
```

## Analysis Object Structure

All analysis objects contain:

```json
{
  "impact_level": "HIGH|MODERATE|LOW",
  "sentiment_interpretation": "string",
  "recommendation": "string",
  "tickers_affected": ["TICKER1", "TICKER2"],
  "requires_disclaimer": true|false
}
```

### Recommendation Types:
- **BUY CONSIDERATION**: Includes disclaimer, suggests accumulation
- **ACTION**: No disclaimer, suggests position review
- **MONITOR**: No disclaimer, informational only

## Scanning Schedule

- **Automatic Scans**: Every 4 hours
- **Manual Scans**: Via `/scan` endpoint
- **Daily Summary**: Generated at 2 AM ET

## Database Storage

Results are stored in Azure SQL Server table `dividend_intelligence_scans` with:
- Full scan JSON data
- Metadata for quick queries
- Historical trend analysis

## Error Handling

All endpoints return standard error responses:

```json
{
  "error": "Error description",
  "success": false
}
```

HTTP Status Codes:
- 200: Success
- 400: Bad Request
- 401: Unauthorized (missing/invalid API key)
- 500: Internal Server Error

## Integration with Harvey Chat

The Harvey chat interface can query these endpoints to:
1. Provide real-time dividend alerts in conversation
2. Analyze user-provided text for dividend relevance
3. Show trending dividend topics
4. Give ticker-specific intelligence

## Security Notes

- **Internal Only**: Service binds to 127.0.0.1 (localhost)
- **API Key Required**: All requests need Harvey API key
- **No External Access**: Not exposed to internet
- **Database Security**: Uses Azure SQL with encrypted connections