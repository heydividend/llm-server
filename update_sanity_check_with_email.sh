#!/bin/bash

# Update Sanity Check Script on Azure VM with Email Alert Capabilities

AZURE_VM_IP="20.81.210.213"
AZURE_USER="azureuser"
REMOTE_DIR="/home/azureuser/harvey"

echo "=================================================="
echo "🚀 Updating Sanity Check with Email Alerts"
echo "=================================================="
echo ""

# Create configuration script
cat > configure_email_alerts.sh << 'EOF'
#!/bin/bash

echo "Configuring email alerts for Harvey sanity check..."

# Set email recipient(s) - comma separated for multiple
echo "Please enter email address(es) to receive alerts (comma-separated):"
read ALERT_EMAILS

# Set from email (should be verified in SendGrid)
echo "Enter the FROM email address (default: alerts@harvey-ai.com):"
read FROM_EMAIL
FROM_EMAIL=${FROM_EMAIL:-alerts@harvey-ai.com}

# Add to environment if not already there
if ! grep -q "ALERT_EMAIL_TO" /home/azureuser/harvey/.env 2>/dev/null; then
    echo "" >> /home/azureuser/harvey/.env
    echo "# Email Alert Configuration" >> /home/azureuser/harvey/.env
    echo "ALERT_EMAIL_TO='$ALERT_EMAILS'" >> /home/azureuser/harvey/.env
    echo "ALERT_EMAIL_FROM='$FROM_EMAIL'" >> /home/azureuser/harvey/.env
fi

# Install SendGrid library if not installed
/home/azureuser/miniconda3/bin/pip install sendgrid

echo "✅ Email alerts configured!"
echo "   Recipients: $ALERT_EMAILS"
echo "   From: $FROM_EMAIL"
echo ""
echo "Note: SENDGRID_API_KEY must be set in environment for alerts to work"
EOF

echo "📤 Step 1: Copying new sanity check script with email alerts..."
echo "You'll be prompted for password:"
scp harvey_sanity_check_v3_with_email.py $AZURE_USER@$AZURE_VM_IP:$REMOTE_DIR/

echo ""
echo "📤 Step 2: Copying configuration script..."
scp configure_email_alerts.sh $AZURE_USER@$AZURE_VM_IP:$REMOTE_DIR/

echo ""
echo "🔧 Step 3: Setting up email configuration..."
ssh $AZURE_USER@$AZURE_VM_IP "cd $REMOTE_DIR && bash configure_email_alerts.sh"

echo ""
echo "🔄 Step 4: Updating cron job to use new script..."
ssh $AZURE_USER@$AZURE_VM_IP << 'REMOTE_COMMANDS'
# Update cron job to use the new script
(crontab -l 2>/dev/null | grep -v "harvey_sanity_check" ; echo "0 2 * * * cd /home/azureuser/harvey && /home/azureuser/miniconda3/bin/python harvey_sanity_check_v3_with_email.py >> /home/azureuser/harvey/logs/sanity_cron.log 2>&1") | crontab -

# Update systemd service if it exists
if [ -f /etc/systemd/system/harvey-sanity-check.service ]; then
    sudo sed -i 's/harvey_sanity_check_with_healing.py/harvey_sanity_check_v3_with_email.py/g' /etc/systemd/system/harvey-sanity-check.service
    sudo systemctl daemon-reload
    echo "✅ Systemd service updated"
fi

echo "✅ Cron job updated to use email-enabled script"
REMOTE_COMMANDS

echo ""
echo "🏃 Step 5: Running test to verify email alerts..."
ssh $AZURE_USER@$AZURE_VM_IP "cd $REMOTE_DIR && /home/azureuser/miniconda3/bin/python harvey_sanity_check_v3_with_email.py"

echo ""
echo "=================================================="
echo "✅ UPDATE COMPLETE!"
echo "=================================================="
echo ""
echo "📧 Email Alert Features:"
echo "  • Sends alerts when health score < 80%"
echo "  • Critical issues trigger immediate alerts"
echo "  • Failed auto-fixes are reported"
echo "  • Daily summary if issues found"
echo ""
echo "📊 Alert Severity Levels:"
echo "  • INFO: System healthy (80-100%)"
echo "  • WARNING: Needs attention (60-80%)"
echo "  • CRITICAL: Immediate action needed (<60%)"
echo ""
echo "⚙️ Email Configuration:"
echo "  • Recipients: Set in ALERT_EMAIL_TO"
echo "  • From: Set in ALERT_EMAIL_FROM"
echo "  • API Key: Uses SENDGRID_API_KEY"
echo ""
echo "To test email manually:"
echo "  ssh $AZURE_USER@$AZURE_VM_IP"
echo "  cd /home/azureuser/harvey"
echo "  python harvey_sanity_check_v3_with_email.py"
echo ""
echo "=================================================="