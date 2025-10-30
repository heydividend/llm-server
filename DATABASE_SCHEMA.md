# AskHeyDividend Database Schema

## Overview
This document describes the complete database structure for the AskHeyDividend financial assistant application, including both the financial data views (read-only) and portfolio management tables (user data).

**INTEGRATION UPDATE (Oct 30, 2025):** This AI system now integrates with the HeyDividend production database, accessing 6 enhanced views that provide:
- **Fresher Data**: Updates every 2 hours (vs. daily) for ETF distributions
- **Higher Quality**: Confidence scores and 3-layer fallback strategy  
- **Real-time Insights**: Social media dividend announcements
- **ML Predictions**: Growth forecasts and cut risk analysis
- **2000+ ETFs**: Coverage from 22 providers (YieldMax, Roundhill, Defiance, etc.)

---

## **Enhanced Views** (PREFERRED - Integrated with HeyDividend Database)

### **1. `dbo.vSecurities`** - Master Security Lookup
Direct mapping from the HeyDividend `Securities` table.

**Source Table**: `Securities`

**Key Columns**:
- `Symbol_ID` - Unique identifier (maps to Canonical_Dividends.symbol_id)
- `Ticker` - Stock/ETF ticker symbol
- `Company_Name` - Company or fund name
- `Exchange` - Exchange code
- `Sector` - Business sector
- `Industry` - Industry classification
- `Market_Cap` - Market capitalization

**Usage**: Required for joining with Canonical_Dividends (which uses symbol_id instead of ticker).

---

### **2. `dbo.vDividendsEnhanced`** - Multi-Source Dividend Data (BEST SOURCE)
Unified dividend data with 3-layer fallback strategy and confidence scoring.

**Source Tables**: 
- Priority 1: `Canonical_Dividends` (hourly updates, highest confidence)
- Priority 2: `distribution_schedules` (2-hour updates, ETF-specific)
- Priority 3: `SocialMediaMentions` (2-minute updates, real-time)

**Key Columns**:
- `Ticker` - Stock/ETF ticker symbol
- `Dividend_Amount` - Dividend amount
- `AdjDividend_Amount` - Adjusted dividend amount
- `Dividend_Type` - Type of dividend
- `Currency` - Currency code
- `Distribution_Frequency` - Payment frequency (12=monthly, 4=quarterly)
- `Declaration_Date` - Declaration date
- `Ex_Dividend_Date` - Ex-dividend date
- `Record_Date` - Record date
- `Payment_Date` - Payment date
- `Confidence_Score` - Data confidence (0-1, filter ≥0.7 recommended)
- `Data_Quality_Score` - Data quality score (0-1)
- `Created_At` - Record timestamp
- `Data_Source` - Source system (Canonical, ETF_Schedule, Social_Media)
- `Priority` - Priority level (1=highest, 3=lowest)

**Query Strategy**: Automatically uses ROW_NUMBER() to select highest-confidence data per ticker/ex_date combination.

**Usage**: PRIMARY dividend source - replaces vDividends for all dividend queries.

---

### **3. `dbo.vDividendSchedules`** - ETF Distribution Calendars
ETF-specific distribution data from 22 providers, updated every 2 hours.

**Source Table**: `distribution_schedules`

**Key Columns**:
- `Ticker` - ETF ticker symbol
- `Distribution_Amount` - Distribution amount
- `Ex_Date` - Ex-dividend date
- `Payment_Date` - Payment date
- `Declaration_Date` - Declaration date
- `Record_Date` - Record date
- `Sponsor` - ETF provider name (YieldMax, Roundhill, Defiance, etc.)
- `Schedule_Type` - Schedule type
- `Confidence_Score` - Confidence score (0-1)
- `Is_Confirmed` - Confirmation flag
- `Last_Updated` - Last update timestamp (2-hour refresh)
- `Source_URL` - Source URL

**Coverage**:
- 2,000+ ETFs from 22 providers
- YieldMax (28 ETFs): TSLY, MSTY, NVDY, CONY, etc.
- Roundhill (37+ ETFs): QDTE, XDTE, NVDW, TSLW, MAGS
- Kurv (9 ETFs): KGLD, KQQQ, AAPY, TSLP, AMZP
- Defiance (50 ETFs): QQQY, IWMY, SPYT, MSTX, QTUM
- ProShares (161 ETFs): ISPY, IQQQ, ITWO
- GraniteShares (55 ETFs): NVYY, TSYY, TQQY, YSPY

