# Harvey Multi-Model Training - Simple Deployment Guide

## ✅ STATUS: All Files Ready

Your multi-model training system is complete and tested. Here's how to deploy it:

---

## 🚀 Deployment Method: Git (Simplest)

### Step 1: Use Replit UI to Commit

1. Click the **Version Control** icon (left sidebar)
2. Stage these files:
   - `scripts/multi_model_training_generator.py`
   - `azure_vm_setup/systemd/harvey-multi-model-training.service`
   - `azure_vm_setup/systemd/harvey-multi-model-training.timer`
   - `MULTI_MODEL_TRAINING_ARCHITECTURE.md`
   - `replit.md`
3. Add commit message: `feat: Multi-model training system`
4. Click **Commit & Push**

### Step 2: Deploy on Azure VM

SSH to your Azure VM and run these commands:

```bash
ssh azureuser@20.81.210.213

# Pull latest code
cd /home/azureuser/harvey
git pull

# Install systemd service
sudo cp azure_vm_setup/systemd/harvey-multi-model-training.service /etc/systemd/system/
sudo cp azure_vm_setup/systemd/harvey-multi-model-training.timer /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/harvey-multi-model-training.*

# Create directory
mkdir -p training_data

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable harvey-multi-model-training.timer
sudo systemctl start harvey-multi-model-training.timer

# Verify
systemctl list-timers harvey-multi-model-training.timer
```

**That's it!** ✅

---

## 📊 What You Get

**Multi-Model Training System:**
- 🤖 Generates **800 questions/week** (200 per model)
- 🎓 Uses GPT-5, Grok-4, DeepSeek-R1, Gemini 2.5 Pro
- 📅 Runs every **Sunday 5:00 AM UTC**
- 💾 Auto-saves to `/home/azureuser/harvey/training_data/`
- 🗄️ Auto-ingests into training database

**Vision:** Harvey learns from 4 AI masters → Eventually stands alone!

---

## 🧪 Test After Deployment

```bash
# Manual test run
sudo systemctl start harvey-multi-model-training.service

# Watch logs
sudo journalctl -u harvey-multi-model-training.service -f

# Check output files
ls -lh ~/harvey/training_data/
```

---

## ✅ Success Criteria

Deployment is successful when:
- ✅ `systemctl list-timers` shows next run as Sunday 5:00 AM
- ✅ Generator script exists at `/home/azureuser/harvey/scripts/multi_model_training_generator.py`
- ✅ Manual test run generates questions without errors

---

**All files are ready in your Replit workspace!**
**Just commit via Replit UI, then deploy on Azure VM.**
