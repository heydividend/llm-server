# Harvey Unified Intelligence API Documentation

**Version:** Harvey-Unified-1.0  
**Last Updated:** November 8, 2025  
**API Base URL:** `http://20.81.210.213:8001/v1/intelligence`

## Overview

The Harvey Unified Intelligence API integrates RAG (Retrieval-Augmented Generation) capabilities with multi-source data orchestration into the main Harvey system. This provides intelligent, context-aware responses enriched with real-time data from multiple sources.

---

## Table of Contents

1. [Architecture](#architecture)
2. [Authentication](#authentication)
3. [Endpoints](#endpoints)
4. [Data Sources](#data-sources)
5. [Request/Response Examples](#requestresponse-examples)
6. [Error Handling](#error-handling)
7. [Integration Guide](#integration-guide)

---

## Architecture

The Unified Intelligence system orchestrates data from multiple sources:
- **Azure SQL Database** - Historical dividend data, ML predictions
- **Yahoo Finance API** - Real-time stock quotes and market data
- **Massive.com API** - Sentiment analysis and news sentiment
- **Harvey ML Service** - Payout ratings, dividend predictions, intelligence insights

All features are now integrated into ONE Harvey API running on port 8001, eliminating the need for separate services.

---

## Authentication

All Intelligence endpoints require API key authentication:

```
X-API-Key: YOUR_HARVEY_AI_API_KEY
```

Or using Bearer token:

```
Authorization: Bearer YOUR_HARVEY_AI_API_KEY
```

---

## Endpoints

### 1. Health Check

**Endpoint:** `GET /v1/intelligence/health`

**Description:** Check the health and availability of the Intelligence system.

**Response:**
```json
{
  "status": "healthy",
  "service": "Harvey Unified AI System",
  "rag_available": true
}
```

### 2. Analyze Query with RAG Enrichment

**Endpoint:** `POST /v1/intelligence/analyze`

**Description:** Main endpoint for AI analysis with multi-source RAG enrichment. Processes natural language queries and returns intelligent recommendations enriched with real-time data.

**Request Body:**
```json
{
  "query": "What are the best dividend stocks under $50?",
  "include_raw_data": false
}
```

**Parameters:**
- `query` (string, required): Natural language query for analysis
- `include_raw_data` (boolean, optional): Include raw data from all sources in response (default: false)

**Response:**
```json
{
  "success": true,
  "recommendation": {
    "summary": "Based on current analysis, here are top dividend stocks under $50...",
    "stocks": [
      {
        "ticker": "T",
        "company": "AT&T Inc.",
        "price": 15.42,
        "dividend_yield": 7.23,
        "payout_rating": "A",
        "sentiment": "positive",
        "reasoning": "Strong dividend history with sustainable payout ratio..."
      }
    ],
    "insights": [
      "Market sentiment is currently positive for telecom sector",
      "Interest rate environment favors high-yield dividend stocks"
    ]
  },
  "confidence": 0.92,
  "sources": [
    "Azure SQL Database (Historical Data)",
    "Yahoo Finance (Real-time Quotes)",
    "Massive.com (Sentiment Analysis)",
    "Harvey ML Predictions"
  ],
  "disclaimer": "This is AI-generated analysis for informational purposes only. Not financial advice."
}
```

### 3. Dividend Alerts (Coming Soon)

**Endpoint:** `GET /v1/intelligence/dividend-alerts`

**Description:** Retrieve latest dividend-related alerts and notifications.

**Response:**
```json
{
  "success": true,
  "alerts": [
    {
      "id": "alert_001",
      "type": "dividend_increase",
      "ticker": "JNJ",
      "message": "Johnson & Johnson announced 6% dividend increase",
      "timestamp": "2025-11-08T10:30:00Z",
      "impact": "positive"
    }
  ]
}
```

### 4. Trending Analysis (Coming Soon)

**Endpoint:** `GET /v1/intelligence/trending`

**Description:** Get trending dividend stocks based on real-time analysis.

**Response:**
```json
{
  "success": true,
  "trending": [
    {
      "ticker": "ABBV",
      "trend_score": 95,
      "reason": "High social sentiment and recent dividend increase",
      "mentions": 1245
    }
  ]
}
```

---

## Data Sources

### 1. Azure SQL Database
- Historical dividend payments
- ML predictions (payout ratings, calendar predictions)
- Company fundamentals
- Dividend intelligence insights

### 2. Yahoo Finance API
- Real-time stock prices
- Current dividend yields
- Market capitalization
- Trading volume

### 3. Massive.com API
- News sentiment analysis
- Social media sentiment
- Trending topics
- Market mood indicators

### 4. Harvey ML Service
- Payout safety ratings (A+, A, B, C)
- Dividend cut risk predictions
- Growth projections
- Yield forecasting

---

## Request/Response Examples

### Example 1: Screening Query

**Request:**
```bash
curl -X POST http://20.81.210.213:8001/v1/intelligence/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "query": "Find monthly dividend stocks with yields above 5%"
  }'
```

**Response:**
```json
{
  "success": true,
  "recommendation": {
    "summary": "Found 8 monthly dividend stocks with yields above 5%",
    "stocks": [
      {
        "ticker": "AGNC",
        "company": "AGNC Investment Corp",
        "monthly_dividend": 0.12,
        "yield": 14.8,
        "payout_rating": "B",
        "risk_level": "moderate"
      }
    ]
  },
  "confidence": 0.88,
  "sources": ["Azure SQL", "Yahoo Finance", "ML Predictions"]
}
```

### Example 2: Specific Stock Analysis

**Request:**
```bash
curl -X POST http://20.81.210.213:8001/v1/intelligence/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "query": "Is Microsoft a good dividend stock to buy now?",
    "include_raw_data": true
  }'
```

**Response with Raw Data:**
```json
{
  "success": true,
  "recommendation": {
    "summary": "Microsoft (MSFT) is a strong dividend growth stock...",
    "rating": "BUY",
    "target_price": 420.00,
    "dividend_score": 92
  },
  "confidence": 0.95,
  "sources": ["All data sources"],
  "raw_data": {
    "yahoo_finance": {
      "price": 380.52,
      "dividend_yield": 0.72,
      "pe_ratio": 35.2
    },
    "massive_sentiment": {
      "score": 0.82,
      "trend": "positive",
      "volume": "high"
    },
    "ml_predictions": {
      "payout_rating": "A+",
      "growth_forecast": 8.5
    }
  }
}
```

---

## Error Handling

### Common Error Responses

**400 Bad Request:**
```json
{
  "success": false,
  "error": "Invalid query format",
  "message": "Query must be a non-empty string"
}
```

**401 Unauthorized:**
```json
{
  "success": false,
  "error": "Authentication failed",
  "message": "Invalid or missing API key"
}
```

**429 Too Many Requests:**
```json
{
  "success": false,
  "error": "Rate limit exceeded",
  "message": "Please wait before making another request",
  "retry_after": 60
}
```

**500 Internal Server Error:**
```json
{
  "success": false,
  "error": "Analysis failed",
  "message": "An error occurred during analysis. Please try again."
}
```

---

## Integration Guide

### JavaScript/TypeScript Example

```javascript
class HarveyIntelligence {
  constructor(apiKey) {
    this.apiKey = apiKey;
    this.baseUrl = 'http://20.81.210.213:8001/v1/intelligence';
  }

  async analyzeQuery(query, includeRawData = false) {
    const response = await fetch(`${this.baseUrl}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': this.apiKey
      },
      body: JSON.stringify({
        query: query,
        include_raw_data: includeRawData
      })
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    return await response.json();
  }

  async checkHealth() {
    const response = await fetch(`${this.baseUrl}/health`, {
      headers: {
        'X-API-Key': this.apiKey
      }
    });
    
    return await response.json();
  }
}

// Usage
const harvey = new HarveyIntelligence('YOUR_API_KEY');

// Analyze a query
const result = await harvey.analyzeQuery(
  "What are the safest dividend stocks for retirement?"
);
console.log(result.recommendation);

// Check system health
const health = await harvey.checkHealth();
console.log(`System status: ${health.status}`);
```

### Python Example

```python
import requests
import json

class HarveyIntelligence:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "http://20.81.210.213:8001/v1/intelligence"
        
    def analyze_query(self, query, include_raw_data=False):
        """Analyze a query with RAG enrichment"""
        response = requests.post(
            f"{self.base_url}/analyze",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": self.api_key
            },
            json={
                "query": query,
                "include_raw_data": include_raw_data
            }
        )
        response.raise_for_status()
        return response.json()
    
    def check_health(self):
        """Check system health"""
        response = requests.get(
            f"{self.base_url}/health",
            headers={"X-API-Key": self.api_key}
        )
        return response.json()

# Usage
harvey = HarveyIntelligence("YOUR_API_KEY")

# Analyze dividend stocks
result = harvey.analyze_query(
    "Find high-yield REITs with stable dividends"
)
print(f"Recommendation: {result['recommendation']['summary']}")
print(f"Confidence: {result['confidence']}")

# Check health
health = harvey.check_health()
print(f"RAG Available: {health['rag_available']}")
```

---

## Rate Limits

- **Standard:** 60 requests per minute
- **Burst:** 10 requests per second
- **Include Raw Data:** 30 requests per minute (uses more resources)

---

## Migration from Separate Services

If you were previously using separate RAG or Intelligence services, migration is simple:

**Old Setup (Multiple Services):**
- RAG Service on port 8002
- Intelligence Service on port 8003
- Harvey Main on port 8001

**New Unified Setup:**
- Everything on port 8001 under `/v1/intelligence/*`
- Same request/response format
- No need to manage multiple services

---

## Support

For issues or questions about the Harvey Unified Intelligence API:
- Email: dev@heydividend.com
- System Status: Check `/v1/intelligence/health` endpoint
- Logs: Available in Azure VM at `/home/azureuser/harvey/logs/`

---

## Changelog

### Version 1.0 (November 8, 2025)
- Initial release of Unified Intelligence API
- Integrated RAG enrichment into main Harvey system
- Added multi-source data orchestration
- Implemented Yahoo Finance and Massive.com integrations
- Fixed database connectivity (switched to pymssql)
- Consolidated all services into single API on port 8001