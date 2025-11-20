# Harvey Multi-Model Training System - Deployment Summary
**Date:** November 20, 2025  
**Status:** ✅ READY FOR DEPLOYMENT

---

## 🎯 What Was Built

### Core System
**Multi-Model Training Generator** that uses ALL 4 AI models to train Harvey:
- **GPT-5** (HarveyGPT-5) - Complex reasoning, comprehensive analysis
- **Grok-4** (grok-4-fast-reasoning) - Fast insights, real-time analysis  
- **DeepSeek-R1** (DeepSeek-R1-0528) - Quantitative modeling, math analysis
- **Gemini 2.5 Pro** - Strategic planning, sustainability analysis

### Training Capacity
- **800 questions/week** (200 per model × 4 models)
- **41,600 questions/year** (8x more than Gemini-only approach)
- **8 dividend categories** (analysis, strategies, risk, timing, ETFs, tax, quant, global)

### Deployment Infrastructure
- ✅ Production-ready Python script with retry logic
- ✅ Systemd service (oneshot with resource limits)
- ✅ Systemd timer (Sunday 5:00 AM UTC)
- ✅ Automated deployment script
- ✅ Comprehensive documentation

---

## 🚀 How to Deploy

### Option 1: Automated Deployment (Recommended)

```bash
# Run the deployment script
./deploy_to_azure_vm.sh
```

This will:
1. Copy generator script to Azure VM
2. Install systemd service and timer
3. Enable and start the timer
4. Verify installation

### Option 2: Manual Deployment

```bash
# 1. Copy files
scp scripts/multi_model_training_generator.py azureuser@20.81.210.213:/home/azureuser/harvey/scripts/
scp azure_vm_setup/systemd/harvey-multi-model-training.* azureuser@20.81.210.213:/tmp/

# 2. SSH and install
ssh azureuser@20.81.210.213

# 3. Install systemd files
sudo cp /tmp/harvey-multi-model-training.* /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/harvey-multi-model-training.*
sudo systemctl daemon-reload

# 4. Enable and start
sudo systemctl enable harvey-multi-model-training.timer
sudo systemctl start harvey-multi-model-training.timer

# 5. Verify
systemctl status harvey-multi-model-training.timer
```

---

## 📅 Scheduler Timeline

| Time | Scheduler | Purpose | Output |
|------|-----------|---------|--------|
| Daily 1:00 AM | Payout Rating ML | A+/A/B/C ratings | ML predictions |
| Sunday 2:00 AM | Dividend Calendar ML | Payment predictions | Calendar data |
| Sunday 3:00 AM | ML Training | Train 7 core models | Model updates |
| Sunday 4:00 AM | Gemini Training | 100 questions/week | Training data |
| **Sunday 5:00 AM** | **Multi-Model Training** | **800 questions/week** | **Training data** |

**Total Training:** 900 questions/week from 5 different AI perspectives!

---

## 🧪 Testing the Deployment

### After Deployment - Manual Test Run

```bash
# SSH into Azure VM
ssh azureuser@20.81.210.213

# Test with small batch (20 questions total)
cd /home/azureuser/harvey
source venv/bin/activate
python scripts/multi_model_training_generator.py \
  --category dividend_analysis \
  --questions-per-model 5 \
  --output /tmp/test_multi_model.json

# Check output
cat /tmp/test_multi_model.json | jq '.stats'

# Expected output:
# {
#   "total_questions": 20,
#   "by_model": {
#     "GPT-5": 5,
#     "Grok-4": 5,
#     "DeepSeek-R1": 5,
#     "Gemini-2.5-Pro": 5
#   }
# }
```

### Trigger Service Manually

```bash
# Trigger the actual systemd service
sudo systemctl start harvey-multi-model-training.service

# Watch logs in real-time
sudo journalctl -u harvey-multi-model-training.service -f

# Check for errors
sudo journalctl -u harvey-multi-model-training.service --since "5 minutes ago"
```

---

## 📊 Monitoring

### Check Timer Status

```bash
# Timer status
sudo systemctl status harvey-multi-model-training.timer

# Next scheduled run
systemctl list-timers harvey-multi-model-training.timer
```

### Check Generated Files

```bash
# View generated training data files
ls -lh /home/azureuser/harvey/training_data/multi_model_weekly_*.json

# View most recent file
cat /home/azureuser/harvey/training_data/multi_model_weekly_*.json | jq '.stats'
```

### Check Database Ingestion

```sql
-- Run in Azure SQL Database
SELECT 
    COUNT(*) as total_questions,
    COUNT(CASE WHEN created_at > DATEADD(day, -7, GETDATE()) THEN 1 END) as last_week
FROM training_questions
WHERE question_id LIKE 'gemini:%'
```

---

## ✅ Success Criteria

Deployment is successful when:

1. ✅ Timer shows `active (waiting)` status
2. ✅ Next trigger shows Sunday 5:00 AM UTC
3. ✅ Manual test generates 20 questions without errors
4. ✅ All 4 models contribute questions
5. ✅ Questions are ingested into database
6. ✅ No API rate limit errors in logs

---

## 🔧 Troubleshooting

### If Timer Doesn't Start

```bash
sudo journalctl -u harvey-multi-model-training.timer -n 50
sudo systemctl restart harvey-multi-model-training.timer
```

### If Service Fails

```bash
sudo journalctl -u harvey-multi-model-training.service -n 100
sudo systemctl status harvey-multi-model-training.service
```

### If API Errors

```bash
# Check environment variables
cat /home/azureuser/harvey/.env | grep -E 'AZURE|GEMINI'

# Test API connectivity
cd /home/azureuser/harvey
source venv/bin/activate
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Azure:', 'OK' if os.getenv('AZURE_OPENAI_API_KEY') else 'MISSING'); print('Gemini:', 'OK' if os.getenv('GEMINI_API_KEY') else 'MISSING')"
```

---

## 📁 Deployed Files

```
Azure VM: /home/azureuser/harvey/

scripts/
  └── multi_model_training_generator.py    # Main generator

training_data/
  └── multi_model_weekly_*.json            # Output files (weekly)

/etc/systemd/system/
  ├── harvey-multi-model-training.service  # Systemd service
  └── harvey-multi-model-training.timer    # Systemd timer
```

---

## 💰 Cost Analysis

**Per Run:** ~$0.45 (800 questions across 4 models)  
**Weekly:** $0.45  
**Monthly:** ~$1.80  
**Yearly:** ~$23  

**ROI:** Eventually eliminate $1,000s in external API costs when Harvey stands alone.

---

## 🎓 The Vision

**Phase 1 (Current):** Deploy multi-model training system  
**Phase 2 (3-6 months):** Collect 20,000+ diverse training examples  
**Phase 3 (6-9 months):** Fine-tune Harvey on multi-model dataset  
**Phase 4 (12+ months):** Harvey stands alone, replaces external models  

**Outcome:** Self-sufficient dividend intelligence with zero external API costs.

---

## 📚 Documentation

- **Architecture:** `MULTI_MODEL_TRAINING_ARCHITECTURE.md`
- **Deployment Guide:** `azure_vm_setup/DEPLOYMENT_GUIDE.md`
- **Project Overview:** `replit.md`

---

**Status:** ✅ PRODUCTION READY  
**Next Action:** Run `./deploy_to_azure_vm.sh`  
**Maintainer:** Harvey Development Team
