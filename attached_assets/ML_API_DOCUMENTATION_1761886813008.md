# HeyDividend ML Prediction Engine & API Documentation

**Version:** 2.0.0  
**Last Updated:** October 31, 2025

Complete API reference and architecture documentation for HeyDividend's Machine Learning prediction engine, covering dividend forecasting, portfolio analytics, NAV erosion predictions, and intelligent investment insights.

---

## Table of Contents

1. [Overview](#overview)
2. [ML Architecture](#ml-architecture)
3. [Authentication](#authentication)
4. [ML Feature Gating](#ml-feature-gating)
5. [ML Scoring Endpoints](#ml-scoring-endpoints)
6. [ML Prediction Endpoints](#ml-prediction-endpoints)
7. [NAV Erosion Analysis](#nav-erosion-analysis)
8. [ML Clustering & Portfolio Optimization](#ml-clustering--portfolio-optimization)
9. [ML Model Management](#ml-model-management)
10. [ML Usage & Monitoring](#ml-usage--monitoring)
11. [Performance Optimization](#performance-optimization)
12. [Error Handling](#error-handling)

---

## Overview

HeyDividend's ML Prediction Engine provides enterprise-grade machine learning capabilities for dividend analysis, portfolio optimization, NAV erosion forecasting, and investment predictions. The engine features advanced performance optimization with multi-tier caching, request coalescing, and real-time drift monitoring.

**Key Capabilities:**
- Real-time dividend quality scoring with ML models
- Dividend growth rate predictions (3-tier system)
- Yield and payout ratio forecasting (3, 6, 12, 24-month horizons)
- NAV erosion detection and ML-powered forecasts
- K-means clustering for portfolio optimization
- Stock similarity analysis and peer discovery
- Batch processing for large portfolios (up to 100 symbols)
- Automated model training and deployment via GitHub Actions

**Base URL:** `/api/ml`

**Model Storage:** Azure Blob Storage (versioned ML models)  
**Training Schedule:** Daily automated training via GitHub Actions  
**Caching Strategy:** 3-tier (L1/L2/L3) with 6-hour TTL

---

## ML Architecture

### Core Services

**MLPredictionService**
- High-performance ML prediction wrapper
- Request coalescing to deduplicate concurrent requests
- 3-tier caching (L1: in-memory, L2: Redis, L3: database)
- Performance metrics tracking (latency, cache hit rate, errors)

**MLService**
- Main ML coordinator orchestrating workflows
- Manages data extraction, feature engineering, model training
- Python ML bridge for scikit-learn/TensorFlow integration
- Anomaly detection ensemble models

**MLFeatureStore**
- Centralized feature repository with versioning
- Pre-computed feature caching (TTL: 1 hour)
- Feature scaling and normalization
- Automatic feature refresh via cron (every 30 minutes)

**MLDriftMonitoringService**
- Real-time model drift detection
- Performance degradation alerts
- Metrics: latency, cache hit rate, prediction accuracy
- Automated model retraining triggers

**MLUsageTracker**
- Per-user ML API usage tracking
- Tier-based quota enforcement
- Usage analytics and reporting

### Performance Optimization

1. **Request Coalescing:** Deduplicates identical concurrent ML requests, reducing compute by ~40%
2. **3-Tier Caching:** 
   - L1 (Memory): <1ms lookup, 10-minute TTL
   - L2 (Redis): <5ms lookup, 1-hour TTL  
   - L3 (Database): <50ms lookup, 6-hour TTL
3. **Feature Store:** Pre-computed features reduce prediction time from ~800ms to ~150ms
4. **Batch Processing:** Vectorized predictions for 50+ symbols with ~60% latency improvement

### Model Training Pipeline

1. **Data Extraction:** 30-year historical dividend data from Canonical_Dividends
2. **Feature Engineering:** 50+ features including growth trends, payout ratios, seasonality
3. **Model Training:** Ensemble models (Random Forest, Gradient Boosting, Neural Networks)
4. **Validation:** Cross-validation with walk-forward testing
5. **Deployment:** Automated deployment to Azure Blob Storage with version control
6. **Monitoring:** Continuous drift monitoring and performance tracking

### Prediction Types

| Type | Model | Input Features | Output | Horizon |
|------|-------|---------------|--------|---------|
| **Dividend Growth Rate** | Gradient Boosting | Historical dividends, payout ratio, earnings trend | Growth % | N/A |
| **Yield Prediction** | Random Forest | Current yield, sector, historical growth | Future yield % | 3/6/12/24 months |
| **Payout Ratio** | Neural Network | Financial ratios, cash flow, debt | Payout ratio % | 3/6/12/24 months |
| **NAV Erosion** | Time Series (LSTM) | Historical NAV, distributions, market data | NAV forecast | 3/6/12 months |
| **Dividend Quality Score** | Ensemble | 50+ features | Score 0-100 | Real-time |

---

## Authentication

All ML endpoints require JWT authentication via the `Authorization` header:

```
Authorization: Bearer YOUR_JWT_TOKEN
```

**Admin Endpoints** (model training, cache management) require additional admin privileges.

---

## ML Feature Gating

ML endpoints are protected by subscription tier requirements. Each endpoint checks for specific ML features:

| Feature Flag | Description | Required Tier |
|-------------|-------------|---------------|
| `mlRealTimeScoring` | Real-time dividend quality scoring | Investor Pro |
| `mlPortfolioAnalytics` | Advanced portfolio ML analytics | Investor Pro |
| `mlBatchProcessing` | Batch ML predictions (50+ symbols) | Investor Pro |
| `mlYieldPrediction` | ML-powered yield forecasting | Investor Pro |
| `mlPayoutForecasting` | Payout ratio predictions | Investor Pro |
| `mlGrowthPrediction` | Dividend growth rate predictions | Free (limited) |
| `mlAdvancedInsights` | Deep ML insights per symbol | Investor Pro |
| `mlClusterAnalysis` | K-means clustering analysis | Investor Pro |
| `mlPortfolioOptimization` | ML-driven portfolio optimization | Investor Pro |
| `mlModelMonitoring` | Model performance metrics | Investor Pro |
| `mlPredictionHistory` | Historical prediction tracking | Investor Pro |

**Error Response (403 Forbidden):**
```json
{
  "error": "This feature requires Investor Pro subscription",
  "feature": "mlRealTimeScoring"
}
```

---

## ML Scoring Endpoints

### POST /api/ml/score/symbol
Score a single stock for dividend quality and sustainability.

**Authentication:** Required  
**Feature Gate:** `mlRealTimeScoring`  
**Rate Limit:** Standard (100 req/min)

**Request Body:**
```json
{
  "symbol": "AAPL"
}
```

**Response:**
```json
{
  "symbol": "AAPL",
  "score": 87.5,
  "factors": {
    "payout_sustainability": 92,
    "growth_consistency": 85,
    "yield_stability": 88,
    "financial_health": 95
  },
  "grade": "A",
  "timestamp": "2025-10-30T23:15:00Z"
}
```

---

### POST /api/ml/score/portfolio
Score an entire portfolio with aggregated ML metrics.

**Authentication:** Required  
**Feature Gate:** `mlPortfolioAnalytics`  
**Rate Limit:** Standard

**Request Body:**
```json
{
  "portfolio_id": 123
}
```

**Response:**
```json
{
  "portfolio_id": 123,
  "overall_score": 82.3,
  "holdings": [
    {
      "symbol": "AAPL",
      "score": 87.5,
      "weight": 0.15,
      "contribution": 13.1
    }
  ],
  "risk_metrics": {
    "dividend_risk": "LOW",
    "concentration_risk": "MEDIUM",
    "sector_diversification": 0.72
  }
}
```

---

### POST /api/ml/score/watchlist
Score all symbols in a user's watchlist.

**Authentication:** Required  
**Feature Gate:** `mlRealTimeScoring`  
**Rate Limit:** Standard

**Request Body:**
```json
{
  "symbols": ["AAPL", "MSFT", "JNJ", "PG"]
}
```

**Response:**
```json
{
  "scores": [
    {
      "symbol": "AAPL",
      "score": 87.5,
      "grade": "A"
    },
    {
      "symbol": "MSFT",
      "score": 91.2,
      "grade": "A+"
    }
  ],
  "summary": {
    "avg_score": 88.4,
    "best_symbol": "MSFT",
    "worst_symbol": "PG"
  }
}
```

---

### POST /api/ml/score/batch
Batch score up to 100 symbols in a single request.

**Authentication:** Required  
**Feature Gate:** `mlBatchProcessing`  
**Rate Limit:** Strict (10 req/min)

**Request Body:**
```json
{
  "symbols": ["AAPL", "MSFT", /* ... up to 100 symbols */]
}
```

**Response:** Same format as `/score/watchlist`

---

## ML Prediction Endpoints

### POST /api/ml/predict/yield
Predict future dividend yield using ML regression models.

**Authentication:** Required  
**Feature Gate:** `mlYieldPrediction`  
**Rate Limit:** Standard

**Request Body:**
```json
{
  "symbol": "AAPL",
  "horizon": "12_months"
}
```

**Response:**
```json
{
  "symbol": "AAPL",
  "current_yield": 0.52,
  "predicted_yield": 0.58,
  "confidence": 0.87,
  "prediction_date": "2026-10-30",
  "factors": {
    "historical_growth": 0.12,
    "payout_ratio_trend": "stable",
    "earnings_momentum": "positive"
  }
}
```

**Supported Horizons:**
- `3_months`
- `6_months`
- `12_months`
- `24_months`

---

### POST /api/ml/predict/growth-rate
Predict dividend growth rate (used in ticker dialogs).

**Authentication:** Required  
**Feature Gate:** `mlGrowthPrediction`  
**Rate Limit:** Standard

**Request Body:**
```json
{
  "symbol": "AAPL"
}
```

**Response:**
```json
{
  "symbol": "AAPL",
  "predicted_growth_rate": 7.2,
  "confidence": 0.82,
  "model_version": "v2.1.0",
  "based_on": {
    "historical_data_points": 48,
    "earnings_trend": "positive",
    "payout_ratio": 15.8
  }
}
```

---

### POST /api/ml/predict/payout-ratio
Forecast future payout ratio sustainability.

**Authentication:** Required  
**Feature Gate:** `mlPayoutForecasting`  
**Rate Limit:** Standard

**Request Body:**
```json
{
  "symbol": "AAPL",
  "horizon": "12_months"
}
```

**Response:**
```json
{
  "symbol": "AAPL",
  "current_payout_ratio": 15.8,
  "predicted_payout_ratio": 16.5,
  "sustainability": "EXCELLENT",
  "risk_level": "LOW",
  "confidence": 0.91
}
```

---

### POST /api/ml/predict/yield/batch
Batch yield predictions for multiple symbols.

**Authentication:** Required  
**Feature Gate:** `mlBatchProcessing`  
**Rate Limit:** Strict (10 req/min)

**Request Body:**
```json
{
  "symbols": ["AAPL", "MSFT", "JNJ"],
  "horizon": "12_months"
}
```

**Response:**
```json
{
  "predictions": [
    {
      "symbol": "AAPL",
      "current_yield": 0.52,
      "predicted_yield": 0.58,
      "confidence": 0.87
    }
  ],
  "processed": 3,
  "failed": 0
}
```

---

### POST /api/ml/predict/payout-ratio/batch
Batch payout ratio predictions.

**Authentication:** Required  
**Feature Gate:** `mlBatchProcessing`  
**Rate Limit:** Strict (10 req/min)

**Request Body & Response:** Similar to yield batch endpoint.

---

## NAV Erosion Analysis

HeyDividend provides ML-powered NAV (Net Asset Value) erosion analysis for high-yield funds and ETFs. This feature detects funds experiencing long-term capital deterioration and forecasts future NAV values using time-series ML models.

### POST /api/analysis/nav-erosion
Analyze NAV erosion with ML-powered forecasts for 3/6/12-month horizons.

**Authentication:** Required  
**Feature Gate:** Free (basic analysis), Investor Pro (ML predictions)  
**Rate Limit:** Standard

**Request Body:**
```json
{
  "symbols": ["JEPI", "QYLD", "RYLD"]
}
```

**Response:**
```json
{
  "results": [
    {
      "symbol": "JEPI",
      "name": "JPMorgan Equity Premium Income ETF",
      "inception_date": "2020-05-20",
      "inception_nav": 50.12,
      "current_nav": 52.35,
      "nav_change_pct": 4.45,
      "nav_change_absolute": 2.23,
      "days_since_inception": 1260,
      "status": "preserved",
      "data_source": "symbols",
      "prediction": {
        "symbol": "JEPI",
        "current_nav": 52.35,
        "forecasts": {
          "3_month": {
            "predicted_nav": 52.89,
            "confidence": 0.85,
            "change_pct": 1.03,
            "trend": "positive"
          },
          "6_month": {
            "predicted_nav": 53.42,
            "confidence": 0.78,
            "change_pct": 2.04,
            "trend": "positive"
          },
          "12_month": {
            "predicted_nav": 54.15,
            "confidence": 0.71,
            "change_pct": 3.44,
            "trend": "positive"
          }
        },
        "risk_factors": [
          "High distribution rate may pressure NAV",
          "Options strategy adds volatility"
        ],
        "model_version": "v1.2.0",
        "predicted_at": "2025-10-31T10:00:00Z"
      }
    },
    {
      "symbol": "QYLD",
      "name": "Global X NASDAQ 100 Covered Call ETF",
      "inception_date": "2013-12-11",
      "inception_nav": 25.00,
      "current_nav": 17.42,
      "nav_change_pct": -30.32,
      "nav_change_absolute": -7.58,
      "days_since_inception": 4342,
      "status": "eroded",
      "data_source": "symbols",
      "prediction": {
        "symbol": "QYLD",
        "current_nav": 17.42,
        "forecasts": {
          "3_month": {
            "predicted_nav": 17.15,
            "confidence": 0.82,
            "change_pct": -1.55,
            "trend": "negative"
          },
          "6_month": {
            "predicted_nav": 16.89,
            "confidence": 0.74,
            "change_pct": -3.04,
            "trend": "negative"
          },
          "12_month": {
            "predicted_nav": 16.32,
            "confidence": 0.68,
            "change_pct": -6.31,
            "trend": "negative"
          }
        },
        "risk_factors": [
          "Historical NAV erosion trend continuing",
          "Covered call strategy limits upside participation",
          "Distribution rate exceeds income generation"
        ],
        "model_version": "v1.2.0",
        "predicted_at": "2025-10-31T10:00:00Z"
      }
    }
  ],
  "summary": {
    "total_analyzed": 3,
    "preserved_count": 1,
    "eroded_count": 2,
    "avg_nav_change_pct": -8.64
  }
}
```

**NAV Erosion Status:**
- `preserved`: NAV has maintained or increased since inception
- `eroded`: NAV has declined since inception (capital deterioration)
- `unknown`: Insufficient data to determine NAV erosion

**ML Prediction Features:**
- **Time-Series LSTM Models:** Trained on historical NAV, distributions, and market data
- **Multi-Horizon Forecasts:** 3, 6, and 12-month NAV predictions
- **Confidence Scores:** Model certainty (0.0-1.0) based on historical volatility
- **Trend Detection:** Identifies positive/negative NAV trajectories
- **Risk Analysis:** Highlights distribution sustainability concerns

**Use Cases:**
1. **High-Yield Fund Screening:** Identify funds with unsustainable distributions
2. **Capital Preservation:** Detect return of capital vs return on capital
3. **Long-Term Viability:** Forecast which funds will maintain NAV over time
4. **Income vs Growth:** Balance yield with capital appreciation

---

## ML Clustering & Portfolio Optimization

### POST /api/ml/cluster/analyze-stock
Analyze stock characteristics using K-means clustering.

**Authentication:** Required  
**Feature Gate:** `mlClusterAnalysis`  
**Rate Limit:** Standard

**Request Body:**
```json
{
  "symbol": "AAPL"
}
```

**Response:**
```json
{
  "symbol": "AAPL",
  "cluster_id": 3,
  "cluster_name": "High Quality Growth Dividend",
  "cluster_characteristics": {
    "avg_yield": 1.2,
    "avg_growth_rate": 8.5,
    "avg_payout_ratio": 25.3
  },
  "peers_in_cluster": ["MSFT", "V", "MA"]
}
```

---

### POST /api/ml/cluster/find-similar
Find stocks similar to a given symbol using ML clustering.

**Authentication:** Required  
**Feature Gate:** `mlSimilarStocks`  
**Rate Limit:** Standard

**Request Body:**
```json
{
  "symbol": "AAPL",
  "limit": 10
}
```

**Response:**
```json
{
  "symbol": "AAPL",
  "similar_stocks": [
    {
      "symbol": "MSFT",
      "similarity_score": 0.94,
      "cluster_id": 3
    },
    {
      "symbol": "V",
      "similarity_score": 0.89,
      "cluster_id": 3
    }
  ]
}
```

---

### POST /api/ml/cluster/optimize-portfolio
Get ML-driven portfolio optimization suggestions.

**Authentication:** Required  
**Feature Gate:** `mlPortfolioOptimization`  
**Rate Limit:** Standard

**Request Body:**
```json
{
  "portfolio_id": 123,
  "optimization_goal": "maximize_yield",
  "constraints": {
    "max_single_position": 0.15,
    "min_diversification_score": 0.7
  }
}
```

**Response:**
```json
{
  "current_portfolio": {
    "yield": 3.2,
    "diversification_score": 0.65,
    "cluster_distribution": { "1": 0.3, "2": 0.4, "3": 0.3 }
  },
  "optimized_portfolio": {
    "suggested_changes": [
      {
        "action": "reduce",
        "symbol": "T",
        "from_weight": 0.20,
        "to_weight": 0.12,
        "reason": "Over-concentrated in low-quality dividend cluster"
      },
      {
        "action": "add",
        "symbol": "MSFT",
        "suggested_weight": 0.08,
        "reason": "Improves diversification and quality"
      }
    ],
    "projected_yield": 3.4,
    "projected_diversification": 0.78
  }
}
```

---

### POST /api/ml/cluster/portfolio-diversification
Analyze portfolio diversification across ML clusters.

**Authentication:** Required  
**Feature Gate:** `mlPortfolioOptimization`  
**Rate Limit:** Standard

**Request Body:**
```json
{
  "portfolio_id": 123
}
```

**Response:**
```json
{
  "portfolio_id": 123,
  "cluster_distribution": {
    "High Quality Growth": 0.35,
    "Stable Income": 0.45,
    "High Yield Risk": 0.20
  },
  "diversification_score": 0.72,
  "recommendations": [
    "Consider reducing exposure to High Yield Risk cluster",
    "Portfolio is well-balanced across quality segments"
  ]
}
```

---

### GET /api/ml/cluster/dashboard
Get overview of all ML clusters and their characteristics.

**Authentication:** Required  
**Feature Gate:** `mlClusterAnalysis`  
**Rate Limit:** Standard

**Response:**
```json
{
  "total_clusters": 5,
  "clusters": [
    {
      "id": 1,
      "name": "Dividend Aristocrats",
      "member_count": 127,
      "avg_yield": 2.8,
      "avg_growth_rate": 6.5,
      "avg_payout_ratio": 52.3
    }
  ],
  "last_updated": "2025-10-30T12:00:00Z"
}
```

---

### GET /api/ml/cluster/portfolio/:portfolioId
Get cluster analysis for a specific portfolio.

**Authentication:** Required  
**Feature Gate:** `mlPortfolioOptimization`  
**Rate Limit:** Standard

**Response:** Detailed cluster breakdown and recommendations.

---

## ML Model Management

### GET /api/ml/models/regression/performance
Get performance metrics for ML regression models.

**Authentication:** Required  
**Feature Gate:** `mlModelMonitoring`  
**Rate Limit:** Standard

**Response:**
```json
{
  "model_type": "regression",
  "models": {
    "yield_prediction": {
      "version": "v2.1.0",
      "mae": 0.12,
      "rmse": 0.18,
      "r2_score": 0.89,
      "last_trained": "2025-10-25T00:00:00Z"
    }
  }
}
```

---

### GET /api/ml/models/timeseries/performance
Get performance metrics for time-series models.

**Authentication:** Required  
**Feature Gate:** `mlModelMonitoring`  
**Rate Limit:** Standard

**Response:** Similar to regression performance endpoint.

---

### POST /api/ml/models/regression/train
Trigger ML model retraining (Admin only).

**Authentication:** Admin required  
**Rate Limit:** Admin (5 req/min)

**Request Body:**
```json
{
  "model_name": "yield_prediction",
  "training_config": {
    "lookback_period": "5_years",
    "validation_split": 0.2
  }
}
```

**Response:**
```json
{
  "status": "training_started",
  "job_id": "train-job-12345",
  "estimated_completion": "2025-10-30T23:45:00Z"
}
```

---

### POST /api/ml/models/timeseries/train
Trigger time-series model retraining (Admin only).

**Authentication:** Admin required  
**Rate Limit:** Admin (5 req/min)

**Request & Response:** Similar to regression training endpoint.

---

## ML Usage & Monitoring

### GET /api/ml/usage-stats
Get ML API usage statistics for the current user.

**Authentication:** Required  
**Rate Limit:** Standard

**Response:**
```json
{
  "user_id": 456,
  "subscription_tier": "investor_pro",
  "usage_period": "2025-10",
  "usage": {
    "ml_score": 127,
    "portfolio_analysis": 15,
    "batch_score": 3,
    "yield_prediction": 42
  },
  "limits": {
    "ml_score": 1000,
    "portfolio_analysis": 100,
    "batch_score": 50
  },
  "remaining": {
    "ml_score": 873,
    "portfolio_analysis": 85
  }
}
```

---

### GET /api/ml/insights/:symbol
Get advanced ML-powered insights for a specific symbol.

**Authentication:** Required  
**Feature Gate:** `mlAdvancedInsights`  
**Rate Limit:** Standard

**URL Parameters:**
- `symbol` (required): Stock ticker symbol

**Response:**
```json
{
  "symbol": "AAPL",
  "ml_insights": {
    "dividend_quality_score": 87.5,
    "growth_prediction": 7.2,
    "yield_forecast_12m": 0.58,
    "payout_sustainability": "EXCELLENT",
    "cluster": "High Quality Growth Dividend",
    "risk_factors": [
      "Payout ratio trending up slightly",
      "Strong earnings growth supports dividend"
    ],
    "opportunities": [
      "Consistent dividend growth track record",
      "Low payout ratio allows for future increases"
    ]
  }
}
```

---

### GET /api/ml/predictions/:symbol/recent
Get recent prediction history for a symbol.

**Authentication:** Required  
**Feature Gate:** `mlPredictionHistory`  
**Rate Limit:** Standard

**URL Parameters:**
- `symbol` (required): Stock ticker symbol

**Response:**
```json
{
  "symbol": "AAPL",
  "predictions": [
    {
      "prediction_type": "yield",
      "predicted_at": "2025-10-15T10:00:00Z",
      "predicted_value": 0.58,
      "actual_value": 0.56,
      "accuracy": 0.97,
      "horizon": "12_months"
    }
  ],
  "accuracy_summary": {
    "avg_accuracy": 0.91,
    "total_predictions": 24
  }
}
```

---

### GET /api/ml/health
Check ML service health and availability.

**Authentication:** Not required  
**Rate Limit:** Standard

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "regression_models": "operational",
    "clustering_engine": "operational",
    "prediction_cache": "operational"
  },
  "model_versions": {
    "yield_prediction": "v2.1.0",
    "growth_rate": "v1.8.3",
    "clustering": "v3.0.1"
  },
  "cache_hit_rate": 0.76,
  "avg_response_time_ms": 142
}
```

---

### POST /api/ml/cache/cleanup (Admin)
Clear stale ML prediction cache entries.

**Authentication:** Admin required  
**Rate Limit:** Admin (5 req/min)

**Response:**
```json
{
  "cleared_entries": 1247,
  "cache_size_before_mb": 128,
  "cache_size_after_mb": 45
}
```

---

## Error Handling

### Common Error Responses

**401 Unauthorized:**
```json
{
  "error": "Authentication required",
  "message": "Please provide a valid JWT token"
}
```

**403 Forbidden (Feature Gated):**
```json
{
  "error": "Feature not available",
  "message": "This feature requires Investor Pro subscription",
  "feature": "mlRealTimeScoring",
  "upgrade_url": "/pricing"
}
```

**429 Too Many Requests:**
```json
{
  "error": "Rate limit exceeded",
  "message": "ML API rate limit exceeded. Try again in 60 seconds.",
  "retry_after": 60
}
```

**500 Internal Server Error:**
```json
{
  "error": "ML model error",
  "message": "Failed to generate prediction. Our team has been notified.",
  "request_id": "req-abc123"
}
```

---

## Best Practices

1. **Cache Predictions:** ML predictions are cached for 6 hours. Don't request the same prediction repeatedly.

2. **Use Batch Endpoints:** For multiple symbols, use batch endpoints instead of individual calls.

3. **Monitor Usage:** Check `/api/ml/usage-stats` regularly to avoid hitting limits.

4. **Handle Errors Gracefully:** ML models may occasionally fail. Always have fallback UI states.

5. **Respect Rate Limits:** Batch endpoints have stricter limits. Plan accordingly.

6. **Feature Gates:** Check user tier before calling ML endpoints to avoid 403 errors.

---

## Frontend Integration Examples

### Using the Dividend Prediction Hook

```typescript
import { useDividendPrediction } from '@/hooks/useDividendPrediction';

function TickerDialog({ symbol }: { symbol: string }) {
  const { prediction, isLoading, error } = useDividendPrediction(symbol);

  if (isLoading) return <div>🤔 Thinking...</div>;
  if (error) return <div>Unable to load prediction</div>;

  return (
    <div>
      <h3>Next Dividend Prediction</h3>
      <p>Predicted Growth: {prediction.predicted_growth_rate}%</p>
      <p>Confidence: {(prediction.confidence * 100).toFixed(0)}%</p>
    </div>
  );
}
```

### Calling ML Scoring API

```typescript
import { apiRequest } from '@/lib/queryClient';

async function scorePortfolio(portfolioId: number) {
  const response = await apiRequest({
    url: '/api/ml/score/portfolio',
    method: 'POST',
    body: { portfolio_id: portfolioId }
  });
  
  return response.data;
}
```

---

**Last Updated:** October 30, 2025  
**Maintained By:** HeyDividend Engineering Team
