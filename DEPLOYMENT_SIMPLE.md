# Harvey - Simple Deployment Steps

## Method 1: Deploy from Azure VM (Easiest)

```bash
# 1. SSH into VM
ssh azureuser@20.81.210.213

# 2. Go to Harvey directory
cd /home/azureuser/harvey

# 3. Run deployment
./deploy_on_azure_vm.sh
```

Done! ✅

---

## Method 2: Deploy from Replit

```bash
# 1. Commit your changes
git add .
git commit -m "Your changes"
git push origin main

# 2. Deploy to VM
./scripts/deploy_from_replit.sh
```

Done! ✅

---

## That's It!

**Harvey URL:** http://20.81.210.213:8001  
**Harvey Directory:** /home/azureuser/harvey

---

## If Something Goes Wrong

```bash
# Check status
ssh azureuser@20.81.210.213
sudo systemctl status harvey-backend

# View logs
sudo journalctl -u harvey-backend -f

# Restart
sudo systemctl restart harvey-backend
```