**Usage**: Freshest ETF dividend data, updated every 2 hours.

---

### **4. `dbo.vDividendSignals`** - Real-time Social Media Dividend Alerts
Real-time dividend announcements from Twitter/X, monitored every 2 minutes.

**Source Table**: `SocialMediaMentions`

**Key Columns**:
- `Ticker` - Stock ticker symbol
- `Dividend_Amount` - Extracted dividend amount
- `Tweet_Text` - Full tweet text
- `Mentioned_At` - Tweet timestamp
- `Twitter_Username` - Twitter username
- `Platform` - Platform name (Twitter/X)
- `Extracted_Dates_JSON` - JSON with extracted dates
- `Confidence_Score` - Extraction confidence (0-1, filter ≥0.8 recommended)
- `Ex_Date` - Parsed ex-dividend date
- `Payment_Date` - Parsed payment date

**Usage**: Captures dividend announcements BEFORE official sources. Use for breaking news and early detection.

---

### **5. `dbo.vQuotesEnhanced`** - Real-time Stock Quotes
Current stock prices and fundamentals from Financial Modeling Prep API.

**Source Table**: `fmp_quotes`

**Key Columns**:
- `Ticker` - Stock ticker symbol
- `Price` - Current price
- `Price_Change` - Price change (dollars)
- `Change_Percent` - Price change (percentage)
- `Volume` - Trading volume
- `Market_Cap` - Market capitalization
- `PE_Ratio` - Price-to-earnings ratio
- `EPS` - Earnings per share
- `Last_Updated` - Last update timestamp

**Usage**: Replaces vPrices for real-time price lookups and fundamental data.

---

### **6. `dbo.vDividendPredictions`** - ML Dividend Forecasts
Machine learning predictions for dividend growth and cut risk.

**Source Tables**:
- `ml_dividend_growth_predictions`
- `ml_dividend_cut_predictions`

**Key Columns**:
- `Ticker` - Stock ticker symbol
- `Growth_Rate_Prediction` - Predicted annual dividend growth rate
- `Growth_Confidence` - Growth prediction confidence (0-1)
- `Cut_Risk_Score` - Dividend cut risk score (0-1, higher = more risk)
- `Cut_Risk_Confidence` - Cut risk prediction confidence (0-1)
- `Risk_Factors_JSON` - Detailed risk analysis (JSON)
- `Prediction_Date` - When prediction was made
- `Growth_Model_Version` - ML model version

**Usage**: Provides ML-powered insights for dividend sustainability analysis.

---

## **Legacy Views** (Backward Compatibility)

### **7. `dbo.vTickers`** - Stock & ETF Information
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
The AI queries both legacy and enhanced views to answer user questions:
- "What are the top dividend stocks in the utilities sector?" → vDividendsEnhanced
- "Show me AAPL's dividend history" → vDividendsEnhanced
- "What's the current price of MSFT?" → vQuotesEnhanced
- "Find high-yield REITs" → vDividendsEnhanced + vQuotesEnhanced
- "What ETFs pay monthly dividends?" → vDividendSchedules
- "Are there any dividend announcements today?" → vDividendSignals
- "What's the dividend cut risk for XYZ?" → vDividendPredictions

### **Passive Income Portfolio Builder**
The portfolio builder feature now uses enhanced views:
1. Queries `vDividendsEnhanced` + `vQuotesEnhanced` + `vSecurities` for optimal dividend stocks
2. Filters by Confidence_Score ≥ 0.7 for high-quality data
3. Calculates required capital based on target income and dividend yields
4. Builds diversified portfolios across 8 sectors
5. Projects 5-year income growth
6. Saves recommendations to `portfolio_groups` and `portfolio_positions` tables

### **Database Safety**
- AI-generated SQL is sandboxed to only SELECT from views
- No writes, updates, or deletes allowed via AI queries
- No access to underlying raw tables (Securities, Canonical_Dividends, etc.)
- Portfolio saves use parameterized queries via SQLAlchemy ORM
- Enhanced views use read-only queries with confidence filtering

