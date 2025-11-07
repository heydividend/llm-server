#!/bin/bash

# Setup Daily Sanity Check with Self-Healing on Azure VM

AZURE_VM_IP="20.81.210.213"
AZURE_USER="azureuser"
REMOTE_DIR="/home/azureuser/harvey"

echo "=================================================="
echo "🚀 Setting Up Daily Sanity Check & Self-Healing"
echo "=================================================="
echo ""

# Create setup script that will run on the VM
cat > setup_sanity_cron.sh << 'EOF'
#!/bin/bash

# Navigate to Harvey directory
cd /home/azureuser/harvey

# Create necessary directories
mkdir -p logs sanity_reports

# Set up daily cron job for sanity check (runs at 2:00 AM daily)
(crontab -l 2>/dev/null | grep -v "harvey_sanity_check_with_healing.py" ; echo "0 2 * * * cd /home/azureuser/harvey && /home/azureuser/miniconda3/bin/python harvey_sanity_check_with_healing.py >> /home/azureuser/harvey/logs/sanity_cron.log 2>&1") | crontab -

# Also create a systemd service for better control (optional)
sudo tee /etc/systemd/system/harvey-sanity-check.service > /dev/null << 'SERVICE'
[Unit]
Description=Harvey Sanity Check and Self-Healing
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/home/azureuser/harvey
ExecStart=/home/azureuser/miniconda3/bin/python /home/azureuser/harvey/harvey_sanity_check_with_healing.py
StandardOutput=journal
StandardError=journal
User=azureuser
Environment="PATH=/home/azureuser/miniconda3/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

[Install]
WantedBy=multi-user.target
SERVICE

# Create systemd timer for daily execution
sudo tee /etc/systemd/system/harvey-sanity-check.timer > /dev/null << 'TIMER'
[Unit]
Description=Daily Harvey Sanity Check Timer
Requires=harvey-sanity-check.service

[Timer]
OnCalendar=daily
OnCalendar=*-*-* 02:00:00
AccuracySec=1m
Persistent=true

[Install]
WantedBy=timers.target
TIMER

# Enable and start the timer
sudo systemctl daemon-reload
sudo systemctl enable harvey-sanity-check.timer
sudo systemctl start harvey-sanity-check.timer

echo "✅ Daily sanity check scheduled successfully!"
echo ""
echo "Cron job: Runs daily at 2:00 AM"
echo "Systemd timer: Also runs daily at 2:00 AM (as backup)"
echo ""
echo "To check status:"
echo "  - Cron: crontab -l"
echo "  - Systemd: sudo systemctl status harvey-sanity-check.timer"
echo ""
echo "To run manually:"
echo "  - Direct: python harvey_sanity_check_with_healing.py"
echo "  - Service: sudo systemctl start harvey-sanity-check.service"
echo ""
echo "Logs are saved to:"
echo "  - /home/azureuser/harvey/logs/sanity_check_*.log"
echo "  - /home/azureuser/harvey/sanity_reports/report_*.json"
EOF

echo "📤 Step 1: Copying sanity check script to Azure VM..."
echo "You'll be prompted for password:"
scp harvey_sanity_check_with_healing.py $AZURE_USER@$AZURE_VM_IP:$REMOTE_DIR/

echo ""
echo "📤 Step 2: Copying setup script to Azure VM..."
scp setup_sanity_cron.sh $AZURE_USER@$AZURE_VM_IP:$REMOTE_DIR/

echo ""
echo "🔧 Step 3: Running setup on Azure VM..."
ssh $AZURE_USER@$AZURE_VM_IP "cd $REMOTE_DIR && bash setup_sanity_cron.sh"

echo ""
echo "🏃 Step 4: Running initial sanity check..."
ssh $AZURE_USER@$AZURE_VM_IP "cd $REMOTE_DIR && /home/azureuser/miniconda3/bin/python harvey_sanity_check_with_healing.py"

echo ""
echo "=================================================="
echo "✅ SETUP COMPLETE!"
echo "=================================================="
echo ""
echo "Daily sanity checks are now scheduled to run at 2:00 AM"
echo "The self-healing service will automatically:"
echo "  • Check all critical components"
echo "  • Fix common issues (restart services, install packages)"
echo "  • Clean up old logs to save disk space"
echo "  • Alert on critical failures"
echo "  • Generate daily health reports"
echo ""
echo "To monitor:"
echo "  ssh $AZURE_USER@$AZURE_VM_IP"
echo "  tail -f /home/azureuser/harvey/logs/sanity_check_*.log"
echo ""
echo "=================================================="