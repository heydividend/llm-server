#!/usr/bin/env python3
"""
Export Anomaly Detection Training Data

Fetches comprehensive dividend history for anomaly detection model training.
Exports both JSON (for model training) and CSV (for quick audits).
"""

import os
import json
import csv
import sys
from datetime import datetime
from typing import List, Dict, Any

def get_db_connection():
    """Get database connection using environment variables (pyodbc or pymssql fallback)"""
    server = os.getenv('AZURE_SQL_SERVER')
    database = os.getenv('AZURE_SQL_DATABASE')
    username = os.getenv('AZURE_SQL_USER')
    password = os.getenv('AZURE_SQL_PASSWORD')
    
    if not all([server, database, username, password]):
        raise ValueError("Missing required environment variables: AZURE_SQL_SERVER, AZURE_SQL_DATABASE, AZURE_SQL_USER, AZURE_SQL_PASSWORD")
    
    print(f"📡 Connecting to Azure SQL: {server}/{database}")
    
    # Try pyodbc first, fall back to pymssql
    conn = None
    try:
        import pyodbc
        conn_str = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no'
        conn = pyodbc.connect(conn_str)
        print("✅ Connected via pyodbc")
    except Exception as e:
        print(f"⚠️  pyodbc failed, trying pymssql...")
        try:
            import pymssql
            conn = pymssql.connect(server=server, user=username, password=password, database=database)
            print("✅ Connected via pymssql")
        except Exception as e2:
            raise RuntimeError(f"Failed to connect with both pyodbc and pymssql: {str(e2)}")
    
    return conn

def fetch_anomaly_detection_data(conn) -> List[Dict[str, Any]]:
    """
    Fetch dividend history for anomaly detection
    
    Features for anomaly detection:
    - Dividend amounts and dates
    - Frequency and consistency
    - Growth patterns
    - Special/unusual dividends
    - Large deviations from historical patterns
    """
    
    query = """
    WITH DividendStats AS (
        -- Calculate per-symbol dividend statistics
        SELECT 
            cd.symbol_id,
            AVG(cd.amount) as avg_dividend,
            STDEV(cd.amount) as stdev_dividend,
            MIN(cd.amount) as min_dividend,
            MAX(cd.amount) as max_dividend,
            COUNT(*) as total_dividends
        FROM Canonical_Dividends cd
        WHERE cd.ex_date >= DATEADD(year, -5, GETDATE())
            AND cd.amount > 0
        GROUP BY cd.symbol_id
        HAVING COUNT(*) >= 4  -- At least 4 dividends for meaningful stats
    )
    SELECT TOP 10000
        s.symbol,
        s.companyName as company_name,
        s.sector,
        s.industry,
        
        -- Dividend details
        cd.ex_date,
        cd.declaration_date,
        cd.record_date,
        cd.pay_date as payment_date,
        cd.amount,
        cd.frequency,
        cd.dividend_type,
        cd.currency,
        
        -- Statistical features for anomaly detection
        stats.avg_dividend,
        stats.stdev_dividend,
        stats.min_dividend,
        stats.max_dividend,
        stats.total_dividends,
        
        -- Deviation from average (z-score)
        CASE 
            WHEN stats.stdev_dividend > 0 
            THEN (cd.amount - stats.avg_dividend) / stats.stdev_dividend
            ELSE 0
        END as z_score,
        
        -- Percent deviation from average
        CASE 
            WHEN stats.avg_dividend > 0
            THEN ((cd.amount - stats.avg_dividend) / stats.avg_dividend) * 100
            ELSE 0
        END as pct_deviation,
        
        -- Flag potential anomalies (>2 standard deviations)
        CASE 
            WHEN stats.stdev_dividend > 0 
                AND ABS(cd.amount - stats.avg_dividend) > (2 * stats.stdev_dividend)
            THEN 1
            ELSE 0
        END as potential_anomaly,
        
        -- Flag special dividends
        CASE 
            WHEN cd.dividend_type LIKE '%special%' 
                OR cd.dividend_type LIKE '%extra%'
            THEN 1
            ELSE 0
        END as is_special_dividend,
        
        -- Market context
        s.marketCap as market_cap,
        CAST(NULL AS FLOAT) as dividend_yield,
        
        -- Timing metrics
        CASE 
            WHEN cd.pay_date IS NOT NULL AND cd.ex_date IS NOT NULL 
            THEN DATEDIFF(day, cd.ex_date, cd.pay_date)
            ELSE NULL 
        END as days_to_payment,
        
        -- Metadata
        GETDATE() as export_date
        
    FROM Canonical_Dividends cd
    INNER JOIN Securities s ON cd.symbol_id = s.id
    INNER JOIN DividendStats stats ON cd.symbol_id = stats.symbol_id
    WHERE cd.ex_date >= DATEADD(year, -3, GETDATE())
        AND cd.amount > 0
    ORDER BY cd.ex_date DESC, s.symbol
    """
    
    cursor = conn.cursor()
    
    try:
        print("🔄 Executing query...")
        cursor.execute(query)
        
        # Get column names
        columns = [column[0] for column in cursor.description]
        
        # Fetch all rows
        data = []
        for row in cursor.fetchall():
            record = {}
            for i, column in enumerate(columns):
                value = row[i]
                # Convert datetime to ISO string
                if hasattr(value, 'isoformat'):
                    value = value.isoformat()
                record[column] = value
            data.append(record)
        
        print(f"✅ Fetched {len(data)} records")
        return data
        
    finally:
        cursor.close()

