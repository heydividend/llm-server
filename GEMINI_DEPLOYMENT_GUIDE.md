# Gemini-Enhanced Harvey Intelligence System - Deployment Guide

## 🎯 Overview

This deployment adds **4 major Gemini 2.5 Pro capabilities** to Harvey AI:

1. **Training Data Generator** - Generate 500+ synthetic training questions
2. **Expanded AI Routing** - 6 new query types routed to Gemini  
3. **Continuous Learning Pipeline** - RLHF from user feedback
4. **ML Model Evaluator** - Cross-validate predictions with explanations

---

## 📦 What's Included

### New Services (13 files):
- `app/services/gemini_client.py` - Shared Gemini API client
- `app/services/gemini_training_generator.py` - Training data generator
- `app/services/gemini_query_handler.py` - Query routing handler
- `app/services/feedback_etl_service.py` - Feedback extraction
- `app/services/gemini_feedback_analyzer.py` - Feedback analysis
- `app/services/rlhf_dataset_builder.py` - Fine-tuning datasets
- `app/services/continuous_learning_service.py` - Learning orchestrator
- `app/services/gemini_ml_evaluator.py` - ML model evaluation

### CLI Tools (3 scripts):
- `scripts/generate_training_data.py` - Generate training questions
- `scripts/generate_learning_data.py` - Analyze feedback & create datasets
- `scripts/evaluate_ml_predictions.py` - Evaluate ML predictions

### Modified Files (3 files):
- `app/core/model_router.py` - Added 6 new query types
- `app/controllers/ai_controller.py` - Integrated Gemini routing
- `app/services/training_ingestion_service.py` - Gemini training integration

### Database Schema:
- `app/config/features_schema.py` - 4 new tables already defined:
  * `feedback_labels` - Gemini-analyzed feedback
  * `fine_tuning_samples` - RLHF training data
  * `learning_metrics` - Learning trends
  * `ml_evaluation_audit` - Model evaluation audit trail

---

## 🚀 Deployment Steps (Azure VM)

### Step 1: Pull Latest Code

```bash
# SSH to Azure VM
ssh azureuser@20.81.210.213

# Navigate to Harvey directory
cd /home/azureuser/harvey

# Pull latest changes from git
git pull origin main
```

### Step 2: Run Deployment Script

```bash
# Make deployment script executable
chmod +x deploy_gemini_enhancements.sh

# Run deployment (this will install packages and create database tables)
./deploy_gemini_enhancements.sh
```

**What the script does:**
1. Activates conda llm environment
2. Installs `google-generativeai==0.8.3`
3. Creates 4 new database tables
4. Restarts Harvey backend service
5. Verifies installation

### Step 3: Verify Deployment

```bash
# Check Harvey backend status
sudo systemctl status harvey-backend

# View recent logs
sudo journalctl -u harvey-backend -n 50 --no-pager

# Check if GEMINI_API_KEY is available
echo $GEMINI_API_KEY
```

---

## 🧪 Testing the Gemini Features

### Test 1: Training Data Generator

```bash
cd /home/azureuser/harvey

# Generate 5 dividend analysis questions
python scripts/generate_training_data.py --category dividend_analysis --count 5

# Generate across all categories
python scripts/generate_training_data.py --count 10 --all-categories --stats
```

Expected output: JSON with generated questions and validation stats

### Test 2: Gemini AI Routing

```bash
# Test dividend sustainability query (should route to Gemini)
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Authorization: Bearer hh_live_X6SPcjPD5jZhTMw69_internal_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Analyze the dividend sustainability of AAPL"}
    ],
    "stream": false
  }'
```

Expected: Response from Gemini with dividend sustainability analysis

### Test 3: Continuous Learning (if you have feedback data)

```bash
# Analyze recent feedback
python scripts/generate_learning_data.py --analyze-feedback --days 30 --limit 10

# Show learning insights
python scripts/generate_learning_data.py --show-insights
```

### Test 4: ML Model Evaluator

```bash
# Evaluate dividend scorer prediction for AAPL
python scripts/evaluate_ml_predictions.py --ticker AAPL --model dividend_scorer

# Batch evaluate recent predictions
python scripts/evaluate_ml_predictions.py --batch --days 7 --limit 20
```

---

## 🔑 Environment Variables Required

The deployment script uses these environment variables (already in your Azure VM):

- `GEMINI_API_KEY` - Google Gemini API key ✅
- `SQLSERVER_HOST` - Azure SQL database host ✅
- `SQLSERVER_DB` - Database name ✅
- `SQLSERVER_USER` - Database user ✅
- `SQLSERVER_PASSWORD` - Database password ✅

---

## 📊 Database Tables Created

The deployment creates 4 new tables:

| Table Name | Purpose |
|------------|---------|
| `feedback_labels` | Stores Gemini-analyzed feedback categorization |
| `fine_tuning_samples` | RLHF training pairs for fine-tuning |
| `learning_metrics` | Tracks learning trends over time |
| `ml_evaluation_audit` | Audit trail of ML prediction evaluations |

---

## 🎯 New Query Types Routed to Gemini

Harvey now routes these query types to Gemini 2.5 Pro:

