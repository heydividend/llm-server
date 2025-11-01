# Harvey Intelligence Engine - Automated Training Pipeline

## Overview
This document provides setup instructions for **automated nightly training** to keep Harvey's ML models fresh and accurate. The VM-based systemd timer solution is **production-ready** and can be deployed immediately without requiring new API endpoints.

## Quick Start (Recommended)

**Deploy nightly training automation in 5 minutes:**

```bash
# On Azure VM (20.81.210.213)
cd /home/azureuser
git clone <your-repo> harvey-deploy
cd harvey-deploy/deploy/training_automation
chmod +x setup_training_automation.sh
./setup_training_automation.sh
```

That's it! Training will run daily at 2:00 AM UTC with automatic backup, validation, and rollback.

---

## Current State vs Target State

### Current State (Manual)
- ✅ Training scripts exist on Azure VM
- ❌ No automated scheduling - requires manual SSH execution
- ❌ No monitoring/alerts
- ❌ No automatic rollback on failures

### Target State ✅ IMPLEMENTED
- ✅ **Nightly Schedule**: Runs at 2:00 AM UTC (systemd timer)
- ✅ **Monitoring**: Slack alerts + comprehensive logging
- ✅ **Rollback**: Keeps last 7 model versions, auto-rollback on errors
- ✅ **Validation**: Tests new models before deploying
- ✅ **Self-Healing**: Automatic backup/restore workflow

---

## Implementation Approach

### ✅ VM-Based Systemd Timer (Production-Ready)

**Components:**
- ✅ `train_daily.sh` - Training script with backup/validation/rollback
- ✅ `harvey-training.service` - Systemd service unit
- ✅ `harvey-training.timer` - Daily schedule (2:00 AM UTC)
- ✅ `setup_training_automation.sh` - One-command deployment

**Benefits:**
- No additional cost
- Simple 5-minute deployment
- Works with existing training scripts (no API endpoints needed)
- Production-ready NOW

---

## Production Deployment

### Step 1: Transfer Files to Azure VM

```bash
# From your local machine
scp -r deploy/training_automation azureuser@20.81.210.213:/home/azureuser/
```

### Step 2: Run Setup Script on Azure VM

```bash
# SSH to Azure VM
ssh azureuser@20.81.210.213

# Run setup
cd /home/azureuser/training_automation
chmod +x setup_training_automation.sh
./setup_training_automation.sh
```

### Step 3: Verify Installation

```bash
# Check timer status
sudo systemctl status harvey-training.timer

# View next scheduled run
sudo systemctl list-timers --all | grep harvey

# Test manual run (optional)
sudo systemctl start harvey-training.service

# Watch logs
sudo journalctl -u harvey-training.service -f
```

---

## Management Commands

### View Status
```bash
# Check timer status
sudo systemctl status harvey-training.timer

# View service status
sudo systemctl status harvey-training.service

# See next scheduled runs
sudo systemctl list-timers --all | grep harvey
```

### View Logs
```bash
# Watch live logs
sudo journalctl -u harvey-training.service -f

# View recent logs
sudo journalctl -u harvey-training.service -n 100

# View training log files
tail -f /var/log/harvey-intelligence/training-*.log
ls -ltr /var/log/harvey-intelligence/
```

### Manual Triggers
```bash
# Start training manually
sudo systemctl start harvey-training.service

# Watch progress
sudo journalctl -u harvey-training.service -f
```

### Disable/Enable
```bash
# Stop automatic training
sudo systemctl stop harvey-training.timer
sudo systemctl disable harvey-training.timer

# Re-enable automatic training
sudo systemctl enable harvey-training.timer
sudo systemctl start harvey-training.timer
```

---

## Optional: Slack Notifications

### Step 1: Create Slack Incoming Webhook

1. Go to https://api.slack.com/apps
2. Create new app or select existing
3. Enable "Incoming Webhooks"
4. Create new webhook URL
5. Copy the webhook URL

### Step 2: Add to Environment

```bash
# On Azure VM
sudo tee -a /etc/environment << EOF
SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
EOF

# Reload systemd
sudo systemctl daemon-reload

# Restart timer
sudo systemctl restart harvey-training.timer
```

---

## Troubleshooting

