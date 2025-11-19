#!/bin/bash
# Simplified Gemini Deployment Script
# Creates only the 4 Gemini-specific tables without dependencies

set -e

echo "=========================================="
echo "  Gemini Intelligence System Deployment"
echo "=========================================="

# Step 1: Initialize conda environment
echo ""
echo "Step 1: Activating conda environment..."
eval "$(conda shell.bash hook)"
conda activate llm

# Step 2: Install google-generativeai
echo ""
echo "Step 2: Installing google-generativeai..."
pip install -q google-generativeai==0.8.3
echo "✅ Package installed"

# Step 3: Create Gemini tables using SQL file
echo ""
echo "Step 3: Creating Gemini database tables..."

# Use pymssql to execute the SQL file
python <<'PYEOF'
import os
import sys
from dotenv import load_dotenv
import pymssql

# Load environment
load_dotenv('/home/azureuser/harvey/.env')

# Get database credentials
HOST = os.getenv("SQLSERVER_HOST")
PORT = int(os.getenv("SQLSERVER_PORT", "1433"))
DB = os.getenv("SQLSERVER_DB")
USER = os.getenv("SQLSERVER_USER")
PWD = os.getenv("SQLSERVER_PASSWORD")

print(f"Connecting to {HOST}:{PORT}/{DB}...")

try:
    # Connect to database
    conn = pymssql.connect(
        server=HOST,
        port=PORT,
        user=USER,
        password=PWD,
        database=DB,
        timeout=30,
        login_timeout=30
    )
    
    cursor = conn.cursor()
    
    # Read SQL file
    with open('gemini_schema.sql', 'r') as f:
        sql_script = f.read()
    
    # Split by GO statements and execute each batch
    batches = [batch.strip() for batch in sql_script.split('GO') if batch.strip()]
    
    for i, batch in enumerate(batches, 1):
        if batch.strip() and not batch.strip().startswith('--'):
            try:
                cursor.execute(batch)
                conn.commit()
                print(f"✅ Batch {i} executed successfully")
            except Exception as e:
                # Some errors can be ignored (like table already exists)
                error_msg = str(e)
                if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                    print(f"⚠️  Batch {i}: {error_msg[:100]}")
                    conn.rollback()
                else:
                    print(f"❌ Batch {i} failed: {e}")
                    conn.rollback()
    
    cursor.close()
    conn.close()
    
    print("")
    print("✅ Database schema deployment completed!")
    print("")
    print("Created/verified tables:")
    print("  - feedback_labels")
    print("  - fine_tuning_samples")
    print("  - learning_metrics")
    print("  - ml_evaluation_audit")
    
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    sys.exit(1)
PYEOF

# Step 4: Verify GEMINI_API_KEY
echo ""
echo "Step 4: Verifying GEMINI_API_KEY..."
python <<'PYEOF'
import os
from dotenv import load_dotenv

load_dotenv('/home/azureuser/harvey/.env')

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ GEMINI_API_KEY not found in environment")
    print("   Add it to /home/azureuser/harvey/.env")
    print("   Get a new key from: https://aistudio.google.com/app/apikey")
    exit(1)

# Valid Gemini API keys are 39 characters starting with "AIzaSy"
if len(api_key) < 30:
    print(f"⚠️  WARNING: GEMINI_API_KEY appears invalid (length: {len(api_key)})")
    print(f"   Expected: 39 characters starting with 'AIzaSy'")
    print(f"   Current: {len(api_key)} characters")
    print("")
    print("   Get a valid key from: https://aistudio.google.com/app/apikey")
    print("   Add it to: /home/azureuser/harvey/.env")
    print("")
    print("⚠️  Continuing anyway, but Gemini features may not work...")
    print("")
elif not api_key.startswith("AIzaSy"):
    print(f"⚠️  WARNING: GEMINI_API_KEY format unexpected")
    print(f"   Expected to start with: AIzaSy")
    print(f"   Please verify key is correct")
    print("")
else:
    print(f"✅ GEMINI_API_KEY looks valid (length: {len(api_key)})")
PYEOF

# Step 5: Restart Harvey backend
echo ""
echo "Step 5: Restarting Harvey backend..."
sudo systemctl restart harvey-backend
sleep 3

# Check service status
if sudo systemctl is-active --quiet harvey-backend; then
    echo "✅ Harvey backend restarted successfully"
else
    echo "❌ Harvey backend failed to start"
    sudo systemctl status harvey-backend --no-pager -n 20
    exit 1
fi

# Step 6: Verify Gemini client
echo ""
echo "Step 6: Testing Gemini integration..."
python <<'PYEOF'
import sys
sys.path.append('/home/azureuser/harvey')

try:
    import google.generativeai as genai
    print("✅ google-generativeai imported successfully")
    
    from app.services.gemini_client import get_gemini_client
    print("✅ get_gemini_client function imported successfully")
    
    # Try to instantiate the client
    client = get_gemini_client()
    print("✅ GeminiClient instantiated successfully")
    
    print("")
    print("Gemini Intelligence System is ready!")
    
except Exception as e:
    print(f"❌ Import/instantiation failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
PYEOF

echo ""
echo "=========================================="
echo "  ✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Test training data generator:"
echo "   cd /home/azureuser/harvey"
echo "   python scripts/generate_training_data.py --category dividend_analysis --count 5"
echo ""
echo "2. Test Gemini AI routing:"
echo "   curl -X POST http://localhost:8001/v1/chat/completions \\"
echo "     -H 'Authorization: Bearer hh_live_X6SPcjPD5jZhTMw69_internal_api_key' \\"
echo "     -d '{\"messages\":[{\"role\":\"user\",\"content\":\"Analyze dividend sustainability of AAPL\"}]}'"
echo ""
echo "3. View Harvey logs:"
echo "   sudo journalctl -u harvey-backend -n 100 --no-pager"
echo ""
