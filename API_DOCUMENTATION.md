# Harvey API Documentation

**Version:** Harvey-1o  
**Last Updated:** October 30, 2025

Complete API reference for integrating with Harvey, your AI-powered financial advisor backend.

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Base URL & Response Format](#base-url--response-format)
4. [Core Chat API](#core-chat-api)
5. [Conversational Memory](#conversational-memory)
6. [Income Ladder Builder](#income-ladder-builder)
7. [Tax Optimization AI](#tax-optimization-ai)
8. [Natural Language Alerts](#natural-language-alerts)
9. [Proactive Insights](#proactive-insights)
10. [ML Predictions](#ml-predictions)
11. [ML Schedulers](#ml-schedulers)
12. [Unified Intelligence (RAG)](#unified-intelligence-rag)
13. [Error Handling](#error-handling)
14. [Code Examples](#code-examples)

---

## Overview

Harvey provides a comprehensive REST API for financial analysis, dividend investing, and AI-powered portfolio management. All endpoints return JSON responses with optional markdown formatting for easy display in chat interfaces.

**Key Features:**
- Streaming chat responses with Server-Sent Events (SSE)
- Token-aware conversational memory (4000 token budget)
- ML-powered dividend analysis and predictions
- Tax optimization and loss harvesting
- Natural language alert creation
- Daily portfolio digests

---

## Authentication

All protected endpoints require API key authentication using the `Authorization` header:

```
Authorization: Bearer YOUR_HARVEY_AI_API_KEY
```

**Public Endpoints (No Auth Required):**
- `GET /` - Health check
- `GET /healthz` - Detailed health status

**Protected Endpoints:**
- All `/v1/*` endpoints require authentication

**Error Response (401 Unauthorized):**
```json
{
  "detail": "Invalid or missing API key"
}
```

---

## Base URL & Response Format

**Base URL:** `https://your-harvey-deployment.repl.co/v1`

**Standard Response Format:**
```json
{
  "success": true,
  "markdown": "# User-friendly markdown response",
  "data": { /* Structured data */ },
  "error": null
}
```

**Error Response Format:**
```json
{
  "success": false,
  "error": "Error message",
  "detail": "Detailed error information"
}
```

---

## Core Chat API

### POST /v1/chat/completions

Main endpoint for conversational AI interactions with streaming responses.

#### JSON Request Format

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY
```

**Request Body:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "What's the dividend yield for AAPL?"
    }
  ],
  "model": "gpt-4o",
  "stream": true,
  "meta": {
    "session_id": "user-session-123",
    "conversation_id": "conv-456"
  }
}
```

**Request Parameters:**
- `messages` (required): Array of message objects with `role` and `content`
- `model` (optional): AI model to use (default: "gpt-4o")
- `stream` (optional): Enable streaming responses (default: true)
- `meta` (optional): Metadata including `session_id`, `conversation_id`, overrides
- `debug` (optional): Enable debug mode (boolean)

#### Multipart/Form-Data Request Format (For File Uploads)

**Request Headers:**
```
Content-Type: multipart/form-data
Authorization: Bearer YOUR_API_KEY
```

**Form Fields:**
- `messages` (required): JSON string array of message objects
- `meta` (optional): JSON string with metadata (session_id, conversation_id, etc.)
- `model` (optional): AI model name string
- `stream` (optional): "true" or "false" (default: "true")
- `debug` (optional): "true" or "false" (default: "false")
- `session_id` (optional): User session ID string
- `conversation_id` (optional): Conversation thread ID string
- `file` / `files` / `file[]` / `files[]` / `upload` / `attachment` (optional): File upload (PDF, image, spreadsheet)
  - Accepts any of these field names for file uploads
  - Single file per request (first file found is processed)
  - Multiple field names supported for client compatibility

**Example Multipart Request (JavaScript):**
```javascript
const formData = new FormData();
formData.append('messages', JSON.stringify([
  { role: 'user', content: 'Analyze this dividend statement' }
]));
formData.append('meta', JSON.stringify({
  session_id: 'user-session-123'
}));
formData.append('stream', 'true');
formData.append('file', fileInput.files[0]);

const response = await fetch('https://your-harvey.repl.co/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${API_KEY}`
  },
  body: formData
});
```

**Supported File Types:**
- PDF documents (dividend statements, annual reports)
- Images (JPG, PNG - OCR extraction)
- Spreadsheets (XLSX, CSV - portfolio data)

**File Processing:**
- Automatic OCR and text extraction
- Content prepended to user message
- Max extracted text: 4000 characters (truncated if larger)

**Streaming Response (SSE):**
```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","choices":[{"delta":{"content":"The "}}]}
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","choices":[{"delta":{"content":"dividend "}}]}
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","choices":[{"delta":{"content":"yield..."}}]}
data: [DONE]
```

**Non-Streaming Response:**
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "The dividend yield for AAPL is approximately 0.5%..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 120,
    "total_tokens": 135
  },
  "tickers": ["AAPL"]
}
```

**Features:**
- Automatic ticker extraction from questions
- SQL query generation for database lookups
- Web search fallback for real-time data
- ML prediction integration
- Conversational memory with token-aware context

---

## Conversational Memory

Harvey automatically manages conversation history using session and conversation IDs.

### How It Works

1. **Session Creation:** Each user gets a unique `session_id` (UUID)
2. **Conversation Threads:** Multiple conversations per session with `conversation_id`
3. **Token Management:** Loads last 4000 tokens of context automatically
4. **Message Storage:** All messages stored in Azure SQL database

### Using Sessions in Chat

**Include in chat request:**
```json
{
  "messages": [...],
  "meta": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "conversation_id": "660e8400-e29b-41d4-a716-446655440001"
  }
}
```

**Response includes:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "conversation_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

**Best Practices:**
- Generate `session_id` once per user (store in localStorage/cookies)
- Create new `conversation_id` for each chat thread
- Backend automatically loads conversation history
- No manual history management needed

---

## Income Ladder Builder

Build diversified monthly income portfolios from quarterly dividend payers.

### POST /v1/income-ladder/build

Create a new income ladder portfolio.

**Request:**
```json
{
  "session_id": "user-session-123",
  "target_monthly_income": 1000.00,
  "risk_tolerance": "moderate",
  "preferences": {
    "sectors_to_avoid": ["Tech"],
    "min_yield": 3.0,
    "max_positions": 15
  }
}
```

**Parameters:**
- `session_id` (required): User session ID
- `target_monthly_income` (required): Target monthly income (> 0)
- `risk_tolerance` (optional): "conservative", "moderate", or "aggressive" (default: "moderate")
- `preferences` (optional): Additional preferences object

**Response:**
```json
{
  "success": true,
  "ladder_id": "ladder-789",
  "target_monthly_income": 1000.00,
  "total_capital_needed": 240000.00,
  "monthly_allocations": {
    "January": [
      {
        "ticker": "VZ",
        "company_name": "Verizon Communications",
        "shares": 500,
        "price_per_share": 40.50,
        "total_cost": 20250.00,
        "monthly_dividend": 83.33,
        "annual_yield": 4.93
      }
    ],
    "February": [...],
    "March": [...]
  },
  "diversification": {
    "by_sector": {
      "Utilities": 25.0,
      "REITs": 20.0,
      "Consumer Staples": 15.0
    },
    "by_ticker": {
      "VZ": 8.4,
      "T": 7.2
    }
  },
  "annual_income": 12000.00,
  "effective_yield": 5.0,
  "risk_tolerance": "moderate",
  "created_at": "2025-10-30T10:30:00Z",
  "markdown": "# Income Ladder Plan\n\n**Target:** $1,000/month..."
}
```

### GET /v1/income-ladder/{ladder_id}

Retrieve a saved income ladder by ID.

**Response:** Same as build response

### GET /v1/income-ladder/session/{session_id}

List all income ladders for a session.

**Query Parameters:**
- `limit` (optional): Max ladders to return (1-100, default: 10)

**Response:**
```json
{
  "success": true,
  "session_id": "user-session-123",
  "count": 3,
  "ladders": [
    {
      "ladder_id": "ladder-789",
      "target_monthly_income": 1000.00,
      "total_capital_needed": 240000.00,
      "effective_yield": 5.0,
      "created_at": "2025-10-30T10:30:00Z"
    }
  ]
}
```

---

## Tax Optimization AI

Analyze tax efficiency and find harvesting opportunities.

### POST /v1/tax/analyze-portfolio

Analyze qualified vs ordinary dividends.

**Request:**
```json
{
  "session_id": "user-session-123",
  "portfolio_tickers": ["AAPL", "MSFT", "VZ"],
  "user_tax_bracket": "medium"
}
```

**Parameters:**
- `session_id` (required): User session ID
- `portfolio_tickers` (optional): List of tickers (if null, uses user_portfolios table)
- `user_tax_bracket` (optional): "low", "medium", or "high" (default: "medium")

**Response:**
```json
{
  "success": true,
  "total_dividend_income": 5000.00,
  "qualified_dividends": 4500.00,
  "ordinary_dividends": 500.00,
  "qualified_percentage": 90.0,
  "tax_savings_estimate": 450.00,
  "breakdown_by_ticker": [
    {
      "ticker": "AAPL",
      "annual_dividend": 2000.00,
      "qualified_status": "qualified",
      "holding_period_days": 365,
      "tax_rate": 15.0
    }
  ],
  "recommendations": [
    "Hold AAPL for 60+ days to maintain qualified status",
    "Consider replacing XYZ with higher-quality dividend stock"
  ],
  "markdown": "# Tax Analysis\n\n**Qualified Dividends:** 90%..."
}
```

### POST /v1/tax/harvest-opportunities

Find tax-loss harvesting opportunities.

**Request:**
```json
{
  "session_id": "user-session-123",
  "min_loss_threshold": 1000.00,
  "user_tax_bracket": "medium"
}
```

**Parameters:**
- `session_id` (required): User session ID
- `min_loss_threshold` (optional): Minimum loss to consider (default: 1000, >= 0)
- `user_tax_bracket` (optional): Tax bracket

**Response:**
```json
{
  "success": true,
  "opportunities": [
    {
      "ticker": "XYZ",
      "purchase_price": 100.00,
      "current_price": 85.00,
      "unrealized_loss": -1500.00,
      "shares": 100,
      "tax_benefit": 525.00,
      "replacement_suggestions": [
        {
          "ticker": "ABC",
          "similarity_score": 0.92,
          "sector": "Technology",
          "reason": "Similar sector exposure, different issuer (wash sale safe)"
        }
      ]
    }
  ],
  "total_harvestable_losses": -3000.00,
  "estimated_tax_savings": 1050.00,
  "markdown": "# Tax-Loss Harvesting Opportunities\n\n..."
}
```

### POST /v1/tax/scenario

Calculate tax implications for different scenarios.

**Request:**
```json
{
  "session_id": "user-session-123",
  "scenario_type": "harvest",
  "user_tax_bracket": "medium",
  "harvest_losses": true
}
```

**Parameters:**
- `session_id` (required): User session ID
- `scenario_type` (required): "current", "optimized", or "harvest"
- `user_tax_bracket` (optional): Tax bracket
- `harvest_losses` (optional): Include harvesting (default: false)

**Response:**
```json
{
  "success": true,
  "scenario_type": "harvest",
  "annual_dividend_income": 10000.00,
  "qualified_income": 9000.00,
  "ordinary_income": 1000.00,
  "capital_losses_harvested": -3000.00,
  "total_tax_owed": 1200.00,
  "effective_tax_rate": 12.0,
  "potential_savings": 450.00,
  "markdown": "# Tax Scenario: Harvest\n\n..."
}
```

### GET /v1/tax/recommendations/{session_id}

Get AI-generated tax optimization recommendations.

**Query Parameters:**
- `user_tax_bracket` (optional): Tax bracket (default: "medium")

**Response:**
```json
{
  "success": true,
  "recommendations": "Based on your portfolio...",
  "action_items": [
    "Hold AAPL for 5 more days to qualify for lower tax rate",
    "Consider harvesting $2,500 loss in XYZ before year-end"
  ],
  "estimated_savings": 750.00
}
```

### GET /v1/tax/scenarios/{session_id}

List saved tax scenarios for a session.

**Query Parameters:**
- `limit` (optional): Max scenarios (1-100, default: 10)

**Response:**
```json
{
  "success": true,
  "session_id": "user-session-123",
  "count": 2,
  "scenarios": [
    {
      "scenario_id": "scenario-456",
      "scenario_type": "harvest",
      "potential_savings": 750.00,
      "tax_year": 2025,
      "created_at": "2025-10-30T10:30:00Z"
    }
  ]
}
```

---

## Natural Language Alerts

Create and manage alerts using plain English.

### POST /v1/alerts/create

Create an alert from natural language.

**Request:**
```json
{
  "session_id": "user-session-123",
  "natural_language": "Tell me when AAPL goes above $200"
}
```

**Parameters:**
- `session_id` (required): User session ID
- `natural_language` (required): Natural language alert request

**Examples:**
- "Tell me when AAPL goes above $200"
- "Alert me if any of my stocks cut their dividend"
- "Notify me when VYM yield exceeds 4%"
- "Let me know if MSFT drops below $350"

**Response:**
```json
{
  "success": true,
  "alert_id": "alert-123",
  "rule_name": "AAPL price above $200",
  "condition_type": "price_target",
  "ticker": "AAPL",
  "trigger_condition": {
    "type": "price_above",
    "threshold": 200.00
  },
  "is_active": true,
  "markdown": "## ✅ Alert Created\n\n**Alert:** AAPL price above $200..."
}
```

### GET /v1/alerts/session/{session_id}

List all alerts for a session.

**Query Parameters:**
- `active_only` (optional): Only active alerts (default: true)

**Response:**
```json
{
  "success": true,
  "session_id": "user-session-123",
  "count": 5,
  "alerts": [
    {
      "alert_id": "alert-123",
      "rule_name": "AAPL price above $200",
      "condition_type": "price_target",
      "ticker": "AAPL",
      "is_active": true,
      "created_at": "2025-10-30T10:00:00Z"
    }
  ]
}
```

### GET /v1/alerts/events/{session_id}

List triggered alert events (notifications).

**Query Parameters:**
- `unread_only` (optional): Only unread events (default: true)
- `limit` (optional): Max events (1-200, default: 50)

**Response:**
```json
{
  "success": true,
  "session_id": "user-session-123",
  "count": 3,
  "events": [
    {
      "event_id": "event-456",
      "alert_id": "alert-123",
      "rule_name": "AAPL price above $200",
      "ticker": "AAPL",
      "triggered_at": "2025-10-30T14:30:00Z",
      "trigger_data": {
        "current_price": 205.50,
        "threshold": 200.00
      },
      "is_read": false
    }
  ]
}
```

### DELETE /v1/alerts/{alert_id}

Delete an alert rule.

**Response:**
```json
{
  "success": true,
  "message": "Alert alert-123 deleted successfully"
}
```

### PUT /v1/alerts/events/{event_id}/read

Mark an alert event as read.

**Response:**
```json
{
  "success": true,
  "message": "Alert event event-456 marked as read"
}
```

### POST /v1/alerts/check

Manually trigger alert checking.

**Query Parameters:**
- `alert_id` (optional): Check specific alert, or all if not provided

**Response:**
```json
{
  "success": true,
  "checked": "all",
  "triggered_count": 2,
  "triggered_alerts": [
    {
      "alert_id": "alert-123",
      "rule_name": "AAPL price above $200",
      "triggered_at": "2025-10-30T15:00:00Z"
    }
  ]
}
```

**Note:** Background scheduler checks alerts every 5 minutes automatically.

---

## Proactive Insights

Daily portfolio digests and automated insights.

### GET /v1/insights/{session_id}

Get insights and notifications for a session.

**Query Parameters:**
- `unread_only` (optional): Only unread insights (default: true)
- `limit` (optional): Max insights (1-100, default: 10)

**Response:**
```json
{
  "success": true,
  "session_id": "user-session-123",
  "count": 5,
  "insights": [
    {
      "insight_id": "insight-789",
      "insight_type": "daily_digest",
      "title": "Daily Portfolio Digest - Oct 30, 2025",
      "content": "Your portfolio gained 2.5% today...",
      "priority": "high",
      "created_at": "2025-10-30T08:00:00Z",
      "is_read": false,
      "metadata": {
        "portfolio_value_change": 2500.00,
        "top_gainer": "AAPL",
        "top_loser": "XYZ"
      }
    },
    {
      "insight_id": "insight-790",
      "insight_type": "significant_change",
      "title": "AAPL up 5.5%",
      "content": "Apple Inc. (AAPL) is up 5.5% today...",
      "priority": "medium",
      "created_at": "2025-10-30T14:30:00Z",
      "is_read": false
    }
  ]
}
```

**Insight Types:**
- `daily_digest`: Daily portfolio summary (generated at 8 AM)
- `significant_change`: Stock price movement > 5%
- `dividend_announcement`: New dividend declared
- `ex_date_reminder`: Upcoming ex-dividend date

### POST /v1/insights/generate-digest

Manually generate a daily digest.

**Request:**
```json
{
  "session_id": "user-session-123"
}
```

**Response:**
```json
{
  "success": true,
  "insight_id": "insight-999",
  "title": "Daily Portfolio Digest - Oct 30, 2025",
  "content": "# Daily Portfolio Summary\n\n**Portfolio Value:** $125,000...",
  "priority": "high",
  "metadata": {
    "total_value": 125000.00,
    "day_change": 2500.00,
    "day_change_pct": 2.0
  }
}
```

**Note:** Bypasses normal 8 AM schedule for on-demand generation.

### PUT /v1/insights/{insight_id}/read

Mark an insight as read.

**Response:**
```json
{
  "success": true,
  "message": "Insight insight-789 marked as read"
}
```

### POST /v1/insights/portfolio-alert

Create portfolio-specific alert (system/testing use).

**Query Parameters:**
- `session_id` (required): User session ID
- `alert_type` (required): "significant_change", "dividend_announcement", or "ex_date_reminder"
- `ticker` (required): Stock ticker symbol

**Response:**
```json
{
  "success": true,
  "insight_id": "insight-888",
  "title": "AAPL up 5.5%",
  "content": "Apple Inc. (AAPL) is up 5.5% today...",
  "priority": "medium"
}
```

---

## ML Predictions

Harvey integrates with HeyDividend's Internal ML API for advanced dividend analysis.

### ML Query Types

ML predictions are accessed through the main chat endpoint by asking natural language questions:

**1. Payout Sustainability Rating (0-100)**
- Question: "What's the payout rating for AAPL?"
- Question: "Is MSFT's dividend sustainable?"
- Returns: Sustainability score, quality metrics, NAV protection

**2. Dividend Growth Forecast**
- Question: "What's the dividend growth forecast for VZ?"
- Question: "Will T increase its dividend next year?"
- Returns: Predicted growth rate, confidence level

**3. Dividend Cut Risk (0-100)**
- Question: "What's the cut risk for XYZ?"
- Question: "Is ABC likely to cut its dividend?"
- Returns: 12-month cut probability, risk factors

**4. Anomaly Detection**
- Question: "Are there any anomalies in AAPL's dividend history?"
- Question: "Check for irregular payments in MSFT"
- Returns: Unusual patterns, payment irregularities

**5. Comprehensive ML Score**
- Question: "Give me the complete ML analysis for VZ"
- Question: "Full dividend quality score for T"
- Returns: Overall quality score, buy/sell recommendation

### ML Response Format

ML predictions stream progressively in the chat response:

```markdown
## 📊 Dividend Payout Rating

### AAPL - Apple Inc.
**Payout Rating:** 92/100 (Excellent)
**Quality Score:** 8.5/10
**NAV Protection:** Strong

The dividend is highly sustainable with excellent coverage...

### MSFT - Microsoft Corporation
**Payout Rating:** 88/100 (Very Good)
...
```

**Features:**
- Progressive streaming (results appear ticker-by-ticker)
- Real-time analysis from ML API
- Integrated into natural conversation flow
- Automatic ticker extraction

---

## ML Schedulers

Harvey includes enterprise-grade ML schedulers that provide cached, high-performance dividend predictions. These schedulers run automatically to ensure fast responses and consistent predictions across all users.

### Scheduler Overview

**Automated ML Tasks:**
- **Payout Rating Scheduler**: Runs daily at 1:00 AM UTC
- **Dividend Calendar Scheduler**: Runs every Sunday at 2:00 AM UTC
- **ML Model Training**: Runs every Sunday at 3:00 AM UTC

**Key Benefits:**
- ⚡ Instant responses from cached predictions
- 📊 Consistent ratings across all users
- 🔄 Automatic self-healing if services fail
- 📈 Reduced API load and improved performance

### GET /v1/ml-schedulers/health

Monitor the health status of all ML schedulers.

**Request:**
```http
GET /v1/ml-schedulers/health
Authorization: Bearer YOUR_API_KEY
```

**Response:**
```json
{
  "success": true,
  "schedulers": {
    "payout_rating": {
      "status": "healthy",
      "last_run": "2025-11-07T01:00:00Z",
      "next_run": "2025-11-08T01:00:00Z",
      "cached_symbols": 2500
    },
    "dividend_calendar": {
      "status": "healthy",
      "last_run": "2025-11-03T02:00:00Z",
      "next_run": "2025-11-10T02:00:00Z",
      "predictions_cached": 1800
    },
    "ml_training": {
      "status": "active",
      "last_training": "2025-11-03T03:00:00Z",
      "next_training": "2025-11-10T03:00:00Z",
      "models_trained": 5
    }
  },
  "overall_health": "healthy",
  "last_check": "2025-11-07T04:30:00Z"
}
```

### POST /v1/ml-schedulers/payout-ratings

Get cached payout ratings for dividend stocks with A+ to F grades.

**Request:**
```http
POST /v1/ml-schedulers/payout-ratings
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

```json
{
  "symbols": ["AAPL", "MSFT", "JNJ", "O", "SCHD"],
  "force_refresh": false
}
```

**Parameters:**
- `symbols` (required): Array of stock ticker symbols (max 100)
- `force_refresh` (optional): Force refresh from ML API instead of cache (default: false)

**Response:**
```json
{
  "success": true,
  "ratings": {
    "AAPL": {
      "symbol": "AAPL",
      "grade": "A+",
      "score": 92.5,
      "quality": "Excellent",
      "sustainability": "Very Strong",
      "recommendation": "Strong Buy",
      "cached_at": "2025-11-07T01:00:00Z"
    },
    "MSFT": {
      "symbol": "MSFT",
      "grade": "A",
      "score": 88.3,
      "quality": "Very Good",
      "sustainability": "Strong",
      "recommendation": "Buy",
      "cached_at": "2025-11-07T01:00:00Z"
    }
  },
  "from_cache": true,
  "cache_timestamp": "2025-11-07T01:00:00Z"
}
```

### POST /v1/ml-schedulers/dividend-calendar

Get predicted dividend payment dates for the next 6 months.

**Request:**
```http
POST /v1/ml-schedulers/dividend-calendar
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

```json
{
  "symbols": ["O", "SCHD", "JEPI", "JEPQ"],
  "months_ahead": 6
}
```

**Parameters:**
- `symbols` (required): Array of stock ticker symbols (max 100)
- `months_ahead` (optional): Number of months to predict ahead (default: 6, max: 12)

**Response:**
```json
{
  "success": true,
  "predictions": {
    "O": {
      "next_ex_date": "2025-11-15",
      "next_pay_date": "2025-11-30",
      "predicted_amount": 0.265,
      "confidence": 0.92,
      "frequency": "Monthly",
      "upcoming_dates": [
        {"ex_date": "2025-11-15", "pay_date": "2025-11-30", "amount": 0.265},
        {"ex_date": "2025-12-15", "pay_date": "2025-12-31", "amount": 0.265},
        {"ex_date": "2026-01-15", "pay_date": "2026-01-31", "amount": 0.268}
      ]
    },
    "SCHD": {
      "next_ex_date": "2025-12-05",
      "next_pay_date": "2025-12-20",
      "predicted_amount": 0.75,
      "confidence": 0.88,
      "frequency": "Quarterly",
      "upcoming_dates": [
        {"ex_date": "2025-12-05", "pay_date": "2025-12-20", "amount": 0.75},
        {"ex_date": "2026-03-05", "pay_date": "2026-03-20", "amount": 0.77}
      ]
    }
  },
  "months_ahead": 6,
  "from_cache": true
}
```

### GET /v1/ml-schedulers/training-status

Get the status of ML model training and performance metrics.

**Request:**
```http
GET /v1/ml-schedulers/training-status
Authorization: Bearer YOUR_API_KEY
```

**Response:**
```json
{
  "success": true,
  "status": "completed",
  "last_training": "2025-11-03T03:00:00Z",
  "next_training": "2025-11-10T03:00:00Z",
  "models_trained": [
    "dividend_scorer",
    "yield_predictor",
    "growth_predictor",
    "payout_predictor",
    "cut_risk_analyzer"
  ],
  "performance": {
    "dividend_scorer": {
      "accuracy": 0.92,
      "precision": 0.89,
      "recall": 0.94
    },
    "yield_predictor": {
      "mae": 0.15,
      "rmse": 0.22
    },
    "cut_risk_analyzer": {
      "accuracy": 0.87,
      "f1_score": 0.85
    }
  },
  "training_duration": "2h 45m",
  "records_processed": 125000
}
```

### GET /v1/ml-schedulers/admin/dashboard

Admin dashboard for monitoring all ML scheduler operations.

**Request:**
```http
GET /v1/ml-schedulers/admin/dashboard
Authorization: Bearer YOUR_ADMIN_API_KEY
```

**Response:**
```json
{
  "success": true,
  "dashboard": {
    "schedulers": {
      "payout_rating": {
        "status": "healthy",
        "uptime": "99.8%",
        "last_error": null,
        "execution_times": [45.2, 43.8, 44.1],
        "cache_hit_rate": 0.92
      },
      "dividend_calendar": {
        "status": "healthy",
        "uptime": "99.9%",
        "last_error": null,
        "execution_times": [62.3, 61.7, 63.2],
        "cache_hit_rate": 0.88
      }
    },
    "self_healing": {
      "circuit_breakers": {
        "ml_api": {"state": "closed", "failures": 0},
        "ml_payout_rating": {"state": "closed", "failures": 0},
        "ml_dividend_calendar": {"state": "closed", "failures": 0},
        "ml_training": {"state": "closed", "failures": 0}
      },
      "recovery_history": [
        {
          "service": "ml_api",
          "timestamp": "2025-11-06T14:30:00Z",
          "action": "recovery_success"
        }
      ],
      "overall_health": 0.95
    },
    "cache_stats": {
      "total_cached_symbols": 2500,
      "cache_memory_mb": 45.6,
      "cache_hits_today": 15234,
      "cache_misses_today": 1823
    }
  }
}
```

### Self-Healing Features

The ML Schedulers include automatic self-healing capabilities:

**Circuit Breakers:**
- Automatically detect service failures
- Open circuit after threshold failures (5 for API, 3 for schedulers)
- Attempt recovery after timeout period

**Recovery Strategies:**
- **ML API**: Restart harvey-ml service on Azure VM
- **Payout Rating**: Restart harvey-payout-rating.timer
- **Dividend Calendar**: Restart harvey-dividend-calendar.timer  
- **ML Training**: Restart harvey-ml-training.timer

**Health Monitoring:**
- Continuous health score tracking (0.0 to 1.0)
- Automatic recovery when health drops below 0.5
- Recovery history tracking and audit logs

### Integration with Chat API

The ML Scheduler predictions are automatically integrated into the chat API responses:

**Example Questions:**
- "What are the payout ratings for my portfolio?" - Uses cached payout ratings
- "When are the next dividend payments?" - Uses cached dividend calendar
- "Has the ML model been trained recently?" - Shows training status

**Benefits:**
- ⚡ 10x faster responses from cache
- 📊 Consistent predictions for all users
- 🔄 Automatic fallback to direct API if cache miss
- 💾 Reduced database and API load

---

## Unified Intelligence (RAG)

Harvey's Unified Intelligence API integrates advanced RAG (Retrieval-Augmented Generation) capabilities with multi-source data orchestration. All Intelligence features are now integrated into the main Harvey API on port 8001.

**Key Features:**
- Multi-source data orchestration (Azure SQL, Yahoo Finance, Massive.com)
- Real-time market data enrichment
- Sentiment analysis integration
- Self-evaluation loops for quality control

### POST /v1/intelligence/analyze

Main endpoint for AI analysis with RAG enrichment. Processes natural language queries and returns intelligent recommendations enriched with real-time data from multiple sources.

**Request:**
```http
POST /v1/intelligence/analyze
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

```json
{
  "query": "What are the best dividend stocks under $50?",
  "include_raw_data": false
}
```

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
        "sentiment": "positive"
      }
    ]
  },
  "confidence": 0.92,
  "sources": ["Azure SQL", "Yahoo Finance", "Massive.com", "ML Predictions"],
  "disclaimer": "This is AI-generated analysis for informational purposes only."
}
```

### GET /v1/intelligence/health

Check the health and availability of the Intelligence system.

**Request:**
```http
GET /v1/intelligence/health
Authorization: Bearer YOUR_API_KEY
```

**Response:**
```json
{
  "status": "healthy",
  "service": "Harvey Unified AI System",
  "rag_available": true
}
```

**For complete Intelligence API documentation, see:** [API_DOCUMENTATION_UNIFIED_INTELLIGENCE.md](./API_DOCUMENTATION_UNIFIED_INTELLIGENCE.md)

---

## Error Handling

### HTTP Status Codes

- `200 OK`: Successful request
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid API key
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side error

### Error Response Format

```json
{
  "success": false,
  "error": "Brief error message",
  "detail": "Detailed error information for debugging"
}
```

### Common Error Scenarios

**Invalid API Key:**
```json
{
  "detail": "Invalid or missing API key"
}
```

**Resource Not Found:**
```json
{
  "success": false,
  "error": "Income ladder ladder-123 not found"
}
```

**Validation Error:**
```json
{
  "success": false,
  "error": "scenario_type must be 'current', 'optimized', or 'harvest'"
}
```

**No Portfolio Data:**
```json
{
  "success": false,
  "error": "No portfolio holdings found for this session",
  "detail": "User must add holdings before requesting analysis"
}
```

---

## Code Examples

### JavaScript/TypeScript

#### Chat with Streaming Response

```typescript
async function chatWithHarvey(message: string, sessionId: string) {
  const response = await fetch('https://your-harvey.repl.co/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.HARVEY_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      messages: [
        { role: 'user', content: message }
      ],
      stream: true,
      meta: {
        session_id: sessionId
      }
    })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n').filter(line => line.trim() !== '');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') continue;

        const parsed = JSON.parse(data);
        const content = parsed.choices[0]?.delta?.content;
        if (content) {
          console.log(content); // Display incrementally
        }
      }
    }
  }
}

// Usage
chatWithHarvey("What's the dividend yield for AAPL?", "user-session-123");
```

#### Create Income Ladder

```typescript
async function buildIncomeLadder(
  sessionId: string,
  targetMonthlyIncome: number,
  riskTolerance: 'conservative' | 'moderate' | 'aggressive' = 'moderate'
) {
  const response = await fetch('https://your-harvey.repl.co/v1/income-ladder/build', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.HARVEY_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      session_id: sessionId,
      target_monthly_income: targetMonthlyIncome,
      risk_tolerance: riskTolerance
    })
  });

  const data = await response.json();

  if (!data.success) {
    throw new Error(data.error);
  }

  console.log(`Ladder ID: ${data.ladder_id}`);
  console.log(`Capital Needed: $${data.total_capital_needed.toLocaleString()}`);
  console.log(`Annual Income: $${data.annual_income.toLocaleString()}`);
  console.log(`Effective Yield: ${data.effective_yield}%`);

  return data;
}

// Usage
buildIncomeLadder("user-session-123", 1000, "moderate");
```

#### Create Natural Language Alert

```typescript
async function createAlert(sessionId: string, alertText: string) {
  const response = await fetch('https://your-harvey.repl.co/v1/alerts/create', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.HARVEY_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      session_id: sessionId,
      natural_language: alertText
    })
  });

  const data = await response.json();

  if (!data.success) {
    throw new Error(data.error);
  }

  console.log(`Alert Created: ${data.rule_name}`);
  console.log(`Alert ID: ${data.alert_id}`);
  console.log(data.markdown); // Display to user

  return data;
}

// Usage
createAlert("user-session-123", "Tell me when AAPL goes above $200");
```

#### Get Triggered Alerts

```typescript
async function getAlertNotifications(sessionId: string, unreadOnly: boolean = true) {
  const url = new URL(`https://your-harvey.repl.co/v1/alerts/events/${sessionId}`);
  url.searchParams.set('unread_only', String(unreadOnly));

  const response = await fetch(url.toString(), {
    headers: {
      'Authorization': `Bearer ${process.env.HARVEY_API_KEY}`
    }
  });

  const data = await response.json();

  console.log(`Found ${data.count} alert notifications`);
  
  data.events.forEach(event => {
    console.log(`[${event.triggered_at}] ${event.rule_name}`);
    console.log(`  Ticker: ${event.ticker}`);
    console.log(`  Data:`, event.trigger_data);
  });

  return data.events;
}

// Usage
getAlertNotifications("user-session-123");
```

#### Get Daily Insights

```typescript
async function getDailyInsights(sessionId: string) {
  const response = await fetch(
    `https://your-harvey.repl.co/v1/insights/${sessionId}?unread_only=true&limit=10`,
    {
      headers: {
        'Authorization': `Bearer ${process.env.HARVEY_API_KEY}`
      }
    }
  );

  const data = await response.json();

  console.log(`You have ${data.count} new insights:`);
  
  data.insights.forEach(insight => {
    console.log(`\n${insight.title} [${insight.priority}]`);
    console.log(insight.content);
  });

  return data.insights;
}

// Usage
getDailyInsights("user-session-123");
```

#### Analyze Portfolio for Tax Efficiency

```typescript
async function analyzeTaxes(
  sessionId: string,
  tickers?: string[],
  taxBracket: 'low' | 'medium' | 'high' = 'medium'
) {
  const response = await fetch('https://your-harvey.repl.co/v1/tax/analyze-portfolio', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.HARVEY_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      session_id: sessionId,
      portfolio_tickers: tickers,
      user_tax_bracket: taxBracket
    })
  });

  const data = await response.json();

  console.log(`Qualified Dividends: ${data.qualified_percentage}%`);
  console.log(`Estimated Tax Savings: $${data.tax_savings_estimate}`);
  console.log(data.markdown); // Display to user

  return data;
}

// Usage
analyzeTaxes("user-session-123", ["AAPL", "MSFT", "VZ"], "medium");
```

### Python

#### Chat with Streaming Response

```python
import requests
import json
import os

def chat_with_harvey(message: str, session_id: str):
    url = "https://your-harvey.repl.co/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('HARVEY_API_KEY')}",
        "Content-Type": "application/json"
    }
    payload = {
        "messages": [
            {"role": "user", "content": message}
        ],
        "stream": True,
        "meta": {
            "session_id": session_id
        }
    }

    response = requests.post(url, headers=headers, json=payload, stream=True)

    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                data = line_str[6:]
                if data == '[DONE]':
                    break
                
                chunk = json.loads(data)
                content = chunk.get('choices', [{}])[0].get('delta', {}).get('content')
                if content:
                    print(content, end='', flush=True)

# Usage
chat_with_harvey("What's the dividend yield for AAPL?", "user-session-123")
```

#### Create Income Ladder

```python
import requests
import os

def build_income_ladder(
    session_id: str,
    target_monthly_income: float,
    risk_tolerance: str = "moderate"
):
    url = "https://your-harvey.repl.co/v1/income-ladder/build"
    headers = {
        "Authorization": f"Bearer {os.getenv('HARVEY_API_KEY')}",
        "Content-Type": "application/json"
    }
    payload = {
        "session_id": session_id,
        "target_monthly_income": target_monthly_income,
        "risk_tolerance": risk_tolerance
    }

    response = requests.post(url, headers=headers, json=payload)
    data = response.json()

    if not data.get('success'):
        raise Exception(data.get('error'))

    print(f"Ladder ID: {data['ladder_id']}")
    print(f"Capital Needed: ${data['total_capital_needed']:,.2f}")
    print(f"Annual Income: ${data['annual_income']:,.2f}")
    print(f"Effective Yield: {data['effective_yield']}%")

    return data

# Usage
build_income_ladder("user-session-123", 1000, "moderate")
```

---

## Summary

Harvey's API provides comprehensive financial analysis capabilities through:

✅ **Streaming Chat** - Real-time AI conversations with financial intelligence  
✅ **Conversational Memory** - Seamless multi-turn conversations  
✅ **Income Ladders** - Monthly income portfolio planning  
✅ **Tax Optimization** - Qualified dividend analysis & loss harvesting  
✅ **Natural Language Alerts** - "Tell me when X happens" monitoring  
✅ **Proactive Insights** - Daily portfolio digests at 8 AM  
✅ **ML Predictions** - Advanced dividend sustainability analysis  

All APIs return markdown-formatted responses for easy chat integration and structured JSON for programmatic access.

**Need Help?**
- Check error responses for detailed debugging information
- All endpoints include `markdown` field for user-friendly display
- Use `debug: true` in chat requests for verbose logging

---

**Last Updated:** October 30, 2025  
**Version:** Harvey-1o
