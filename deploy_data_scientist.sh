#!/bin/bash
set -e

echo "=========================================="
echo "Harvey AI - Data Scientist Agent Deployment"
echo "=========================================="
echo ""

# Use environment variables from Replit secrets (already loaded)
# No need to export from .env since AZURE_VM_* vars are in Replit secrets

AZURE_VM="${AZURE_VM_USER}@${AZURE_VM_IP}"
HARVEY_DIR="/home/azureuser/harvey"

echo "🎯 Target: $AZURE_VM"
echo "📁 Directory: $HARVEY_DIR"
echo ""

# Step 1: Copy SQL schema
echo "📤 Step 1: Copying SQL schema..."
sshpass -p "$SSH_VM_PASSWORD" scp -o StrictHostKeyChecking=no \
  /tmp/create_training_tables.sql \
  $AZURE_VM:/tmp/create_training_tables.sql
echo "   ✅ SQL schema copied"

# Step 2: Copy table creation script
echo "📤 Step 2: Copying table creation script..."
sshpass -p "$SSH_VM_PASSWORD" scp -o StrictHostKeyChecking=no \
  azure_vm_setup/create_training_tables.py \
  $AZURE_VM:$HARVEY_DIR/azure_vm_setup/create_training_tables.py
echo "   ✅ Table creation script copied"

# Step 3: Copy updated Data Scientist Agent
echo "📤 Step 3: Copying Data Scientist Agent..."
sshpass -p "$SSH_VM_PASSWORD" scp -o StrictHostKeyChecking=no \
  app/services/data_scientist_agent.py \
  $AZURE_VM:$HARVEY_DIR/app/services/data_scientist_agent.py
echo "   ✅ Data Scientist Agent copied"

# Step 4: Create training tables
echo "🗄️  Step 4: Creating training tables..."
sshpass -p "$SSH_VM_PASSWORD" ssh -o StrictHostKeyChecking=no $AZURE_VM << 'ENDSSH'
cd /home/azureuser/harvey
python3 azure_vm_setup/create_training_tables.py
ENDSSH
echo "   ✅ Training tables created"

# Step 5: Test connection
echo "🧪 Step 5: Testing database connection..."
sshpass -p "$SSH_VM_PASSWORD" ssh -o StrictHostKeyChecking=no $AZURE_VM << 'ENDSSH'
cd /home/azureuser/harvey
python3 -c "
import pymssql, os
from dotenv import load_dotenv

load_dotenv(override=True)

conn = pymssql.connect(
    server=os.getenv('SQLSERVER_HOST'),
    user=os.getenv('SQLSERVER_USER'),
    password=os.getenv('SQLSERVER_PASSWORD'),
    database=os.getenv('SQLSERVER_DB')
)

cursor = conn.cursor()

# Test training tables
tables = ['training_questions', 'training_responses', 'harvey_training_data', 
          'conversation_history', 'feedback_log', 'model_audit']

print('📊 Training Tables Status:')
print('=' * 60)
for table in tables:
    cursor.execute(f'SELECT COUNT(*) FROM {table}')
    count = cursor.fetchone()[0]
    print(f'   ✓ {table:<30} {count:>8} rows')
print('=' * 60)

conn.close()
"
ENDSSH
echo "   ✅ Database connection verified"

# Step 6: Run Data Scientist Agent (Schema Analysis)
echo "📊 Step 6: Running Data Scientist Agent (schema analysis)..."
sshpass -p "$SSH_VM_PASSWORD" ssh -o StrictHostKeyChecking=no $AZURE_VM << 'ENDSSH'
cd /home/azureuser/harvey
python3 scripts/data_scientist_agent.py --schema-only
ENDSSH

# Step 7: Run Full Analysis with AI Recommendations
echo "🤖 Step 7: Running full analysis with Gemini AI recommendations..."
sshpass -p "$SSH_VM_PASSWORD" ssh -o StrictHostKeyChecking=no $AZURE_VM << 'ENDSSH'
cd /home/azureuser/harvey
python3 scripts/data_scientist_agent.py --analyze --output /tmp/harvey_analysis.json
echo ""
echo "📄 Analysis report saved to: /tmp/harvey_analysis.json"
ENDSSH

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "📋 What was deployed:"
echo "   • Training tables (6 tables created)"
echo "   • Data Scientist Agent with pymssql"
echo "   • Database schema analysis"
echo "   • AI-powered ML recommendations"
echo ""
echo "📊 View the full analysis:"
echo "   sshpass -p \"\$SSH_VM_PASSWORD\" ssh $AZURE_VM 'cat /tmp/harvey_analysis.json' | jq ."
echo ""
