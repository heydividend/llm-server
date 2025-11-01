# Harvey's ML Learning & Improvement Capabilities

## Current State: What ML Models Exist

### 1. **External ML Prediction API** (Azure VM on Port 9000)

**Pre-Trained Models (22+ Endpoints):**

| Model | What It Learns From | Training Frequency | Purpose |
|-------|---------------------|-------------------|---------|
| **Dividend Growth Forecasting** | Historical dividend data from Azure SQL | Weekly (soon daily) | Predicts future dividend growth rates |
| **Dividend Cut Risk Prediction** | Company financials, dividend history | Weekly (soon daily) | Predicts probability of dividend cuts |
| **ESG Scoring** | Company sustainability data | Weekly (soon daily) | Environmental/social/governance scores |
| **Anomaly Detection** | Dividend payment patterns | Weekly (soon daily) | Detects unusual dividend behavior |
| **Payout Quality Rating** | Financial metrics, payout ratios | Weekly (soon daily) | Assesses dividend sustainability |
| **Sector Clustering** | Company characteristics | Weekly (soon daily) | Groups similar dividend payers |
| **Portfolio Optimization** | Historical returns, correlations | Weekly (soon daily) | Suggests optimal portfolio mixes |

**Data Sources:**
- ✅ Historical dividend payments (Canonical_Dividends table)
- ✅ Stock prices (vQuotesEnhanced view)
- ✅ Company fundamentals (Securities table)
- ✅ Financial metrics (from database)
- ❌ **NOT user interactions or feedback**

---

### 2. **GPT-4o (OpenAI)** - Harvey's Conversational Brain

**What It Does:**
- Natural language understanding
- Query classification
- SQL generation
- Response formatting
- Conversational flow

**Learning:**
- ❌ **Does NOT learn from Harvey's specific interactions**
- ✅ OpenAI continuously improves GPT-4o globally (not user-specific)
- ❌ No fine-tuning on Harvey's conversation logs

---

### 3. **Query Response Logger** (Currently Passive)

**What It Captures:**
```
logs/
  └── daily_queries/
      └── queries_2025-11-01.txt
  └── daily_conversations/
      └── conversations_2025-11-01.txt
```

**Data Logged:**
- ✅ User queries (every question asked)
- ✅ Harvey responses (full conversation)
- ✅ Metadata (tickers, timestamps, request IDs)
- ✅ Errors (if any)
- ❌ **User feedback (satisfaction, ratings)**
- ❌ **Conversation outcomes (helpful vs. unhelpful)**

**Current Use:**
- Debugging
- Performance monitoring
- Manual review

**Missed Opportunity:**
- 🚫 Not used for model training
- 🚫 Not used for response quality improvement
- 🚫 Not used for learning user preferences

---

## What's Missing: User Feedback Learning Loop

### **The Gap:**

```
Current Flow:
User Question → Harvey Answer → [END]
                                 ↑
                          No feedback captured
                          No learning happens
```

**What Should Happen:**
```
User Question → Harvey Answer → User Feedback → Training Data → Model Improvement
                    ↓                                                    ↑
                    └──────────── Continuous Learning Loop ────────────┘
```

---

## Proposed: Feedback-Driven Learning System

### **Phase 1: Feedback Collection** (Immediate)

Add feedback mechanisms to every Harvey response:

```json
{
  "response": "Your portfolio has...",
  "response_id": "resp_abc123",
  "feedback_options": {
    "thumbs_up": "/v1/feedback/resp_abc123/positive",
    "thumbs_down": "/v1/feedback/resp_abc123/negative",
    "rating": "/v1/feedback/resp_abc123/rating/{1-5}"
  }
}
```

**Capture:**
- ✅ Thumbs up/down on responses
- ✅ 1-5 star ratings
- ✅ Specific issue tags (inaccurate, incomplete, confusing, perfect)
- ✅ Follow-up questions (indicates incomplete answer)
- ✅ User corrections (when Harvey gets something wrong)

