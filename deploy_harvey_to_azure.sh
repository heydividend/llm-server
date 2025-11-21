#!/bin/bash
# Harvey Deployment Script - Deploy to Azure VM from Replit
# Uses sshpass for password authentication
# SECURITY WARNING: SSH key authentication is more secure - consider switching

set -e

# Validate environment variables
if [ -z "$AZURE_VM_USER" ] || [ -z "$AZURE_VM_IP" ] || [ -z "$AZURE_VM_PASSWORD" ]; then
    echo "❌ ERROR: Missing required environment variables"
    echo "   Required: AZURE_VM_USER, AZURE_VM_IP, AZURE_VM_PASSWORD"
    exit 1
fi

echo "=========================================================================="
echo "🚀 Harvey Deployment - Azure VM"
echo "=========================================================================="
echo "Target: ${AZURE_VM_USER}@${AZURE_VM_IP}"
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Step 1: Pull latest code
echo "📥 Step 1: Pulling latest code on Azure VM..."
sshpass -p "$AZURE_VM_PASSWORD" ssh -o StrictHostKeyChecking=no ${AZURE_VM_USER}@${AZURE_VM_IP} \
    "cd /home/azureuser/harvey && git pull"
echo "   ✅ Code updated"
echo ""

# Step 2: Restart Harvey backend
echo "🔄 Step 2: Restarting Harvey backend service..."
sshpass -p "$AZURE_VM_PASSWORD" ssh -o StrictHostKeyChecking=no ${AZURE_VM_USER}@${AZURE_VM_IP} \
    "sudo systemctl restart harvey-backend"
sleep 3
echo "   ✅ Service restarted"
echo ""

# Step 3: Verify service status
echo "🔍 Step 3: Verifying deployment..."
sshpass -p "$AZURE_VM_PASSWORD" ssh -o StrictHostKeyChecking=no ${AZURE_VM_USER}@${AZURE_VM_IP} << 'VERIFY'
    echo ""
    echo "══════════════════════════════════════════════════════════════════"
    echo "Service Status:"
    echo "══════════════════════════════════════════════════════════════════"
    systemctl status harvey-backend --no-pager | head -12
    
    echo ""
    echo "══════════════════════════════════════════════════════════════════"
    echo "Recent Logs:"
    echo "══════════════════════════════════════════════════════════════════"
    sudo journalctl -u harvey-backend -n 15 --no-pager
VERIFY

echo ""
echo "=========================================================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================================================="
echo ""
echo "🌐 Harvey is live at:"
echo "   • API: http://20.81.210.213:8001"
echo "   • Docs: http://20.81.210.213:8001/docs"
echo "   • Health: http://20.81.210.213:8001/health"
echo ""
echo "📝 View logs:"
echo "   sudo journalctl -u harvey-backend -f"
echo ""
echo "⚠️  SECURITY RECOMMENDATION:"
echo "   Consider switching to SSH key authentication for better security"
echo "=========================================================================="