1. **Dividend Sustainability** - Deep fundamental analysis
2. **Risk Assessment** - Portfolio risk & volatility analysis
3. **Portfolio Optimization** - Allocation strategies
4. **Tax Strategy** - Tax-efficient dividend investing
5. **Global Markets** - International dividend analysis
6. **Multimodal Documents** - Analyze PDFs/images

Plus existing: **Charts** and **FX Trading**

---

## 💰 Cost Controls

All Gemini features have built-in cost controls:

- **Rate Limiting:** 60 requests/minute (token bucket)
- **Caching:** 1-hour TTL for repeated queries
- **Daily Limits:** 
  - Training generation: Configurable per run
  - Feedback analysis: Max 100 Gemini calls/run
  - ML evaluation: Max 1000 evaluations/day

---

## 🔍 Monitoring

### Check Gemini Usage

```bash
# View Gemini API calls in Harvey logs
sudo journalctl -u harvey-backend | grep -i gemini | tail -n 50

# Check error rates
sudo journalctl -u harvey-backend | grep -i "gemini.*error" | tail -n 20
```

### Database Queries

```sql
-- Check feedback analysis count
SELECT COUNT(*) FROM feedback_labels;

-- Check fine-tuning samples ready
SELECT COUNT(*) FROM fine_tuning_samples WHERE ready_for_training = 1;

-- View learning metrics
SELECT * FROM learning_metrics ORDER BY period_start DESC;

-- Check ML evaluation audit
SELECT model_name, COUNT(*) as eval_count
FROM ml_evaluation_audit
GROUP BY model_name;
```

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'google.generativeai'"

**Solution:**
```bash
conda activate llm
pip install google-generativeai==0.8.3
sudo systemctl restart harvey-backend
```

### Issue: "Table 'feedback_labels' doesn't exist"

**Solution:**
```bash
# Re-run the database migration part of deployment script
python /home/azureuser/harvey/deploy_gemini_enhancements.sh
```

### Issue: "GEMINI_API_KEY not found"

**Solution:**
```bash
# Check if secret exists
echo $GEMINI_API_KEY

# If not, add to .env file
cd /home/azureuser/harvey
echo "GEMINI_API_KEY=your_key_here" >> .env
```

### Issue: Harvey backend won't start

**Solution:**
```bash
# Check logs for specific error
sudo journalctl -u harvey-backend -n 100 --no-pager

# Check if all dependencies installed
conda activate llm
pip list | grep google-generativeai
```

---

## 📚 Usage Examples

### Generate 50 Training Questions per Category

```bash
python scripts/generate_training_data.py \
  --count 50 \
  --all-categories \
  --output training_questions_500.json \
  --stats
```

### Continuous Learning Weekly Run

```bash
# Full learning cycle: analyze feedback → build datasets → track metrics
python scripts/generate_learning_data.py \
  --full-cycle \
  --days 7 \
  --max-gemini-calls 50
```

### Monthly ML Model Evaluation Report

```bash
# Generate evaluation report for all models
python scripts/evaluate_ml_predictions.py \
  --report \
  --model all \
  --days 30
```

---

## 🎉 Success Indicators

After deployment, you should see:

✅ Harvey backend running without errors
✅ `google-generativeai` package installed
✅ 4 new database tables created
✅ Gemini API key validated
✅ Test queries successfully routed to Gemini
✅ ML training scheduler still running (Sunday 3 AM)

---

## 🔄 Integration with ML Training Scheduler

The Gemini enhancements integrate seamlessly with your existing ML training scheduler:

**Current Schedule:**
- **Payout Rating ML:** Daily 1:00 AM
- **Dividend Calendar ML:** Sunday 2:00 AM
- **ML Training:** Sunday 3:00 AM ← Now uses Gemini-generated training data!

**Optional: Add Gemini Data Generation to Scheduler**

You can schedule Gemini training data generation before the Sunday ML training run:

```bash
# Edit: /etc/systemd/system/heydividend-ml-schedulers.service
# Add before ML training:
ExecStartPre=/home/azureuser/miniconda3/envs/llm/bin/python \
  /home/azureuser/harvey/scripts/generate_training_data.py \
  --count 50 --all-categories --to-database
```

---

## 📞 Support

If you encounter issues:

1. Check Harvey backend logs: `sudo journalctl -u harvey-backend -n 100`
2. Check ML scheduler logs: `sudo journalctl -u heydividend-ml-schedulers -n 100`
3. Verify database connection: Test with any Harvey query
4. Verify Gemini API key: `python -c "import os; print(os.getenv('GEMINI_API_KEY')[:10])"`

---

## 🚀 Next Steps

After successful deployment:

1. **Generate Initial Training Data:** Run training generator to expand from 120 to 500+ questions
2. **Monitor Gemini Routing:** Watch logs to see which queries get routed to Gemini
3. **Enable Continuous Learning:** Schedule weekly feedback analysis runs
4. **Evaluate ML Models:** Run monthly evaluation reports to track model quality

---

**Deployment Date:** November 19, 2025
**Harvey Backend:** FastAPI on port 8001
**Azure VM:** 20.81.210.213
**Status:** ✅ Ready for Production
