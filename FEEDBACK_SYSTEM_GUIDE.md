# Harvey Feedback & Learning System - Complete Guide

## Overview

Harvey now includes a comprehensive feedback-driven learning system that enables continuous improvement through user feedback collection, analytics, and GPT-4o fine-tuning capabilities.

---

## 🚀 Quick Start

### 1. Create Database Tables

Run the SQL schema to create feedback tables:

```bash
# Via sqlcmd (Azure SQL Server)
sqlcmd -S $SQLSERVER_HOST -d $SQLSERVER_DB -U $SQLSERVER_USER -P $SQLSERVER_PASSWORD -i app/database/feedback_schema.sql

# Via Azure Portal Query Editor (recommended)
# 1. Go to Azure Portal → Your SQL Database → Query Editor
# 2. Paste contents of app/database/feedback_schema.sql
# 3. Click "Run"
```

**Important:** This schema is designed for **Azure SQL Server** and uses SQL Server-specific syntax (DATEADD, BIT, DATETIME, GO batches). It is **not** compatible with PostgreSQL.

### 2. Test Feedback Collection

```bash
# Submit thumbs up
curl -X POST http://localhost:5000/v1/feedback/resp_123/positive

# Submit rating
curl -X POST http://localhost:5000/v1/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "response_id": "resp_abc123",
    "sentiment": "positive",
    "rating": 5,
    "comment": "Perfect dividend analysis!",
    "tags": ["accurate", "helpful", "fast"]
  }'
```

### 3. View Analytics

```bash
# Dashboard overview
curl http://localhost:5000/v1/feedback/analytics/dashboard?days=7

# Feedback trends
curl http://localhost:5000/v1/feedback/analytics/trends?days=30

# Response patterns
curl http://localhost:5000/v1/feedback/analytics/patterns
```

---

## 📊 API Endpoints

### Feedback Collection

#### `POST /v1/feedback` - Full Feedback Submission

**Request:**
```json
{
  "response_id": "resp_abc123",
  "sentiment": "positive",  // or "negative", "neutral"
  "rating": 5,              // 1-5 stars (optional)
  "comment": "Great analysis!",  // optional
  "tags": ["accurate", "helpful", "fast"],  // optional
  
  // Optional context (usually auto-populated by system)
  "user_query": "What's AAPL's dividend history?",
  "harvey_response": "AAPL has paid...",
  "query_type": "dividend_history",
  "action_taken": "sql_query"
}
```

**Response:**
```json
{
  "success": true,
  "feedback_id": "fb_a1b2c3d4e5f6",
  "message": "Feedback recorded successfully"
}
```

#### `POST /v1/feedback/{response_id}/{sentiment}` - Quick Feedback

**Usage:**
```bash
# Thumbs up
POST /v1/feedback/resp_123/positive

# Thumbs down
POST /v1/feedback/resp_123/negative
```

---

### Analytics Endpoints

#### `GET /v1/feedback/summary?days=7` - Feedback Summary

**Response:**
```json
{
  "total_feedback": 150,
  "avg_rating": 4.2,
  "positive_count": 120,
  "negative_count": 20,
  "neutral_count": 10,
  "success_rate": 80.0
}
```

#### `GET /v1/feedback/analytics/dashboard?days=7` - Dashboard Metrics

**Response:**
```json
{
  "success": true,
  "period_days": 7,
  "overall": {
    "total_feedback": 150,
    "avg_rating": 4.2,
    "success_rate": 80.0,
    "unique_sessions": 45,
    "unique_responses": 100
  },
  "top_performers": [
    {
      "query_type": "dividend_history",
      "action_taken": "sql_query",
      "response_count": 50,
      "avg_rating": 4.8,
      "success_rate": 95.0
    }
  ],
  "bottom_performers": [
    {
      "query_type": "complex_analysis",
      "action_taken": "web_search",
      "response_count": 15,
      "avg_rating": 2.5,
      "failure_rate": 60.0
    }
  ],
  "training_data": {
    "total_examples": 500,
    "high_quality_count": 200,
    "unused_count": 180,
    "avg_quality_score": 0.84,
    "ready_for_finetuning": false  // true when >= 1000 examples
  },
  "improvement_suggestions": [
    {
      "priority": "high",
      "category": "low_rating",
      "query_type": "complex_analysis",
      "recommendation": "Improve complex_analysis responses..."
    }
  ]
}
```

