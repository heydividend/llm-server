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
