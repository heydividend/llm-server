# 🚀 Harvey Deployment Instructions

## Method 1: Using Replit's Git Interface (Recommended)

### Step 1: Open Git Pane in Replit
1. Click **Tools** in the sidebar
2. Click the **+** button  
3. Search for and select **Git**
4. The Git pane will open

### Step 2: Connect to GitHub
1. In the Git pane, click **Connect to GitHub**
2. Authorize Replit to access your GitHub account
3. Create a new repository or connect to existing one

### Step 3: Commit and Push
1. Review changes in the Git pane
2. Stage all files (except .env with secrets)
3. Enter commit message: "Harvey AI with ML Service"
4. Click **Push** to send to GitHub

### Step 4: Deploy to Azure VM
SSH into your Azure VM and clone from GitHub:
```bash
ssh azureuser@20.81.210.213
cd /home/azureuser
git clone https://github.com/yourusername/harvey.git
cd harvey
```

---

## Method 2: Direct File Transfer (Quick Alternative)

### Step 1: Create Deployment Package
I'll create a tar archive with all necessary files:

```bash
# This will be created for you
harvey-deployment.tar.gz
```

### Step 2: Transfer to Azure VM
From your local machine:
```bash
# Download from Replit (use Replit's download feature)
# Then upload to Azure VM:
scp harvey-deployment.tar.gz azureuser@20.81.210.213:~/
```

### Step 3: Extract and Deploy on Azure VM
```bash
ssh azureuser@20.81.210.213
tar -xzf harvey-deployment.tar.gz
cd harvey
./deploy_harvey_azure.sh
```

---

## Method 3: Using Replit Shell (Manual Git)

### Step 1: Open Shell in Replit
1. Click **Tools** → **+** → **Shell**
2. You now have full Git access!

### Step 2: Initialize and Push
In the Shell, run:
```bash
git init
git add .
git commit -m "Harvey AI with ML Service"
git remote add origin https://github.com/yourusername/harvey.git
git push -u origin main
```

### Step 3: Clone on Azure VM
Same as Method 1 - clone from GitHub on your VM.

---

## 📦 Files Ready for Deployment

### Core Files:
- ✅ `main.py` - Harvey backend
- ✅ `ml_training/ml_api.py` - ML service
- ✅ `app/` - All services and models
- ✅ `requirements.txt` - Dependencies

### Deployment Scripts:
- ✅ `deploy_harvey_azure.sh` - Automated setup
- ✅ `setup_git_deployment.sh` - Git configuration

### Frontend:
- ✅ `harvey-test.html` - Web interface
- ✅ `harvey-frontend-api.js` - API integration

---

## 🔄 Quick Update Process

Once deployed, updates are simple:

### In Replit:
1. Make your changes
2. Open Git pane
3. Commit and push

### On Azure VM:
```bash
cd /home/azureuser/harvey
git pull
sudo systemctl restart harvey-backend harvey-ml
```

---

## 🎯 Recommended: Use Replit's Git Pane

This is the easiest method:
1. **Connect to GitHub** through Replit's interface
2. **Push your code** with one click
3. **Pull on Azure VM** to deploy

No command-line Git needed in Replit!