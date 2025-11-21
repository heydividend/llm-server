# Harvey AI - Git Deployment Quick Start

## 🚀 Deploy to Azure VM in 3 Steps

### Method 1: Deploy from Azure VM (Recommended)

```bash
# 1. SSH into Azure VM
ssh azureuser@20.81.210.213

# 2. Navigate to Harvey directory
cd /home/azureuser/harvey

# 3. Run deployment script
./deploy_on_azure_vm.sh
```

Done! The script automatically:
- Pulls latest code from git
- Updates dependencies
- Restarts all services
- Runs health checks

---

### Method 2: Deploy from Replit

```bash
# 1. Commit your changes (or use Replit Git UI)
git add .
git commit -m "Your changes"
git push origin main

# 2. Run remote deployment script
./scripts/deploy_from_replit.sh
```

Done! This pushes to git and deploys to Azure VM remotely.

---

## 📋 What Gets Deployed

- **Harvey Backend** (FastAPI) - Port 8001
- **ML Schedulers** (5 automated jobs)
- **Multi-Currency Service** (7 currencies)
- **Nginx** (Reverse proxy)

---

## ✅ Quick Health Checks

```bash
# Check if Harvey is running
curl http://20.81.210.213:8001/health

# Check multi-currency feature
curl http://20.81.210.213:8001/v1/currency/supported

# View logs
sudo journalctl -u harvey-backend -n 50
```

---

## 🔄 Service Commands

```bash
# Restart Harvey
sudo systemctl restart harvey-backend

# Check status
sudo systemctl status harvey-backend

# View live logs
sudo journalctl -u harvey-backend -f
```

---

## 🔙 Rollback

```bash
cd /home/azureuser/harvey
git log -5 --oneline  # Find commit to rollback to
git reset --hard <commit-hash>
sudo systemctl restart harvey-backend
```

---

## 📁 Key Files

- `deploy_on_azure_vm.sh` - Main deployment script (run on VM)
- `scripts/deploy_from_replit.sh` - Remote deployment (run from Replit)
- `DEPLOYMENT.md` - Full deployment documentation

---

**Harvey Directory:** `/home/azureuser/harvey`  
**Production URL:** `http://20.81.210.213:8001`  
**Last Updated:** November 21, 2025
