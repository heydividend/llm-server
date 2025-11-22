#!/usr/bin/env python3
"""
Export Dividend Cut Prediction Training Data

Fetches financial metrics and dividend history from Azure SQL for dividend cut risk modeling.
Uses quantitative factors (payout ratios, debt, liquidity, earnings trends).
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
    username = os.getenv('AZURE_SQL_USERNAME')  # Fixed: was AZURE_SQL_USER
    password = os.getenv('AZURE_SQL_PASSWORD')
    
    if not all([server, database, username, password]):
        raise ValueError("Missing required environment variables: AZURE_SQL_SERVER, AZURE_SQL_DATABASE, AZURE_SQL_USERNAME, AZURE_SQL_PASSWORD")
    
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

def fetch_dividend_cut_data(conn) -> List[Dict[str, Any]]:
    """
    Fetch dividend cut prediction features from database
    
    Features (27 total):
    - Coverage ratios (3): earnings_payout_ratio, fcf_payout_ratio, dividend_coverage_ratio
    - Financial health (4): debt_to_equity, current_ratio, interest_coverage, cash_to_debt
    - Profitability trends (6): roe, roa, profit_margin, operating_margin, earnings_growth_yoy, revenue_growth_yoy
    - Dividend history (4): dividend_streak_years, dividend_growth_3y, dividend_volatility, special_dividends_count
    - Market signals (4): stock_momentum_3m, volatility_30d, beta, short_interest_ratio
    - Company characteristics (3): market_cap_log, age_years, sector_risk_score
    """
    
    query = """
    -- ================================================
    -- Dividend Cut Prediction Data Export
    -- ================================================
    
    WITH DividendHistory AS (
        -- Get dividend history for last 5 years per symbol
        SELECT 
            cd.symbol_id,
            cd.ex_date,
            cd.amount,
            cd.dividend_type,
            YEAR(cd.ex_date) as div_year,
            LAG(cd.amount, 1) OVER (PARTITION BY cd.symbol_id ORDER BY cd.ex_date) as prev_amount,
            LAG(cd.amount, 4) OVER (PARTITION BY cd.symbol_id ORDER BY cd.ex_date) as prev_year_amount,
            ROW_NUMBER() OVER (PARTITION BY cd.symbol_id ORDER BY cd.ex_date DESC) as rn
        FROM Canonical_Dividends cd
        WHERE cd.ex_date >= DATEADD(year, -5, GETDATE())
            AND cd.amount > 0
    ),
    
    DividendCuts AS (
        -- Identify dividend cuts (>10% reduction QoQ or YoY)
        SELECT 
            symbol_id,
            CASE 
                WHEN prev_amount IS NOT NULL AND amount < (prev_amount * 0.9) THEN 1
                ELSE 0
            END as dividend_cut_qoq,
            CASE
                WHEN prev_year_amount IS NOT NULL AND amount < (prev_year_amount * 0.9) THEN 1
                ELSE 0
            END as dividend_cut_yoy
        FROM DividendHistory
        WHERE rn = 1  -- Most recent dividend only
    ),
    
    DividendStreaks AS (
        -- Calculate consecutive years of dividend payments
        SELECT 
            symbol_id,
            COUNT(DISTINCT div_year) as dividend_streak_years
        FROM DividendHistory
        WHERE dividend_type = 'REGULAR'
        GROUP BY symbol_id
    ),
    
    DividendGrowth AS (
        -- Calculate 3-year dividend CAGR
        SELECT 
            symbol_id,
            CASE 
                WHEN MIN(amount) > 0 AND MAX(amount) > 0 THEN
                    POWER(CAST(MAX(amount) AS FLOAT) / CAST(MIN(amount) AS FLOAT), 1.0/3.0) - 1
                ELSE NULL
            END as dividend_growth_3y
        FROM DividendHistory
        WHERE ex_date >= DATEADD(year, -3, GETDATE())
            AND dividend_type = 'REGULAR'
        GROUP BY symbol_id
    ),
    
    DividendVolatility AS (
        -- Calculate dividend payment volatility (standard deviation)
        SELECT 
            symbol_id,
            STDEV(amount) as dividend_volatility
        FROM DividendHistory
        WHERE dividend_type = 'REGULAR'
            AND ex_date >= DATEADD(year, -3, GETDATE())
        GROUP BY symbol_id
        HAVING COUNT(*) >= 4  -- Need at least 4 dividends for meaningful volatility
    ),
    
    SpecialDividends AS (
        -- Count special dividends in last 2 years
        SELECT 
            symbol_id,
            COUNT(*) as special_dividends_count
        FROM DividendHistory
        WHERE dividend_type IN ('SPECIAL', 'LIQUIDATING')
            AND ex_date >= DATEADD(year, -2, GETDATE())
        GROUP BY symbol_id
    ),
    
    LatestFinancials AS (
        -- Get most recent financial statement per symbol
        SELECT 
            fs.*,
            ROW_NUMBER() OVER (PARTITION BY fs.symbol_id ORDER BY fs.reporting_date DESC) as rn
        FROM FinancialStatements fs
        WHERE fs.reporting_date >= DATEADD(year, -1, GETDATE())  -- Last year only
            AND fs.period_type = 'quarterly'  -- Use quarterly for most recent data
    )
    
    SELECT TOP 5000
        -- Company identifiers
        s.symbol_id,
        s.ticker as symbol,
        s.company_name,
        COALESCE(s.sector, 'Unknown') as sector,
        COALESCE(s.industry, 'Unknown') as industry,
        
        -- Dividend cut labels (target variable)
        COALESCE(dc.dividend_cut_qoq, 0) as dividend_cut_qoq,
        COALESCE(dc.dividend_cut_yoy, 0) as dividend_cut_yoy,
        COALESCE(dc.dividend_cut_qoq, dc.dividend_cut_yoy, 0) as dividend_cut,  -- Combined label
        
        -- ========================================
        -- COVERAGE RATIOS (3 features)
        -- ========================================
        COALESCE(fs.earnings_payout_ratio, 0.5) as earnings_payout_ratio,
        COALESCE(fs.fcf_payout_ratio, 0.5) as fcf_payout_ratio,
        COALESCE(fs.dividend_coverage_ratio, 2.0) as dividend_coverage_ratio,
        
        -- ========================================
        -- FINANCIAL HEALTH (4 features)
        -- ========================================
        COALESCE(fs.debt_to_equity, 0.5) as debt_to_equity,
        COALESCE(fs.current_ratio, 1.5) as current_ratio,
        COALESCE(fs.interest_coverage, 5.0) as interest_coverage,
        COALESCE(fs.cash_to_debt, 0.3) as cash_to_debt,
        
        -- ========================================
        -- PROFITABILITY TRENDS (6 features)
        -- ========================================
        COALESCE(fs.roe, 0.10) as roe,
        COALESCE(fs.roa, 0.05) as roa,
        COALESCE(fs.profit_margin, 0.10) as profit_margin,
        COALESCE(fs.operating_margin, 0.15) as operating_margin,
        COALESCE(fs.earnings_growth_yoy, 0.05) as earnings_growth_yoy,
        COALESCE(fs.revenue_growth_yoy, 0.05) as revenue_growth_yoy,
        
        -- ========================================
        -- DIVIDEND HISTORY (4 features)
        -- ========================================
        COALESCE(ds.dividend_streak_years, 0) as dividend_streak_years,
        COALESCE(dg.dividend_growth_3y, 0.0) as dividend_growth_3y,
        COALESCE(dv.dividend_volatility, 0.0) as dividend_volatility,
        COALESCE(sd.special_dividends_count, 0) as special_dividends_count,
        
        -- ========================================
        -- MARKET SIGNALS (4 features)
        -- ========================================
        COALESCE(fs.stock_momentum_3m, 0.0) as stock_momentum_3m,
        COALESCE(fs.volatility_30d, 0.15) as volatility_30d,
        COALESCE(fs.beta, 1.0) as beta,
        COALESCE(fs.short_interest_ratio, 0.02) as short_interest_ratio,
        
        -- ========================================
        -- COMPANY CHARACTERISTICS (3 features)
        -- ========================================
        CASE 
            WHEN s.market_cap > 0 THEN LOG(s.market_cap)
            ELSE 20.0  -- Default log(market_cap) ~ $500M
        END as market_cap_log,
        COALESCE(fs.age_years, 10) as age_years,  -- Default to 10 years if unknown
        COALESCE(fs.sector_risk_score, 50.0) as sector_risk_score,  -- Default medium risk
        
        -- ========================================
        -- METADATA FOR TRACKING
        -- ========================================
        fs.reporting_date as financial_statement_date,
        s.market_cap,
        fs.revenue,
        fs.net_income,
        fs.free_cash_flow,
        fs.total_debt,
        fs.shareholders_equity,
        
        -- Data quality metrics
        CASE 
            WHEN fs.earnings_payout_ratio IS NULL THEN 0 ELSE 1 END +
            CASE WHEN fs.fcf_payout_ratio IS NULL THEN 0 ELSE 1 END +
            CASE WHEN fs.debt_to_equity IS NULL THEN 0 ELSE 1 END +
            CASE WHEN fs.current_ratio IS NULL THEN 0 ELSE 1 END +
            CASE WHEN fs.interest_coverage IS NULL THEN 0 ELSE 1 END +
            CASE WHEN fs.roe IS NULL THEN 0 ELSE 1 END +
            CASE WHEN fs.roa IS NULL THEN 0 ELSE 1 END +
            CASE WHEN fs.profit_margin IS NULL THEN 0 ELSE 1 END
        as feature_completeness_score,  -- Count of non-null critical features (max 8)
        
        GETDATE() as export_date
        
    FROM Symbols s
    
    -- Join latest financial statements
    INNER JOIN LatestFinancials fs ON s.symbol_id = fs.symbol_id AND fs.rn = 1
    
    -- Join dividend history aggregates
    LEFT JOIN DividendCuts dc ON s.symbol_id = dc.symbol_id
    LEFT JOIN DividendStreaks ds ON s.symbol_id = ds.symbol_id
    LEFT JOIN DividendGrowth dg ON s.symbol_id = dg.symbol_id
    LEFT JOIN DividendVolatility dv ON s.symbol_id = dv.symbol_id
    LEFT JOIN SpecialDividends sd ON s.symbol_id = sd.symbol_id
    
    WHERE 
        s.ticker IS NOT NULL
        AND s.market_cap > 100000000  -- Only companies > $100M market cap
        AND EXISTS (
            -- Must have dividend payment history
            SELECT 1 
            FROM Canonical_Dividends cd 
            WHERE cd.symbol_id = s.symbol_id 
                AND cd.ex_date >= DATEADD(year, -2, GETDATE())
        )
        -- Data quality filter: require at least 50% feature completeness
        AND (
            CASE WHEN fs.earnings_payout_ratio IS NULL THEN 0 ELSE 1 END +
            CASE WHEN fs.fcf_payout_ratio IS NULL THEN 0 ELSE 1 END +
            CASE WHEN fs.debt_to_equity IS NULL THEN 0 ELSE 1 END +
            CASE WHEN fs.current_ratio IS NULL THEN 0 ELSE 1 END +
            CASE WHEN fs.interest_coverage IS NULL THEN 0 ELSE 1 END +
            CASE WHEN fs.roe IS NULL THEN 0 ELSE 1 END +
            CASE WHEN fs.roa IS NULL THEN 0 ELSE 1 END +
            CASE WHEN fs.profit_margin IS NULL THEN 0 ELSE 1 END
        ) >= 4  -- At least 4 out of 8 critical features must be non-null
        
    ORDER BY 
        s.market_cap DESC,  -- Prioritize larger companies
        fs.reporting_date DESC;
    """
    
    cursor = conn.cursor()
    
    try:
        print("🔄 Executing query...")
        print("   - Joining Symbols, FinancialStatements, Canonical_Dividends")
        print("   - Calculating dividend history features (streaks, growth, volatility)")
        print("   - Filtering for companies with dividend history and >$100M market cap")
        print("   - Enforcing data quality requirements (>50% feature completeness)")
        
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
                # Convert Decimal to float for JSON serialization
                if hasattr(value, '__float__'):
                    value = float(value)
                record[column] = value
            data.append(record)
        
        print(f"✅ Fetched {len(data)} records with {len(columns)} features")
        return data
        
    except Exception as e:
        print(f"❌ Query execution failed: {e}")
        raise
    finally:
        cursor.close()

def validate_data(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate exported data quality"""
    
    validation = {
        'total_records': len(data),
        'valid_records': 0,
        'issues': [],
        'stats': {},
        'feature_quality': {}
    }
    
    if not data:
        validation['issues'].append("No data exported")
        return validation
    
    # Required features (27 total)
    required_features = [
        'earnings_payout_ratio', 'fcf_payout_ratio', 'dividend_coverage_ratio',
        'debt_to_equity', 'current_ratio', 'interest_coverage', 'cash_to_debt',
        'roe', 'roa', 'profit_margin', 'operating_margin', 'earnings_growth_yoy', 'revenue_growth_yoy',
        'dividend_streak_years', 'dividend_growth_3y', 'dividend_volatility', 'special_dividends_count',
        'stock_momentum_3m', 'volatility_30d', 'beta', 'short_interest_ratio',
        'market_cap_log', 'age_years', 'sector_risk_score'
    ]
    
    # Count records with key features
    symbols = set()
    cut_count = 0
    no_cut_count = 0
    feature_null_counts = {feature: 0 for feature in required_features}
    
    for record in data:
        if record.get('symbol'):
            symbols.add(record['symbol'])
            validation['valid_records'] += 1
        
        # Track dividend cuts
        if record.get('dividend_cut') == 1:
            cut_count += 1
        else:
            no_cut_count += 1
        
        # Track feature completeness
        for feature in required_features:
            if feature not in record or record[feature] is None:
                feature_null_counts[feature] += 1
    
    validation['stats'] = {
        'unique_symbols': len(symbols),
        'dividend_cuts': cut_count,
        'no_cuts': no_cut_count,
        'cut_rate': round(cut_count / len(data) * 100, 2) if data else 0
    }
    
    # Feature quality analysis
    for feature in required_features:
        null_rate = (feature_null_counts[feature] / len(data) * 100) if data else 0
        validation['feature_quality'][feature] = {
            'null_count': feature_null_counts[feature],
            'null_rate': round(null_rate, 2),
            'completeness': round(100 - null_rate, 2)
        }
    
    # Calculate overall feature completeness
    total_features = len(required_features) * len(data)
    total_nulls = sum(feature_null_counts.values())
    overall_completeness = ((total_features - total_nulls) / total_features * 100) if total_features > 0 else 0
    validation['stats']['overall_feature_completeness'] = round(overall_completeness, 2)
    
    # Identify low-quality features (>30% NULL)
    low_quality_features = [
        f for f in required_features 
        if validation['feature_quality'][f]['null_rate'] > 30
    ]
    
    # Check for data issues
    if len(symbols) < 10:
        validation['issues'].append(f"Low symbol diversity: only {len(symbols)} symbols")
    
    if cut_count == 0:
        validation['issues'].append("No dividend cuts found - model training may be limited")
    
    if cut_count / len(data) > 0.5:
        validation['issues'].append(f"High cut rate ({validation['stats']['cut_rate']}%) - data may be biased")
    
    if overall_completeness < 70:
        validation['issues'].append(f"Low feature completeness: {overall_completeness:.1f}% - many missing values")
    
    if low_quality_features:
        validation['issues'].append(f"Low-quality features (>30% NULL): {', '.join(low_quality_features[:5])}")
    
    if len(data) < 100:
        validation['issues'].append(f"Small dataset: only {len(data)} records - may not be sufficient for training")
    
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
    print("📊 Dividend Cut Prediction Data Export")
    print("=" * 60)
    print()
    
    try:
        # Connect to database
        conn = get_db_connection()
        
        # Fetch data
        print("🔄 Fetching dividend cut prediction data...")
        data = fetch_dividend_cut_data(conn)
        conn.close()
        
        # Validate data
        print("\n📋 Validating data quality...")
        validation = validate_data(data)
        
        print(f"\n✅ Validation Results:")
        print(f"   Total records: {validation['total_records']}")
        print(f"   Valid records: {validation['valid_records']}")
        print(f"   Unique symbols: {validation['stats']['unique_symbols']}")
        print(f"   Dividend cuts: {validation['stats']['dividend_cuts']}")
        print(f"   No cuts: {validation['stats']['no_cuts']}")
        print(f"   Cut rate: {validation['stats']['cut_rate']}%")
        print(f"   Overall feature completeness: {validation['stats']['overall_feature_completeness']}%")
        
        if validation['issues']:
            print(f"\n⚠️  Issues detected:")
            for issue in validation['issues']:
                print(f"   - {issue}")
        
        # Show top low-quality features if any
        low_quality = [(f, v['null_rate']) for f, v in validation['feature_quality'].items() if v['null_rate'] > 20]
        if low_quality:
            print(f"\n📊 Features with >20% NULL values:")
            for feature, null_rate in sorted(low_quality, key=lambda x: x[1], reverse=True)[:10]:
                print(f"   - {feature}: {null_rate}% NULL")
        
        # Create metadata
        metadata = {
            'export_date': datetime.utcnow().isoformat(),
            'model': 'dividend_cut_predictor',
            'version': '2.0.0',
            'data_source': 'Azure SQL - FinancialStatements + Canonical_Dividends',
            'features_count': 27,
            'validation': validation
        }
        
        # Export to JSON
        output_path = "data/dividend_cut_data.json"
        print(f"\n📤 Exporting to {output_path}...")
        export_to_json(data, output_path, metadata)
        
        print("\n" + "=" * 60)
        print("✨ Export complete!")
        print("=" * 60)
        print(f"\n📁 Data saved to: {output_path}")
        print(f"\n📊 Dataset Summary:")
        print(f"   - {len(data)} total records")
        print(f"   - {validation['stats']['unique_symbols']} unique symbols")
        print(f"   - {validation['stats']['overall_feature_completeness']}% feature completeness")
        print(f"   - {validation['stats']['dividend_cuts']} dividend cuts ({validation['stats']['cut_rate']}%)")
        print("\n🎯 Next steps:")
        print("  1. Review exported data quality")
        print("  2. Train model: python3 dividend_cut_prediction.py \\")
        print(f"                  --data {output_path} \\")
        print("                  --output models/dividend_cut_model.joblib")
        print()
        
    except Exception as e:
        print(f"\n❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
