#!/bin/bash
#
# Setup logging infrastructure for Harvey on Azure VM
#

set -e

echo "Setting up Harvey logging infrastructure..."

# Create log directories
echo "Creating log directories..."
sudo mkdir -p /var/log/harvey
sudo mkdir -p /opt/harvey-backend/logs
sudo mkdir -p /opt/harvey-intelligence/logs

# Set permissions
echo "Setting permissions..."
sudo chown -R azureuser:azureuser /var/log/harvey
sudo chown -R azureuser:azureuser /opt/harvey-backend/logs
sudo chown -R azureuser:azureuser /opt/harvey-intelligence/logs

# Create logrotate configuration
echo "Setting up log rotation..."
sudo tee /etc/logrotate.d/harvey > /dev/null << 'EOF'
# Harvey Backend logs
/var/log/harvey/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0644 azureuser azureuser
    sharedscripts
    postrotate
        systemctl reload harvey-backend || true
        systemctl reload harvey-intelligence || true
    endscript
}

# Harvey application logs
/opt/harvey-backend/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 azureuser azureuser
}

/opt/harvey-intelligence/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 azureuser azureuser
}
EOF

# Create rsyslog configuration for Harvey
echo "Setting up rsyslog for Harvey..."
sudo tee /etc/rsyslog.d/30-harvey.conf > /dev/null << 'EOF'
# Harvey Backend Service
if $programname == 'harvey-backend' then /var/log/harvey/backend.log
& stop

# Harvey Intelligence Service
if $programname == 'harvey-intelligence' then /var/log/harvey/intelligence.log
& stop
EOF

# Restart rsyslog
sudo systemctl restart rsyslog

# Create journald configuration for Harvey
echo "Configuring journald for Harvey..."
sudo mkdir -p /etc/systemd/journal.conf.d/
sudo tee /etc/systemd/journal.conf.d/harvey.conf > /dev/null << 'EOF'
[Journal]
# Keep Harvey logs for 30 days
MaxRetentionSec=30d
SystemMaxUse=1G
SystemKeepFree=100M
EOF

# Reload journald
sudo systemctl restart systemd-journald

# Create log monitoring script
echo "Creating log monitoring script..."
sudo tee /usr/local/bin/harvey-logs > /dev/null << 'EOF'
#!/bin/bash
#
# Harvey log monitoring utility
#

case "$1" in
    backend)
        sudo journalctl -u harvey-backend -f
        ;;
    intelligence)
        sudo journalctl -u harvey-intelligence -f
        ;;
    all)
        sudo journalctl -u harvey-backend -u harvey-intelligence -f
        ;;
    errors)
        sudo journalctl -u harvey-backend -u harvey-intelligence -p err -f
        ;;
    *)
        echo "Usage: harvey-logs {backend|intelligence|all|errors}"
        echo ""
        echo "  backend      - Show harvey-backend logs"
        echo "  intelligence - Show harvey-intelligence logs"
        echo "  all         - Show all Harvey logs"
        echo "  errors      - Show only error logs"
        exit 1
        ;;
esac
EOF

sudo chmod +x /usr/local/bin/harvey-logs

echo "Logging infrastructure setup complete!"
echo ""
echo "Log locations:"
echo "  - System logs: /var/log/harvey/"
echo "  - Application logs: /opt/harvey-backend/logs/"
echo "  - ML Engine logs: /opt/harvey-intelligence/logs/"
echo ""
echo "View logs with:"
echo "  - harvey-logs backend       # Backend logs"
echo "  - harvey-logs intelligence  # ML engine logs"
echo "  - harvey-logs all          # All logs"
echo "  - harvey-logs errors       # Error logs only"
echo ""
echo "Or use journalctl directly:"
echo "  - sudo journalctl -u harvey-backend -f"
echo "  - sudo journalctl -u harvey-intelligence -f"