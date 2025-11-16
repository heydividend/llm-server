# Harvey AI - New Features API Documentation

## Overview

This document covers three new Harvey AI features deployed to production:

1. **Video Answer Service** - YouTube @heydividedtv integration
2. **Investor Education Service** - Investment misconception detection
3. **Dividend Lists Management** - Curated dividend stock categories

**Base URL:** `https://20.81.210.213:8001` (Production) or `http://localhost:8001` (Local)

---

## 1. Video Answer Service

Search and recommend relevant videos from the @heydividedtv YouTube channel.

### Endpoints

#### POST /api/videos/search
Search for relevant videos based on user query.

**Request:**
```json
{
  "query": "dividend investing basics",
  "max_results": 3
}
```

**Response:**
```json
{
  "query": "dividend investing basics",
  "videos": [
    {
      "video_id": "intro_dividend_investing",
      "title": "Dividend Investing for Beginners - Complete Guide",
      "url": "https://youtube.com/@heydividedtv",
      "duration": "12:45",
      "topics": ["dividend basics", "passive income", "investing 101"],
      "keywords": ["dividend", "passive income", "beginner"],
      "description": "Comprehensive introduction to dividend investing",
      "relevance_score": 10
    }
  ],
  "total_results": 1
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8001/api/videos/search \
  -H "Content-Type: application/json" \
  -d '{"query": "REIT investing", "max_results": 2}'
```

---

#### GET /api/videos/stats
Get statistics about the video knowledge base.

**Response:**
```json
{
  "total_videos": 5,
  "total_topics": 16,
  "total_keywords": 40,
  "average_keywords_per_video": 6.2
}
```

**cURL Example:**
```bash
curl -X GET http://localhost:8001/api/videos/stats
```

---

#### GET /api/videos/topics
Get all available video topics.

**Response:**
```json
{
  "topics": [
    "dividend basics",
    "passive income",
    "REITs",
    "tax optimization"
  ],
  "total_count": 4
}
```

---

#### POST /api/videos/recommend
Get formatted video recommendations with markdown response.

**Request:**
```json
{
  "query": "monthly dividend stocks",
  "max_results": 2
}
```

**Response:**
```json
{
  "query": "monthly dividend stocks",
  "videos": [...],
  "formatted_response": "\n\n### 🎥 Related Videos from @heydividedtv\n\n**Build a Monthly Dividend Income Portfolio** (18:30)\nhttps://youtube.com/@heydividedtv\n*Step-by-step guide to creating a portfolio that pays dividends every month*\n\n"
}
```

---

## 2. Dividend Lists Management

Access curated dividend stock categories and manage watchlists/portfolios.

### Endpoints

#### GET /api/dividend-lists/categories
Get all available dividend list categories.

**Response:**
```json
[
  {
    "category_id": "dividend_aristocrats",
    "name": "Dividend Aristocrats",
    "description": "S&P 500 companies with 25+ years of consecutive dividend increases",
    "criteria": "25+ years of dividend growth, S&P 500 member"
  },
  {
    "category_id": "dividend_kings",
    "name": "Dividend Kings",
    "description": "Companies with 50+ years of consecutive dividend increases",
    "criteria": "50+ years of dividend growth"
  }
]
```

**Available Categories:**
- `dividend_aristocrats` - 25+ years of dividend growth (S&P 500)
- `dividend_kings` - 50+ years of dividend growth
- `dividend_champions` - 25+ years of dividend growth (any index)
- `high_yield` - Dividend yield >= 5%
- `monthly_payers` - Monthly dividend payment frequency
- `quarterly_growth` - Strong quarterly dividend growth
- `reits` - Real Estate Investment Trusts
- `utilities` - Utility sector dividend stocks
- `dividend_etfs` - Dividend-focused ETFs
- `low_payout_ratio` - Payout ratio < 60%

---

#### GET /api/dividend-lists/categories/{category_id}
Get stocks for a specific dividend category.

**Parameters:**
- `category_id` (path): Category identifier
- `limit` (query, optional): Max stocks to return (default: 50)

**Example:** `GET /api/dividend-lists/categories/dividend_aristocrats?limit=5`

**Response:**
```json
[
  {
    "ticker": "JNJ",
    "company_name": "Johnson & Johnson",
    "current_price": 156.50,
    "dividend_yield": 3.15,
    "annual_dividend": 4.93,
    "payout_ratio": 52.3,
    "consecutive_years": 61,
    "payment_frequency": "Quarterly",
    "sector": "Healthcare"
  }
]
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8001/api/dividend-lists/categories/high_yield?limit=10"
```