#### `GET /v1/feedback/analytics/trends?days=30` - Feedback Trends

**Response:**
```json
{
  "success": true,
  "period_days": 30,
  "daily_trends": [
    {
      "date": "2025-11-01",
      "feedback_count": 25,
      "avg_rating": 4.3,
      "positive": 20,
      "negative": 3,
      "success_rate": 80.0
    }
  ]
}
```

#### `GET /v1/feedback/analytics/patterns?min_responses=10` - Response Patterns

**Response:**
```json
{
  "success": true,
  "count": 12,
  "patterns": [
    {
      "pattern_id": "dividend_history_sql_query",
      "query_type": "dividend_history",
      "action_type": "sql_query",
      "avg_rating": 4.8,
      "positive_feedback_count": 48,
      "negative_feedback_count": 2,
      "total_responses": 50,
      "success_rate": 96.0
    }
  ]
}
```

#### `GET /v1/feedback/training-data/export?limit=1000&min_quality=0.8` - Export Training Data

**Response:**
```json
{
  "success": true,
  "count": 250,
  "format": "openai_finetuning",
  "training_data": [
    {
      "messages": [
        {"role": "user", "content": "What's AAPL's dividend history?"},
        {"role": "assistant", "content": "**AAPL Dividend History:**\n\n..."}
      ],
      "metadata": {
        "quality_score": 1.0,
        "query_type": "dividend_history"
      }
    }
  ]
}
```

---

## 🤖 GPT-4o Fine-Tuning Process

### Phase 1: Data Collection (Weeks 1-4)

**Goal:** Collect 1,000+ high-quality training examples

1. **Enable Feedback in Frontend:**
   ```javascript
   // Add to your Next.js chat component
   <div className="feedback-buttons">
     <button onClick={() => submitFeedback(responseId, 'positive')}>
       👍 Helpful
     </button>
     <button onClick={() => submitFeedback(responseId, 'negative')}>
       👎 Not Helpful
     </button>
     <StarRating onRate={(rating) => submitRating(responseId, rating)} />
   </div>
   ```

2. **Monitor Progress:**
   ```bash
   # Check training data count
   curl http://localhost:5000/v1/feedback/analytics/dashboard | jq '.training_data'
   ```

3. **Target Metrics:**
   - Minimum: 1,000 high-quality examples
   - Recommended: 3,000-5,000 examples
   - Quality score: ≥ 0.8 (4+ star ratings)

---

### Phase 2: Data Export & Preparation (Day 1)

1. **Export Training Data:**
   ```bash
   curl "http://localhost:5000/v1/feedback/training-data/export?limit=5000&min_quality=0.8" \
     > training_data.json
   ```

2. **Convert to JSONL Format:**
   ```bash
   # Python script to convert to JSONL
   python3 << 'EOF'
   import json
   
   with open('training_data.json', 'r') as f:
       data = json.load(f)
   
   with open('training_data.jsonl', 'w') as f:
       for example in data['training_data']:
           f.write(json.dumps(example) + '\n')
   
   print(f"Exported {len(data['training_data'])} examples to training_data.jsonl")
   EOF
   ```

3. **Validate Format:**
   ```bash
   # Check first 3 examples
   head -n 3 training_data.jsonl | jq .
   ```

---

### Phase 3: OpenAI Fine-Tuning (Days 2-3)

