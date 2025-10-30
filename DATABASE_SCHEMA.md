# AskHeyDividend Database Schema

## Overview
This document describes the complete database structure for the AskHeyDividend financial assistant application, including both the financial data views (read-only) and portfolio management tables (user data).

---

## **Financial Data Views** (Read-only for AI queries)

### **1. `dbo.vTickers`** - Stock & ETF Information
Combines data from both stock and ETF ticker tables.

**Source Tables**: 
- `Ingest_Tickers_ETF_Data` 
- `Ingest_Tickers_Stock_Data`

**Key Columns**:
- `Ticker_ID` - Unique identifier
- `Ticker` - Stock/ETF ticker symbol
- `Ticker_Symbol_Name` - Full symbol name
- `Exchange` - Exchange code
- `Exchange_Full_Name` - Full exchange name
- `Company_Name` - Company or fund name
- `Website` - Company website URL
- `Sector` - Business sector (e.g., Utilities, Healthcare, Energy)
- `Industry` - Specific industry classification
- `Country` - Country of origin
- `Security_Type` - 'Stock' or 'ETF'
- `Reference_Asset` - Underlying asset reference
- `Benchmark_Index` - Benchmark index tracked
- `Description` - Full description
- `Inception_Date` - When the security was created
- `Gross_Expense_Ratio` - Annual expense ratio
- `ThirtyDay_SEC_Yield` - 30-day SEC yield
- `Distribution_Frequency` - Dividend distribution frequency
- `Created_At` - Record creation timestamp
- `Updated_At` - Record update timestamp

**Usage**: Queried for company information, sector analysis, and ticker lookups.

---

### **2. `dbo.vDividends`** - Dividend Payment History
Combines dividend data from stocks and ETFs.

**Source Tables**: 
- `Ingest_Dividends_Stock_Data` 
- `Ingest_Dividends_ETF_Data`

**Key Columns**:
- `Dividend_ID` - Unique identifier
- `Ticker` - Stock/ETF ticker symbol
- `Dividend_Amount` - Original dividend amount
- `AdjDividend_Amount` - Adjusted dividend amount (defaults to Dividend_Amount for ETFs)
- `Dividend_Type` - Type of dividend (stocks only)
- `Currency` - Currency code (stocks only)
- `Distribution_Frequency` - How often dividends are paid (stocks only)
- `Declaration_Date` - Date dividend was declared
- `Ex_Dividend_Date` - Ex-dividend date
- `Record_Date` - Record date
- `Payment_Date` - Date dividend was/will be paid
- `Security_Type` - 'Stock' or 'ETF'
- `Created_At` - Record creation timestamp
- `Updated_At` - Record update timestamp

**Usage**: Dividend history analysis, yield calculations, passive income portfolio planning.

---

### **3. `dbo.vPrices`** - Current Stock Prices & Volume
Combines price data from multiple sources.

**Source Tables**: 
- `Ingest_Prices_ETF_Data` 
- `Ingest_Prices_Stock_Data`

**Key Columns**:
- `Price_ID` - Unique identifier
- `Ticker` - Stock/ETF ticker symbol
- `Price` - Current or last trade price
- `Volume` - Trading volume
- `Bid` - Current bid price
- `Ask` - Current ask price
- `Bid_Size` - Bid size (ETFs only)
- `Ask_Size` - Ask size (ETFs only)
- `Trade_Timestamp_UTC` - Trade timestamp in UTC (ETFs only)
- `Quote_Timestamp_UTC` - Quote timestamp in UTC (ETFs only)
- `Snapshot_Timestamp` - Snapshot timestamp (stocks only)
- `Change_Percent` - Price change percentage (stocks only)
- `Source` - Data source
- `Security_Type` - 'Stock' or 'ETF'
- `Created_At` - Record creation timestamp
- `Updated_At` - Record update timestamp

**Usage**: Real-time price lookups, dividend yield calculations, portfolio valuations.

---

## **Portfolio Management Tables** (User data storage)

### **4. `dbo.user_profiles`** - User Accounts
Stores user account information.

**Columns**:
- `user_id` - INT IDENTITY(1,1) PRIMARY KEY - Unique user identifier
- `email` - NVARCHAR(255) NOT NULL UNIQUE - User email address
- `name` - NVARCHAR(255) - User full name
- `created_at` - DATETIME2 DEFAULT GETDATE() - Account creation timestamp

**Indexes**:
- `idx_user_email` - Index on email for fast lookups

**Usage**: User account management, associating portfolios with users.

---

### **5. `dbo.portfolio_groups`** - Portfolios & Watchlists
Stores portfolio and watchlist definitions.

**Columns**:
- `group_id` - INT IDENTITY(1,1) PRIMARY KEY - Unique group identifier
- `user_id` - INT - Foreign key to user_profiles
- `name` - NVARCHAR(255) NOT NULL - Portfolio/watchlist name
- `type` - NVARCHAR(50) NOT NULL - 'portfolio' or 'watchlist'
- `metadata` - NVARCHAR(MAX) - JSON metadata (target income, time horizon, risk tolerance, etc.)
- `created_at` - DATETIME2 DEFAULT GETDATE() - Creation timestamp

**Foreign Keys**:
- `fk_group_user` - References `user_profiles(user_id)` ON DELETE CASCADE

**Indexes**:
- `idx_group_user` - Index on user_id
- `idx_group_type` - Index on type

**Constraints**:
- `type` must be either 'portfolio' or 'watchlist'

**Usage**: Organizing collections of stocks into portfolios or watchlists.

