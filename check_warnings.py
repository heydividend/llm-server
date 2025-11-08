#!/usr/bin/env python3
"""Check and analyze system warnings"""

import pymssql
import os
import sys
import requests

def check_database_tables():
    """Check for tables that trigger warnings"""
    print("=" * 60)
    print("DATABASE TABLE ANALYSIS")
    print("=" * 60)
    
    try:
        # Load environment variables
        env_path = '/home/azureuser/harvey/.env'
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip().strip('"').strip("'")
        
        # Connect to database
        conn = pymssql.connect(
            server=os.getenv('SQLSERVER_HOST'),
            user=os.getenv('SQLSERVER_USER'),
            password=os.getenv('SQLSERVER_PASSWORD'),
            database=os.getenv('SQLSERVER_DB')
        )
        cursor = conn.cursor()
        
        print("\n1. CHECKING FOR WARNING-TRIGGERING TABLES:")
        print("-" * 40)
        
        # Tables that the sanity check looks for
        required_tables = ['tickers', 'dividend_history', 'ticker_info']
        missing_tables = []
        existing_tables = []
        
        for table in required_tables:
            cursor.execute(f"""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = '{table}'
            """)
            exists = cursor.fetchone()[0] > 0
            if exists:
                cursor.execute(f'SELECT COUNT(*) FROM [{table}]')
                count = cursor.fetchone()[0]
                print(f"  ✅ {table}: EXISTS ({count:,} rows)")
                existing_tables.append(table)
            else:
                print(f"  ⚠️  {table}: NOT FOUND")
                missing_tables.append(table)
        
        print("\n2. ACTUAL DIVIDEND/TICKER RELATED TABLES:")
        print("-" * 40)
        
        # Find actual dividend/ticker related tables
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            AND (
                TABLE_NAME LIKE '%dividend%' 
                OR TABLE_NAME LIKE '%ticker%' 
                OR TABLE_NAME LIKE '%stock%'
                OR TABLE_NAME LIKE '%symbol%'
            )
            ORDER BY TABLE_NAME
        """)
        
        actual_tables = cursor.fetchall()
        if actual_tables:
            for row in actual_tables:
                table_name = row[0]
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM [{table_name}]')
                    count = cursor.fetchone()[0]
                    print(f"  • {table_name} ({count:,} rows)")
                except:
                    print(f"  • {table_name}")
        else:
            print("  No dividend/ticker related tables found!")
        
        print("\n3. LOOKING FOR ALTERNATIVE TABLE NAMES:")
        print("-" * 40)
        
        # Look for potential alternatives
        alternatives = {
            'dividend_history': ['dividends', 'dividend', 'dividend_data', 
                               'dividend_payments', 'stock_dividends', 
                               'historical_dividends', 'dividend_records'],
            'ticker_info': ['ticker_information', 'stock_info', 'stocks', 
                          'ticker_data', 'companies', 'symbols', 
                          'stock_symbols', 'company_info']
        }
        
        replacements = {}
        for missing_table in missing_tables:
            if missing_table in alternatives:
                print(f"\nAlternatives for '{missing_table}':")
                found_alternative = None
                for alt in alternatives[missing_table]:
                    cursor.execute(f"""
                        SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                        WHERE TABLE_NAME = '{alt}'
                    """)
                    if cursor.fetchone()[0] > 0:
                        cursor.execute(f'SELECT COUNT(*) FROM [{alt}]')
                        count = cursor.fetchone()[0]
                        print(f"  ✅ FOUND: {alt} ({count:,} rows)")
                        found_alternative = alt
                        replacements[missing_table] = alt
                        break
                if not found_alternative:
                    print(f"  ❌ No alternatives found")
        
        cursor.close()
        conn.close()
        
        return missing_tables, replacements
        
    except Exception as e:
        print(f"Database check error: {str(e)}")
        return [], {}

def check_endpoints():
    """Check API endpoints"""
    print("\n" + "=" * 60)
    print("API ENDPOINT ANALYSIS")
    print("=" * 60)
    
    print("\n1. HARVEY API:")
    try:
        # Try root endpoint
        response = requests.get("http://localhost:8001/", timeout=3)
        if response.status_code == 200:
            print(f"  ✅ Root endpoint: OK")
        else:
            print(f"  ⚠️  Root endpoint: Status {response.status_code}")
    except Exception as e:
        print(f"  ❌ Root endpoint: {str(e)}")
    
    # Try health endpoint
    try:
        response = requests.get("http://localhost:8001/health", timeout=3)
        if response.status_code == 200:
            print(f"  ✅ Health endpoint: OK")
        elif response.status_code == 404:
            print(f"  ⚠️  Health endpoint: Not Found (404)")
            print("     Consider adding: @app.get('/health')")
        else:
            print(f"  ⚠️  Health endpoint: Status {response.status_code}")
    except Exception as e:
        print(f"  ❌ Health endpoint: {str(e)}")
    
    print("\n2. ML SERVICE:")
    try:
        response = requests.get("http://localhost:9000/health", timeout=3)
        if response.status_code == 200:
            print(f"  ✅ ML Service: OK")
            print(f"     Response: {response.json()}")
        else:
            print(f"  ⚠️  ML Service: Status {response.status_code}")
    except Exception as e:
        print(f"  ❌ ML Service: {str(e)}")

def main():
    print("HARVEY SYSTEM WARNING ANALYSIS")
    print("=" * 60)
    
    # Check database tables
    missing_tables, replacements = check_database_tables()
    
    # Check endpoints
    check_endpoints()
    
    # Print recommendations
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS TO CLEAR WARNINGS")
    print("=" * 60)
    
    if missing_tables:
        print("\n📌 DATABASE TABLE WARNINGS:")
        for table in missing_tables:
            if table in replacements:
                print(f"  • '{table}' not found but '{replacements[table]}' exists")
                print(f"    → Update sanity check to look for '{replacements[table]}' instead")
            else:
                print(f"  • '{table}' is missing and no alternatives found")
                print(f"    → Either create the table or update sanity check to not require it")
    
    print("\n📌 API ENDPOINT WARNINGS:")
    print("  • Harvey API /health endpoint returns 404")
    print("    → Add a /health endpoint to main.py for proper health checks")
    
    print("\n📌 ACTION ITEMS TO GET TO 100% HEALTH:")
    print("  1. Update sanity check to use correct table names")
    print("  2. Add /health endpoint to Harvey API")
    print("  3. Remove deprecated datetime.utcnow() warnings")
    
if __name__ == "__main__":
    main()