1. **Upload Training File:**
   ```bash
   # Install OpenAI CLI
   pip install openai
   
   # Set API key
   export OPENAI_API_KEY="sk-..."
   
   # Upload file
   openai api files.create \
     -f training_data.jsonl \
     -p fine-tune
   
   # Note the file ID: file-abc123...
   ```

2. **Create Fine-Tuning Job:**
   ```bash
   openai api fine_tuning.jobs.create \
     -t file-abc123 \
     -m gpt-4o-2024-08-06 \
     --suffix "harvey-v1"
   
   # Note the job ID: ftjob-xyz789...
   ```

3. **Monitor Progress:**
   ```bash
   # Check status
   openai api fine_tuning.jobs.retrieve -i ftjob-xyz789
   
   # Stream events
   openai api fine_tuning.jobs.follow -i ftjob-xyz789
   ```

4. **Training Time:**
   - 1,000 examples: ~1-2 hours
   - 5,000 examples: ~4-6 hours
   - 10,000 examples: ~8-12 hours

---

### Phase 4: Testing & Deployment (Day 4-7)

1. **Get Fine-Tuned Model ID:**
   ```bash
   openai api fine_tuning.jobs.retrieve -i ftjob-xyz789 | jq -r '.fine_tuned_model'
   # Example: ft:gpt-4o-2024-08-06:harvey:harvey-v1:abc123
   ```

2. **A/B Test Setup:**
   ```python
   # Update Harvey's AI controller
   FINE_TUNED_MODEL = "ft:gpt-4o-2024-08-06:harvey:harvey-v1:abc123"
   BASE_MODEL = "gpt-4o"
   
   # Route 50% traffic to fine-tuned model
   import random
   model_to_use = FINE_TUNED_MODEL if random.random() < 0.5 else BASE_MODEL
   ```

3. **Compare Performance:**
   ```bash
   # After 1 week of A/B testing
   curl "http://localhost:5000/v1/feedback/analytics/dashboard?days=7" | \
     jq '.overall.avg_rating'
   
   # Compare:
   # - Base model avg rating
   # - Fine-tuned model avg rating
   # - Response quality improvements
   ```

4. **Deploy to Production:**
   ```python
   # If fine-tuned model performs better (higher avg rating, lower negative feedback)
   DEFAULT_MODEL = "ft:gpt-4o-2024-08-06:harvey:harvey-v1:abc123"
   ```

---

## 📈 Continuous Improvement Workflow

### Weekly Review (Every Monday)

```bash
# 1. Check last week's feedback
curl "http://localhost:5000/v1/feedback/analytics/dashboard?days=7"

# 2. Review improvement suggestions
curl "http://localhost:5000/v1/feedback/analytics/dashboard" | \
  jq '.improvement_suggestions'

# 3. Identify low-performing query types
curl "http://localhost:5000/v1/feedback/analytics/dashboard" | \
  jq '.bottom_performers'

# 4. Address issues before next fine-tuning cycle
```

### Monthly Fine-Tuning (Every 1st of Month)

```bash
# 1. Export new high-quality examples from last month
curl "http://localhost:5000/v1/feedback/training-data/export?limit=10000" \
  > new_training_data.json

# 2. Merge with existing training data
python merge_training_data.py

# 3. Create new fine-tuning job
openai api fine_tuning.jobs.create \
  -t file-new123 \
  -m ft:gpt-4o-2024-08-06:harvey:harvey-v1:abc123 \
  --suffix "harvey-v2"

# 4. Test and deploy v2
```

---

## 💾 Database Schema

### Tables Created

1. **conversation_feedback** - User feedback on responses
2. **successful_response_patterns** - Analytics on response patterns
3. **user_preferences** - Personalization data (future use)
4. **gpt_training_data** - High-quality examples for fine-tuning

### Key Indexes

- `idx_feedback_response_id` - Fast lookup by response
- `idx_feedback_rating` - Filter by rating
- `idx_feedback_query_type` - Group by query type
- `idx_training_quality` - Find high-quality examples