### **Data Flow (Updated with Enhanced Integration)**
```
External Sources (Twitter, FMP, Alpha Vantage, YieldMax, Roundhill, etc.)
        ↓
Raw Tables (Canonical_Dividends, distribution_schedules, SocialMediaMentions, 
            fmp_quotes, ml_predictions, Securities)
        ↓
Enhanced Views (vDividendsEnhanced, vQuotesEnhanced, vDividendSchedules, 
                vDividendSignals, vDividendPredictions, vSecurities)
        ↓
Legacy Views (vTickers, vDividends, vPrices) ← Backward Compatibility
        ↓
AI Queries (Read-Only SELECT statements with confidence filtering)
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

## **Enhanced View Example Queries**

### Find High-Quality Dividend Stocks (Using vDividendsEnhanced)
```sql
WITH HighConfidenceDividends AS (
    SELECT 
        Ticker,
        SUM(AdjDividend_Amount) AS annual_dividend,
        MAX(Confidence_Score) AS max_confidence,
        MAX(Data_Source) AS primary_source
    FROM dbo.vDividendsEnhanced
    WHERE Payment_Date >= DATEADD(year, -1, CAST(GETDATE() AS DATE))
        AND Confidence_Score >= 0.7
    GROUP BY Ticker
)
SELECT TOP 20
    s.Ticker,
    s.Company_Name,
    s.Sector,
    hcd.annual_dividend,
    q.Price,
    (hcd.annual_dividend / NULLIF(q.Price, 0) * 100) AS dividend_yield_pct,
    hcd.max_confidence AS confidence_score,
    hcd.primary_source AS data_source
FROM dbo.vSecurities s
INNER JOIN HighConfidenceDividends hcd ON s.Ticker = hcd.Ticker
INNER JOIN dbo.vQuotesEnhanced q ON s.Ticker = q.Ticker
WHERE q.Price > 0
    AND hcd.annual_dividend > 0
    AND (hcd.annual_dividend / NULLIF(q.Price, 0)) > 0.03
ORDER BY dividend_yield_pct DESC
```

### Find Monthly Dividend ETFs (Using vDividendSchedules)
```sql
SELECT TOP 20
    Ticker,
    Sponsor,
    Distribution_Amount,
    Ex_Date,
    Payment_Date,
    Confidence_Score,
    Is_Confirmed
FROM dbo.vDividendSchedules
WHERE Ex_Date >= CAST(GETDATE() AS DATE)
    AND Is_Confirmed = 1
    AND Confidence_Score >= 0.8
ORDER BY Ex_Date ASC
```

### Real-time Dividend Announcements (Using vDividendSignals)
```sql
SELECT TOP 10
    Ticker,
    Dividend_Amount,
    Tweet_Text,
    Mentioned_At,
    Twitter_Username,
    Confidence_Score
FROM dbo.vDividendSignals
WHERE Mentioned_At >= CAST(GETDATE() AS DATE)
    AND Confidence_Score >= 0.85
ORDER BY Mentioned_At DESC
```

### ML Dividend Sustainability Analysis (Using vDividendPredictions)
```sql
SELECT TOP 20
    dp.Ticker,
    s.Company_Name,
    s.Sector,
    dp.Growth_Rate_Prediction,
    dp.Growth_Confidence,
    dp.Cut_Risk_Score,
    dp.Cut_Risk_Confidence,
    dp.Risk_Factors_JSON
FROM dbo.vDividendPredictions dp
INNER JOIN dbo.vSecurities s ON dp.Ticker = s.Ticker
WHERE dp.Growth_Confidence >= 0.7
    AND dp.Cut_Risk_Confidence >= 0.7
ORDER BY dp.Cut_Risk_Score ASC, dp.Growth_Rate_Prediction DESC
```

### Multi-Source Dividend Data Comparison
```sql
SELECT 
    Ticker,
    Dividend_Amount,
    Ex_Dividend_Date,
    Payment_Date,
    Data_Source,
    Confidence_Score,
    Priority
FROM dbo.vDividendsEnhanced
WHERE Ticker = 'TSLY'
    AND Ex_Dividend_Date >= DATEADD(month, -3, CAST(GETDATE() AS DATE))
ORDER BY Ex_Dividend_Date DESC, Priority ASC
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
