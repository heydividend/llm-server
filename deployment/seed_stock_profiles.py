#!/usr/bin/env python3
"""
Stock Profiles Data Seeder
Populates the stock_profiles table with sample dividend stocks for testing Dividend Lists feature
"""
import pymssql
import os
from datetime import datetime

def load_env():
    """Load environment variables from .env file"""
    env_vars = {}
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    
    if not os.path.exists(env_path):
        env_path = '/home/azureuser/harvey/.env'
    
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value.strip().strip('"').strip("'")
    
    return env_vars

def create_table(cursor):
    """Create stock_profiles table if it doesn't exist"""
    print("Creating stock_profiles table...")
    cursor.execute("""
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'stock_profiles')
    BEGIN
        CREATE TABLE stock_profiles (
            id INT IDENTITY(1,1) PRIMARY KEY,
            ticker VARCHAR(10) NOT NULL UNIQUE,
            company_name VARCHAR(200) NOT NULL,
            sector VARCHAR(100),
            current_price DECIMAL(18, 4),
            dividend_yield DECIMAL(10, 4),
            annual_dividend DECIMAL(18, 4),
            payout_ratio DECIMAL(10, 4),
            consecutive_years INT,
            payment_frequency VARCHAR(20),
            is_active BIT NOT NULL DEFAULT 1,
            last_updated DATETIME DEFAULT GETDATE()
        );
        
        CREATE INDEX IX_stock_profiles_ticker ON stock_profiles(ticker);
        CREATE INDEX IX_stock_profiles_sector ON stock_profiles(sector);
        CREATE INDEX IX_stock_profiles_dividend_yield ON stock_profiles(dividend_yield);
    END
    """)
    print("✓ Table created/verified")

def get_sample_stocks():
    """Return sample dividend stock data"""
    return [
        # Dividend Aristocrats (25+ years)
        ('JNJ', 'Johnson & Johnson', 'Healthcare', 156.50, 3.15, 4.93, 52.3, 61, 'Quarterly'),
        ('PG', 'Procter & Gamble', 'Consumer Staples', 152.30, 2.45, 3.73, 63.8, 67, 'Quarterly'),
        ('KO', 'The Coca-Cola Company', 'Consumer Staples', 58.75, 3.10, 1.82, 75.2, 61, 'Quarterly'),
        ('MMM', '3M Company', 'Industrials', 98.20, 6.12, 6.01, 248.5, 65, 'Quarterly'),
        ('CAT', 'Caterpillar Inc.', 'Industrials', 285.40, 2.10, 5.99, 35.4, 29, 'Quarterly'),
        
        # Dividend Kings (50+ years)
        ('ABBV', 'AbbVie Inc.', 'Healthcare', 168.90, 3.85, 6.50, 45.6, 52, 'Quarterly'),
        ('XOM', 'Exxon Mobil', 'Energy', 112.30, 3.25, 3.65, 42.1, 41, 'Quarterly'),
        ('CVX', 'Chevron Corporation', 'Energy', 158.75, 3.45, 5.48, 52.3, 36, 'Quarterly'),
        
        # High Yield (>5%)
        ('T', 'AT&T Inc.', 'Telecom', 19.85, 5.82, 1.16, 78.5, 39, 'Quarterly'),
        ('VZ', 'Verizon Communications', 'Telecom', 42.15, 6.25, 2.63, 65.2, 18, 'Quarterly'),
        ('MO', 'Altria Group', 'Consumer Staples', 48.20, 8.15, 3.93, 85.6, 54, 'Quarterly'),
        
        # REITs (Monthly Payers)
        ('O', 'Realty Income Corp', 'Real Estate', 59.30, 5.45, 3.23, 82.1, 28, 'Monthly'),
        ('STAG', 'STAG Industrial Inc', 'Real Estate', 38.75, 4.20, 1.63, 78.3, 13, 'Monthly'),
        ('MAIN', 'Main Street Capital', 'Financials', 45.60, 6.80, 3.10, 95.2, 14, 'Monthly'),
        
        # Additional quality dividend stocks
        ('WMT', 'Walmart Inc.', 'Consumer Staples', 175.85, 1.45, 2.55, 38.7, 50, 'Quarterly'),
        ('TGT', 'Target Corporation', 'Consumer Staples', 148.20, 3.15, 4.67, 58.2, 52, 'Quarterly'),
        ('HD', 'The Home Depot', 'Consumer Discretionary', 342.50, 2.35, 8.05, 45.8, 13, 'Quarterly'),
        ('LOW', 'Lowe\'s Companies', 'Consumer Discretionary', 258.30, 1.90, 4.91, 32.5, 61, 'Quarterly'),
        ('MCD', 'McDonald\'s Corporation', 'Consumer Discretionary', 292.75, 2.25, 6.59, 58.9, 47, 'Quarterly'),
        ('SBUX', 'Starbucks Corporation', 'Consumer Discretionary', 97.20, 2.15, 2.09, 68.4, 13, 'Quarterly'),
    ]

def seed_stocks(cursor, conn):
    """Insert sample stock data"""
    sample_stocks = get_sample_stocks()
    
    print(f"\nInserting {len(sample_stocks)} sample stocks...")
    inserted = 0
    skipped = 0
    
    for stock in sample_stocks:
        try:
            cursor.execute("""
                INSERT INTO stock_profiles 
                (ticker, company_name, sector, current_price, dividend_yield, 
                 annual_dividend, payout_ratio, consecutive_years, payment_frequency, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
            """, stock)
            conn.commit()
            inserted += 1
            print(f"  ✓ {stock[0]} - {stock[1]}")
        except Exception as e:
            if 'duplicate' in str(e).lower() or 'unique' in str(e).lower():
                skipped += 1
                print(f"  ⊘ {stock[0]} - Already exists (skipped)")
            else:
                print(f"  ✗ {stock[0]}: {str(e)[:80]}")
    
    return inserted, skipped, len(sample_stocks)

def main():
    """Main seeding function"""
    print("=" * 60)
    print("Stock Profiles Data Seeder")
    print("=" * 60)
    
    # Load environment
    env = load_env()
    
    # Connect to database
    print(f"\nConnecting to: {env['SQLSERVER_HOST']} / {env['SQLSERVER_DB']}")
    conn = pymssql.connect(
        server=env['SQLSERVER_HOST'],
        user=env['SQLSERVER_USER'],
        password=env['SQLSERVER_PASSWORD'],
        database=env['SQLSERVER_DB']
    )
    
    cursor = conn.cursor()
    
    # Create table
    create_table(cursor)
    conn.commit()
    
    # Seed data
    inserted, skipped, total = seed_stocks(cursor, conn)
    
    # Close connection
    cursor.close()
    conn.close()
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ Seeding complete!")
    print(f"   Inserted: {inserted}/{total} stocks")
    if skipped > 0:
        print(f"   Skipped:  {skipped} (already exist)")
    print("\nStock distribution:")
    print("  - Dividend Aristocrats (25+ years): 5 stocks")
    print("  - Dividend Kings (50+ years): 3 stocks")
    print("  - High Yield (>5%): 3 stocks")
    print("  - Monthly Payers (REITs): 3 stocks")
    print("  - Additional quality stocks: 6 stocks")
    print("=" * 60)

if __name__ == "__main__":
    main()
