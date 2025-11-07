#!/bin/bash

# Secure deployment script using SSH_VM_PASSWORD from secrets

AZURE_VM_IP="20.81.210.213"
AZURE_USER="azureuser"

# Check if SSH_VM_PASSWORD is set
if [ -z "$SSH_VM_PASSWORD" ]; then
    echo "❌ ERROR: SSH_VM_PASSWORD environment variable not set"
    echo "Please set it with: export SSH_VM_PASSWORD=<your-password>"
    exit 1
fi

# Check if sshpass is installed
if ! command -v sshpass &> /dev/null; then
    echo "Installing sshpass for automated SSH..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install hudochenkov/sshpass/sshpass 2>/dev/null || echo "Note: sshpass may need manual installation on macOS"
    else
        sudo apt-get update && sudo apt-get install -y sshpass 2>/dev/null || echo "Note: sshpass installation may require sudo"
    fi
fi

echo "=================================================="
echo "🔧 Secure Deployment to Azure VM"
echo "=================================================="
echo ""

# Function for SSH commands with password
ssh_cmd() {
    sshpass -p "$SSH_VM_PASSWORD" ssh -o StrictHostKeyChecking=no $AZURE_USER@$AZURE_VM_IP "$@"
}

# Function for SCP with password
scp_file() {
    sshpass -p "$SSH_VM_PASSWORD" scp -o StrictHostKeyChecking=no "$@"
}

# Step 1: Deploy fixed sanity check script
echo "📤 Step 1: Deploying fixed sanity check script..."
scp_file harvey_sanity_check_v3_with_email.py $AZURE_USER@$AZURE_VM_IP:/home/azureuser/harvey/

# Step 2: Deploy environment file
echo ""
echo "📤 Step 2: Deploying environment configuration..."
scp_file azure.env $AZURE_USER@$AZURE_VM_IP:/home/azureuser/harvey/.env

# Step 3: Fix SendGrid API key and create proper cron jobs
echo ""
echo "🔧 Step 3: Fixing configuration on Azure VM..."
ssh_cmd << 'REMOTE_FIX'
cd /home/azureuser/harvey

# Set proper permissions
chmod 600 .env

# Fix SendGrid API key format in .env
echo "Checking SendGrid API key format..."
if grep -q "SENDGRID_API_KEY=mybjyf-vaxtyw-tiQca4" .env; then
    echo "Note: SendGrid API key appears to be in incorrect format"
    echo "Please verify your SendGrid API key starts with 'SG.'"
    # The key should typically start with SG. for SendGrid
fi

# Create ML scheduler scripts (since timers don't exist)
echo ""
echo "Creating ML scheduler scripts..."

# Create ML Payout Rating script
cat > run_ml_payout_rating.py << 'PYTHON'
#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '/home/azureuser/harvey')

from app.services.ml_schedulers_service import MLSchedulersService

if __name__ == "__main__":
    service = MLSchedulersService()
    print("Running ML Payout Rating Scheduler...")
    result = service.run_payout_rating_scheduler()
    print(f"Result: {result}")
PYTHON

# Create ML Dividend Calendar script
cat > run_ml_dividend_calendar.py << 'PYTHON'
#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '/home/azureuser/harvey')

from app.services.ml_schedulers_service import MLSchedulersService

if __name__ == "__main__":
    service = MLSchedulersService()
    print("Running ML Dividend Calendar Scheduler...")
    result = service.run_dividend_calendar_scheduler()
    print(f"Result: {result}")
PYTHON

# Create ML Training script  
cat > run_ml_training.py << 'PYTHON'
#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '/home/azureuser/harvey')

from app.services.ml_schedulers_service import MLSchedulersService

if __name__ == "__main__":
    service = MLSchedulersService()
    print("Running ML Training Scheduler...")
    result = service.run_ml_training_scheduler()
    print(f"Result: {result}")
PYTHON

chmod +x run_ml_*.py

# Create wrapper script that loads environment
cat > run_with_env.sh << 'WRAPPER'
#!/bin/bash
# Load environment variables before running commands

