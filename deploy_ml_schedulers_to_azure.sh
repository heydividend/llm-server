#!/bin/bash

# Harvey ML Schedulers Deployment Script
# Syncs new ML scheduler features from Replit to Azure VM
# Author: Harvey Team
# Date: November 2024

set -e  # Exit on error

# Configuration
AZURE_VM_IP="20.81.210.213"
AZURE_USER="azureuser"
REMOTE_PATH="/home/azureuser/harvey"
LOCAL_PATH="."

echo "=================================================="
echo "🚀 Harvey ML Schedulers Deployment to Azure VM"
echo "=================================================="
echo "Target: $AZURE_USER@$AZURE_VM_IP"
echo "Remote Path: $REMOTE_PATH"
echo ""

# Function to check if SSH is available
check_ssh() {
    echo "🔍 Checking SSH connection..."
    if ssh -o ConnectTimeout=5 $AZURE_USER@$AZURE_VM_IP "echo 'SSH connection successful'" > /dev/null 2>&1; then
        echo "✅ SSH connection established"
        return 0
    else
        echo "❌ Cannot connect to Azure VM via SSH"
        echo "Please ensure:"
        echo "1. SSH key is configured"
        echo "2. VM is running"
        echo "3. Network connection is available"
        exit 1
    fi
}

# Function to backup existing files
backup_files() {
    echo ""
    echo "📦 Creating backup on Azure VM..."
    ssh $AZURE_USER@$AZURE_VM_IP << 'EOF'
        cd /home/azureuser/harvey
        backup_dir="backups/backup_$(date +%Y%m%d_%H%M%S)"
        mkdir -p $backup_dir
        
        # Backup critical files
        cp -r app/routes $backup_dir/routes_backup 2>/dev/null || true
        cp -r app/services $backup_dir/services_backup 2>/dev/null || true
        cp -r app/core $backup_dir/core_backup 2>/dev/null || true
        cp main.py $backup_dir/main.py.backup 2>/dev/null || true
        
        echo "✅ Backup created at: $backup_dir"
EOF
}

# Function to sync new files
sync_files() {
    echo ""
    echo "📤 Syncing new ML scheduler files to Azure VM..."
    
    # Create list of files to sync
    cat > /tmp/sync_files.txt << 'EOF'
app/routes/ml_schedulers.py
app/services/ml_schedulers_service.py
app/services/ml_api_client.py
app/services/ml_integration.py
app/core/self_healing.py
main.py
API_DOCUMENTATION.md
API_USAGE_GUIDE.md
replit.md
EOF

    # Sync each file
    while IFS= read -r file; do
        if [ -f "$file" ]; then
            echo "  📄 Syncing $file..."
            # Create directory structure if it doesn't exist
            dir=$(dirname "$file")
            ssh $AZURE_USER@$AZURE_VM_IP "mkdir -p $REMOTE_PATH/$dir"
            # Copy the file
            scp -q "$file" "$AZURE_USER@$AZURE_VM_IP:$REMOTE_PATH/$file"
        else
            echo "  ⚠️  File not found: $file (skipping)"
        fi
    done < /tmp/sync_files.txt
    
    echo "✅ File sync completed"
    rm /tmp/sync_files.txt
}

# Function to install dependencies
install_dependencies() {
    echo ""
    echo "📦 Installing Python dependencies on Azure VM..."
    ssh $AZURE_USER@$AZURE_VM_IP << 'EOF'
        cd /home/azureuser/harvey
        
        # Check if aiohttp is in requirements.txt
        if ! grep -q "aiohttp" requirements.txt; then
            echo "aiohttp==3.12.15" >> requirements.txt
            echo "Added aiohttp to requirements.txt"
        fi
        
        # Install/update dependencies
        source venv/bin/activate
        pip install aiohttp --upgrade
        
        echo "✅ Dependencies installed"
EOF
}

