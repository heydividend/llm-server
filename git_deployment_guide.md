# 🚀 Harvey Git Deployment Guide

## Quick Start: Deploy Harvey Using Git

### Step 1: On Your Local Machine (or GitHub)

Create a new repository and push Harvey code:

```bash
# Create new GitHub repository (via GitHub website)
# Repository name: harvey-ai-advisor

# On your local machine, create deployment package
mkdir harvey-deployment
cd harvey-deployment

# Copy essential files from Replit
# - main.py
# - All app/ directory files
# - ml_training/ml_api.py
# - requirements.txt
# - .env.example (with secrets removed)
```

### Step 2: Initialize Git Repository

```bash
git init
git add .
git commit -m "Initial Harvey deployment with ML service"
git remote add origin https://github.com/yourusername/harvey-ai-advisor.git
git push -u origin main
```

### Step 3: On Azure VM - Clone and Deploy

```bash
# SSH into Azure VM
ssh azureuser@20.81.210.213

# Clone the repository
cd /home/azureuser
git clone https://github.com/yourusername/harvey-ai-advisor.git harvey

# Navigate to directory
cd harvey

# Copy environment variables
cp .env.example .env
nano .env  # Add your actual API keys and database credentials

# Install dependencies
/home/azureuser/miniconda3/bin/pip install -r requirements.txt

# Set up services
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable harvey-backend harvey-ml
sudo systemctl start harvey-backend harvey-ml
```

## 🔄 Updating Harvey (After Initial Deploy)

Once Git is set up, updates are super simple:

### On Your Development Machine:
```bash
# Make changes to code
git add .
git commit -m "Add new feature: enhanced dividend analysis"
git push origin main
```

### On Azure VM:
```bash
cd /home/azureuser/harvey
git pull origin main
sudo systemctl restart harvey-backend harvey-ml
```

That's it! Your changes are live.

## 📁 Repository Structure

```
harvey-ai-advisor/
├── app/
│   ├── core/
│   ├── services/
│   ├── models/
│   └── web_search/
├── ml_training/
│   └── ml_api.py
├── systemd/
│   ├── harvey-backend.service
│   └── harvey-ml.service
├── frontend/
│   ├── harvey-test.html
│   └── harvey-frontend-api.js
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
├── deploy.sh
└── README.md
```

## 🛠️ Automated Deployment Script

Create `deploy.sh` in your repository:

```bash
#!/bin/bash
# One-command deployment

echo "🚀 Deploying Harvey updates..."

# Pull latest code
git pull origin main

# Update dependencies
/home/azureuser/miniconda3/bin/pip install -r requirements.txt

# Restart services
sudo systemctl restart harvey-backend harvey-ml

# Show status
sudo systemctl status harvey-backend harvey-ml --no-pager

echo "✅ Deployment complete!"
```

Make it executable: `chmod +x deploy.sh`

Then deploy with: `./deploy.sh`

## 🔐 Security Best Practices

### Never commit these to Git:
- `.env` file with real credentials
- API keys or passwords
- Database connection strings
- SSL certificates

### Instead, use:
- `.env.example` with placeholder values
- Azure Key Vault for production secrets
- Environment variables on the server

## 📋 Git Workflow Commands

### Daily Development:
```bash
# Check status
git status

# Add changes
git add .

# Commit with message
git commit -m "Fix: Improved ML prediction accuracy"

# Push to repository
git push origin main
```

### On Azure VM:
```bash
# Pull updates
git pull origin main

# Check what changed
git log --oneline -5

# If issues, rollback
git reset --hard HEAD~1
```

## 🚨 Troubleshooting

### If services don't start after update:
```bash
# Check logs
sudo journalctl -u harvey-backend -n 50
sudo journalctl -u harvey-ml -n 50

# Check Python errors
cd /home/azureuser/harvey
/home/azureuser/miniconda3/bin/python main.py  # Test manually
```

### If database connection fails:
```bash
# Verify .env file
cat .env | grep SQLSERVER

# Test connection
/home/azureuser/miniconda3/bin/python -c "import pyodbc; print('OK')"
```

## 🎯 Complete Deployment Checklist

- [ ] Create GitHub repository
- [ ] Push code to repository
- [ ] Clone on Azure VM
- [ ] Configure .env with real credentials
- [ ] Install Python dependencies
- [ ] Set up systemd services
- [ ] Open ports in Azure NSG (8001, 9000)
- [ ] Test endpoints
- [ ] Set up automated deployment script

## 🔄 CI/CD with GitHub Actions (Optional)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Azure VM

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - name: Deploy to Azure VM
      uses: appleboy/ssh-action@master
      with:
        host: 20.81.210.213
        username: azureuser
        key: ${{ secrets.SSH_PRIVATE_KEY }}
        script: |
          cd /home/azureuser/harvey
          git pull origin main
          ./deploy.sh
```

This automates deployment on every push to main branch!