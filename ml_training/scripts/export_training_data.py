#!/usr/bin/env python3
"""
Export Training Data from Production Database

Fetches historical dividend data from Azure SQL and exports to JSON for model training.
"""

import os
import json
import sys
from typing import List, Dict, Any
import pyodbc  # Install: pip install pyodbc

def get_connection_string() -> str:
    """Get database connection string from environment"""
    conn_str = os.getenv('DATABASE_URL')
    if not conn_str:
        raise ValueError("DATABASE_URL environment variable not set")
    return conn_str

def fetch_training_data(conn_str: str) -> List[Dict[str, Any]]:
    """Fetch training data from database"""
    
    query = """
    SELECT 
        symbol,
        amount,
        ex_date,
        payment_date,
        frequency,
        growth_1yr,
        growth_3yr,
        growth_5yr,
        payout_ratio,
        sector
    FROM dividend_schedules
    WHERE ex_date >= DATEADD(year, -10, GETDATE())
    ORDER BY symbol, ex_date
    """
    
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    try:
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        
        data = []
        for row in cursor.fetchall():
            data.append(dict(zip(columns, row)))
        
        return data
        
    finally:
        cursor.close()
        conn.close()

def export_to_json(data: List[Dict[str, Any]], output_path: str):
    """Export data to JSON file"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    print(f"✅ Exported {len(data)} records to {output_path}")

def main():
    print("📊 Exporting training data from production database...")
    print()
    
    try:
        # Get connection
        conn_str = get_connection_string()
        
        # Fetch data
        print("🔄 Fetching data from database...")
        data = fetch_training_data(conn_str)
        
        # Export to JSON
        output_path = "../data/training_data.json"
        export_to_json(data, output_path)
        
        # Summary
        print()
        print("📈 Data Summary:")
        print(f"   Total records: {len(data)}")
        
        if data:
            symbols = set(d['symbol'] for d in data)
            print(f"   Unique symbols: {len(symbols)}")
            
            sectors = set(d.get('sector') for d in data if d.get('sector'))
            print(f"   Sectors: {len(sectors)}")
        
        print()
        print("✨ Export complete!")
        print(f"   Data saved to: {output_path}")
        print()
        print("Next steps:")
        print("  1. Review exported data")
        print("  2. Run training: ./train_all_models.sh")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