---

#### POST /api/dividend-lists/add-to-watchlist
Add top stocks from a category to user's watchlist.

**Headers:**
- `X-User-Id`: User identifier (optional, defaults to 1)

**Request:**
```json
{
  "category_id": "dividend_aristocrats",
  "max_stocks": 10
}
```

**Response:**
```json
{
  "success": true,
  "category": "dividend_aristocrats",
  "stocks_added": 8,
  "total_stocks": 10
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8001/api/dividend-lists/add-to-watchlist \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 123" \
  -d '{"category_id": "monthly_payers", "max_stocks": 5}'
```

---

#### GET /api/dividend-lists/watchlist
Get user's watchlist with dividend data.

**Headers:**
- `X-User-Id`: User identifier (optional, defaults to 1)

**Response:**
```json
{
  "watchlist": [
    {
      "ticker": "O",
      "added_date": "2025-11-16T18:00:00",
      "company_name": "Realty Income Corp",
      "current_price": 59.30,
      "dividend_yield": 5.45,
      "annual_dividend": 3.23,
      "payout_ratio": 82.1,
      "sector": "Real Estate"
    }
  ],
  "total": 1
}
```

---

#### GET /api/dividend-lists/portfolio
Get user's portfolio with dividend projections.

**Headers:**
- `X-User-Id`: User identifier (optional, defaults to 1)

**Response:**
```json
{
  "portfolio": [
    {
      "ticker": "JNJ",
      "shares": 100,
      "cost_basis": 150.00,
      "purchase_date": "2024-01-15",
      "company_name": "Johnson & Johnson",
      "current_price": 156.50,
      "dividend_yield": 3.15,
      "annual_dividend": 4.93,
      "payment_frequency": "Quarterly",
      "projected_annual_income": 493.00,
      "current_value": 15650.00,
      "unrealized_gain": 650.00
    }
  ],
  "summary": {
    "total_value": 15650.00,
    "total_annual_income": 493.00,
    "average_yield": 3.15,
    "position_count": 1,
    "monthly_income": 41.08
  },
  "total_positions": 1
}
```

---

## 3. Investor Education Service

The Investor Education Service runs automatically during chat interactions and detects common misconceptions. It's not directly exposed via API but enhances chat responses.

**Misconceptions Detected:**
1. **CUSIP vs Ticker Symbol** - Using CUSIP numbers instead of ticker symbols
2. **Distribution vs Dividend** - Tax differences between distributions and dividends
3. **High Yield Risks** - Warning about unsustainably high dividend yields
4. **DRIP Tax Implications** - Reinvested dividends are still taxable
5. **Ex-Dividend Date Timing** - When to buy for dividend eligibility
6. **Payout Ratio Guidelines** - Understanding dividend sustainability

**Integration:** The service automatically enhances chat responses when misconceptions are detected in user queries.

---

## Error Handling

All endpoints return standard HTTP status codes:

- `200 OK` - Successful request
- `400 Bad Request` - Invalid parameters
- `404 Not Found` - Category or resource not found
- `500 Internal Server Error` - Server error

**Error Response Format:**
```json
{
  "detail": "Category not found or no stocks available"
}
```

---

## Frontend Integration Examples

### React/Next.js Example

```typescript
// Search videos
async function searchVideos(query: string) {
  const response = await fetch('http://localhost:8001/api/videos/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, max_results: 3 })
  });
  return await response.json();
}

// Get dividend aristocrats
async function getDividendAristocrats(limit = 10) {
  const response = await fetch(
    `http://localhost:8001/api/dividend-lists/categories/dividend_aristocrats?limit=${limit}`
  );
  return await response.json();
}

// Add category to watchlist
async function addToWatchlist(userId: number, categoryId: string) {
  const response = await fetch('http://localhost:8001/api/dividend-lists/add-to-watchlist', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id': userId.toString()
    },
    body: JSON.stringify({ category_id: categoryId, max_stocks: 10 })
  });
  return await response.json();
}
```

---

## Rate Limiting & Performance

- No rate limiting currently implemented
- Video search: ~50ms average response time
- Dividend lists: ~100-200ms (database query)
- Recommended: Cache category lists on frontend (changes infrequently)

---

## Production URLs

- **Backend API:** `https://20.81.210.213:8001`
- **Health Check:** `https://20.81.210.213:8001/healthz`

---

## Support & Issues

For issues or questions, contact the Harvey AI development team.

**Last Updated:** November 16, 2025
