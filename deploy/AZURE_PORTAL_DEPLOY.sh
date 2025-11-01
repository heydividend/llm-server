#!/bin/bash
# Harvey Backend - Azure Portal Deployment Script
# Copy and paste this ENTIRE script into Azure Portal → VM → Run Command

set -e

echo "=========================================="
echo "Harvey Backend - Azure Portal Deployment"
echo "=========================================="
echo ""

# Configuration
HARVEY_DIR="/opt/harvey-backend"
GITHUB_REPO="https://github.com/heydividend/llm-server.git"

# Navigate to Harvey directory
cd "$HARVEY_DIR"

# Backup current .env
if [ -f .env ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo "✓ .env backed up"
fi

# Pull latest code from GitHub
echo "Pulling latest code from GitHub..."
git fetch origin
git reset --hard origin/main
git pull origin main
echo "✓ Code updated to commit: $(git rev-parse --short HEAD)"

# Install/update Python dependencies
echo "Installing Python dependencies..."
/opt/harvey-backend/venv/bin/pip install -r requirements.txt --upgrade --quiet
echo "✓ Dependencies updated"

# Restart Harvey backend service
echo "Restarting Harvey backend..."
systemctl restart harvey-backend
sleep 3
echo "✓ Service restarted"

# Check service status
echo ""
echo "Service Status:"
systemctl status harvey-backend --no-pager -l

# Test health endpoint
echo ""
echo "Testing health endpoint..."
sleep 2
if curl -s http://localhost:8000/healthz | grep -q "healthy"; then
    echo "✓ Harvey backend is healthy!"
else
    echo "⚠ Health check failed"
fi

# Show recent logs
echo ""
echo "Recent logs (last 30 lines):"
journalctl -u harvey-backend -n 30 --no-pager

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo "Latest commit: $(git rev-parse --short HEAD)"
echo "Service status: $(systemctl is-active harvey-backend)"
echo ""
echo "New features deployed:"
echo "  ✓ Portfolio upload (CSV, Excel, PDF, screenshots)"
echo "  ✓ PDF.co integration"
echo "  ✓ Feedback-driven learning system"
echo "  ✓ ML API timeout optimizations"
echo ""
echo "Next steps:"
echo "1. Deploy feedback database schema to Azure SQL Server"
echo "2. Test new features at http://20.81.210.213"
echo ""
