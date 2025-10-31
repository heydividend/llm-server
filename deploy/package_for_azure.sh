#!/bin/bash
# Package Harvey Backend for Azure VM Deployment
# Run this script in Replit to create deployment package

echo "========================================="
echo "Harvey Backend - Creating Deployment Package"
echo "========================================="
echo ""

# Create deployment directory
mkdir -p /tmp/harvey-deployment

echo "📦 Packaging Harvey backend..."

# Copy all necessary files, excluding unwanted directories
tar -czf /tmp/harvey-deployment/harvey-backend.tar.gz \
  --exclude='.git' \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.pythonlibs' \
  --exclude='venv' \
  --exclude='.env' \
  --exclude='attached_assets' \
  --exclude='.replit' \
  --exclude='replit.nix' \
  --exclude='.config' \
  --exclude='.cache' \
  --exclude='ML_*.md' \
  --exclude='DEPLOYMENT_*.md' \
  --exclude='DAILY_*.md' \
  --exclude='AZURE_*.md' \
  .

echo "✅ Harvey backend packaged"
echo ""

echo "📋 Creating deployment instructions..."

cat > /tmp/harvey-deployment/DEPLOY.md <<'EOF'
# Harvey Backend - Azure VM Deployment Instructions

## Quick Start (5 Commands)

### 1. Transfer files to Azure VM

On your local machine (where you downloaded the deployment package):

```bash
# Transfer the deployment package
scp harvey-backend.tar.gz setup_azure_vm.sh deploy_harvey.sh azureuser@20.81.210.213:/tmp/
```

### 2. SSH into Azure VM

```bash
ssh azureuser@20.81.210.213
```

### 3. Run system setup

```bash
cd /tmp
chmod +x setup_azure_vm.sh
./setup_azure_vm.sh
```

### 4. Extract Harvey code

```bash
cd /opt/harvey-backend
tar -xzf /tmp/harvey-backend.tar.gz
```

### 5. Create .env file

```bash
cd /opt/harvey-backend
nano .env
```

Paste your secrets (get from Replit Secrets):

```env
HARVEY_AI_API_KEY=<from_replit_secrets>
SQLSERVER_HOST=<from_replit_secrets>
SQLSERVER_DB=<from_replit_secrets>
SQLSERVER_USER=<from_replit_secrets>
SQLSERVER_PASSWORD=<from_replit_secrets>
OPENAI_API_KEY=<from_replit_secrets>
ML_API_BASE_URL=http://127.0.0.1:9000/api/internal/ml
INTERNAL_ML_API_KEY=<from_replit_secrets>
ODBCSYSINI=/etc
ENVIRONMENT=production
```

Save and exit (Ctrl+X, Y, Enter)

### 6. Deploy Harvey

```bash
cd /opt/harvey-backend
chmod +x deploy_harvey.sh
./deploy_harvey.sh
```

## That's It!

Harvey will be accessible at: http://20.81.210.213/

## Verification

Test the deployment:

```bash
# Test Harvey
curl http://20.81.210.213/

# Test ML health
curl http://20.81.210.213/v1/ml/health

# View logs
sudo journalctl -u harvey.service -f
```

## Troubleshooting

If services fail to start:

```bash
# Check Harvey logs
sudo journalctl -u harvey.service -n 100

# Check ML API logs
sudo journalctl -u ml-api.service -n 100

# Check Nginx logs
sudo tail -100 /var/log/nginx/harvey_error.log

# Restart services
sudo systemctl restart harvey.service
sudo systemctl restart ml-api.service
```

## Azure NSG Configuration

Don't forget to configure Azure Network Security Group:

1. Go to Azure Portal → VM → Networking
2. Add inbound rules for ports 80 and 443
3. Remove/block port 9000 (should only be localhost)

## Post-Deployment

After confirming everything works:

1. Set up SSL with: `sudo certbot --nginx`
2. Configure automated backups
3. Set up monitoring
4. Update your frontend to point to new API URL
5. Keep Replit running for 48 hours as backup
EOF

echo "✅ Deployment instructions created"
echo ""

echo "========================================="
echo "✅ Deployment Package Ready!"
echo "========================================="
echo ""
echo "📁 Files created in /tmp/harvey-deployment/:"
echo "  - harvey-backend.tar.gz (Harvey code)"
echo "  - setup_azure_vm.sh (system setup script)"
echo "  - deploy_harvey.sh (deployment script)"
echo "  - DEPLOY.md (instructions)"
echo ""
echo "📥 Next steps:"
echo "1. Download these files from /tmp/harvey-deployment/"
echo "2. Follow instructions in DEPLOY.md"
echo ""
echo "Quick command to download:"
echo "  scp azureuser@20.81.210.213:/tmp/harvey-deployment/* ."
echo ""
