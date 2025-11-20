# Harvey Multi-Model Training - Quick Deployment Guide

## ✅ What's Been Created

All files are ready for deployment:

```
✅ scripts/multi_model_training_generator.py
✅ azure_vm_setup/systemd/harvey-multi-model-training.service
✅ azure_vm_setup/systemd/harvey-multi-model-training.timer
✅ azure_vm_setup/DEPLOYMENT_GUIDE.md
✅ MULTI_MODEL_TRAINING_ARCHITECTURE.md
✅ DEPLOYMENT_SUMMARY.md
✅ deploy_multi_model_training.sh
✅ replit.md (updated)
```

---

## 🚀 Deploy Now (3 Steps)

### Step 1: Commit Changes to Git

```bash
# Remove git lock if needed
rm -f .git/index.lock

# Add files
git add scripts/multi_model_training_generator.py \
  azure_vm_setup/systemd/ \
  azure_vm_setup/DEPLOYMENT_GUIDE.md \
  MULTI_MODEL_TRAINING_ARCHITECTURE.md \
  DEPLOYMENT_SUMMARY.md \
  deploy_multi_model_training.sh \
  replit.md

# Commit
git commit -m "feat: Multi-model training system - Harvey learns from 4 AI masters"

# Push to remote (if needed)
git push origin main
```

### Step 2: Deploy to Azure VM

```bash
# Option A: Automated deployment (recommended)
export AZURE_SSH_PASSWORD="your-password"
./deploy_multi_model_training.sh

# Option B: Manual deployment
ssh azureuser@20.81.210.213
cd /home/azureuser/harvey
git pull
sudo cp azure_vm_setup/systemd/harvey-multi-model-training.* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable harvey-multi-model-training.timer
sudo systemctl start harvey-multi-model-training.timer
```

### Step 3: Verify Deployment

```bash
ssh azureuser@20.81.210.213
systemctl status harvey-multi-model-training.timer
systemctl list-timers harvey-multi-model-training.timer
```

---

## 📊 What Gets Deployed

**Multi-Model Training System:**
- ✅ Runs every Sunday at 5:00 AM UTC
- ✅ Generates 800 questions/week (200 per model)
- ✅ Uses GPT-5, Grok-4, DeepSeek-R1, Gemini 2.5 Pro
- ✅ Auto-ingests into training database
- ✅ Saves to `/home/azureuser/harvey/training_data/`

**Vision:** Harvey learns from 4 AI masters → Eventually stands alone!

---

## 🧪 Test After Deployment

```bash
# Manual test run
ssh azureuser@20.81.210.213
sudo systemctl start harvey-multi-model-training.service
sudo journalctl -u harvey-multi-model-training.service -f
```

---

**Status:** ✅ READY TO DEPLOY  
**Next Action:** Run Step 1, 2, 3 above