### Training Fails to Start

**Check Conda Environment:**
```bash
# Verify conda is installed
ls /home/azureuser/miniconda3

# Check llm environment exists
/home/azureuser/miniconda3/bin/conda env list | grep llm
```

**Check Permissions:**
```bash
# Ensure azureuser owns the script
ls -la /opt/harvey-intelligence/train_daily.sh

# Fix if needed
sudo chown azureuser:azureuser /opt/harvey-intelligence/train_daily.sh
```

### Training Scripts Not Found

**Verify Paths:**
```bash
# Check training script exists
ls -la /home/azureuser/ml-prediction-api/scripts/

# Update script paths in train_daily.sh if needed
sudo nano /opt/harvey-intelligence/train_daily.sh
```

### Models Not Loading After Training

**Check Intelligence Engine Status:**
```bash
# Verify service restarted
sudo systemctl status harvey-intelligence.service || sudo systemctl status ml-api.service

# Check health endpoint
curl http://127.0.0.1:9000/api/internal/ml/health
```

**Manual Restart:**
```bash
sudo systemctl restart harvey-intelligence.service
```

---

## Architecture Details

### Training Workflow

```
1. Backup Current Models
   ↓
2. Run Training Scripts (via Conda)
   ↓
3. Validate New Models
   ├─ Pass → Continue
   └─ Fail → Rollback to Backup
   ↓
4. Restart Intelligence Engine
   ├─ Success → Continue
   └─ Fail → Rollback to Backup
   ↓
5. Cleanup Old Backups (keep last 7)
   ↓
6. Send Success Notification
```

### File Locations

- **Training Script**: `/opt/harvey-intelligence/train_daily.sh`
- **Systemd Service**: `/etc/systemd/system/harvey-training.service`
- **Systemd Timer**: `/etc/systemd/system/harvey-training.timer`
- **Log Files**: `/var/log/harvey-intelligence/training-*.log`
- **Model Backups**: `/opt/harvey-intelligence/model-backups/backup_*/`
- **Production Models**: `/home/azureuser/ml-prediction-api/models/`

### Backup Retention

- **Automatic**: Last 7 backups kept
- **Manual cleanup**: `rm -rf /opt/harvey-intelligence/model-backups/backup_20241101_*`
- **Restore manually**:
  ```bash
  cp /opt/harvey-intelligence/model-backups/backup_TIMESTAMP/*.pkl \
     /home/azureuser/ml-prediction-api/models/
  sudo systemctl restart harvey-intelligence.service
  ```

---

## Future Enhancements

### Azure Automation Integration (Deferred)

Once training control API endpoints are implemented (`/api/internal/training/*`), you can migrate to Azure Automation for:
- Centralized management across multiple VMs
- Built-in Azure Monitor integration
- Managed identity authentication
- Advanced scheduling with dependencies

**Prerequisites for Migration:**
1. Implement training control API endpoints
2. Add authentication layer
3. Create Azure Automation Hybrid Worker
4. Migrate from systemd timer to runbook

**Why Deferred:** The current VM-based approach works perfectly for single-VM deployments and doesn't require additional API development. Azure Automation provides value mainly for multi-VM orchestration.

---

## Cost Analysis

### Current (VM-Based)
- **Additional Cost**: $0/month
- **Requirements**: Azure VM already running 24/7

### Future (Azure Automation)
- **Runbook Execution**: ~$0.002/minute × 30 minutes × 30 days = ~$1.80/month
- **Storage**: $0.02/GB/month for model backups
- **Total**: ~$2-3/month

**Recommendation**: Start with VM-based approach (zero cost), migrate to Azure Automation only if you need centralized management across multiple VMs.

---

## Summary

✅ **Production-Ready Solution**
- Nightly training at 2:00 AM UTC
- Automatic backup before each run
- Model validation with rollback
- Comprehensive logging
- Optional Slack alerts
- Zero additional cost

🚀 **Deploy in 5 Minutes:**
```bash
ssh azureuser@20.81.210.213
cd /home/azureuser/training_automation
./setup_training_automation.sh
```

📊 **Monitor:**
```bash
sudo systemctl status harvey-training.timer
sudo journalctl -u harvey-training.service -f
```
