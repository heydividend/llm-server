#!/bin/bash
# Script to commit and push ML endpoint fixes to GitHub

echo "================================================"
echo "📝 Pushing ML Endpoint Fixes to GitHub"
echo "================================================"
echo ""

# Check if we're in a git repository
if [ ! -d .git ]; then
    echo "❌ Error: Not in a git repository!"
    echo "Please run this from your project root directory"
    exit 1
fi

# Remove any lock files if they exist
if [ -f .git/index.lock ]; then
    echo "🔓 Removing git lock file..."
    rm -f .git/index.lock
    echo "✅ Lock file removed"
fi

# Check git status
echo "📊 Current git status:"
echo "------------------------"
git status --short

echo ""
echo "📝 Adding changes..."
git add app/services/ml_api_client.py

echo ""
echo "💾 Creating commit..."
git commit -m "Fix ML endpoint paths to match actual ML Service API

- Changed insights endpoint from GET /insights/{ticker} to POST /insights/symbol
- Changed health endpoint from /api/internal/ml/health to /health
- These changes fix the 404 errors when Harvey tries to communicate with ML Service"

echo ""
echo "🚀 Pushing to GitHub..."
git push origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "================================================"
    echo "✅ Successfully pushed to GitHub!"
    echo "================================================"
    echo ""
    echo "Next steps:"
    echo "1. SSH to Azure VM: ssh azureuser@20.81.210.213"
    echo "2. Pull changes: cd /home/azureuser/harvey && git pull origin main"
    echo "3. Restart Harvey: sudo systemctl restart harvey-backend"
    echo ""
else
    echo ""
    echo "⚠️ Push failed. Try running these commands manually:"
    echo "  git add app/services/ml_api_client.py"
    echo "  git commit -m 'Fix ML endpoint paths'"
    echo "  git push origin main"
fi