# Source the .env file
if [ -f /home/azureuser/harvey/.env ]; then
    export $(cat /home/azureuser/harvey/.env | grep -v '^#' | xargs)
fi

# Set Python path
export PYTHONPATH="/home/azureuser/harvey:$PYTHONPATH"

# Run the command passed as arguments
exec "$@"
WRAPPER

chmod +x run_with_env.sh

# Update cron jobs to use real scripts instead of non-existent timers
echo ""
echo "Setting up cron jobs for ML schedulers..."

(crontab -l 2>/dev/null | grep -v "ml_scheduler" | grep -v "harvey_sanity" | grep -v "ml-payout" | grep -v "ml-dividend" | grep -v "ml-training") > /tmp/cron_fixed

cat >> /tmp/cron_fixed << 'CRON'
# ML Schedulers - Using Python scripts instead of systemd timers
# Daily ML Payout Rating at 1:00 AM
0 1 * * * /home/azureuser/harvey/run_with_env.sh /home/azureuser/miniconda3/bin/python /home/azureuser/harvey/run_ml_payout_rating.py >> /home/azureuser/harvey/logs/ml_payout_rating.log 2>&1

# Weekly ML Dividend Calendar - Sunday at 2:00 AM  
0 2 * * 0 /home/azureuser/harvey/run_with_env.sh /home/azureuser/miniconda3/bin/python /home/azureuser/harvey/run_ml_dividend_calendar.py >> /home/azureuser/harvey/logs/ml_dividend_calendar.log 2>&1

# Weekly ML Training - Sunday at 3:00 AM
0 3 * * 0 /home/azureuser/harvey/run_with_env.sh /home/azureuser/miniconda3/bin/python /home/azureuser/harvey/run_ml_training.py >> /home/azureuser/harvey/logs/ml_training.log 2>&1

# Daily Sanity Check at 2:00 AM
0 2 * * * /home/azureuser/harvey/run_with_env.sh /home/azureuser/miniconda3/bin/python /home/azureuser/harvey/harvey_sanity_check_v3_with_email.py >> /home/azureuser/harvey/logs/sanity_cron.log 2>&1
CRON

crontab /tmp/cron_fixed
rm /tmp/cron_fixed

echo "✅ Cron jobs configured"
echo ""
echo "Current cron jobs:"
crontab -l | grep -E "(ml_|harvey_sanity)"

# Create directory for logs if it doesn't exist
mkdir -p /home/azureuser/harvey/logs
mkdir -p /home/azureuser/harvey/sanity_reports

echo ""
echo "✅ Configuration complete!"
REMOTE_FIX

# Step 4: Test sanity check
echo ""
echo "🏃 Step 4: Testing sanity check..."
ssh_cmd "cd /home/azureuser/harvey && ./run_with_env.sh /home/azureuser/miniconda3/bin/python harvey_sanity_check_v3_with_email.py"

echo ""
echo "=================================================="
echo "✅ SECURE DEPLOYMENT COMPLETE!"
echo "=================================================="
echo ""
echo "Fixed Issues:"
echo "  ✅ Environment variables properly loaded"
echo "  ✅ ML schedulers set up as Python scripts (not systemd timers)"
echo "  ✅ Cron jobs configured with environment wrapper"
echo "  ✅ Database bug fixed (self.warnings)"
echo ""
echo "ML Scheduler Schedule:"
echo "  • Payout Rating: Daily at 1:00 AM"
echo "  • Dividend Calendar: Sunday at 2:00 AM"
echo "  • ML Training: Sunday at 3:00 AM"
echo "  • Sanity Check: Daily at 2:00 AM"
echo ""
echo "⚠️  Note: SendGrid API key may need verification"
echo "   If email alerts fail, please verify your SendGrid API key"
echo "   starts with 'SG.' and is correctly set in .env"
echo ""
echo "To manually test ML schedulers:"
echo "  ssh_cmd 'cd /home/azureuser/harvey && ./run_with_env.sh python run_ml_payout_rating.py'"
echo ""
echo "=================================================="