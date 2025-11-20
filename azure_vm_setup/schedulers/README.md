# Harvey AI - Gemini Training Data Scheduler

Automated training data generation using Gemini 1.5 Flash API.

## Overview

The Gemini Training Scheduler automatically generates **100 high-quality training questions per week** across 10 dividend investing categories, continuously expanding Harvey's knowledge base.

### Schedule
- **When:** Every Sunday at 4:00 AM UTC
- **What:** Generates 10 questions per category (100 total)
- **Where:** Saves to `training_questions` database table
- **Model:** Gemini 1.5 Flash (stable, better free tier quotas)

### Categories (10 Total)
1. Dividend Analysis
2. Income Strategies
3. Technical Timing
4. ETF Funds
5. Tax Optimization
6. Risk Management
7. Market Analysis
8. Portfolio Construction
9. Dividend Sustainability
10. Global Dividend Markets

---

## Quick Deployment

### Prerequisites
- Harvey backend deployed on Azure VM at `/home/azureuser/harvey`
- Valid GEMINI_API_KEY in `/home/azureuser/harvey/.env`
- Google Generative Language API enabled
- Python environment with conda/miniconda

### Deploy in 3 Steps

```bash
# 1. SSH to Azure VM
ssh azureuser@20.81.210.213

# 2. Pull latest code
cd /home/azureuser/harvey
git pull origin main

# 3. Run deployment script
chmod +x azure_vm_setup/schedulers/deploy_gemini_scheduler.sh
./azure_vm_setup/schedulers/deploy_gemini_scheduler.sh
```

**Expected output:**
```
✓ Log directory ready
✓ Scheduler script ready
✓ Dependencies installed
✓ Prerequisites check passed
✓ Systemd service installed
✓ Gemini Training Scheduler is running
```

---

## Service Management

### Check Status
```bash
sudo systemctl status gemini-training-scheduler
```

### View Logs (Real-time)
```bash
# Main application log
sudo journalctl -u gemini-training-scheduler -f

# View last 100 lines
sudo journalctl -u gemini-training-scheduler -n 100 --no-pager

# Filter by today
sudo journalctl -u gemini-training-scheduler --since today
```

### Control Service
```bash
# Restart
sudo systemctl restart gemini-training-scheduler

# Stop
sudo systemctl stop gemini-training-scheduler

# Start
sudo systemctl start gemini-training-scheduler

# Disable (prevent auto-start)
sudo systemctl disable gemini-training-scheduler

# Enable (auto-start on boot)
sudo systemctl enable gemini-training-scheduler
```

---

## Manual Execution

### Test Run (5 Questions)
```bash
cd /home/azureuser/harvey
python azure_vm_setup/schedulers/gemini_training_scheduler.py --mode test
```

### Generate Once (Custom Count)
```bash
# Generate 50 questions across all categories
python azure_vm_setup/schedulers/gemini_training_scheduler.py \
  --mode once \
  --count 50

# Generate 20 questions for specific category
python azure_vm_setup/schedulers/gemini_training_scheduler.py \
  --mode once \
  --category dividend_analysis \
  --count 20
```

### Available Categories
- `dividend_analysis`
- `income_strategies`
- `technical_timing`
- `etf_funds`
- `tax_optimization`
- `risk_management`
- `market_analysis`
- `portfolio_construction`
- `dividend_sustainability`
- `global_dividend_markets`

---

## Monitoring & Metrics

### Status File
```bash
# View current status
cat /var/log/harvey/gemini_training_status.json
```

Example output:
```json
{
  "status": "completed",
  "total_generated": 98,
  "last_run": "2025-11-20T04:05:32.123456+00:00",
  "last_updated": "2025-11-20T04:05:32.123456+00:00"
}
```

### Metrics File
```bash
# View historical metrics (last 50 runs)
cat /home/azureuser/harvey/gemini_training_metrics.json | python -m json.tool
```

### Log Files
- **Main log:** `/var/log/harvey/gemini_training.log`
- **Error log:** `/var/log/harvey/gemini_training_error.log`
- **Status:** `/var/log/harvey/gemini_training_status.json`
- **Metrics:** `/home/azureuser/harvey/gemini_training_metrics.json`

---

## Troubleshooting

### Service Won't Start

**Check logs:**
```bash
sudo journalctl -u gemini-training-scheduler -n 50 --no-pager
```

**Common issues:**
1. **Invalid GEMINI_API_KEY**
   ```bash
   # Verify key
   cd /home/azureuser/harvey
   python -c "import os; from dotenv import load_dotenv; load_dotenv(override=True); print('OK' if os.getenv('GEMINI_API_KEY') and len(os.getenv('GEMINI_API_KEY')) == 39 else 'INVALID')"
   ```

2. **Missing dependencies**
   ```bash
   /home/azureuser/miniconda3/bin/pip install schedule python-dotenv google-generativeai
   ```

