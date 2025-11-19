#!/bin/bash
# Deploy Gemini Enhancements to Azure VM
# Run this script on Azure VM (20.81.210.213) after git pull

set -e

echo "=========================================="
echo "  Deploying Gemini Enhancements to Harvey"
echo "=========================================="

# Step 1: Initialize and activate conda environment
echo ""
echo "Step 1: Initializing and activating conda environment..."
eval "$(conda shell.bash hook)"
conda activate llm

# Step 2: Install google-generativeai package
echo ""
echo "Step 2: Installing google-generativeai package..."
pip install google-generativeai==0.8.3

# Step 3: Create Gemini database tables
echo ""
echo "Step 3: Creating Gemini database tables..."
python <<'EOF'
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

# Load environment
load_dotenv()

# Get database connection from environment
HOST = os.getenv("SQLSERVER_HOST")
PORT = os.getenv("SQLSERVER_PORT", "1433")
DB = os.getenv("SQLSERVER_DB")
USER = os.getenv("SQLSERVER_USER")
PWD = os.getenv("SQLSERVER_PASSWORD")

# Create engine
ENGINE_URL = f"mssql+pymssql://{quote_plus(USER)}:{quote_plus(PWD)}@{HOST}:{PORT}/{quote_plus(DB)}"
engine = create_engine(ENGINE_URL)

# Read schema SQL
sys.path.append('/home/azureuser/harvey')
from app.config.features_schema import CREATE_FEATURES_TABLES_SQL

print("Executing database schema creation...")
with engine.connect() as conn:
    # Split and execute each statement
    statements = CREATE_FEATURES_TABLES_SQL.split('GO')
    for stmt in statements:
        if stmt.strip():
            conn.execute(text(stmt))
            conn.commit()

print("✅ Database tables created successfully!")
print("")
print("Created tables:")
print("  - feedback_labels")
print("  - fine_tuning_samples")
print("  - learning_metrics")
print("  - ml_evaluation_audit")
EOF

# Step 4: Restart Harvey backend
echo ""
echo "Step 4: Restarting Harvey backend..."
sudo systemctl restart harvey-backend

# Step 5: Verify installation
echo ""
echo "Step 5: Verifying Gemini installation..."
python -c "import google.generativeai as genai; print('✅ google-generativeai imported successfully')"

# Step 6: Test Gemini client
echo ""
echo "Step 6: Testing Gemini client..."
python <<'EOF'
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    print(f"✅ GEMINI_API_KEY found (length: {len(api_key)})")
else:
    print("❌ GEMINI_API_KEY not found in environment")
    exit(1)

# Test import of Gemini services
try:
    from app.services.gemini_client import gemini_client
    print("✅ GeminiClient imported successfully")
except Exception as e:
    print(f"❌ Failed to import GeminiClient: {e}")
    exit(1)
EOF

echo ""
echo "=========================================="
echo "  ✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Test Gemini training generator:"
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
