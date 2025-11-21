# Harvey Deployment Scripts

## Overview

This directory contains deployment automation scripts for Harvey AI.

## Scripts

### 1. `deploy_from_replit.sh`

**Purpose:** Deploy Harvey from Replit development environment to Azure VM production

**Usage:**
```bash
./scripts/deploy_from_replit.sh
```

**What it does:**
1. Validates git working directory is clean
2. Pushes latest changes to git remote
3. Copies `deploy_on_azure_vm.sh` to Azure VM
4. Executes deployment remotely via SSH
5. Shows deployment results

**Requirements:**
- Environment variables: `AZURE_VM_IP`, `AZURE_VM_USER`, `AZURE_VM_PASSWORD`
- `sshpass` installed for automated SSH
- Git repository with remote configured

---

### 2. `../deploy_on_azure_vm.sh`

**Purpose:** Main deployment script that runs ON the Azure VM

**Usage:**
```bash
# SSH into Azure VM
ssh azureuser@20.81.210.213
cd /home/azureuser/harvey

# Run deployment
./deploy_on_azure_vm.sh
```

**What it does:**
1. Pulls latest changes from git
2. Stashes uncommitted changes (with user confirmation)
3. Updates Python dependencies
4. Stops Harvey services
5. Runs database migrations (if configured)
6. Restarts all services
7. Reloads Nginx
8. Runs health checks
9. Shows service status and logs

**Features:**
- ✅ Colored output for clarity
- ✅ Error handling with exit on failure
- ✅ Automatic service health validation
- ✅ Deployment history logging
- ✅ Recent commits display
- ✅ Rollback guidance

---

## Deployment Workflow

```
Development (Replit)
    │
    │ git commit & push
    ▼
Git Remote (GitHub/GitLab)
    │
    │ git pull
    ▼
Production (Azure VM)
    │
    │ restart services
    ▼
Harvey Live (Port 8001)
```

---

## Environment Variables

Required for `deploy_from_replit.sh`:

```bash
AZURE_VM_IP=20.81.210.213
AZURE_VM_USER=azureuser
AZURE_VM_PASSWORD=your-vm-password
```

Set these in Replit Secrets or `.env` file.

---

## Troubleshooting

### "sshpass: command not found"

Install sshpass on Replit:
```bash
nix-env -iA nixpkgs.sshpass
```

### "Permission denied (publickey)"

Ensure `AZURE_VM_PASSWORD` is set correctly:
```bash
echo $AZURE_VM_PASSWORD
```

### "Git working directory not clean"

Commit or stash your changes:
```bash
git status
git add .
git commit -m "Your changes"
```

### Services fail to start

Check logs on Azure VM:
```bash
sudo journalctl -u harvey-backend -n 50
sudo systemctl status harvey-backend
```

---

## Service Management

On Azure VM:

```bash
# Restart Harvey backend
sudo systemctl restart harvey-backend

# Restart ML schedulers
sudo systemctl restart heydividend-ml-schedulers

# Check status
sudo systemctl status harvey-backend

# View logs
sudo journalctl -u harvey-backend -f
```

---

## Rollback

If deployment breaks production:

```bash
cd /home/azureuser/harvey
git log -10 --oneline
git reset --hard <previous-commit-hash>
sudo systemctl restart harvey-backend
sudo systemctl restart heydividend-ml-schedulers
```

---

## Additional Scripts

### `multi_model_training_generator.py`

Generates training data using all 4 AI models (GPT-5, Grok-4, DeepSeek-R1, Gemini 2.5 Pro)

**Usage:**
```bash
python3 scripts/multi_model_training_generator.py --questions 200
```

---

## Documentation

- **Quick Start:** `DEPLOYMENT_QUICK_START.md`
- **Full Guide:** `DEPLOYMENT.md`
- **Architecture:** `replit.md`

---

**Last Updated:** November 21, 2025  
**Harvey Version:** Multi-Currency Support (v2.1)
