# Harvey Multi-Model Training System - Azure VM Deployment Guide

**Date:** November 20, 2025  
**Target VM:** 20.81.210.213 (Azure Ubuntu)  
**Service:** Multi-Model Training Data Generator

---

## 📋 Prerequisites

Before deploying, ensure:

1. ✅ Harvey backend is running on Azure VM
2. ✅ All 4 AI models are configured with API keys:
   - Azure OpenAI (GPT-5, Grok-4, DeepSeek-R1)
   - Google Gemini 2.5 Pro
3. ✅ Azure SQL Database connection is working
4. ✅ Python virtual environment exists at `/home/azureuser/harvey/venv`
5. ✅ Required Python packages installed (see below)

---

## 🚀 Deployment Steps

### Step 1: Copy Files to Azure VM

```bash
# From your local machine (Replit or dev environment)
scp scripts/multi_model_training_generator.py azureuser@20.81.210.213:/home/azureuser/harvey/scripts/
scp azure_vm_setup/systemd/harvey-multi-model-training.service azureuser@20.81.210.213:/tmp/
scp azure_vm_setup/systemd/harvey-multi-model-training.timer azureuser@20.81.210.213:/tmp/
```

### Step 2: SSH into Azure VM

```bash
ssh azureuser@20.81.210.213
```

### Step 3: Install Python Dependencies

```bash
cd /home/azureuser/harvey
source venv/bin/activate

# Install required packages if not already installed
pip install python-dotenv
pip install openai
pip install google-generativeai
pip install pymssql
pip install sqlalchemy

# Verify installation
python -c "import openai, google.generativeai, pymssql; print('All packages installed')"
```

### Step 4: Test Multi-Model Generator (Dry Run)

```bash
# Test with small batch (5 questions per model = 20 total)
python scripts/multi_model_training_generator.py \
  --category dividend_analysis \
  --questions-per-model 5 \
  --output /tmp/test_multi_model.json

# Check output file
cat /tmp/test_multi_model.json | jq '.stats'

# Expected output:
# {
#   "total_questions": 20,
#   "by_model": {
#     "GPT-5": 5,
#     "Grok-4": 5,
#     "DeepSeek-R1": 5,
#     "Gemini-2.5-Pro": 5
#   },
#   ...
# }
```

### Step 5: Install Systemd Service & Timer

```bash
# Copy service files to systemd directory
sudo cp /tmp/harvey-multi-model-training.service /etc/systemd/system/
sudo cp /tmp/harvey-multi-model-training.timer /etc/systemd/system/

# Set correct permissions
sudo chmod 644 /etc/systemd/system/harvey-multi-model-training.service
sudo chmod 644 /etc/systemd/system/harvey-multi-model-training.timer

# Reload systemd to recognize new services
sudo systemctl daemon-reload

# Enable timer (auto-start on boot)
sudo systemctl enable harvey-multi-model-training.timer

# Start timer immediately
sudo systemctl start harvey-multi-model-training.timer
```

### Step 6: Verify Installation

```bash
# Check timer status
sudo systemctl status harvey-multi-model-training.timer

# Expected output:
# ● harvey-multi-model-training.timer - Harvey Multi-Model Training Generator Timer
#      Loaded: loaded (/etc/systemd/system/harvey-multi-model-training.timer; enabled)
#      Active: active (waiting) since ...
#     Trigger: Sun 2025-11-23 05:00:00 UTC

# List next scheduled run
systemctl list-timers harvey-multi-model-training.timer

# Check service status (should be inactive until triggered)
sudo systemctl status harvey-multi-model-training.service
```

### Step 7: Manual Test Run (Optional)

```bash
# Trigger service manually to test before Sunday
sudo systemctl start harvey-multi-model-training.service

# Watch logs in real-time
sudo journalctl -u harvey-multi-model-training.service -f

# Check for errors
sudo journalctl -u harvey-multi-model-training.service --since "5 minutes ago"
```

---

## 📊 Expected Behavior

### Scheduler Timeline

| Time | Scheduler | Purpose |
|------|-----------|---------|
| Daily 1:00 AM | Payout Rating ML | A+/A/B/C dividend safety ratings |
| Sunday 2:00 AM | Dividend Calendar ML | Next dividend payment predictions |
| Sunday 3:00 AM | ML Training | Train 7 core ML models |
| Sunday 4:00 AM | Gemini Training | Generate 100 training questions (Gemini only) |
| **Sunday 5:00 AM** | **Multi-Model Training** | **Generate 800 training questions (all 4 models)** |

### Training Output

**Per Weekly Run:**
- **Total Questions:** 800
- **GPT-5:** 200 questions (complex reasoning, comprehensive analysis)
- **Grok-4:** 200 questions (fast insights, real-time analysis)
- **DeepSeek-R1:** 200 questions (quantitative analysis, mathematical modeling)
- **Gemini 2.5 Pro:** 200 questions (strategic planning, sustainability analysis)

**Categories Covered (8 total):**
1. dividend_analysis
2. income_strategies
3. risk_assessment
4. technical_timing
5. etf_funds
6. tax_optimization
7. quantitative_analysis
8. global_dividends

