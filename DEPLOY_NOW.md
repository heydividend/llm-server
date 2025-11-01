# 🚀 Harvey - Ready to Deploy to Azure VM

## ✅ Everything is Fixed and Ready!

### What I Just Fixed:
1. ✅ **Database Driver** - Installed FreeTDS + unixODBC (was missing, causing all DB queries to fail)
2. ✅ **ML API Timeouts** - Reduced from 120s → 5s (no more hanging!)
3. ✅ **Circuit Breaker** - Optimized for fast failures instead of long waits
4. ✅ **Server Startup** - All services initialize correctly
5. ✅ **API Endpoints** - Chat streaming tested and working

### Current Status in Replit:
- ✅ Server running on port 5000
- ✅ Database connections working (Azure SQL Server)
- ✅ Chat streaming endpoint working
- ✅ Background scheduler running
- ✅ Cache system active
- ✅ Feedback system code ready

---

## 🎯 How to Deploy to Your Azure VM

### I Cannot Deploy Directly Because:
- ❌ I don't have SSH access to your Azure VM
- ❌ I don't have access to your Azure Portal
- ❌ I can't run Azure CLI commands from Replit

### But I've Prepared Everything You Need! ✨

---

## 📦 Option 1: Azure Run Command (Fastest - 5 Minutes)

**No SSH required! Just copy/paste in Azure Portal:**

### Step 1: Edit the Deployment Script
1. Open file: `deploy/AZURE_RUN_COMMAND_DEPLOY.sh` in this project
2. Find lines 18-25 (the secrets section)
3. Replace all `<YOUR_*>` placeholders with your actual values:
   ```bash
   HARVEY_AI_API_KEY="your-actual-key-here"
   SQLSERVER_HOST="your-server.database.windows.net"
   SQLSERVER_DB="HeyDividend"
   SQLSERVER_USER="your-username"
   SQLSERVER_PASSWORD="your-password"
   OPENAI_API_KEY="sk-..."
   INTERNAL_ML_API_KEY="your-ml-key"
   PDFCO_API_KEY="your-pdfco-key"
   ```

### Step 2: Deploy via Azure Portal
1. Go to **Azure Portal** (portal.azure.com)
2. Navigate to your VM → **Run Command** (left sidebar)
3. Select **RunShellScript**
4. Copy the **entire contents** of `deploy/AZURE_RUN_COMMAND_DEPLOY.sh`
5. Paste into the script box
6. Click **Run**
7. Wait 3-5 minutes

### Step 3: Verify It Worked
```bash
# Test Harvey backend (replace with your VM IP)
curl http://YOUR-VM-IP/health

# Test chat endpoint
curl -X POST http://YOUR-VM-IP/v1/chat/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_HARVEY_API_KEY" \
  -d '{"message": "What is AAPL?", "session_id": "test"}'

# Should see streaming response!
```

---

## 📦 Option 2: SSH Deployment (Traditional Method)

If you prefer SSH:

```bash
# 1. SSH into your Azure VM
ssh azureuser@your-vm-ip

# 2. Download deployment script
curl -o deploy.sh https://your-replit-or-github-url/deploy/AZURE_RUN_COMMAND_DEPLOY.sh

# 3. Edit secrets in the script
nano deploy.sh
# Update lines 18-25 with your actual secrets

# 4. Run deployment
sudo bash deploy.sh

# 5. Check status
sudo systemctl status harvey-backend
sudo systemctl status ml-api
sudo systemctl status nginx
```

---

## 🔍 After Deployment: Create Feedback Tables

Once Harvey is deployed, run this **one-time setup**:

### Option A: Via Azure Portal Query Editor (Easiest)
1. Go to Azure Portal → Your SQL Database → **Query Editor**
2. Open file `app/database/feedback_schema.sql` from this project
3. Copy entire contents
4. Paste into Query Editor
5. Click **Run**

### Option B: Via sqlcmd on Azure VM
```bash
# SSH into your Azure VM
ssh azureuser@your-vm-ip

# Run the schema
cd /opt/harvey-backend
sqlcmd -S $SQLSERVER_HOST \
  -d $SQLSERVER_DB \
  -U $SQLSERVER_USER \
  -P $SQLSERVER_PASSWORD \
  -i app/database/feedback_schema.sql

# Restart Harvey
sudo systemctl restart harvey-backend
```

### Test Feedback System:
```bash
# Submit test feedback
curl -X POST http://YOUR-VM-IP/v1/feedback/test123/positive

# View analytics
curl http://YOUR-VM-IP/v1/feedback/analytics/dashboard
```

---

## 📋 Deployment Checklist

See `DEPLOYMENT_CHECKLIST.md` for complete verification steps.

**Quick Checklist:**
- [ ] Edit deployment script with your secrets
- [ ] Run deployment via Azure Portal or SSH
- [ ] Verify Harvey responds: `curl http://YOUR-VM-IP/health`
- [ ] Create feedback tables on Azure SQL
- [ ] Test all endpoints
- [ ] Configure SSL/TLS (optional but recommended)

---

## 🆘 Need Help?

### Common Issues:

**"Can't open lib 'FreeTDS'"**
- The deployment script installs this automatically
- If error persists, check: `sudo dpkg -l | grep freetds`

**"ML API timeout"**
- ML API runs on port 9000 inside the VM
- Check NSG allows port 9000 (internal only)
- Verify: `curl http://localhost:9000/health` from VM

**"Feedback tables not found"**
- You need to run `feedback_schema.sql` (see above)

**"Database connection failed"**
- Verify Azure SQL firewall allows your VM's IP
- Test: `sqlcmd -S $SQLSERVER_HOST -d $SQLSERVER_DB -U $SQLSERVER_USER -P $SQLSERVER_PASSWORD -Q "SELECT 1"`

---

## 🎉 What You'll Have After Deployment

```
Your Azure VM:
├── Harvey Backend (port 8000) → exposed via Nginx on port 80
├── ML Prediction API (port 9000) → internal only
├── Nginx (ports 80/443) → reverse proxy
├── All background services running
│   ├── Alert monitoring (every 5 min)
│   ├── Daily portfolio digests (8 AM)
│   ├── Cache prewarming
│   └── ML health monitoring
└── Production-ready feedback system
```

**Your app will be live at:** `http://YOUR-VM-IP/` or `https://YOUR-DOMAIN.com/`

---

## 📞 I'm Here to Help!

While I can't deploy directly to your Azure VM, I can:
- ✅ Help troubleshoot deployment issues
- ✅ Update deployment scripts if needed
- ✅ Test features here in Replit first
- ✅ Create new endpoints or fix bugs
- ✅ Optimize performance

**Just let me know if you hit any issues during deployment!** 🚀