---

### **Phase 2: Conversation Quality Database** (Week 1)

**New Database Tables:**

```sql
-- Store feedback on Harvey responses
CREATE TABLE conversation_feedback (
    feedback_id VARCHAR(50) PRIMARY KEY,
    request_id VARCHAR(50) NOT NULL,
    session_id VARCHAR(50),
    conversation_id VARCHAR(50),
    
    -- Feedback data
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    sentiment VARCHAR(20), -- 'positive', 'negative', 'neutral'
    feedback_tags TEXT[], -- ['accurate', 'helpful', 'fast', etc.]
    user_comment TEXT,
    
    -- Context
    user_query TEXT NOT NULL,
    harvey_response TEXT NOT NULL,
    response_metadata JSONB, -- tickers, ML predictions used, etc.
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    user_ip VARCHAR(50),
    session_duration_sec INTEGER
);

-- Track response patterns that work well
CREATE TABLE successful_response_patterns (
    pattern_id VARCHAR(50) PRIMARY KEY,
    query_type VARCHAR(100), -- 'dividend_history', 'portfolio_analysis', etc.
    
    -- Pattern data
    avg_rating DECIMAL(3,2),
    positive_feedback_count INTEGER DEFAULT 0,
    total_responses INTEGER DEFAULT 0,
    
    -- What makes this pattern successful
    key_features JSONB, -- {'includes_ml_predictions': true, 'table_format': true}
    example_queries TEXT[],
    example_responses TEXT[],
    
    -- Metadata
    last_updated TIMESTAMP DEFAULT NOW()
);
```

---

### **Phase 3: GPT-4o Fine-Tuning** (Month 1-2)

**Use Logged Conversations to Fine-Tune:**

```python
# Prepare training data from successful conversations
SELECT 
    cf.user_query,
    cf.harvey_response,
    cf.rating,
    cf.sentiment
FROM conversation_feedback cf
WHERE cf.rating >= 4 -- Only high-quality responses
  AND cf.sentiment = 'positive'
  AND cf.created_at > NOW() - INTERVAL '30 days'
ORDER BY cf.rating DESC
LIMIT 10000;
```

**Fine-Tuning Dataset Format (OpenAI):**
```jsonl
{"messages": [{"role": "user", "content": "What's AAPL's dividend history?"}, {"role": "assistant", "content": "**AAPL Dividend History:**\n\n| Date | Amount | Yield |\n..."}]}
{"messages": [{"role": "user", "content": "Analyze my portfolio"}, {"role": "assistant", "content": "**Portfolio Analysis (12 holdings):**\n..."}]}
```

**Benefits:**
- ✅ Harvey learns YOUR users' preferred response style
- ✅ Improves answer quality for common queries
- ✅ Reduces hallucinations (learns from correct responses)
- ✅ Faster, more relevant responses

**Cost:**
- ~$200-500 for fine-tuning (one-time)
- ~10-20% premium on API calls vs base GPT-4o

---

### **Phase 4: Reinforcement Learning from Human Feedback (RLHF)** (Month 3-6)

**Advanced Learning System:**

```
1. Harvey generates multiple response candidates
2. Users rate which response is best
3. Reward model learns user preferences
4. Policy model optimizes for high-rated responses
```

**Use Cases:**
- Portfolio recommendations (learn which suggestions users act on)
- Stock picks (track which tickers users add to watchlists)
- Income ladders (learn which income strategies users prefer)

---

### **Phase 5: Personalized User Models** (Month 6+)

**Per-User Learning:**

```python
# Track individual user preferences
user_preferences = {
    "user_id": "user_123",
    "preferred_response_length": "detailed", # vs "concise"
    "favorite_features": ["ml_predictions", "charts", "tax_tips"],
    "risk_tolerance": "moderate",
    "portfolio_style": "dividend_growth", # vs "high_yield"
    "communication_style": "professional" # vs "casual"
}
```

