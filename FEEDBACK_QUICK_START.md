# Harvey Feedback System - Quick Start Guide

**Important:** Harvey deploys to **Azure VM** in production. Replit is only for development. See `DEPLOYMENT.md` for full deployment instructions.

## ✅ What's Been Implemented

The complete feedback-driven learning system is now live in Harvey! Here's what you have:

### 📊 Feedback Collection
- **Thumbs Up/Down:** Simple sentiment feedback
- **1-5 Star Ratings:** Detailed quality ratings
- **User Comments:** Capture specific feedback
- **Automatic Context:** Tracks query, response, session, and metadata

### 📈 Analytics Dashboard
- **Overall Metrics:** Total feedback, avg rating, success rate
- **Performance Analysis:** Top/bottom performing query types
- **Trend Tracking:** Daily feedback trends over time
- **Improvement Suggestions:** AI-generated recommendations

### 🤖 GPT-4o Fine-Tuning Pipeline
- **Training Data Export:** High-quality examples in OpenAI format
- **Quality Filtering:** Automatically selects 4-5 star responses
- **Batch Management:** Track which data has been used

---

## 🚀 Setup (5 Minutes)

### Step 1: Create Database Tables

Run this SQL on your Azure SQL Server:

```bash
# Via Azure Portal Query Editor
# Or via sqlcmd:
sqlcmd -S $SQLSERVER_HOST -d $SQLSERVER_DB -U $SQLSERVER_USER -P $SQLSERVER_PASSWORD -i app/database/feedback_schema.sql
```

This creates 4 tables:
- `conversation_feedback` - User feedback
- `successful_response_patterns` - Analytics
- `user_preferences` - Personalization (future)
- `gpt_training_data` - Fine-tuning dataset

### Step 2: Test the API

```bash
# Test feedback submission
curl -X POST http://your-harvey-url/v1/feedback/test123/positive

# View dashboard
curl http://your-harvey-url/v1/feedback/analytics/dashboard?days=7
```

### Step 3: Add Frontend Integration

Add to your Next.js chat component:

```javascript
// After receiving Harvey response
async function submitFeedback(responseId, sentiment) {
  await fetch(`/v1/feedback/${responseId}/${sentiment}`, {
    method: 'POST'
  });
}

// In your UI
<div className="feedback-buttons">
  <button onClick={() => submitFeedback(response.response_id, 'positive')}>
    👍 Helpful
  </button>
  <button onClick={() => submitFeedback(response.response_id, 'negative')}>
    👎 Not Helpful
  </button>
</div>
```

---

## 📍 API Endpoints

### Submit Feedback
```bash
# Quick thumbs up/down
POST /v1/feedback/{response_id}/positive
POST /v1/feedback/{response_id}/negative

# Detailed feedback with rating
POST /v1/feedback
{
  "response_id": "resp_abc123",
  "sentiment": "positive",
  "rating": 5,
  "comment": "Perfect analysis!"
}
```

### View Analytics
```bash
# Dashboard overview
GET /v1/feedback/analytics/dashboard?days=7

# Trends over time
GET /v1/feedback/analytics/trends?days=30

# Response patterns
GET /v1/feedback/analytics/patterns?min_responses=10
```

### Export Training Data
```bash
# Get high-quality examples for GPT-4o fine-tuning
GET /v1/feedback/training-data/export?limit=1000&min_quality=0.8
```

---

## 📊 Dashboard Example

```json
{
  "overall": {
    "total_feedback": 150,
    "avg_rating": 4.2,
    "success_rate": 80.0
  },
  "top_performers": [
    {
      "query_type": "dividend_history",
      "avg_rating": 4.8,
      "success_rate": 95.0
    }
  ],
  "training_data": {
    "high_quality_count": 200,
    "ready_for_finetuning": false
  },
  "improvement_suggestions": [
    {
      "priority": "high",
      "recommendation": "You have 200 high-quality examples - keep collecting to reach 1000!"
    }
  ]
}
```

---

## 🔄 Continuous Improvement Workflow

### Week 1-4: Collect Feedback
- **Goal:** Reach 1,000+ high-quality examples
- **Action:** Encourage users to rate responses
- **Monitor:** `/v1/feedback/analytics/dashboard`

### Month 2: First Fine-Tuning
1. Export training data: `/v1/feedback/training-data/export?limit=5000`
2. Convert to JSONL format
3. Upload to OpenAI
4. Create fine-tuning job
5. Test and deploy

### Month 3+: Monthly Cycles
- Export new high-quality examples
- Fine-tune new model version
- A/B test vs previous version
- Deploy best-performing model

---

## 🎯 Success Metrics

### Data Collection Phase
✅ **Target:** 1,000+ high-quality examples (4-5 star ratings)  
✅ **Check:** `/v1/feedback/analytics/dashboard` → `training_data.high_quality_count`

### Model Improvement Phase
✅ **Target:** Avg rating improves by ≥0.3 points  
✅ **Check:** Compare avg_rating before/after fine-tuning

### Production Phase
✅ **Target:** 85%+ success rate  
✅ **Check:** `/v1/feedback/summary` → `success_rate`

---

## 🔧 Troubleshooting

### "Feedback tables may not exist"
- Run `app/database/feedback_schema.sql` on your Azure SQL Server
- Verify with: `SELECT TOP 1 * FROM conversation_feedback`

### Analytics queries failing
- All SQL is Azure SQL Server compatible
- Uses DATEADD, TOP, BIT types (not PostgreSQL syntax)

### No training data showing
- Users need to rate responses 4-5 stars
- Check: `SELECT COUNT(*) FROM gpt_training_data WHERE is_high_quality = 1`

---

## 📚 Full Documentation

- **Complete Guide:** `FEEDBACK_SYSTEM_GUIDE.md`
- **ML Capabilities:** `HARVEY_ML_LEARNING_CAPABILITIES.md`
- **Database Schema:** `app/database/feedback_schema.sql`

---

## 🎉 Next Steps

1. **Today:** Run feedback_schema.sql
2. **This Week:** Add feedback buttons to frontend
3. **This Month:** Collect 1,000+ examples
4. **Month 2:** First GPT-4o fine-tuning

**The feedback system is production-ready and Azure SQL Server compatible! 🚀**