---

### **6. `dbo.portfolio_positions`** - Individual Stock Positions
Stores individual stock positions within portfolios/watchlists.

**Columns**:
- `position_id` - INT IDENTITY(1,1) PRIMARY KEY - Unique position identifier
- `group_id` - INT NOT NULL - Foreign key to portfolio_groups
- `ticker` - NVARCHAR(50) NOT NULL - Stock ticker symbol
- `shares` - DECIMAL(18, 4) - Number of shares
- `target_allocation_pct` - DECIMAL(5, 2) - Target allocation percentage
- `notes` - NVARCHAR(MAX) - User notes about the position
- `created_at` - DATETIME2 DEFAULT GETDATE() - Creation timestamp

**Foreign Keys**:
- `fk_position_group` - References `portfolio_groups(group_id)` ON DELETE CASCADE

**Indexes**:
- `idx_position_group` - Index on group_id
- `idx_position_ticker` - Index on ticker

**Usage**: Tracking individual stock holdings within portfolios, allocation planning.

---

## **How the Database is Used**

### **AI Query Generation**
The three views (`vTickers`, `vDividends`, `vPrices`) are queried by the AI to answer user questions:
- "What are the top dividend stocks in the utilities sector?"
- "Show me AAPL's dividend history"
- "What's the current price of MSFT?"
- "Find high-yield REITs"

### **Passive Income Portfolio Builder**
The portfolio builder feature:
1. Queries `vDividends` + `vPrices` + `vTickers` to find optimal dividend stocks
2. Calculates required capital based on target income and dividend yields
3. Builds diversified portfolios across 8 sectors
4. Projects 5-year income growth
5. Saves recommendations to `portfolio_groups` and `portfolio_positions` tables

### **Database Safety**
- AI-generated SQL is sandboxed to only SELECT from views
- No writes, updates, or deletes allowed via AI queries
- No access to underlying ingestion tables
- Portfolio saves use parameterized queries via SQLAlchemy ORM

### **Data Flow**
```
External Data Sources
        ↓
Ingestion Tables (Ingest_Tickers_*, Ingest_Dividends_*, Ingest_Prices_*)
        ↓
Views (vTickers, vDividends, vPrices) ← AI Queries (Read-Only)
        ↓
AI Analysis & Portfolio Building
        ↓
Portfolio Tables (user_profiles, portfolio_groups, portfolio_positions)
```

---

## **Example Queries**

### Find Top Dividend Stocks
```sql
WITH LatestDividends AS (
    SELECT 
        Ticker,
        AdjDividend_Amount,
        Payment_Date,
        ROW_NUMBER() OVER (PARTITION BY Ticker ORDER BY Payment_Date DESC) AS rn
    FROM dbo.vDividends
    WHERE Payment_Date >= DATEADD(year, -1, CAST(GETDATE() AS DATE))
        AND AdjDividend_Amount > 0
),
AnnualDividends AS (
    SELECT 
        Ticker,
        SUM(AdjDividend_Amount) AS annual_dividend
    FROM dbo.vDividends
    WHERE Payment_Date >= DATEADD(year, -1, CAST(GETDATE() AS DATE))
        AND AdjDividend_Amount > 0
    GROUP BY Ticker
),
LatestPrices AS (
    SELECT 
        Ticker,
        Price,
        ROW_NUMBER() OVER (PARTITION BY Ticker ORDER BY 
            COALESCE(Trade_Timestamp_UTC, Snapshot_Timestamp) DESC) AS rn
    FROM dbo.vPrices
    WHERE Price > 0
)
SELECT TOP 20
    t.Ticker,
    t.Company_Name,
    t.Sector,
    ad.annual_dividend,
    p.Price,
    (ad.annual_dividend / NULLIF(p.Price, 0) * 100) AS dividend_yield_pct
FROM dbo.vTickers t
INNER JOIN AnnualDividends ad ON t.Ticker = ad.Ticker
INNER JOIN LatestPrices p ON t.Ticker = p.Ticker AND p.rn = 1
WHERE t.Country = 'United States'
    AND p.Price > 0
    AND ad.annual_dividend > 0
    AND (ad.annual_dividend / NULLIF(p.Price, 0)) > 0.02
ORDER BY dividend_yield_pct DESC
```

### Get Company Information
```sql
SELECT 
    Ticker,
    Company_Name,
    Sector,
    Industry,
    Country,
    Security_Type,
    Website,
    Description
FROM dbo.vTickers
WHERE Ticker = 'AAPL'
```

### Get Dividend History
```sql
SELECT 
    Ticker,
    AdjDividend_Amount,
    Payment_Date,
    Ex_Dividend_Date,
    Distribution_Frequency
FROM dbo.vDividends
WHERE Ticker = 'JNJ'
    AND Payment_Date >= DATEADD(year, -5, CAST(GETDATE() AS DATE))
ORDER BY Payment_Date DESC
```

---

## **Database Connection Details**

**Provider**: Azure SQL Server  
**Driver**: FreeTDS ODBC (TDS Version 7.3)  
**Connection Pool**: 20 connections, max 40 with overflow  
**Pool Recycle**: 3600s (1 hour)  
**Pool Timeout**: 30s  

**Environment Variables**:
- `SQLSERVER_HOST` - Azure SQL Server hostname
- `SQLSERVER_DB` - Database name
- `SQLSERVER_USER` - Database username
- `SQLSERVER_PASSWORD` - Database password
- `SQLSERVER_PORT` - Port (default: 1433)
