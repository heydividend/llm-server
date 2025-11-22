#!/usr/bin/env python3
"""
Export ESG-Enhanced Dividend Scoring Data

Fetches financial metrics + ESG scores from Azure SQL for dividend sustainability prediction.
Combines traditional financial health indicators with ESG factors for enhanced accuracy.
"""

import os
import json
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

def fetch_esg_data(conn) -> List[Dict[str, Any]]:
    """
    Fetch ESG-enhanced dividend scoring features
    
    Features:
    - Traditional financial metrics (7-metric system)
    - ESG scores (environmental, social, governance)
    - Dividend sustainability score (target variable)
    """
    
    query = """
    WITH LatestDividends AS (
        -- Get most recent dividend per symbol
        SELECT 
            cd.symbol_id,
            cd.amount,
            cd.frequency,
            cd.ex_date,
            ROW_NUMBER() OVER (PARTITION BY cd.symbol_id ORDER BY cd.ex_date DESC) as rn
        FROM Canonical_Dividends cd
        WHERE cd.ex_date >= DATEADD(year, -1, GETDATE())
            AND cd.amount > 0
    ),
    DividendGrowth AS (
        -- Calculate dividend growth stability
        SELECT 
            cd.symbol_id,
            AVG(cd.amount) as avg_dividend,
            STDEV(cd.amount) as stdev_dividend,
            (MAX(cd.amount) - MIN(cd.amount)) / NULLIF(MIN(cd.amount), 0) as growth_range
        FROM Canonical_Dividends cd
        WHERE cd.ex_date >= DATEADD(year, -3, GETDATE())
            AND cd.amount > 0
        GROUP BY cd.symbol_id
    ),
    LatestESG AS (
        -- Get most recent ESG scores per symbol
        SELECT 
            esg.symbol_id,
            esg.environmental_score,
            esg.social_score,
            esg.governance_score,
            esg.esg_composite,
            esg.esg_controversy_score,
            esg.carbon_intensity,
            esg.board_diversity,
            esg.labor_practices_score,
            ROW_NUMBER() OVER (PARTITION BY esg.symbol_id ORDER BY esg.scoring_date DESC) as rn
        FROM ESG_Scores esg
    )
    SELECT TOP 3000
        s.symbol,
        s.companyName as company_name,
        s.sector,
        s.industry,
        
        -- Latest dividend info
        cd.amount as current_dividend,
        cd.frequency,
        cd.ex_date,
        
        -- Traditional financial metrics (7-metric system)
        -- Note: These would ideally come from FinancialStatements table
        CAST(NULL AS FLOAT) as payout_ratio,
        CAST(NULL AS FLOAT) as fcf_payout_ratio,
        CAST(NULL AS FLOAT) as debt_to_equity,
        CAST(NULL AS FLOAT) as interest_coverage,
        CAST(NULL AS FLOAT) as earnings_growth_3y,
        COALESCE(dg.stdev_dividend / NULLIF(dg.avg_dividend, 0), 0) as dividend_growth_stability,
        CAST(NULL AS FLOAT) as cash_ratio,
        
        -- ESG metrics from ESG_Scores table (real data!)
        CAST(esg.environmental_score AS FLOAT) as environmental_score,
        CAST(esg.social_score AS FLOAT) as social_score,
        CAST(esg.governance_score AS FLOAT) as governance_score,
        CAST(esg.esg_composite AS FLOAT) as esg_composite,
        CAST(esg.esg_controversy_score AS FLOAT) as esg_controversy_score,
        CAST(esg.carbon_intensity AS FLOAT) as carbon_intensity,
        CAST(esg.board_diversity AS FLOAT) as board_diversity,
        CAST(esg.labor_practices_score AS FLOAT) as labor_practices_score,
        
        -- Dividend sustainability score (target variable)
        -- Simple proxy: higher growth stability + no cuts = higher score
        CASE 
            WHEN dg.stdev_dividend IS NULL OR dg.avg_dividend = 0 THEN 5.0
            WHEN dg.stdev_dividend / dg.avg_dividend < 0.1 THEN 9.0
            WHEN dg.stdev_dividend / dg.avg_dividend < 0.2 THEN 7.5
            WHEN dg.stdev_dividend / dg.avg_dividend < 0.3 THEN 6.0
            ELSE 4.0
        END as dividend_safety_score,
        
        -- Market context
        s.marketCap as market_cap,
        CAST(NULL AS FLOAT) as dividend_yield,
        
        -- Metadata
        GETDATE() as export_date
        
    FROM LatestDividends cd
    INNER JOIN Securities s ON cd.symbol_id = s.id
    LEFT JOIN DividendGrowth dg ON cd.symbol_id = dg.symbol_id
    LEFT JOIN LatestESG esg ON cd.symbol_id = esg.symbol_id AND esg.rn = 1
    WHERE cd.rn = 1  -- Most recent dividend only
        AND s.symbol IS NOT NULL
    ORDER BY s.marketCap DESC
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
    safety_scores = []
    sectors = set()
    
    for record in data:
        if record.get('symbol'):
            symbols.add(record['symbol'])
            validation['valid_records'] += 1
        
        if record.get('dividend_safety_score'):
            safety_scores.append(record['dividend_safety_score'])
        
        if record.get('sector'):
            sectors.add(record['sector'])
    
    validation['stats'] = {
        'unique_symbols': len(symbols),
        'unique_sectors': len(sectors),
        'avg_safety_score': round(sum(safety_scores) / len(safety_scores), 2) if safety_scores else 0,
        'min_safety_score': round(min(safety_scores), 2) if safety_scores else 0,
        'max_safety_score': round(max(safety_scores), 2) if safety_scores else 0
    }
    
    # Check for data issues
    if len(symbols) < 100:
        validation['issues'].append(f"Low symbol diversity: only {len(symbols)} symbols")
    
    if len(sectors) < 5:
        validation['issues'].append(f"Low sector diversity: only {len(sectors)} sectors")
    
    if not safety_scores:
        validation['issues'].append("No dividend safety scores calculated")
    
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

def main():
    print("=" * 60)
    print("📊 ESG-Enhanced Dividend Scoring Data Export")
    print("=" * 60)
    print()
    
    try:
        # Connect to database
        conn = get_db_connection()
        
        # Fetch data
        print("🔄 Fetching ESG dividend scoring data...")
        data = fetch_esg_data(conn)
        conn.close()
        
        # Validate data
        print("\n📋 Validating data quality...")
        validation = validate_data(data)
        
        print(f"\n✅ Validation Results:")
        print(f"   Total records: {validation['total_records']}")
        print(f"   Valid records: {validation['valid_records']}")
        print(f"   Unique symbols: {validation['stats']['unique_symbols']}")
        print(f"   Unique sectors: {validation['stats']['unique_sectors']}")
        print(f"   Avg safety score: {validation['stats']['avg_safety_score']}")
        print(f"   Safety score range: {validation['stats']['min_safety_score']} - {validation['stats']['max_safety_score']}")
        
        if validation['issues']:
            print(f"\n⚠️  Issues detected:")
            for issue in validation['issues']:
                print(f"   - {issue}")
        else:
            print(f"\n✅ No validation issues detected")
        
        # Create metadata
        metadata = {
            'export_date': datetime.utcnow().isoformat(),
            'model': 'esg_dividend_scorer',
            'version': '1.1.0',
            'validation': validation,
            'note': 'ESG scores from ESG_Scores table (FMP ESG Risk Ratings API)',
            'esg_data_provider': 'FMP',
            'esg_coverage': 'Letter ratings (A-C) converted to numeric scores. Pillar scores may be NULL for limited provider data.'
        }
        
        # Export to JSON
        output_path = "data/esg_dividend_data.json"
        print(f"\n📤 Exporting to {output_path}...")
        export_to_json(data, output_path, metadata)
        
        print("\n" + "=" * 60)
        print("✨ Export complete!")
        print("=" * 60)
        print(f"\n📁 Data saved to: {output_path}")
        print("\n🎯 Next steps:")
        print("  1. Review exported data")
        print("  2. Train model: python3 esg_integration.py \\")
        print(f"                  --data {output_path} \\")
        print("                  --output models/esg_scorer_model.joblib")
        print("\n📊 ESG Data Status:")
        print("   ✅ Real ESG scores from ESG_Scores table")
        print("   ✅ FMP ESG Risk Ratings API (letter ratings → numeric)")
        print("   ⚠️  Limited provider data: pillar scores may be NULL")
        print("\n💡 For enhanced ESG coverage:")
        print("   - Add complementary ESG providers (MSCI, Sustainalytics)")
        print("   - Run: python3 scripts/esg_ingestion.py --limit 1000")
        print()
        
    except Exception as e:
        print(f"\n❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