3. **Harvey directory not found**
   ```bash
   ls -la /home/azureuser/harvey
   ```

### API Quota Exceeded

**Error:** `429 Quota exceeded`

**Solution:**
1. Check quota: https://ai.dev/usage?tab=rate-limit
2. Wait for quota reset (typically midnight UTC)
3. Or enable billing for higher quotas (~$0.075 per 1M tokens)

**Temporary fix - reduce frequency:**
```bash
# Edit systemd service
sudo nano /etc/systemd/system/gemini-training-scheduler.service

# Change schedule in code to bi-weekly:
# schedule.every(2).weeks.do(self.weekly_generation)

sudo systemctl daemon-reload
sudo systemctl restart gemini-training-scheduler
```

### Questions Not Saving to Database

**Check database connection:**
```bash
cd /home/azureuser/harvey
python scripts/generate_training_data.py --mode test --count 1 --to-database
```

**Verify database credentials in .env:**
```bash
grep "SQLSERVER" /home/azureuser/harvey/.env
```

### Generation Taking Too Long

**Normal duration:** 10-15 minutes for 100 questions

**If stuck > 30 minutes:**
```bash
# Check if process is running
ps aux | grep gemini_training

# Kill stuck process
sudo pkill -f gemini_training_scheduler

# Restart service
sudo systemctl restart gemini-training-scheduler
```

---

## Integration with Existing Services

### ML Scheduler Timeline (Sunday)
- **1:00 AM** - Payout Rating ML (heydividend-ml-schedulers)
- **2:00 AM** - Dividend Calendar ML (heydividend-ml-schedulers)
- **3:00 AM** - ML Training (heydividend-ml-schedulers)
- **4:00 AM** - **Gemini Training Data Generator** ✨

This ensures Gemini generates fresh training data **after** ML models are retrained.

### Database Tables Used
- `training_questions` - Stores generated questions and answers
- `fine_tuning_samples` - Used by continuous learning pipeline
- `learning_metrics` - Tracks model performance over time

---

## API Key Management

### Get Valid API Key
1. Go to https://aistudio.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Enable "Generative Language API" at https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com
5. Copy the 39-character key (starts with `AIzaSy`)

### Update API Key
```bash
cd /home/azureuser/harvey
nano .env

# Update this line:
GEMINI_API_KEY=AIzaSy...your_key_here

# Restart service
sudo systemctl restart gemini-training-scheduler
```

---

## Uninstall

```bash
# Stop and disable service
sudo systemctl stop gemini-training-scheduler
sudo systemctl disable gemini-training-scheduler

# Remove service file
sudo rm /etc/systemd/system/gemini-training-scheduler.service
sudo systemctl daemon-reload

# Remove logs (optional)
sudo rm -rf /var/log/harvey/gemini_training*
rm /home/azureuser/harvey/gemini_training_metrics.json
```

---

## Performance & Costs

### API Usage
- **Model:** Gemini 1.5 Flash
- **Weekly calls:** ~10 API calls (one per category)
- **Tokens per call:** ~2,000 input + 1,500 output
- **Total tokens/week:** ~35,000 tokens

### Cost Estimate (with billing enabled)
- **Input:** $0.075 per 1M tokens × 20,000 = $0.0015/week
- **Output:** $0.30 per 1M tokens × 15,000 = $0.0045/week
- **Total:** ~$0.006/week (~$0.31/year)

### Free Tier Limits
- **Requests:** 15 requests/minute, 1,500 requests/day
- **Our usage:** Well within limits (10 requests/week)

---

## Support

**Logs location:**
- `/var/log/harvey/gemini_training.log`
- `/var/log/harvey/gemini_training_error.log`

**Configuration files:**
- `/etc/systemd/system/gemini-training-scheduler.service`
- `/home/azureuser/harvey/.env`
- `/home/azureuser/harvey/azure_vm_setup/schedulers/gemini_training_scheduler.py`

**Documentation:**
- This README
- Main project README: `/home/azureuser/harvey/README.md`
- Deployment guide: `/home/azureuser/harvey/GEMINI_DEPLOYMENT_GUIDE.md`

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Systemd Service (gemini-training-scheduler)       │
│  Runs: Sunday 4:00 AM UTC                          │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  gemini_training_scheduler.py                       │
│  - Checks prerequisites (API key, Harvey dir)       │
│  - Iterates through 10 categories                   │
│  - Calls generate_training_data.py for each         │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  generate_training_data.py                          │
│  - Loads GEMINI_API_KEY from .env                   │
│  - Calls Gemini 1.5 Flash API                       │
│  - Generates 10 questions with answers              │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  Azure SQL Database (training_questions table)      │
│  - Stores questions, answers, metadata              │
│  - Used by Harvey's continuous learning pipeline    │
└─────────────────────────────────────────────────────┘
```

---

**Last Updated:** November 20, 2025  
**Version:** 1.0.0  
**Status:** Production Ready ✅