**Adaptive Responses:**
```python
if user_prefers_detailed:
    include_ml_predictions()
    include_tax_analysis()
    include_sector_breakdown()
else:
    show_summary_only()
```

---

## Implementation Roadmap

### **✅ Phase 0: Current State (Already Done)**
- [x] QueryResponseLogger capturing conversations
- [x] ML API with dividend prediction models
- [x] Daily training pipeline (soon)
- [x] Conversation memory system

### **🚀 Phase 1: Basic Feedback (Week 1)**
- [ ] Add feedback endpoints to FastAPI
- [ ] Create `conversation_feedback` table
- [ ] Add thumbs up/down to responses
- [ ] Log feedback to database

### **📊 Phase 2: Analytics & Patterns (Week 2-3)**
- [ ] Analyze feedback data
- [ ] Identify successful response patterns
- [ ] Create dashboards for feedback metrics
- [ ] Generate training datasets

### **🤖 Phase 3: GPT-4o Fine-Tuning (Month 1-2)**
- [ ] Prepare fine-tuning dataset (10k+ examples)
- [ ] Fine-tune GPT-4o on Harvey conversations
- [ ] A/B test fine-tuned vs base model
- [ ] Deploy fine-tuned model if performance improves

### **🎯 Phase 4: RLHF (Month 3-6)**
- [ ] Implement reward model training
- [ ] Generate multiple response candidates
- [ ] Collect comparison feedback
- [ ] Train policy model on preferences

### **👤 Phase 5: Personalization (Month 6+)**
- [ ] Track per-user preferences
- [ ] Implement adaptive response system
- [ ] A/B test personalized vs standard responses
- [ ] Roll out to all users

---

## Quick Win: Add Feedback Today

### **Minimal Implementation (30 minutes):**

```python
# Add to main.py
@app.post("/v1/feedback/{response_id}/{sentiment}")
async def record_feedback(
    response_id: str,
    sentiment: str,  # 'positive' or 'negative'
    rating: Optional[int] = None,
    comment: Optional[str] = None
):
    # Log to file (quick start)
    feedback_data = {
        "response_id": response_id,
        "sentiment": sentiment,
        "rating": rating,
        "comment": comment,
        "timestamp": datetime.now().isoformat()
    }
    
    with open("logs/feedback.jsonl", "a") as f:
        f.write(json.dumps(feedback_data) + "\n")
    
    return {"success": True, "message": "Feedback recorded"}
```

**Start collecting data immediately, even without database!**

---

## Summary: Current vs Ideal State

| Capability | Current State | Ideal State |
|-----------|---------------|-------------|
| **ML Models** | ✅ Trained on financial data | ✅ + User feedback |
| **Conversation Logging** | ✅ Passive logs | ✅ + Feedback labels |
| **GPT-4o** | ❌ Base model | ✅ Fine-tuned on Harvey data |
| **User Preferences** | ❌ Not tracked | ✅ Personalized per user |
| **Response Quality** | ❌ No measurement | ✅ Metrics & A/B testing |
| **Continuous Learning** | ❌ Static responses | ✅ Improves daily |

---

## Bottom Line

**Current Answer:**  
Harvey's ML models **learn from financial data** (dividends, prices, companies) but **NOT from user interactions**.

**Recommendation:**  
Implement a **feedback collection system** (Phase 1) **immediately** to start capturing data. Then:
1. Week 1: Add thumbs up/down buttons
2. Month 1: Analyze feedback patterns
3. Month 2: Fine-tune GPT-4o on successful conversations
4. Month 3+: Advanced RLHF and personalization

**ROI:**
- **Better responses** → Higher user satisfaction
- **Fewer errors** → Reduced support tickets
- **Personalization** → Increased engagement
- **Competitive advantage** → Harvey gets smarter while competitors stay static

**The models exist, the logs exist, we just need to close the feedback loop!** 🚀