---

## 🎯 Success Metrics

### Week 1-4: Data Collection
- ✅ **Target:** 1,000+ high-quality examples
- ✅ **Metric:** `training_data.high_quality_count >= 1000`

### Month 2: First Fine-Tuning
- ✅ **Target:** Deploy fine-tuned model
- ✅ **Metric:** Avg rating increases by ≥0.3 points

### Month 3: Continuous Improvement
- ✅ **Target:** Monthly fine-tuning cycle established
- ✅ **Metric:** Success rate ≥ 85%

### Month 6: Personalization
- ✅ **Target:** Per-user response adaptation
- ✅ **Metric:** User retention increases by 20%

---

## 🔧 Integration with Harvey Chat

### Automatic Response ID Generation

Every Harvey response now includes a unique `response_id` for feedback tracking:

```python
# In ai_controller.py (automatically added)
response_id = f"resp_{uuid.uuid4().hex[:12]}"

# Response includes feedback metadata
{
  "response": "Your dividend analysis...",
  "response_id": "resp_abc123",
  "feedback_url": {
    "thumbs_up": "/v1/feedback/resp_abc123/positive",
    "thumbs_down": "/v1/feedback/resp_abc123/negative"
  }
}
```

---

## 📊 Analytics Dashboard Example

**Sample Query:**
```bash
curl http://localhost:5000/v1/feedback/analytics/dashboard?days=30
```

**Sample Output:**
```json
{
  "overall": {
    "total_feedback": 450,
    "avg_rating": 4.1,
    "success_rate": 78.2,
    "unique_sessions": 120
  },
  "top_performers": [
    {
      "query_type": "dividend_history",
      "avg_rating": 4.8,
      "success_rate": 95.0
    },
    {
      "query_type": "ml_predictions",
      "avg_rating": 4.6,
      "success_rate": 92.0
    }
  ],
  "bottom_performers": [
    {
      "query_type": "portfolio_analysis",
      "avg_rating": 2.8,
      "failure_rate": 45.0
    }
  ],
  "training_data": {
    "high_quality_count": 1250,
    "ready_for_finetuning": true
  },
  "improvement_suggestions": [
    {
      "priority": "high",
      "category": "training_ready",
      "recommendation": "1250 high-quality examples ready for GPT-4o fine-tuning!"
    }
  ]
}
```

---

## 🚀 Next Steps

1. **Immediate (Today):**
   - ✅ Run feedback_schema.sql to create tables
   - ✅ Test feedback endpoints
   - ✅ Start collecting feedback

2. **Week 1:**
   - Add feedback buttons to frontend
   - Monitor feedback collection
   - Review analytics daily

3. **Month 1:**
   - Reach 1,000+ training examples
   - Export training data
   - Submit first fine-tuning job

4. **Month 2+:**
   - Deploy fine-tuned model
   - Establish monthly fine-tuning cycle
   - Implement personalization features

---

## 💡 Best Practices

1. **Feedback Collection:**
   - Make feedback buttons prominent
   - Offer both quick (thumbs) and detailed (ratings + comments) options
   - Incentivize feedback (e.g., "Help Harvey improve!")

2. **Data Quality:**
   - Only use 4-5 star ratings for training
   - Review and validate training examples
   - Remove duplicate or low-quality examples

3. **Fine-Tuning:**
   - Start with smaller batches (1,000-3,000 examples)
   - A/B test before full deployment
   - Monitor performance metrics closely

4. **Continuous Improvement:**
   - Review analytics weekly
   - Address low-performing query types
   - Fine-tune monthly for best results

---

## 🤝 Support

For questions or issues:
1. Check analytics dashboard: `/v1/feedback/analytics/dashboard`
2. Review feedback logs: `logs/daily_conversations/`
3. Export training data: `/v1/feedback/training-data/export`

**The feedback system is now live and ready to make Harvey smarter every day!** 🚀