# Function to restart services
restart_services() {
    echo ""
    echo "🔄 Restarting Harvey services..."
    ssh $AZURE_USER@$AZURE_VM_IP << 'EOF'
        # Restart Harvey main API
        echo "  Restarting Harvey API..."
        sudo systemctl restart harvey
        sleep 5
        
        # Check if service is running
        if sudo systemctl is-active --quiet harvey; then
            echo "  ✅ Harvey API restarted successfully"
        else
            echo "  ❌ Harvey API failed to restart"
            sudo journalctl -u harvey -n 20
        fi
        
        # Note: ML schedulers don't need restart as they run on timers
        echo "  ℹ️  ML Schedulers run on timers (no restart needed)"
EOF
}

# Function to verify deployment
verify_deployment() {
    echo ""
    echo "🔍 Verifying deployment..."
    echo ""
    
    # Check main API health
    echo "1. Testing Harvey API health..."
    if curl -s http://$AZURE_VM_IP:8001/healthz | grep -q "true"; then
        echo "   ✅ Harvey API is healthy"
    else
        echo "   ❌ Harvey API health check failed"
    fi
    
    # Check new ML scheduler endpoints
    echo ""
    echo "2. Testing new ML scheduler endpoints..."
    
    # Test health endpoint
    response=$(curl -s -w "\n%{http_code}" http://$AZURE_VM_IP:8001/v1/ml-schedulers/health 2>/dev/null | tail -n 1)
    if [ "$response" = "200" ]; then
        echo "   ✅ ML Scheduler health endpoint working"
    else
        echo "   ⚠️  ML Scheduler health endpoint returned: $response"
        echo "   Note: May require API key authentication"
    fi
    
    # Check ML Service
    echo ""
    echo "3. Testing ML Service..."
    if curl -s http://$AZURE_VM_IP:9000/health | grep -q "healthy"; then
        echo "   ✅ ML Service is healthy"
    else
        echo "   ❌ ML Service health check failed"
    fi
    
    echo ""
    echo "=================================================="
}

# Function to show next steps
show_next_steps() {
    echo "📋 Deployment Complete!"
    echo ""
    echo "✅ What was deployed:"
    echo "   • ML Scheduler API endpoints (/v1/ml-schedulers/*)"
    echo "   • Self-healing system with circuit breakers"
    echo "   • Enhanced ML integration with caching"
    echo "   • Updated API documentation"
    echo ""
    echo "🔧 Next steps:"
    echo "1. Test the new endpoints with your API key:"
    echo "   curl http://$AZURE_VM_IP:8001/v1/ml-schedulers/health -H 'Authorization: Bearer YOUR_API_KEY'"
    echo ""
    echo "2. Monitor the logs:"
    echo "   ssh $AZURE_USER@$AZURE_VM_IP 'sudo journalctl -u harvey -f'"
    echo ""
    echo "3. Check scheduler status:"
    echo "   ssh $AZURE_USER@$AZURE_VM_IP 'sudo systemctl status harvey-payout-rating.timer'"
    echo "   ssh $AZURE_USER@$AZURE_VM_IP 'sudo systemctl status harvey-dividend-calendar.timer'"
    echo ""
    echo "⏰ Scheduler Schedule:"
    echo "   • Payout Rating: Daily at 1:00 AM UTC"
    echo "   • Dividend Calendar: Sunday at 2:00 AM UTC"
    echo "   • ML Training: Sunday at 3:00 AM UTC"
    echo ""
    echo "=================================================="
}

# Main execution
main() {
    echo "Starting deployment process..."
    echo ""
    
    # Step 1: Check SSH connection
    check_ssh
    
    # Step 2: Backup existing files
    read -p "Do you want to create a backup? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        backup_files
    fi
    
    # Step 3: Sync files
    sync_files
    
    # Step 4: Install dependencies
    install_dependencies
    
    # Step 5: Restart services
    restart_services
    
    # Step 6: Verify deployment
    verify_deployment
    
    # Step 7: Show next steps
    show_next_steps
}

# Handle script interruption
trap 'echo ""; echo "🛑 Deployment interrupted!"; exit 1' INT TERM

# Run main function
main

echo ""
echo "🎉 Deployment script completed!"