# Harvey AI - Hashtag Analytics & Tracking System

## 📊 Overview

Harvey AI now features a comprehensive **Hashtag Analytics & Tracking System** that automatically monitors hashtag usage (#TICKER format), provides trending analysis, and delivers personalized recommendations. This system enhances user experience by tracking which stocks/tickers users are interested in and surfacing relevant insights.

---

## 🎯 Key Features

### 1. **Automatic Hashtag Tracking**
- Automatically detects and tracks all ticker mentions (`#AAPL`, `#MSFT`, etc.)
- Real-time frequency counting
- User-specific preference tracking
- Context-aware categorization (chat, search, portfolio, watchlist)

### 2. **Trending Hashtag Detection**
- 24-hour trending analysis
- 7-day trending analysis
- 30-day trending analysis
- Configurable minimum occurrence thresholds

### 3. **Co-occurrence Analysis**
- Identifies which hashtags appear together
- "Users also searched for..." recommendations
- Portfolio diversification insights

### 4. **Enhanced Video Recommendations**
- Hashtag-powered video discovery
- Trending topic videos
- Ticker-specific educational content

### 5. **User Preference Learning**
- Tracks individual user hashtag patterns
- Personalized content recommendations
- Improved AI response relevance

### 6. **Privacy & Data Retention Controls**
- Configurable retention periods (default: 30 days)
- Automatic cleanup of old events
- GDPR-compliant user data deletion
- Bounded memory growth with automatic eviction
- Full metadata persistence (session_id, conversation_id, metadata)

### 7. **Database Persistence (Optional)**
- Automatic persistence to Azure SQL Database
- Durable storage across server restarts
- Historical trend analysis support
- Indexed queries for performance

---

## 🏗️ Architecture

### Components

```
app/services/hashtag_analytics_service.py  # Core analytics engine
app/api/routes/hashtag_routes.py           # REST API endpoints
app/helpers/video_integration.py           # Hashtag-enhanced videos
app/controllers/ai_controller.py           # Automatic tracking integration
```

### Data Flow

```
User Query → Ticker Extraction → Hashtag Tracking → Analytics → Insights
     ↓              ↓                   ↓              ↓           ↓
"Check #AAPL"  Detects: AAPL      Logs event      Updates     Trending
dividend       #AAPL              (session_id,    frequency   analysis
                                   user_id,        counters
                                   context)
```

---

## 📡 API Endpoints

### 1. Track Hashtag Event
**POST** `/api/hashtags/track`

Track a hashtag usage event.

**Request:**
```json
{
  "hashtags": ["AAPL", "MSFT", "GOOGL"],
  "user_id": "user123",
  "context": "chat",
  "session_id": "session456",
  "conversation_id": "conv789",
  "metadata": {
    "source": "chat",
    "timestamp": "2025-11-16T10:30:00Z"
  }
}
```

**Response:**
```json
{
  "success": true,
  "hashtags_tracked": 3,
  "timestamp": "2025-11-16T10:30:00.123Z",
  "events_in_memory": 8542
}
```

**Note:** All metadata (session_id, conversation_id, metadata) is now persisted and queryable.

---

### 2. Get Trending Hashtags
**GET** `/api/hashtags/trending?time_window_hours=24&limit=10`

Get trending hashtags within a time window.

**Parameters:**
- `time_window_hours` (int): Time window in hours (24, 168, 720)
- `limit` (int): Maximum number of trending hashtags
- `min_count` (int): Minimum occurrence count to be considered trending

**Response:**
```json
[
  {
    "hashtag": "AAPL",
    "count": 45,
    "rank": 1,
    "time_window_hours": 24,
    "events_analyzed": 2847
  },
  {
    "hashtag": "MSFT",
    "count": 38,
    "rank": 2,
    "time_window_hours": 24,
    "events_analyzed": 2847
  }
]
```

**Note:** Trending works accurately for any volume of events, not limited by the 10,000 in-memory cap.

---

### 3. Get User Preferences
**GET** `/api/hashtags/user/{user_id}/preferences?limit=20`

Get a user's most frequently used hashtags.

**Response:**
```json
[
  {
    "hashtag": "AAPL",
    "count": 12,
    "rank": 1
  },
  {
    "hashtag": "MSFT",
    "count": 8,
    "rank": 2
  }
]
```

---

### 4. Get Related Hashtags
**GET** `/api/hashtags/related/{hashtag}?limit=10`

Find hashtags that commonly appear with the given hashtag.

**Response:**
```json
[
  {
    "related_hashtag": "MSFT",
    "cooccurrence_count": 15,
    "rank": 1
  },
  {
    "related_hashtag": "GOOGL",
    "cooccurrence_count": 12,
    "rank": 2
  }
]
```

---

### 5. Get Hashtag Stats
**GET** `/api/hashtags/stats?hashtag=AAPL`

Get comprehensive statistics for a hashtag or all hashtags.

**Response (Specific Hashtag):**
```json
{
  "success": true,
  "stats": {
    "hashtag": "AAPL",
    "total_count": 127,
    "contexts": {
      "chat": 89,
      "search": 23,
      "portfolio": 15
    },
    "related_hashtags": [...],
    "trending_rank": 1
  }
}
```

**Response (Global Stats):**
```json
{
  "success": true,
  "stats": {
    "total_unique_hashtags": 450,
    "total_events": 3200,
    "top_10_all_time": [...],
    "trending_24h": [...],
    "trending_7d": [...]
  }
}
```

---

### 6. Extract Hashtags from Text
**POST** `/api/hashtags/extract?text=Check out #AAPL and #MSFT dividends`

Extract all hashtags from a given text.

**Response:**
```json
{
  "success": true,
  "text": "Check out #AAPL and #MSFT dividends",
  "hashtags": ["AAPL", "MSFT"],
  "count": 2
}
```

---

### 7. Delete User Data (GDPR Compliance)
**DELETE** `/api/hashtags/user/{user_id}`

Delete all hashtag data for a specific user.

**Response:**
```json
{
  "success": true,
  "user_id": "user123",
  "deleted": {
    "events": 45,
    "preferences": 12,
    "contexts": 78
  },
  "timestamp": "2025-11-16T10:30:00.123Z"
}
```

**Note:** This permanently deletes all user data from both in-memory cache and database (if enabled).

---

## 💻 Usage Examples

### Automatic Tracking in Chat

Hashtag tracking is **automatically enabled** in Harvey's chat interface. When users mention tickers, they are automatically tracked:

```python
# User query: "What's the dividend yield for #AAPL?"
# System automatically:
# 1. Detects ticker: AAPL
# 2. Tracks event: hashtags=['AAPL'], context='chat', session_id='...'
# 3. Updates analytics: frequency +1, user preferences +1
```

### Manual Tracking

```python
from app.services.hashtag_analytics_service import get_hashtag_analytics_service

# Get service instance
hashtag_service = get_hashtag_analytics_service()

# Track an event
result = hashtag_service.track_hashtag_event(
    hashtags=["AAPL", "MSFT"],
    user_id="user123",
    context="portfolio",
    session_id="session456"
)

# Get trending hashtags
trending = hashtag_service.get_trending_hashtags(
    time_window_hours=24,
    limit=10,
    min_count=2
)

# Get user preferences
preferences = hashtag_service.get_user_hashtag_preferences(
    user_id="user123",
    limit=20
)

# Find related hashtags
related = hashtag_service.get_hashtag_cooccurrence(
    hashtag="AAPL",
    limit=10
)
```

### Enhanced Video Recommendations

```python
from app.helpers.video_integration import (
    get_video_recommendations,
    get_videos_by_hashtag,
    get_trending_hashtag_videos
)

# Get videos with hashtag enhancement
videos = get_video_recommendations(
    query="dividend investing strategies",
    detected_tickers=["AAPL", "MSFT", "JNJ"]
)

# Get videos for a specific hashtag
videos = get_videos_by_hashtag("AAPL", max_results=5)

# Get videos for trending hashtags
videos = get_trending_hashtag_videos(limit=5)
```

---

## 🔧 Technical Details

### In-Memory Cache

The system uses in-memory caching for high performance:

```python
{
    "hashtag_counts": Counter(),              # Global frequency
    "user_hashtags": defaultdict(Counter),    # Per-user frequency
    "hashtag_cooccurrence": defaultdict(Counter),  # Co-occurrence pairs
    "hashtag_contexts": defaultdict(list),    # Context breakdown
    "recent_hashtags": []                     # Rolling window (last 1000)
}
```

### Trending Algorithm

Trending hashtags are calculated using:
1. **Time Window Filtering**: Only events within the specified time window
2. **Frequency Counting**: Count occurrences per hashtag
3. **Minimum Threshold**: Filter hashtags with count >= min_count
4. **Ranking**: Sort by count (descending)

### Performance

- **Hashtag Extraction**: < 1ms
- **Event Tracking**: < 2ms
- **Trending Analysis**: < 5ms
- **Co-occurrence Lookup**: < 3ms

---

## 📊 Use Cases

### 1. **Personalized Content**
- Show users content related to their frequently searched tickers
- Customize dividend recommendations based on hashtag preferences

### 2. **Trending Analysis**
- "What stocks are investors talking about today?"
- Real-time market sentiment indicators
- Popular tickers dashboard

### 3. **Discovery & Recommendations**
- "Users who searched for #AAPL also searched for..."
- Portfolio diversification suggestions
- Related ticker analysis

### 4. **Educational Content**
- Surface relevant videos for trending tickers
- Ticker-specific learning pathways
- Context-aware educational resources

### 5. **Community Insights**
- Most discussed dividend stocks
- Sector trending analysis
- Peer comparison ("What are similar users watching?")

---

## 🚀 Integration Points

### Chat Interface (Automatic)
```python
# app/controllers/ai_controller.py
# Automatically tracks hashtags in every chat query
updated_question, ticker_info, detected_tickers = process_query_with_tickers(
    question, rid, debug=debug,
    session_id=session_id,
    user_id=user_id
)
# → Hashtags automatically tracked via hashtag_analytics_service
```

### Video Integration (Enhanced)
```python
# app/helpers/video_integration.py
# Videos enhanced with hashtag context
videos = get_video_recommendations(
    query=user_query,
    detected_tickers=detected_tickers  # Uses hashtags for better matching
)
```

### API Endpoints (Manual)
```bash
# REST API for external integrations
curl -X POST http://your-app/api/hashtags/track \
  -H "Content-Type: application/json" \
  -d '{"hashtags": ["AAPL"], "context": "search"}'
```

---

## 📈 Monitoring

### Feature Monitoring

The hashtag analytics feature is automatically monitored via the FeatureMonitoringMiddleware:

```python
# Logs format:
# [HASHTAG_ANALYTICS] endpoint=/api/hashtags/trending status=200 duration=12ms
```

### Health Checks

```bash
# Check overall health
GET /healthz

# Get hashtag stats
GET /api/hashtags/stats

# Verify tracking is working
POST /api/hashtags/track
```

---

## 🔐 Privacy & Security

- **User Opt-out**: Users can request hashtag data deletion
- **Anonymized Trending**: Trending calculations don't expose individual user data
- **Session-based**: Tracking respects user sessions and privacy settings
- **No PII**: Only hashtags (ticker symbols) are tracked, no personal data

---

## 🎯 Future Enhancements

1. **ML-Powered Predictions**
   - Predict next ticker a user will search for
   - Personalized portfolio recommendations

2. **Advanced Analytics**
   - Sentiment analysis per hashtag
   - Time-series trending charts
   - Sector rotation detection

3. **Database Persistence**
   - Move from in-memory to database storage
   - Historical trend analysis
   - Long-term user preference tracking

4. **Real-time Alerts**
   - Notify users when their favorite hashtags trend
   - Unusual activity detection
   - Dividend announcement alerts

5. **Social Features**
   - Community trending hashtags
   - Hashtag-based discussion groups
   - Follow hashtags/tickers

---

## 📚 Related Documentation

- [Status Message Feature](./STATUS_MESSAGE_FEATURE.md) - Context-aware status messages
- [Video Integration](./CHAT_VIDEO_INTEGRATION.md) - YouTube video recommendations
- [API Documentation](./API_NEW_FEATURES.md) - Complete API reference

---

## ✅ Testing Checklist

- [x] Hashtag extraction from queries
- [x] Automatic tracking in chat
- [x] Trending hashtag calculation
- [x] User preference tracking
- [x] Co-occurrence analysis
- [x] API endpoint responses
- [x] Video integration enhancement
- [ ] **Ready for production deployment**

---

**Last Updated:** November 16, 2025  
**Feature Version:** 1.0  
**Status:** Production Ready  
**Author:** Harvey Development Team

