#!/bin/bash
# Find or create Harvey API key

echo "=== Checking for API keys in Harvey environment ==="

# Check .env for API keys
cd /home/azureuser/harvey
echo -e "\n1. Checking .env for Harvey API keys:"
grep -i "harvey.*api.*key\|internal.*api.*key\|api.*key.*harvey" .env 2>/dev/null || echo "No Harvey API key found in .env"

# Check if there's a database table with API keys
echo -e "\n2. Checking database for API keys:"
python3 << 'PYEOF'
import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

try:
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={os.getenv('SQLSERVER_HOST')};"
        f"DATABASE={os.getenv('SQLSERVER_DB')};"
        f"UID={os.getenv('SQLSERVER_USER')};"
        f"PWD={os.getenv('SQLSERVER_PASSWORD')};"
        f"TrustServerCertificate=yes;"
    )
    conn = pyodbc.connect(conn_str, timeout=5)
    cursor = conn.cursor()
    
    # Check for api_keys table
    cursor.execute("SELECT TOP 1 api_key FROM api_keys ORDER BY created_at DESC")
    row = cursor.fetchone()
    if row:
        print(f"✅ Found API key in database: {row[0][:20]}...")
    else:
        print("No API keys found in database")
    conn.close()
except Exception as e:
    print(f"Could not check database: {e}")
PYEOF

# Check auth configuration
echo -e "\n3. Checking auth settings:"
grep -i "require.*auth\|auth.*required\|disable.*auth" .env 2>/dev/null || echo "No auth settings found"

