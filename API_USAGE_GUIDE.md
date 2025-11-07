# Harvey API - Usage Guide

## 🌐 Base URL
```
http://20.81.210.213
```

---

## ✅ Working Endpoints

### 1. Health Check
```bash
curl http://20.81.210.213/healthz
```
**Response:**
```json
{"ok": true}
```

---

### 2. Chat Completions (Main Endpoint)

**Endpoint:** `POST /v1/chat/completions`

**Format:**
```bash
curl -X POST http://20.81.210.213/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACTUAL_API_KEY" \
  -d '{
    "messages": [
      {"role": "user", "content": "What is AAPL dividend yield?"}
    ],
    "stream": true
  }'
```

**Important:**
- Use `messages` (array) - NOT `message` (single)
- Each message has `role` and `content`
- Replace `YOUR_ACTUAL_API_KEY` with your real HARVEY_AI_API_KEY

**Example with conversation history:**
```bash
curl -X POST http://20.81.210.213/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "messages": [
      {"role": "user", "content": "Tell me about Apple stock"},
      {"role": "assistant", "content": "Apple (AAPL) is a technology company..."},
      {"role": "user", "content": "What is its dividend yield?"}
    ],
    "stream": true
  }'
```

---

### 3. Web Interface

**URL:** `http://20.81.210.213/`

Open this in your browser to access the full chat interface with:
- Real-time streaming responses
- Interactive charts
- PDF export
- Conversation history

---

### 4. Feedback Endpoints

#### Submit Feedback
```bash
# Thumbs up
curl -X POST http://20.81.210.213/v1/feedback/RESPONSE_ID/positive

# Thumbs down
curl -X POST http://20.81.210.213/v1/feedback/RESPONSE_ID/negative

# Detailed feedback
curl -X POST http://20.81.210.213/v1/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "response_id": "abc123",
    "rating": 5,
    "sentiment": "positive",
    "comment": "Great analysis!"
  }'
```

#### View Feedback Analytics
```bash
# Summary
curl http://20.81.210.213/v1/feedback/summary

# Dashboard
curl http://20.81.210.213/v1/feedback/analytics/dashboard

# Trends
curl http://20.81.210.213/v1/feedback/analytics/trends

# Export training data for GPT-4o fine-tuning
curl http://20.81.210.213/v1/feedback/training-data/export
```

**Note:** Feedback endpoints will return errors until you create the feedback tables on Azure SQL (see below).

---

### 5. Portfolio Analysis

```bash
# Upload portfolio file
curl -X POST http://20.81.210.213/v1/portfolio/upload \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@portfolio.csv"

# Supported formats: CSV, Excel, PDF, images
```

---

### 6. ML Schedulers (NEW! 🚀)

#### Check Scheduler Health
```bash
curl http://20.81.210.213/v1/ml-schedulers/health \
  -H "Authorization: Bearer YOUR_API_KEY"
```

#### Get Cached Payout Ratings (A+ to F grades)
```bash
curl -X POST http://20.81.210.213/v1/ml-schedulers/payout-ratings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "symbols": ["AAPL", "MSFT", "JNJ", "O", "SCHD"],
    "force_refresh": false
  }'
```

**Response Example:**
```json
{
  "success": true,
  "ratings": {
    "AAPL": {
      "grade": "A+",
      "score": 92.5,
      "quality": "Excellent",
      "recommendation": "Strong Buy"
    }
  }
}
```

#### Get Dividend Calendar Predictions
```bash
curl -X POST http://20.81.210.213/v1/ml-schedulers/dividend-calendar \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "symbols": ["O", "SCHD", "JEPI"],
    "months_ahead": 6
  }'
```

**Response Example:**
```json
{
  "success": true,
  "predictions": {
    "O": {
      "next_ex_date": "2025-11-15",
      "next_pay_date": "2025-11-30",
      "predicted_amount": 0.265,
      "frequency": "Monthly"
    }
  }
}
```

#### Check Training Status
```bash
curl http://20.81.210.213/v1/ml-schedulers/training-status \
  -H "Authorization: Bearer YOUR_API_KEY"
```

#### Admin Dashboard (Admin API Key Required)
```bash
curl http://20.81.210.213/v1/ml-schedulers/admin/dashboard \
  -H "Authorization: Bearer YOUR_ADMIN_API_KEY"
```

**Key Benefits:**
- ⚡ 10x faster responses from cache
- 📊 Daily payout ratings at 1 AM UTC
- 📅 Weekly dividend calendar updates (Sunday 2 AM)
- 🔄 Automatic self-healing if services fail

---

### 7. Tax Optimization

