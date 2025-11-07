#!/bin/bash

# Deploy environment configuration to Azure VM

AZURE_VM_IP="20.81.210.213"
AZURE_USER="azureuser"

echo "=================================================="
echo "🔐 Deploying Environment Configuration to Azure VM"
echo "=================================================="
echo ""

# Step 1: Deploy the environment file
echo "📤 Step 1: Uploading environment file..."
echo "You'll be prompted for password:"
scp azure.env $AZURE_USER@$AZURE_VM_IP:/home/azureuser/harvey/.env

echo ""
echo "🔧 Step 2: Setting up environment on Azure VM..."
ssh $AZURE_USER@$AZURE_VM_IP << 'REMOTE_SETUP'
cd /home/azureuser/harvey

# Set proper permissions for .env file
chmod 600 .env

# Create system-wide environment for services
echo "Creating system environment file..."
sudo tee /etc/environment.d/harvey.conf > /dev/null << 'SYSENV'
# Load from .env file
source /home/azureuser/harvey/.env

# Export all variables
$(cat /home/azureuser/harvey/.env | grep -v '^#' | grep '=' | sed 's/^/export /')
SYSENV

# Create wrapper script for cron jobs
cat > /home/azureuser/harvey/run_with_env.sh << 'WRAPPER'
#!/bin/bash
# Load environment variables before running Python scripts

# Source the .env file
if [ -f /home/azureuser/harvey/.env ]; then
    set -a
    source /home/azureuser/harvey/.env
    set +a
fi

# Run the command passed as arguments
exec "$@"
WRAPPER

chmod +x /home/azureuser/harvey/run_with_env.sh

# Update cron jobs to use the wrapper
echo "Updating cron jobs..."
(crontab -l 2>/dev/null | grep -v "sanity_check" | grep -v "ml_scheduler") > /tmp/cron_updated

# Add sanity check with environment loading
cat >> /tmp/cron_updated << 'CRON'
# Daily sanity check at 2:00 AM with environment loading
0 2 * * * /home/azureuser/harvey/run_with_env.sh /home/azureuser/miniconda3/bin/python /home/azureuser/harvey/harvey_sanity_check_v3_with_email.py >> /home/azureuser/harvey/logs/sanity_cron.log 2>&1

# ML Schedulers (if needed in future)
# 0 1 * * * /home/azureuser/harvey/run_with_env.sh /home/azureuser/miniconda3/bin/python /home/azureuser/harvey/run_ml_payout_rating.py >> /home/azureuser/harvey/logs/ml_payout.log 2>&1
CRON

crontab /tmp/cron_updated
rm /tmp/cron_updated

echo "✅ Cron jobs updated"

# Test environment loading
echo ""
echo "Testing environment variables..."
/home/azureuser/harvey/run_with_env.sh /home/azureuser/miniconda3/bin/python << 'TEST'
import os

vars_to_check = [
    ("HARVEY_AI_API_KEY", True),
    ("SENDGRID_API_KEY", True), 
    ("SQLSERVER_HOST", False),
    ("SQLSERVER_DB", False),
    ("SQLSERVER_USER", False),
    ("SQLSERVER_PASSWORD", True),
    ("ML_API_BASE_URL", False),
    ("GEMINI_API_KEY", True),
    ("ALERT_EMAIL_TO", False)
]

print("\n✅ Environment Variables Loaded:")
print("-" * 50)
for var, is_secret in vars_to_check:
    value = os.getenv(var)
    if value:
        if is_secret:
            masked = f"***{value[-4:]}" if len(value) > 4 else "***"
            print(f"  {var}: {masked}")
        else:
            print(f"  {var}: {value}")
    else:
        print(f"  {var}: ⚠️ NOT SET")
print("-" * 50)
TEST

echo ""
echo "✅ Environment setup complete!"
REMOTE_SETUP

echo ""
echo "🏃 Step 3: Running sanity check with new environment..."
ssh $AZURE_USER@$AZURE_VM_IP "/home/azureuser/harvey/run_with_env.sh /home/azureuser/miniconda3/bin/python /home/azureuser/harvey/harvey_sanity_check_v3_with_email.py"

echo ""
echo "=================================================="
echo "✅ ENVIRONMENT DEPLOYMENT COMPLETE!"
echo "=================================================="
echo ""
echo "Summary:"
echo "  ✓ Environment file deployed to Azure VM"
echo "  ✓ Permissions secured (600)"
echo "  ✓ Wrapper script created for cron jobs"
echo "  ✓ Cron jobs updated to load environment"
echo "  ✓ Email alerts: dev@heydividend.com"
echo ""
echo "Critical services configured:"
echo "  • Database: Azure SQL Server"
echo "  • Email: SendGrid"
echo "  • ML Service: Port 9000"
echo "  • Harvey API: Port 8001"
echo ""
echo "To manually test sanity check:"
echo "  ssh $AZURE_USER@$AZURE_VM_IP"
echo "  cd /home/azureuser/harvey"
echo "  ./run_with_env.sh python harvey_sanity_check_v3_with_email.py"
echo ""
echo "=================================================="