**Annual Projection:**
- 800 questions/week × 52 weeks = **41,600 questions/year**
- 8x more training data than Gemini-only approach (100/week)

---

## 🔍 Monitoring & Troubleshooting

### Check Logs

```bash
# View last 50 lines
sudo journalctl -u harvey-multi-model-training.service -n 50

# View logs from last run
sudo journalctl -u harvey-multi-model-training.service --since "1 day ago"

# Follow logs in real-time during run
sudo journalctl -u harvey-multi-model-training.service -f
```

### Common Issues & Solutions

#### Issue 1: API Rate Limits

**Symptom:** "Rate limit exceeded" errors

**Solution:**
```bash
# Reduce questions-per-model in service file
sudo nano /etc/systemd/system/harvey-multi-model-training.service

# Change from 25 to 15:
ExecStart=... --questions-per-model 15 ...

sudo systemctl daemon-reload
sudo systemctl restart harvey-multi-model-training.timer
```

#### Issue 2: Database Connection Failures

**Symptom:** "Cannot connect to database" errors

**Solution:**
```bash
# Check environment variables
cat /home/azureuser/harvey/.env | grep SQLSERVER

# Test database connection
cd /home/azureuser/harvey
source venv/bin/activate
python -c "import pymssql; conn = pymssql.connect(...); print('Connected')"
```

#### Issue 3: Missing API Keys

**Symptom:** "API key not found" errors

**Solution:**
```bash
# Verify all API keys exist
cd /home/azureuser/harvey
source venv/bin/activate
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('Azure OpenAI:', os.getenv('AZURE_OPENAI_API_KEY')[:10] if os.getenv('AZURE_OPENAI_API_KEY') else 'MISSING')
print('Gemini:', os.getenv('GEMINI_API_KEY')[:10] if os.getenv('GEMINI_API_KEY') else 'MISSING')
"
```

#### Issue 4: Service Won't Start

**Symptom:** Service fails immediately

**Solution:**
```bash
# Check service file syntax
sudo systemd-analyze verify harvey-multi-model-training.service

# Check file permissions
ls -la /home/azureuser/harvey/scripts/multi_model_training_generator.py

# Test script manually
cd /home/azureuser/harvey
source venv/bin/activate
python scripts/multi_model_training_generator.py --help
```

---

## 📈 Performance Metrics

### Resource Usage (Estimated)

- **CPU:** 40-60% during run (~10-15 minutes)
- **Memory:** 500MB - 1.5GB
- **Network:** ~5MB upload (API requests), ~2MB download (responses)
- **Disk:** ~5MB per weekly run (JSON output files)

### Timing Estimates

- GPT-5: ~3-4 minutes for 200 questions
- Grok-4: ~2-3 minutes for 200 questions
- DeepSeek-R1: ~3-4 minutes for 200 questions
- Gemini 2.5 Pro: ~3-4 minutes for 200 questions
- **Total runtime:** 12-15 minutes

---

## 🔄 Maintenance

### Weekly Checks (Recommended)

```bash
# Check last run status
sudo systemctl status harvey-multi-model-training.service

# Check generated files
ls -lh /home/azureuser/harvey/training_data/multi_model_weekly_*.json

# Check database ingestion
# (Run from Harvey SQL database)
SELECT 
    COUNT(*) as total_questions,
    COUNT(CASE WHEN created_at > DATEADD(day, -7, GETDATE()) THEN 1 END) as recent_questions
FROM training_questions
WHERE question_id LIKE 'gemini:%'
```

### Monthly Review

1. Review logs for any recurring errors
2. Check training data quality in database
3. Monitor API costs (should be ~$2/month for 800 questions/week)
4. Verify all 4 models are generating questions

### Updating the Generator

```bash
# Stop timer
sudo systemctl stop harvey-multi-model-training.timer

# Update script
scp scripts/multi_model_training_generator.py azureuser@20.81.210.213:/home/azureuser/harvey/scripts/

# Restart timer
sudo systemctl start harvey-multi-model-training.timer
```

---

## 🎯 Success Criteria

The deployment is successful when:

1. ✅ Timer shows `active (waiting)` with next trigger on Sunday 5:00 AM
2. ✅ Manual test run generates 20+ questions without errors
3. ✅ All 4 models (GPT-5, Grok-4, DeepSeek-R1, Gemini) contribute questions
4. ✅ Questions are successfully ingested into database
5. ✅ No API rate limit errors in logs
6. ✅ Output JSON files are created in `/home/azureuser/harvey/training_data/`

---

## 📞 Support & Rollback

### Rollback to Gemini-Only Training

```bash
# Disable multi-model training
sudo systemctl stop harvey-multi-model-training.timer
sudo systemctl disable harvey-multi-model-training.timer

# Gemini-only training continues at Sunday 4:00 AM
sudo systemctl status gemini-training-scheduler.timer
```

### Re-enable Multi-Model Training

```bash
sudo systemctl enable harvey-multi-model-training.timer
sudo systemctl start harvey-multi-model-training.timer
```

---

**Deployment Guide Version:** 1.0  
**Last Updated:** November 20, 2025  
**Maintainer:** Harvey Development Team
