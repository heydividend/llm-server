#!/bin/bash

# Deploy Sanity Check with dev@heydividend.com configured

AZURE_VM_IP="20.81.210.213"
AZURE_USER="azureuser"
REMOTE_DIR="/home/azureuser/harvey"

echo "=================================================="
echo "🚀 Deploying Sanity Check with Email Alerts"
echo "   Recipient: dev@heydividend.com"
echo "=================================================="
echo ""

echo "📤 Copying updated sanity check script..."
echo "You'll be prompted for password:"
scp harvey_sanity_check_v3_with_email.py $AZURE_USER@$AZURE_VM_IP:$REMOTE_DIR/

echo ""
echo "🔧 Configuring email settings on Azure VM..."
ssh $AZURE_USER@$AZURE_VM_IP << 'REMOTE_COMMANDS'
cd /home/azureuser/harvey

# Create or update .env file with email configuration
if [ ! -f .env ]; then
    touch .env
fi

# Add email configuration if not already present
if ! grep -q "ALERT_EMAIL_TO" .env; then
    echo "" >> .env
    echo "# Email Alert Configuration" >> .env
    echo "ALERT_EMAIL_TO=dev@heydividend.com" >> .env
    echo "ALERT_EMAIL_FROM=alerts@harvey-ai.com" >> .env
else
    # Update existing configuration
    sed -i 's/^ALERT_EMAIL_TO=.*/ALERT_EMAIL_TO=dev@heydividend.com/' .env
fi

# Install SendGrid if not installed
/home/azureuser/miniconda3/bin/pip install sendgrid --quiet

# Update cron job to use the email-enabled script
(crontab -l 2>/dev/null | grep -v "harvey_sanity_check" ; echo "0 2 * * * cd /home/azureuser/harvey && /home/azureuser/miniconda3/bin/python harvey_sanity_check_v3_with_email.py >> /home/azureuser/harvey/logs/sanity_cron.log 2>&1") | crontab -

# Update systemd service if it exists
if [ -f /etc/systemd/system/harvey-sanity-check.service ]; then
    sudo sed -i 's/harvey_sanity_check.*\.py/harvey_sanity_check_v3_with_email.py/g' /etc/systemd/system/harvey-sanity-check.service
    sudo systemctl daemon-reload
fi

echo "✅ Configuration complete!"
echo "   Email alerts will be sent to: dev@heydividend.com"
echo "   From: alerts@harvey-ai.com"
REMOTE_COMMANDS

echo ""
echo "🏃 Running test sanity check..."
ssh $AZURE_USER@$AZURE_VM_IP "cd $REMOTE_DIR && /home/azureuser/miniconda3/bin/python harvey_sanity_check_v3_with_email.py"

echo ""
echo "=================================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=================================================="
echo ""
echo "📧 Email alerts configured:"
echo "   • Recipient: dev@heydividend.com"
echo "   • Sender: alerts@harvey-ai.com"
echo "   • Schedule: Daily at 2:00 AM"
echo ""
echo "📊 Alerts will be sent when:"
echo "   • Health score < 80%"
echo "   • Critical services fail"
echo "   • Auto-fixes can't resolve issues"
echo ""
echo "📝 To manually test:"
echo "   ssh $AZURE_USER@$AZURE_VM_IP"
echo "   cd /home/azureuser/harvey"
echo "   python harvey_sanity_check_v3_with_email.py"
echo ""
echo "=================================================="