def validate_data(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate exported data quality"""
    
    validation = {
        'total_records': len(data),
        'valid_records': 0,
        'issues': [],
        'stats': {}
    }
    
    if not data:
        validation['issues'].append("No data exported")
        return validation
    
    # Count records with key features
    symbols = set()
    anomaly_count = 0
    special_dividend_count = 0
    missing_dates = 0
    
    for record in data:
        if record.get('symbol'):
            symbols.add(record['symbol'])
            validation['valid_records'] += 1
        
        if record.get('potential_anomaly') == 1:
            anomaly_count += 1
        
        if record.get('is_special_dividend') == 1:
            special_dividend_count += 1
        
        if not record.get('ex_date'):
            missing_dates += 1
    
    validation['stats'] = {
        'unique_symbols': len(symbols),
        'potential_anomalies': anomaly_count,
        'special_dividends': special_dividend_count,
        'anomaly_rate': round(anomaly_count / len(data) * 100, 2) if data else 0,
        'missing_ex_dates': missing_dates
    }
    
    # Check for data issues
    if len(symbols) < 50:
        validation['issues'].append(f"Low symbol diversity: only {len(symbols)} symbols")
    
    if anomaly_count == 0:
        validation['issues'].append("No potential anomalies found (model may have nothing to learn)")
    
    if missing_dates > len(data) * 0.1:
        validation['issues'].append(f"High missing date rate: {missing_dates} records missing ex_date")
    
    return validation

def export_to_json(data: List[Dict[str, Any]], output_path: str, metadata: Dict[str, Any]):
    """Export data to JSON file with metadata"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    export_package = {
        'metadata': metadata,
        'data': data
    }
    
    with open(output_path, 'w') as f:
        json.dump(export_package, f, indent=2, default=str)
    
    print(f"✅ Exported {len(data)} records to {output_path}")

def export_to_csv(data: List[Dict[str, Any]], output_path: str):
    """Export data to CSV file (for quick audits)"""
    if not data:
        return
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Get all keys from first record
    headers = list(data[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"✅ Exported CSV to {output_path}")

def main():
    print("=" * 60)
    print("📊 Anomaly Detection Data Export")
    print("=" * 60)
    print()
    
    try:
        # Connect to database
        conn = get_db_connection()
        
        # Fetch data
        print("🔄 Fetching dividend anomaly detection data...")
        data = fetch_anomaly_detection_data(conn)
        conn.close()
        
        # Validate data
        print("\n📋 Validating data quality...")
        validation = validate_data(data)
        
        print(f"\n✅ Validation Results:")
        print(f"   Total records: {validation['total_records']}")
        print(f"   Valid records: {validation['valid_records']}")
        print(f"   Unique symbols: {validation['stats']['unique_symbols']}")
        print(f"   Potential anomalies: {validation['stats']['potential_anomalies']}")
        print(f"   Special dividends: {validation['stats']['special_dividends']}")
        print(f"   Anomaly rate: {validation['stats']['anomaly_rate']}%")
        
        if validation['issues']:
            print(f"\n⚠️  Issues detected:")
            for issue in validation['issues']:
                print(f"   - {issue}")
        
        # Create metadata
        metadata = {
            'export_date': datetime.utcnow().isoformat(),
            'model': 'anomaly_detection',
            'version': '1.0.0',
            'validation': validation
        }
        
        # Export to JSON
        json_output = "data/dividends_anomaly.json"
        print(f"\n📤 Exporting to {json_output}...")
        export_to_json(data, json_output, metadata)
        
        # Export to CSV (for quick audits)
        csv_output = "data/dividends_anomaly.csv"
        print(f"📤 Exporting to {csv_output}...")
        export_to_csv(data, csv_output)
        
        print("\n" + "=" * 60)
        print("✨ Export complete!")
        print("=" * 60)
        print(f"\n📁 Files created:")
        print(f"   - {json_output} (for model training)")
        print(f"   - {csv_output} (for quick audits)")
        print("\n🎯 Next steps:")
        print("  1. Review exported data")
        print("  2. Train model: python3 anomaly_detection.py \\")
        print(f"                  --input {csv_output} \\")
        print("                  --mode train \\")
        print("                  --output models/anomaly_detection_model.joblib")
        print()
        
    except Exception as e:
        print(f"\n❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