```bash
curl -X POST http://20.81.210.213/v1/tax/optimize \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "ticker": "AAPL",
    "shares": 100,
    "purchase_price": 150.00
  }'
```

---

### 7. Income Ladder Builder

```bash
curl -X POST http://20.81.210.213/v1/income-ladder/build \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "monthly_income_target": 1000,
    "initial_capital": 50000,
    "risk_tolerance": "moderate"
  }'
```

---

### 8. Alerts

```bash
# Create alert
curl -X POST http://20.81.210.213/v1/alerts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "description": "Alert me when AAPL drops below $150",
    "session_id": "user123"
  }'

# List alerts
curl http://20.81.210.213/v1/alerts/user123 \
  -H "Authorization: Bearer YOUR_API_KEY"
```

---

## ⚠️ Common Errors & Solutions

### Error: `{"detail":"Not Found"}`
**Cause:** Wrong endpoint path  
**Solution:** Use `/v1/chat/completions` not `/v1/chat/stream`

### Error: `{"error":"messages[] required"}`
**Cause:** Using `"message"` instead of `"messages"`  
**Solution:** Change to `"messages": [{"role": "user", "content": "..."}]`

### Error: `{"error":"invalid JSON"}`
**Cause:** Malformed JSON (usually backslashes or quotes)  
**Solution:** Use single quotes for bash, double quotes inside JSON

### Error: Feedback endpoints return error
**Cause:** Feedback tables not created on Azure SQL  
**Solution:** Run `feedback_schema.sql` (see below)

---

## 🗄️ Create Feedback Tables (One-Time Setup)

Your feedback system code is deployed, but the database tables don't exist yet.

### Option 1: Azure Portal Query Editor (Easiest)
1. Go to **Azure Portal** → Your SQL Database → **Query Editor**
2. Open `app/database/feedback_schema.sql` from this project
3. Copy entire contents
4. Paste and click **Run**

### Option 2: Via sqlcmd
```bash
# SSH into your Azure VM
ssh azureuser@20.81.210.213

# Run the schema
sqlcmd -S YOUR_SERVER.database.windows.net \
  -d HeyDividend \
  -U YOUR_USERNAME \
  -P 'YOUR_PASSWORD' \
  -i /opt/harvey-backend/app/database/feedback_schema.sql

# Restart Harvey
sudo systemctl restart harvey-backend
```

### Test Feedback After Creating Tables:
```bash
curl -X POST http://20.81.210.213/v1/feedback/test123/positive
curl http://20.81.210.213/v1/feedback/summary
```

---

## 📊 Full API Documentation

For complete API documentation with all parameters, visit:
```
http://20.81.210.213/docs
```

This shows the interactive Swagger UI with all available endpoints.

---

## 🚀 Quick Start Example

```bash
# 1. Test health
curl http://20.81.210.213/healthz

# 2. Ask about a dividend stock
curl -X POST http://20.81.210.213/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "messages": [
      {"role": "user", "content": "What is the dividend yield and payout ratio for Johnson & Johnson (JNJ)?"}
    ],
    "stream": true
  }'

# 3. Open web UI in browser
# http://20.81.210.213/
```

---

## 🔑 Finding Your API Key

Your `HARVEY_AI_API_KEY` is the value you set when deploying. It's stored in:
- Azure VM: `/etc/systemd/system/harvey-backend.service`
- Or check your deployment script: `deploy/AZURE_RUN_COMMAND_DEPLOY.sh`

To view it on the VM:
```bash
ssh azureuser@20.81.210.213
sudo cat /etc/systemd/system/harvey-backend.service | grep HARVEY_AI_API_KEY
```

---

## 📝 Response Format

Harvey returns **streaming responses** by default. Each chunk contains:
```
data: {"token": "Apple", "type": "text"}
data: {"token": " stock", "type": "text"}
...
data: [DONE]
```

For non-streaming:
```json
{
  "messages": [...],
  "stream": false
}
```

---

## 💡 Tips

1. **Use the Web UI** (`http://20.81.210.213/`) for the best experience
2. **API is for integration** with your own frontend or scripts
3. **Streaming is recommended** for real-time responses
4. **Create feedback tables** to enable the learning system
5. **Check `/docs`** for complete API reference

---

## 🆘 Need Help?

**Check logs on Azure VM:**
```bash
ssh azureuser@20.81.210.213
sudo journalctl -u harvey-backend -n 100 --no-pager
```

**Test local endpoints on VM:**
```bash
curl http://localhost:8000/healthz
```

**Verify database connection:**
```bash
sqlcmd -S $SQLSERVER_HOST -d $SQLSERVER_DB -U $SQLSERVER_USER -P $SQLSERVER_PASSWORD -Q "SELECT 1"
```
