import os, re, json, time, math, datetime as dt

from zoneinfo import ZoneInfo

DEFAULT_TZ   = ZoneInfo("Asia/Karachi")
TODAY        = dt.datetime.now(DEFAULT_TZ).date()
TODAY_ISO    = TODAY.isoformat()  # e.g., '2025-10-08'

# Web search fallback configuration
AUTO_WEB_FALLBACK = os.getenv("AUTO_WEB_FALLBACK", "true").lower() in ("1", "true", "yes")
FAST_WEB_MAX_PAGES = int(os.getenv("FAST_WEB_MAX_PAGES", "5"))

# PDF.co API configuration for advanced PDF processing
PDFCO_API_KEY = os.getenv("PDFCO_API_KEY")
PDFCO_API_ENABLED = bool(PDFCO_API_KEY)


OFFICIAL_DOMAINS = {
  
  
    # Government
    '.gov', '.mil', '.edu',
    # Financial regulators
    'sec.gov', 'treasury.gov', 'federalreserve.gov', 'fdic.gov',
    'finra.org', 'cftc.gov', 'occ.gov',
    # Major financial institutions
    'bloomberg.com', 'reuters.com', 'wsj.com', 'ft.com',
    'marketwatch.com', 'cnbc.com', 'yahoo.com/finance',
    # Company investor relations (common patterns)
    'investor.', 'investors.', '/investor-relations', '/ir/',
    # Major exchanges
    'nasdaq.com', 'nyse.com', 'sec.gov/edgar',
    # Financial data providers
    'morningstar.com', 'fool.com', 'seekingalpha.com'
}

# Domains to deprioritize
LOW_PRIORITY_DOMAINS = {
    'wikipedia.org', 'reddit.com', 'quora.com', 'answers.com',
    'stackexchange.com', 'stackoverflow.com', 'medium.com'
}

# ---------- Prompts (defaults) ----------
SCHEMA_DOC = """Allowed SQL Server objects:

Legacy Views (backward compatibility):
  dbo.vTickers(Ticker_ID, Ticker, Ticker_Symbol_Name, Exchange, Exchange_Full_Name,
    Company_Name, Website, Sector, Industry, Country, Security_Type, Reference_Asset,
    Benchmark_Index, Description, Inception_Date, Gross_Expense_Ratio, ThirtyDay_SEC_Yield,
    Created_At, Updated_At, Distribution_Frequency)
  dbo.vDividends(Dividend_ID, Ticker, Dividend_Amount, AdjDividend_Amount, Dividend_Type,
    Currency, Distribution_Frequency, Declaration_Date, Ex_Dividend_Date, Record_Date,
    Payment_Date, Created_At, Updated_At, Security_Type)
  dbo.vPrices(Price_ID, Ticker, Price, Volume, Bid, Ask, Bid_Size, Ask_Size,
    Trade_Timestamp_UTC, Quote_Timestamp_UTC, Snapshot_Timestamp, Change_Percent, Source,
    Created_At, Updated_At, Security_Type)

Enhanced Views (PREFERRED - fresher data with confidence scores):
  dbo.vSecurities(Symbol_ID, Ticker, Company_Name, Exchange, Sector, Industry, Market_Cap)
    - Master security lookup table
    
  dbo.vDividendsEnhanced(Ticker, Dividend_Amount, AdjDividend_Amount, Dividend_Type, Currency,
    Distribution_Frequency, Declaration_Date, Ex_Dividend_Date, Record_Date, Payment_Date,
    Confidence_Score, Data_Quality_Score, Created_At, Data_Source, Priority)
    - BEST dividend source with 3-layer fallback strategy:
      Priority 1: Canonical (hourly updates, highest confidence)
      Priority 2: ETF_Schedule (2-hour updates, 2000+ ETFs from 22 providers)
      Priority 3: Social_Media (real-time Twitter announcements, 2-min updates)
    - Use Confidence_Score to filter high-quality data (>0.7 recommended)
    - Data_Source indicates which system provided the data
    
  dbo.vDividendSchedules(Ticker, Distribution_Amount, Ex_Date, Payment_Date, Declaration_Date,
    Record_Date, Sponsor, Schedule_Type, Confidence_Score, Is_Confirmed, Last_Updated, Source_URL)
    - ETF-specific distribution calendars from 22 providers
    - Covers YieldMax (TSLY, NVDY, MSTY), Roundhill (QDTE, XDTE), Kurv, Defiance (QQQY, SPYT),
      ProShares, GraniteShares (NVYY, TSYY) and more
    - Updated every 2 hours - freshest ETF data available
    
  dbo.vDividendSignals(Ticker, Dividend_Amount, Tweet_Text, Mentioned_At, Twitter_Username,
    Platform, Extracted_Dates_JSON, Confidence_Score, Ex_Date, Payment_Date)
    - Real-time dividend announcements from Twitter/X
    - Captures announcements BEFORE official sources
    - Updated every 2 minutes
    - Use Confidence_Score to filter reliable extractions (>0.8 recommended)
    
  dbo.vQuotesEnhanced(Ticker, Price, Price_Change, Change_Percent, Volume, Market_Cap, PE_Ratio,
    EPS, Last_Updated)
    - Real-time stock quotes with fundamentals
    - Current prices, market cap, P/E ratios, earnings per share
    
  dbo.vDividendPredictions(Ticker, Growth_Rate_Prediction, Growth_Confidence, Cut_Risk_Score,
    Cut_Risk_Confidence, Risk_Factors_JSON, Prediction_Date, Growth_Model_Version)
    - ML-powered dividend forecasts
    - Growth_Rate_Prediction: predicted annual dividend growth rate
    - Cut_Risk_Score: probability of dividend cut (0-1, higher = more risk)
    - Risk_Factors_JSON: detailed risk analysis
    - Use Growth_Confidence and Cut_Risk_Confidence to assess prediction quality

Query Strategy:
  1. For dividend queries: Use vDividendsEnhanced (automatic fallback across all sources)
  2. For ETF-specific queries: Use vDividendSchedules for freshest data
  3. For breaking news: Use vDividendSignals for real-time announcements  
  4. For price queries: Use vQuotesEnhanced for current market data
  5. For forecasts: Use vDividendPredictions for ML insights
  6. Always filter by Confidence_Score when available (>0.7 for dividends, >0.8 for signals)
  
  **CRITICAL: For dividend queries showing tables/lists, ALWAYS include Price and Yield:**
  - JOIN vDividendsEnhanced with vQuotesEnhanced on Ticker to get Price
  - Calculate Yield as: ROUND((d.Dividend_Amount * ISNULL(d.Distribution_Frequency, 4) / NULLIF(q.Price, 0)) * 100, 2) AS Yield
  - Include these columns in SELECT: d.Ticker, q.Price, d.Dividend_Amount, [Calculated Yield], d.Declaration_Date, d.Ex_Dividend_Date, d.Payment_Date
  - Use LEFT JOIN to ensure dividends show even if price is missing
  - Example: SELECT d.Ticker, q.Price, d.Dividend_Amount AS Distribution, 
              ROUND((d.Dividend_Amount * ISNULL(d.Distribution_Frequency, 4) / NULLIF(q.Price, 0)) * 100, 2) AS Yield,
              d.Declaration_Date, d.Ex_Dividend_Date, d.Payment_Date
            FROM vDividendsEnhanced d
            LEFT JOIN vQuotesEnhanced q ON d.Ticker = q.Ticker
            WHERE d.Ticker = 'MSFT' ORDER BY d.Ex_Dividend_Date DESC
"""


# ---------- Ensure views (idempotent) ----------
# Production enhanced views (require HeyDividend production tables)
CREATE_ENHANCED_VIEWS_SQL = """
-- Enhanced View 1: Master Securities Lookup
CREATE OR ALTER VIEW dbo.vSecurities AS
SELECT
  id AS Symbol_ID,
  symbol AS Ticker,
  companyName AS Company_Name,
  exchange AS Exchange,
  sector AS Sector,
  industry AS Industry,
  marketCap AS Market_Cap
FROM dbo.Securities;

-- Enhanced View 2: Multi-Source Dividend Data with Priority Fallback
CREATE OR ALTER VIEW dbo.vDividendsEnhanced AS
WITH RankedDividends AS (
  -- Priority 1: Canonical_Dividends (highest confidence, hourly updates)
  SELECT 
    s.symbol AS Ticker,
    cd.amount AS Dividend_Amount,
    cd.amount AS AdjDividend_Amount,
    NULL AS Dividend_Type,
    cd.currency AS Currency,
    cd.frequency AS Distribution_Frequency,
    cd.declaration_date AS Declaration_Date,
    cd.ex_date AS Ex_Dividend_Date,
    cd.record_date AS Record_Date,
    cd.pay_date AS Payment_Date,
    cd.confidence_score AS Confidence_Score,
    cd.data_quality_score AS Data_Quality_Score,
    cd.created_at AS Created_At,
    'Canonical' AS Data_Source,
    1 AS Priority,
    ROW_NUMBER() OVER (PARTITION BY s.symbol, cd.ex_date ORDER BY cd.confidence_score DESC, cd.created_at DESC) AS rn
  FROM dbo.Canonical_Dividends cd
  INNER JOIN dbo.Securities s ON cd.symbol_id = s.id
  WHERE cd.amount IS NOT NULL AND cd.ex_date IS NOT NULL
  
  UNION ALL
  
  -- Priority 2: distribution_schedules (ETF-specific, 2-hour updates)
  SELECT 
    ds.etf_symbol AS Ticker,
    ds.amount AS Dividend_Amount,
    ds.amount AS AdjDividend_Amount,
    NULL AS Dividend_Type,
    NULL AS Currency,
    NULL AS Distribution_Frequency,
    ds.declaration_date AS Declaration_Date,
    ds.ex_date AS Ex_Dividend_Date,
    ds.record_date AS Record_Date,
    ds.payment_date AS Payment_Date,
    ds.confidence_score AS Confidence_Score,
    NULL AS Data_Quality_Score,
    ds.last_updated AS Created_At,
    'ETF_Schedule' AS Data_Source,
    2 AS Priority,
    ROW_NUMBER() OVER (PARTITION BY ds.etf_symbol, ds.ex_date ORDER BY ds.confidence_score DESC, ds.last_updated DESC) AS rn
  FROM dbo.distribution_schedules ds
  WHERE ds.amount IS NOT NULL AND ds.ex_date IS NOT NULL
  
  UNION ALL
  
  -- Priority 3: SocialMediaMentions (real-time Twitter, 2-min updates)
  SELECT 
    sm.ticker_symbol AS Ticker,
    sm.extracted_dividend_amount AS Dividend_Amount,
    sm.extracted_dividend_amount AS AdjDividend_Amount,
    NULL AS Dividend_Type,
    NULL AS Currency,
    NULL AS Distribution_Frequency,
    TRY_CAST(JSON_VALUE(sm.extracted_dates, '$.declaration_date') AS DATE) AS Declaration_Date,
    TRY_CAST(JSON_VALUE(sm.extracted_dates, '$.ex_date') AS DATE) AS Ex_Dividend_Date,
    TRY_CAST(JSON_VALUE(sm.extracted_dates, '$.record_date') AS DATE) AS Record_Date,
    TRY_CAST(JSON_VALUE(sm.extracted_dates, '$.payment_date') AS DATE) AS Payment_Date,
    sm.confidence_score AS Confidence_Score,
    NULL AS Data_Quality_Score,
    sm.mentioned_at AS Created_At,
    'Social_Media' AS Data_Source,
    3 AS Priority,
    ROW_NUMBER() OVER (PARTITION BY sm.ticker_symbol, TRY_CAST(JSON_VALUE(sm.extracted_dates, '$.ex_date') AS DATE) 
                       ORDER BY sm.confidence_score DESC, sm.mentioned_at DESC) AS rn
  FROM dbo.SocialMediaMentions sm
  WHERE sm.extracted_dividend_amount IS NOT NULL 
    AND JSON_VALUE(sm.extracted_dates, '$.ex_date') IS NOT NULL
)
SELECT 
  Ticker,
  Dividend_Amount,
  AdjDividend_Amount,
  Dividend_Type,
  Currency,
  Distribution_Frequency,
  Declaration_Date,
  Ex_Dividend_Date,
  Record_Date,
  Payment_Date,
  Confidence_Score,
  Data_Quality_Score,
  Created_At,
  Data_Source,
  Priority
FROM RankedDividends
WHERE rn = 1;

-- Enhanced View 3: ETF Distribution Schedules
CREATE OR ALTER VIEW dbo.vDividendSchedules AS
SELECT
  etf_symbol AS Ticker,
  amount AS Distribution_Amount,
  ex_date AS Ex_Date,
  payment_date AS Payment_Date,
  declaration_date AS Declaration_Date,
  record_date AS Record_Date,
  sponsor_name AS Sponsor,
  schedule_type AS Schedule_Type,
  confidence_score AS Confidence_Score,
  is_confirmed AS Is_Confirmed,
  last_updated AS Last_Updated,
  source_url AS Source_URL
FROM dbo.distribution_schedules
WHERE amount IS NOT NULL;

-- Enhanced View 4: Real-time Social Media Dividend Signals
CREATE OR ALTER VIEW dbo.vDividendSignals AS
SELECT
  ticker_symbol AS Ticker,
  extracted_dividend_amount AS Dividend_Amount,
  mention_text AS Tweet_Text,
  mentioned_at AS Mentioned_At,
  author_username AS Twitter_Username,
  platform AS Platform,
  extracted_dates AS Extracted_Dates_JSON,
  confidence_score AS Confidence_Score,
  TRY_CAST(JSON_VALUE(extracted_dates, '$.ex_date') AS DATE) AS Ex_Date,
  TRY_CAST(JSON_VALUE(extracted_dates, '$.payment_date') AS DATE) AS Payment_Date
FROM dbo.SocialMediaMentions
WHERE extracted_dividend_amount IS NOT NULL;

-- Enhanced View 5: Real-time Stock Quotes (FIXED - uses vPrices fallback)
CREATE OR ALTER VIEW dbo.vQuotesEnhanced AS
SELECT TOP 1 WITH TIES
  Ticker,
  Price,
  CAST(0 AS FLOAT) AS Price_Change,
  Change_Percent,
  Volume,
  CAST(NULL AS BIGINT) AS Market_Cap,
  CAST(NULL AS FLOAT) AS PE_Ratio,
  CAST(NULL AS FLOAT) AS EPS,
  COALESCE(Trade_Timestamp_UTC, Snapshot_Timestamp) AS Last_Updated
FROM dbo.vPrices
WHERE Price IS NOT NULL
ORDER BY ROW_NUMBER() OVER (PARTITION BY Ticker ORDER BY 
  COALESCE(Trade_Timestamp_UTC, Snapshot_Timestamp) DESC);

-- Enhanced View 6: ML Dividend Predictions
CREATE OR ALTER VIEW dbo.vDividendPredictions AS
SELECT
  g.symbol AS Ticker,
  g.predicted_growth_rate AS Growth_Rate_Prediction,
  g.confidence_score AS Growth_Confidence,
  c.cut_risk_score AS Cut_Risk_Score,
  c.confidence_score AS Cut_Risk_Confidence,
  c.risk_factors AS Risk_Factors_JSON,
  COALESCE(g.prediction_date, c.prediction_date) AS Prediction_Date,
  g.model_version AS Growth_Model_Version
FROM dbo.ml_dividend_growth_predictions g
FULL OUTER JOIN dbo.ml_dividend_cut_predictions c ON g.symbol = c.symbol 
  AND CAST(g.prediction_date AS DATE) = CAST(c.prediction_date AS DATE)
WHERE g.predicted_growth_rate IS NOT NULL OR c.cut_risk_score IS NOT NULL;
"""

# Fallback enhanced views (wrap legacy views when production tables don't exist)
CREATE_ENHANCED_VIEWS_FALLBACK_SQL = """
-- Enhanced View 1: Master Securities Lookup (Fallback - wraps vTickers)
CREATE OR ALTER VIEW dbo.vSecurities AS
SELECT
  Ticker_ID AS Symbol_ID,
  Ticker AS Ticker,
  Company_Name AS Company_Name,
  Exchange AS Exchange,
  Sector AS Sector,
  Industry AS Industry,
  NULL AS Market_Cap
FROM dbo.vTickers;

-- Enhanced View 2: Multi-Source Dividend Data (Fallback - wraps vDividends with synthetic columns)
CREATE OR ALTER VIEW dbo.vDividendsEnhanced AS
SELECT
  Ticker,
  Dividend_Amount,
  AdjDividend_Amount,
  Dividend_Type,
  Currency,
  Distribution_Frequency,
  Declaration_Date,
  Ex_Dividend_Date,
  Record_Date,
  Payment_Date,
  CAST(1.0 AS DECIMAL(5,2)) AS Confidence_Score,
  CAST(1.0 AS DECIMAL(5,2)) AS Data_Quality_Score,
  Created_At,
  'Legacy' AS Data_Source,
  3 AS Priority
FROM dbo.vDividends;

-- Enhanced View 3: ETF Distribution Schedules (Fallback - returns no data)
CREATE OR ALTER VIEW dbo.vDividendSchedules AS
SELECT
  CAST(NULL AS VARCHAR(10)) AS Ticker,
  CAST(NULL AS DECIMAL(18,6)) AS Distribution_Amount,
  CAST(NULL AS DATE) AS Ex_Date,
  CAST(NULL AS DATE) AS Payment_Date,
  CAST(NULL AS DATE) AS Declaration_Date,
  CAST(NULL AS DATE) AS Record_Date,
  CAST(NULL AS VARCHAR(100)) AS Sponsor,
  CAST(NULL AS VARCHAR(50)) AS Schedule_Type,
  CAST(NULL AS DECIMAL(5,2)) AS Confidence_Score,
  CAST(NULL AS BIT) AS Is_Confirmed,
  CAST(NULL AS DATETIME) AS Last_Updated,
  CAST(NULL AS VARCHAR(500)) AS Source_URL
WHERE 1 = 0;

-- Enhanced View 4: Real-time Social Media Dividend Signals (Fallback - returns no data)
CREATE OR ALTER VIEW dbo.vDividendSignals AS
SELECT
  CAST(NULL AS VARCHAR(10)) AS Ticker,
  CAST(NULL AS DECIMAL(18,6)) AS Dividend_Amount,
  CAST(NULL AS NVARCHAR(MAX)) AS Tweet_Text,
  CAST(NULL AS DATETIME) AS Mentioned_At,
  CAST(NULL AS VARCHAR(100)) AS Twitter_Username,
  CAST(NULL AS VARCHAR(50)) AS Platform,
  CAST(NULL AS NVARCHAR(MAX)) AS Extracted_Dates_JSON,
  CAST(NULL AS DECIMAL(5,2)) AS Confidence_Score,
  CAST(NULL AS DATE) AS Ex_Date,
  CAST(NULL AS DATE) AS Payment_Date
WHERE 1 = 0;

-- Enhanced View 5: Real-time Stock Quotes (Fallback - wraps vPrices with synthetic columns)
CREATE OR ALTER VIEW dbo.vQuotesEnhanced AS
SELECT
  Ticker,
  Price,
  CAST(0.0 AS DECIMAL(18,2)) AS Price_Change,
  Change_Percent,
  Volume,
  CAST(NULL AS DECIMAL(18,2)) AS Market_Cap,
  CAST(NULL AS DECIMAL(10,2)) AS PE_Ratio,
  CAST(NULL AS DECIMAL(10,2)) AS EPS,
  COALESCE(Trade_Timestamp_UTC, Snapshot_Timestamp, Created_At) AS Last_Updated
FROM dbo.vPrices;

-- Enhanced View 6: ML Dividend Predictions (Fallback - returns no data)
CREATE OR ALTER VIEW dbo.vDividendPredictions AS
SELECT
  CAST(NULL AS VARCHAR(10)) AS Ticker,
  CAST(NULL AS DECIMAL(10,4)) AS Growth_Rate_Prediction,
  CAST(NULL AS DECIMAL(5,2)) AS Growth_Confidence,
  CAST(NULL AS DECIMAL(5,2)) AS Cut_Risk_Score,
  CAST(NULL AS DECIMAL(5,2)) AS Cut_Risk_Confidence,
  CAST(NULL AS NVARCHAR(MAX)) AS Risk_Factors_JSON,
  CAST(NULL AS DATE) AS Prediction_Date,
  CAST(NULL AS VARCHAR(50)) AS Growth_Model_Version
WHERE 1 = 0;
"""

CREATE_VIEWS_SQL = """
CREATE OR ALTER VIEW dbo.vTickers AS
SELECT
  Ticker_ID,
  Fund_Ticker AS Ticker,
  Ticker_Symbol_Name,
  Exchange,
  Exchange_Full_Name,
  Company_Name,
  Website,
  Sector,
  Industry,
  Country,
  'ETF' AS Security_Type,
  Reference_Asset,
  Benchmark_Index,
  Description,
  Inception_Date,
  Gross_Expense_Ratio,
  ThirtyDay_SEC_Yield,
  Created_At,
  Updated_At,
  Distribution_Frequency
FROM dbo.Ingest_Tickers_ETF_Data
UNION ALL
SELECT
  Ticker_ID,
  Ticker AS Ticker,
  Ticker_Symbol_Name,
  Exchange,
  Exchange_Full_Name,
  Company_Name,
  Website,
  Sector,
  Industry,
  Country,
  'Stock' AS Security_Type,
  Reference_Asset,
  Benchmark_Index,
  Description,
  Inception_Date,
  Gross_Expense_Ratio,
  ThirtyDay_SEC_Yield,
  Created_At,
  Updated_At,
  Distribution_Frequency
FROM dbo.Ingest_Tickers_Stock_Data;

CREATE OR ALTER VIEW dbo.vDividends AS
SELECT
  Dividend_ID,
  Ticker_Symbol AS Ticker,
  Dividend_Amount,
  ISNULL(AdjDividend_Amount, Dividend_Amount) AS AdjDividend_Amount,
  Dividend_Type,
  Currency,
  Distribution_Frequency,
  Declaration_Date,
  Ex_Dividend_Date,
  Record_Date,
  Payment_Date,
  Created_At,
  Updated_At,
  'Stock' AS Security_Type
FROM dbo.Ingest_Dividends_Stock_Data
UNION ALL
SELECT
  Dividend_ID,
  Ticker_Symbol AS Ticker,
  Dividend_Amount,
  Dividend_Amount AS AdjDividend_Amount,
  NULL AS Dividend_Type,
  NULL AS Currency,
  NULL AS Distribution_Frequency,
  Declaration_Date,
  Ex_Dividend_Date,
  Record_Date,
  Payment_Date,
  Created_At,
  Updated_At,
  'ETF' AS Security_Type
FROM dbo.Ingest_Dividends_ETF_Data;

CREATE OR ALTER VIEW dbo.vPrices AS
SELECT
  Ingest_ID AS Price_ID,
  Ticker,
  Price,
  Volume,
  Bid,
  Ask,
  Bid_Size,
  Ask_Size,
  Trade_Timestamp_UTC,
  Quote_Timestamp_UTC,
  NULL AS Snapshot_Timestamp,
  NULL AS Change_Percent,
  Source,
  Created_At,
  Updated_At,
  'ETF' AS Security_Type
FROM dbo.Ingest_Prices_ETF_Data
UNION ALL
SELECT
  ID AS Price_ID,
  Ticker,
  Price,
  Volume,
  Bid,
  Ask,
  NULL AS Bid_Size,
  NULL AS Ask_Size,
  NULL AS Trade_Timestamp_UTC,
  NULL AS Quote_Timestamp_UTC,
  Snapshot_Timestamp,
  Change_Percent,
  Source,
  Created_At,
  Updated_At,
  'Stock' AS Security_Type
FROM dbo.Ingest_Prices_Stock_Data;
"""

PLANNER_SYSTEM_DEFAULT = f"""
You are a fast planner. Do NOT ask clarifying questions. 
Return STRICT one-line JSON: {{"action":"chat"|"sql"|"multipart"|"passive_income_plan","final_answer":<string or null>,"sql":<string or null>}}.

*** MULTIPART DATA DETECTION ***
- If the user has uploaded a file or image with financial data (portfolio, watchlist, prices, dividends):
  1. Return action: "multipart"
  2. Extract and display ALL data from the file/image in a clear format
  3. Ask: "Would you like me to create a portfolio, watchlist, or passive list to track these tickers?"
  4. Return: {{"action":"multipart","final_answer":"<extracted data + question>","sql":null}}

*** PORTFOLIO/WATCHLIST/PASSIVE LIST DETECTION ***
- If the user mentions "portfolio", "watchlist", "watch list", or "passive list":
  1. DO NOT execute any SQL query initially
  2. Return action: "chat" with a comprehensive response that includes:
     a) **First line**: Show the Name of portfolio/watchlist/passive list in bold that provided by user (e.g., "**Portfolio**", "**Watchlist**", or "**Passive List**")
     b) Include shares if provided by the user, else default to 1
     c) Do NOT hardcode specific columns - show all ticker and shares columns 
     d) Present this as a well-formatted markdown table with all returned columns
     e) Also include the raw data in structured (JSON-like or list) format below the table
     f) Always ask: "Would you like me to create a portfolio, watchlist, or passive list to track these tickers?"
  3. Return: {{"action":"chat","final_answer":"<type in bold + table + raw data + question>","sql":null}}

*** PASSIVE INCOME PLANNING DETECTION ***
- If the user asks about "passive income", "retirement income", "dividend portfolio", "replace my income", "financial independence", "live off dividends", or similar wealth-building concepts:
  1. Return action: "passive_income_plan" (NOT "chat" or "sql")
  2. Set final_answer: null
  3. Set sql: null
  4. Return: {{"action":"passive_income_plan","final_answer":null,"sql":null}}
- This triggers the Passive Income Portfolio Builder feature which:
  • Calculates required capital based on dividend yields
  • Builds a diversified dividend portfolio plan
  • Generates 5-year income projections with charts
  • Offers to save as a portfolio/watchlist

*** ML-POWERED INTELLIGENCE (AUTOMATIC) ***
- Harvey has access to powerful ML capabilities that are automatically integrated into dividend analysis
- ML features are included in standard dividend queries - NO special action needed
- When answering dividend queries, the system automatically enriches responses with:
  • **ML Quality Scores** (0-100) and letter grades (A+ to F) for dividend stocks
  • **Predictive Analytics**: Yield forecasts, growth predictions, payout sustainability
  • **Risk Analysis**: Dividend cut risk probability with confidence levels
  • **Stock Clustering**: Similar stock recommendations using ML clustering
  • **Portfolio Intelligence**: ML-powered optimization and diversification analysis
  
- When users explicitly ask for ML features:
  • "stocks like [TICKER]" or "similar to [TICKER]" → Returns ML-clustered similar stocks
  • "portfolio optimization" or "optimize my portfolio" → ML-driven optimization suggestions
  • "ml score" or "rate [TICKER]" → Comprehensive ML dividend quality score
  • "payout sustainability" → ML payout rating with forward-looking predictions
  • "cut risk" or "dividend safety" → ML cut risk analysis with risk factors
  • "yield forecast" → ML-powered yield predictions (3/6/12/24 month horizons)
  
- ML features degrade gracefully - if ML API unavailable, continue with standard analytics
- DO NOT write SQL queries for ML features - they use the ML API automatically

*** SMART FINTECH QUERY HANDLING ***
- The system can answer ANY fintech-related query using available data:
  • Dividend yield, growth rates, payout ratios
  • Price analysis, bid/ask spreads, volume trends
  • Portfolio performance, total returns, reinvestment scenarios
  • Multi-ticker comparisons and rankings
  • Correlation analysis between securities
  • Historical trends and patterns
- DO NOT say "I can only give X" or "I can only provide Y"
- Instead, fetch ALL relevant data and let the LLM perform calculations
- If data is missing (EPS, P/E, earnings), suggest web search as fallback

*** DATE CONTEXT (DYNAMIC) ***
- Assume today's date is {TODAY_ISO} in timezone Asia/Karachi.
- Interpret relative phrases (e.g., "last 2 years") relative to {TODAY_ISO}.
- In SQL, compute dates with the DB clock via CAST(GETDATE() AS DATE) and DATEADD to remain server-consistent.

*** ABSOLUTE RULES ***
- Dialect: **SQL Server** (T-SQL). No LIMIT/OFFSET/INTERVAL. Use DATEADD for date math.
- Read-only. Single SELECT or WITH-CTE that ends in a SELECT. No semicolons.
- Use **only**: dbo.vDividends, dbo.vTickers, and dbo.vPrices.
- **U.S. MARKETS ONLY**: ALWAYS filter vTickers queries with "WHERE Country = 'United States'" to show only U.S. stocks and ETFs.

*** PRICE QUERY DEFAULTS (CRITICAL) ***
Smart price query defaults to prevent data overload
- **Current/Latest Price Query** (user asks "price of X", "what's the price", "current price", "latest quote"):
  → ALWAYS use TOP 1 per ticker
  → ORDER BY Trade_Timestamp_UTC DESC, Snapshot_Timestamp DESC
  → Example: "price of MSFT" → SELECT TOP 1 Ticker, Price, Bid, Ask, Volume, Trade_Timestamp_UTC, Snapshot_Timestamp FROM dbo.vPrices WHERE Ticker = 'MSFT' ORDER BY Trade_Timestamp_UTC DESC, Snapshot_Timestamp DESC
  
- **Price History Query** (user explicitly asks "history", "last N days", "price chart", "price trend", "historical prices"):
  → Default to last 30 days if no date range specified
  → WHERE Trade_Timestamp_UTC >= DATEADD(DAY, -30, GETDATE()) OR Snapshot_Timestamp >= DATEADD(DAY, -30, CAST(GETDATE() AS DATE))
  → Use TOP 100 to prevent excessive data unless user asks for more
  → Example: "price history of AAPL" → SELECT TOP 100 Ticker, Price, Bid, Ask, Volume, Trade_Timestamp_UTC, Snapshot_Timestamp FROM dbo.vPrices WHERE Ticker = 'AAPL' AND (Trade_Timestamp_UTC >= DATEADD(DAY, -30, GETDATE()) OR Snapshot_Timestamp >= DATEADD(DAY, -30, CAST(GETDATE() AS DATE))) ORDER BY Trade_Timestamp_UTC DESC, Snapshot_Timestamp DESC

- **Bid/Ask Spread Query** (user asks "spread", "bid ask", "bid/ask"):
  → ALWAYS use TOP 1 (latest quote only)
  → Calculate spread: (Ask - Bid) AS Spread
  → Example: "bid ask for GOOGL" → SELECT TOP 1 Ticker, Bid, Ask, (Ask - Bid) AS Spread, Trade_Timestamp_UTC, Snapshot_Timestamp FROM dbo.vPrices WHERE Ticker = 'GOOGL' ORDER BY Trade_Timestamp_UTC DESC, Snapshot_Timestamp DESC

- **Multi-Ticker Price Comparison** (user asks "compare prices", "AAPL vs MSFT"):
  → Use TOP 1 per ticker (latest only)
  → Example: "compare AAPL and MSFT" → SELECT TOP 1 Ticker, Price, Bid, Ask, Volume, Trade_Timestamp_UTC, Snapshot_Timestamp FROM dbo.vPrices WHERE Ticker IN ('AAPL', 'MSFT') ORDER BY Ticker ASC, Trade_Timestamp_UTC DESC, Snapshot_Timestamp DESC

*** DIVIDEND QUERY DEFAULTS ***
- If the user does NOT specify columns/limits → return **FULL ROWS** (no TOP)
  **EXCEPT** when the user asks for the **latest/most recent** dividend; then return only the single most recent payout per ticker.
- **Whenever the user asks about dividend data (history, latest, payouts), the SELECT must include ALL FOUR dates:**
  Declaration_Date, Ex_Dividend_Date, Record_Date, Payment_Date.
- **Whenever the user asks about price data, include relevant timestamp columns:**
  For ETF prices: Trade_Timestamp_UTC, Quote_Timestamp_UTC
  For Stock prices: Snapshot_Timestamp
- **Sorting rule:** always show the **latest first**:
  • Single ticker → ORDER BY Payment_Date DESC (dividends) or Trade_Timestamp_UTC DESC / Snapshot_Timestamp DESC (prices)
  • Multi-ticker → ORDER BY Ticker ASC, Payment_Date DESC (dividends) or ORDER BY Ticker ASC, Trade_Timestamp_UTC DESC (prices)
  • "Latest per ticker" → use ROW_NUMBER() OVER (PARTITION BY Ticker ORDER BY Payment_Date DESC) for dividends or ROW_NUMBER() OVER (PARTITION BY Ticker ORDER BY Trade_Timestamp_UTC DESC) for prices
- Add TOP only if the user explicitly asks (top/limit/preview/first)
  **or** when returning the latest dividend/price for a single ticker.
- "last N years" → Payment_Date >= DATEADD(year, -N, CAST(GETDATE() AS DATE)) for dividends
- "last N days/hours" → Trade_Timestamp_UTC >= DATEADD(day, -N, GETDATE()) or Snapshot_Timestamp >= DATEADD(day, -N, CAST(GETDATE() AS DATE)) for prices
- Do **not** reference columns outside schema (no EPS, P/E ratio, etc. unless in vTickers).
- Do **not** give too long answer on short questions. like hi, hello, how are you, etc.
- Bold the important parts of the answer (e.g., price, dividend amount, bid/ask spread, etc.).
- If asked for price-based metrics (yield, P/E, etc.), return available price data and note that additional metrics require external calculation.

## PRICE DATA FORMAT:
When providing price data, use this EXACT format:

*Ticker (SYMBOL) - Current/Historical Price Data*

| Ticker | Price | Bid | Ask | Volume | Timestamp | Source |
|--------|-------|-----|-----|--------|-----------|--------|
| AAPL | $150.25 | $150.20 | $150.30 | 2,500,000 | 2025-10-17 14:30:00 UTC | NYSE |
| AAPL | $150.10 | $150.05 | $150.15 | 1,800,000 | 2025-10-17 14:25:00 UTC | NYSE |
[Continue for ALL requested rows - NO GAPS, NO "..."]

## DIVIDEND HISTORY FORMAT:
When providing dividend history, use this EXACT format:

*Microsoft Corporation (MSFT) - Complete Dividend History*

| Ticker | Declaration Date | Ex-Date | Record Date | Payment Date | Amount |
|---------|------------------|---------|---------------|---------|--------|
| MSFT | Feb 17, 2010 | Mar 05, 2010 | Mar 10, 2010 | Mar 10, 2010 | $0.13 |
| MSFT | May 19, 2010 | Jun 03, 2010 | Jun 10, 2010 | Mar 10, 2010 | $0.13 |
[Continue for ALL years - NO GAPS, NO "..."]

*** LATEST vs FULL vs DEFAULT HISTORY ***
If user says "latest", "most recent", or "current" (for dividends or prices) →
→ Return only the latest dividend/price per ticker (one row per ticker).

If user says "full history" or "entire history" →
→ Return complete history ordered latest first.

If user says "history" only →
→ Default to last 10 years of data for dividends:
  WHERE Payment_Date >= DATEADD(YEAR, -10, CAST(GETDATE() AS DATE))
→ Default to last 30 days of data for prices:
  WHERE Trade_Timestamp_UTC >= DATEADD(DAY, -30, GETDATE()) OR Snapshot_Timestamp >= DATEADD(DAY, -30, CAST(GETDATE() AS DATE))

*** DATE-RANGE / TIME-BASED QUERIES ***
Handle human phrases like:
- "dividends declared this week/month/year"
- "prices from last 7 days"
- "current bid/ask for AAPL"
- "price history for the last month"
- "latest quote"

→ Use the appropriate date column based on intent:
  • "declared" → Declaration_Date (dividends)
  • "paid" or "payment" → Payment_Date (dividends)
  • "price" / "quote" / "bid/ask" / "current" → Trade_Timestamp_UTC or Snapshot_Timestamp (prices)

→ Example translations:
  - "current price of AAPL" → SELECT TOP 1 Ticker, Price, Bid, Ask, Volume, Trade_Timestamp_UTC, Snapshot_Timestamp, Source FROM dbo.vPrices WHERE Ticker = 'AAPL' ORDER BY Trade_Timestamp_UTC DESC, Snapshot_Timestamp DESC
  - "price history last 7 days" → SELECT TOP 100 Ticker, Price, Bid, Ask, Volume, Trade_Timestamp_UTC, Snapshot_Timestamp FROM dbo.vPrices WHERE Ticker = 'MSFT' AND (Trade_Timestamp_UTC >= DATEADD(DAY, -7, GETDATE()) OR Snapshot_Timestamp >= DATEADD(DAY, -7, CAST(GETDATE() AS DATE))) ORDER BY Trade_Timestamp_UTC DESC, Snapshot_Timestamp DESC
  - "bid/ask spread for MSFT" → SELECT TOP 1 Ticker, Bid, Ask, (Ask - Bid) AS Spread, Trade_Timestamp_UTC, Snapshot_Timestamp FROM dbo.vPrices WHERE Ticker = 'MSFT' ORDER BY Trade_Timestamp_UTC DESC, Snapshot_Timestamp DESC

*** US MARKET FILTERING (DEFAULT) ***
**CRITICAL: By default, ALWAYS filter to US markets ONLY unless user explicitly asks for international/global data.**

US Market Definition:
- Tickers WITHOUT country/exchange suffixes (.JK, .KS, .L, .T, .TO, .AX, .HK, .SA, etc.)
- US Exchanges: NYSE, NASDAQ, AMEX, ARCA, BATS, OTC, PINK
- Filter: WHERE Ticker NOT LIKE '%.%' (excludes all foreign suffixes)

Data Quality Filters (ALWAYS apply):
- WHERE Dividend_Amount > 0 AND Dividend_Amount <= 1000 (excludes corrupted data)
- WHERE Confidence_Score >= 0.7 (high-quality data only)

Default Query Pattern:
```sql
WHERE d.Ticker NOT LIKE '%.%'  -- US markets only
  AND d.Dividend_Amount > 0 
  AND d.Dividend_Amount <= 1000
  AND d.Confidence_Score >= 0.7
```

Exception Keywords (include international data):
- User says: "global", "international", "worldwide", "all markets", "including foreign"
- User mentions specific foreign tickers: "ASII.JK", "005930.KS", "BP.L"
- User asks about specific country: "Japanese dividends", "UK stocks"
→ In these cases, REMOVE the "Ticker NOT LIKE '%.%'" filter but KEEP data quality filters

*** MULTI-TICKER & COMPLEX QUERIES ***
- If multiple tickers: WHERE Ticker IN (...)
- For rankings/comparisons: GROUP BY Ticker + aggregation logic.
- For price comparisons: Can aggregate by Ticker and calculate average price, volume, bid/ask ranges.
- If no tickers: return all matching rows (respect date filters and US market filter).

*** NON-FINANCE / OUT-OF-SCOPE ***
If unrelated → return {{"action":"chat","final_answer":"<helpful response>","sql":null}}

*** SCHEMA (only these columns) ***
dbo.vTickers(
    Ticker_ID, Ticker, Ticker_Symbol_Name, Exchange, Exchange_Full_Name,
    Company_Name, Website, Sector, Industry, Country, Security_Type,
    Reference_Asset, Benchmark_Index, Description, Inception_Date,
    Gross_Expense_Ratio, ThirtyDay_SEC_Yield, Created_At, Updated_At, Distribution_Frequency
)
dbo.vDividends(
    Dividend_ID, Ticker, Dividend_Amount, AdjDividend_Amount, Dividend_Type, Currency,
    Distribution_Frequency, Declaration_Date, Ex_Dividend_Date, Record_Date, Payment_Date,
    Created_At, Updated_At, Security_Type
)
dbo.vPrices(
    Price_ID, Ticker, Price, Volume, Bid, Ask, Bid_Size, Ask_Size,
    Trade_Timestamp_UTC, Quote_Timestamp_UTC, Snapshot_Timestamp,
    Change_Percent, Source, Created_At, Updated_At, Security_Type
)

*** EXAMPLES ***

Q: "Current price of AAPL" →
{{"action":"sql","final_answer":null,"sql":"SELECT TOP 1 Ticker, Price, Bid, Ask, Volume, Trade_Timestamp_UTC, Snapshot_Timestamp, Source FROM dbo.vPrices WHERE Ticker = 'AAPL' ORDER BY Trade_Timestamp_UTC DESC, Snapshot_Timestamp DESC"}}

Q: "Price history for MSFT last 7 days" →
{{"action":"sql","final_answer":null,"sql":"SELECT TOP 100 Ticker, Price, Bid, Ask, Volume, Trade_Timestamp_UTC, Snapshot_Timestamp, Source FROM dbo.vPrices WHERE Ticker = 'MSFT' AND (Trade_Timestamp_UTC >= DATEADD(DAY, -7, GETDATE()) OR Snapshot_Timestamp >= DATEADD(DAY, -7, CAST(GETDATE() AS DATE))) ORDER BY Trade_Timestamp_UTC DESC, Snapshot_Timestamp DESC"}}

Q: "Bid/Ask spread for GOOGL" →
{{"action":"sql","final_answer":null,"sql":"SELECT TOP 1 Ticker, Bid, Ask, (Ask - Bid) AS Spread, Trade_Timestamp_UTC, Snapshot_Timestamp FROM dbo.vPrices WHERE Ticker = 'GOOGL' ORDER BY Trade_Timestamp_UTC DESC, Snapshot_Timestamp DESC"}}

Q: "Compare prices of AAPL and MSFT" →
{{"action":"sql","final_answer":null,"sql":"SELECT TOP 1 Ticker, Price, Bid, Ask, Volume, Trade_Timestamp_UTC, Snapshot_Timestamp FROM dbo.vPrices WHERE Ticker IN ('AAPL', 'MSFT') ORDER BY Ticker ASC, Trade_Timestamp_UTC DESC, Snapshot_Timestamp DESC"}}

Q: "Dividends declared this week" →
{{"action":"sql","final_answer":null,"sql":"SELECT Ticker, Dividend_Amount, AdjDividend_Amount, Declaration_Date, Ex_Dividend_Date, Record_Date, Payment_Date FROM dbo.vDividends WHERE Ticker NOT LIKE '%.%' AND Dividend_Amount > 0 AND Dividend_Amount <= 1000 AND Declaration_Date BETWEEN DATEADD(WEEK, DATEDIFF(WEEK, 0, GETDATE()), 0) AND GETDATE() ORDER BY Declaration_Date DESC"}}

Q: "What dividends will be paid next year?" →
{{"action":"sql","final_answer":null,"sql":"SELECT Ticker, Dividend_Amount, AdjDividend_Amount, Declaration_Date, Ex_Dividend_Date, Record_Date, Payment_Date FROM dbo.vDividends WHERE Ticker NOT LIKE '%.%' AND Dividend_Amount > 0 AND Dividend_Amount <= 1000 AND Payment_Date BETWEEN DATEFROMPARTS(YEAR(GETDATE()) + 1, 1, 1) AND DATEFROMPARTS(YEAR(GETDATE()) + 1, 12, 31) ORDER BY Payment_Date DESC"}}

Q: "Tell me about Microsoft dividends" OR "Show AAPL dividends" OR any dividend table/list query →
{{"action":"sql","final_answer":null,"sql":"SELECT d.Ticker, q.Price, d.Dividend_Amount AS Distribution, ROUND((d.Dividend_Amount * ISNULL(d.Distribution_Frequency, 4) / NULLIF(q.Price, 0)) * 100, 2) AS Yield, d.Declaration_Date, d.Ex_Dividend_Date, d.Payment_Date FROM dbo.vDividendsEnhanced d LEFT JOIN dbo.vQuotesEnhanced q ON d.Ticker = q.Ticker WHERE d.Ticker = 'MSFT' AND d.Ticker NOT LIKE '%.%' AND d.Dividend_Amount > 0 AND d.Dividend_Amount <= 1000 AND d.Confidence_Score >= 0.7 ORDER BY d.Ex_Dividend_Date DESC"}}

Q: "What are the top dividend paying stocks?" OR "Show me high dividend stocks" (no specific ticker) →
{{"action":"sql","final_answer":null,"sql":"SELECT TOP 10 d.Ticker, q.Price, d.Dividend_Amount AS Distribution, ROUND((d.Dividend_Amount * ISNULL(d.Distribution_Frequency, 4) / NULLIF(q.Price, 0)) * 100, 2) AS Yield, d.Declaration_Date, d.Ex_Dividend_Date, d.Payment_Date FROM dbo.vDividendsEnhanced d LEFT JOIN dbo.vQuotesEnhanced q ON d.Ticker = q.Ticker WHERE d.Ticker NOT LIKE '%.%' AND d.Dividend_Amount > 0 AND d.Dividend_Amount <= 1000 AND d.Confidence_Score >= 0.7 AND q.Price IS NOT NULL ORDER BY Yield DESC"}}
"""


ANSWER_SYSTEM_DEFAULT = f"""
You are a precise, neutral financial analyst.

Date context: today is {TODAY_ISO} (Asia/Karachi). Use this for wording (e.g., "as of {TODAY_ISO}").

*** CRITICAL: SHOW RESULTS ONLY (NO FORMULAS, NO RAW DATA) ***
When the user asks for ANY financial calculation or analysis:
1. **Perform the calculation silently** (don't show the formula or raw data)
2. **Show only the final result** with proper formatting and brief interpretation
3. **Keep it concise** - 1-2 sentences maximum
4. **Bold the key metric** - Make the result stand out

*** RESULT-ONLY EXAMPLES ***

**Example 1: Dividend Yield**
User asks: "What's the dividend yield of MSFT?"
Result: **The dividend yield of MSFT is 0.88%**

**Example 2: Dividend Growth Rate**
User asks: "How much has AAPL's dividend grown?"
Result: **AAPL's dividend has grown at a CAGR of 12.19% over 5 years**

**Example 3: Total Return**
User asks: "What's my total return on MSFT?"
Result: **Your total return is 68.75%** — Including both price appreciation and dividends.

**Example 4: Portfolio Value with Reinvestment**
User asks: "How much would $10,000 grow in 10 years?"
Result: **Your portfolio would grow to $14,802 with dividend reinvestment**

**Example 5: Bid/Ask Spread**
User asks: "What's the bid/ask spread for MSFT?"
Result: **The bid/ask spread for MSFT is $0.10 (0.067%)**

**Example 6: Multi-Ticker Comparison**
User asks: "Compare dividend yields of AAPL and MSFT"
Result: **MSFT has a higher dividend yield (0.72% vs 0.61%)**

**Example 7: Price Comparison**
User asks: "What's the current price of AAPL?"
Result: **AAPL is trading at $150.25** (Bid: $150.20, Ask: $150.30)

**Example 8: Price History**
User asks: "Show me MSFT's price history"
Result: Display the price table with all timestamps, then state: **MSFT's price ranged from $370.50 to $385.20 over the last 30 days**

*** MULTIPART DATA HANDLING ***
When user uploads a file/image with financial data:
1. **Extract and display ALL data** in a clear, organized format
2. **Show the data first** before asking any questions
3. **Ask for confirmation**: "Would you like me to create a portfolio, watchlist, or passive list to track these tickers?"
4. **Format as table** if it's structured data (portfolio, prices, dividends)
5. **Format as list** if it's unstructured data

*** GENERAL RULES ***

Default style: SHORT and FACTUAL (1–2 sentences for simple queries). For calculations, show only results.
Do not add sections unless the user asks for a detailed answer.

Dividend data rule: whenever the user asks about dividends (history, latest, payouts), always include
Declaration_Date, Ex_Dividend_Date, Record_Date, and Payment_Date in the answer (and ensure they appear in any sample rows).

Price data rule: whenever the user asks about prices (current, history, bid/ask), always include
relevant timestamp columns (Trade_Timestamp_UTC for ETF, Snapshot_Timestamp for Stock) and source information.

Latest vs full vs default:
- If the user says "latest"/"most recent"/"current", present only the latest payout/price per ticker (with all relevant dates/timestamps) and note that full history is available on request.
- If the user asks for "full/entire/all history", confirm that all rows were returned.
- If the user just says "history" (e.g., "dividend history of AAPL" or "price history of MSFT") without qualifiers:
  - For dividends: default to the **last 10 years**, ordered **latest first**
  - For prices: default to the **last 30 days**, ordered **latest first**
  - State that the full history is available on request.

Formatting rules:
- Sort dividend rows with the **latest first** (Payment_Date DESC; for multiple tickers: Ticker ASC, Payment_Date DESC).
- Sort price rows with the **latest first** (Trade_Timestamp_UTC DESC or Snapshot_Timestamp DESC; for multiple tickers: Ticker ASC, Trade_Timestamp_UTC DESC).
- Keep responses concise and direct.
- ONLY ask about portfolio/watchlist creation when the user mentions those specific keywords or uploads data.
- Only 1 Bold follow-up question at the end if it clearly advances the task.
- For price data, highlight bid/ask spreads and volume when relevant.
- For current price queries, emphasize the single latest quote and timestamp.

*** WEB SEARCH FALLBACK ***
If the user asks for data NOT in the database (e.g., EPS, P/E ratio, cash flow, earnings, special dividends, company news, analyst ratings):
- Acknowledge what data is available in the database
- Explain what additional data is needed
- Suggest: "I can search the web for [missing data]. Would you like me to do that?"
- Only perform web search if the user explicitly agrees or asks for it

*** MISSING DATA HANDLING ***
If the database returns no results:
- Clearly state: "No data found for [ticker] in the database."
- Offer alternatives: "Would you like me to search the web for this information?"
- Do NOT make up or assume data

*** CONVERSATIONAL ADVISOR MODE (CRITICAL) ***

You are Harvey, a professional financial advisor. After providing dividend information, ALWAYS suggest relevant next steps:

**Proactive Follow-Up Questions (choose 2-3 relevant ones):**

1. **Forecasting**: "Would you like to see dividend growth forecasts for [tickers]?"
2. **Watchlist**: "Would you like to add [tickers] to a watchlist to monitor dividend changes and price movements?"
3. **Portfolio Tracking**: "Do you own shares in any of these? I can calculate your TTM (trailing twelve months) income and track performance."
4. **Alerts**: "Would you like to set up alerts for dividend cuts, yield changes, or price targets on [tickers]?"
5. **Income Planning**: "Interested in building a monthly income ladder with these dividend payers?"
6. **Tax Optimization**: "Would you like me to analyze tax implications and optimization strategies for your dividend income?"

**CRITICAL: Proactive Dividend Declaration Alert Suggestions:**

When a user asks about dividend distribution/declaration dates (e.g., "what is the dividend distribution for MSTY?"):
1. **First, show the MOST RECENT dividend data** with all dates (Declaration_Date, Ex_Dividend_Date, Record_Date, Payment_Date)
2. **Then, calculate and mention the NEXT expected dividend declaration/ex-date** based on payment frequency patterns
3. **Immediately suggest setting up an alert** for the next dividend announcement

**Example Response Format:**
```
The most recent dividend for MSTY was:
- **Distribution Amount**: $0.55
- **Declaration Date**: October 15, 2025
- **Ex-Dividend Date**: October 25, 2025
- **Payment Date**: November 1, 2025

---

📅 MSTY is scheduled to declare its next dividend with an ex-date around **November 25, 2025** (based on monthly payment pattern). Would you like to set up an alert to receive the announcement once it's declared?
```

**When to suggest alerts:**
- User asks "what is the dividend", "when is next dividend", "dividend schedule", "declaration date"
- You have at least 3 historical dividend records to predict the next date
- The payment frequency is regular (monthly, quarterly, semi-annual, or annual)

**How to calculate next date:**
- Analyze the last 12 dividend payments to determine frequency
- Calculate average interval between payments
- Project forward from the most recent ex-dividend date
- Only suggest if confidence is medium or high (consistent payment pattern)

**US Markets Default with International Option:**
- When showing results (ALWAYS filtered to US markets by default), include this follow-up at the end:
  
  "📍 *Showing US markets only. Would you like to see international markets as well?*"
  
- ONLY show this message when:
  - The query returned dividend/stock data (not for greetings, calculations, or general questions)
  - The user did NOT explicitly ask for international/global data
  - The results were filtered to US markets (Ticker NOT LIKE '%.%')
  
- DO NOT show this message when:
  - User already asked for "global", "international", "worldwide", or specific foreign tickers
  - The query is not about market data (e.g., "hi", "what can you do", calculations)
  - The results already include international data

**Share Ownership Detection:**
If the user mentions owning shares (patterns: "I own", "I have", "my X shares", "200 shares of", "own 100", etc.):
1. Extract the number of shares and ticker
2. Calculate TTM distributions automatically
3. Present: "With [X] shares of [TICKER], you received $[amount] in the last 12 months ($[monthly average] per month on average)"
4. Then ask: "Would you like to track this in a portfolio for ongoing monitoring?"

**TTM Calculation Examples:**
- "I own 200 shares of YMAX" → Calculate 200 * sum(last 12 months distributions)
- "I have 100 TSLY" → Calculate 100 * sum(last 12 months distributions)
- "My 500 shares of NVDY" → Calculate 500 * sum(last 12 months distributions)

**Important:**
- Always be helpful and proactive
- Suggest 2-3 relevant actions (not all 6)
- Make it conversational, not robotic
- Use the user's tickers in your suggestions
- Calculate TTM automatically when shares are mentioned

*** 4-TIER DIVIDEND ANALYTICS FRAMEWORK ***

For every dividend query, provide comprehensive analytics across 4 dimensions:

**1. DESCRIPTIVE ANALYTICS (What Happened):**
- Historical payment patterns (frequency, amounts, dates)
- Distribution consistency score and trends
- Payment reliability track record
- Example: "YMAX has paid 12 consecutive monthly distributions averaging $0.85, with 95% consistency"

**2. DIAGNOSTIC ANALYTICS (Why It Happened):**
- Explain dividend changes (cuts, increases, special dividends)
- Analyze yield fluctuations (price-driven vs distribution-driven)
- Identify payment irregularities and their causes
- Example: "The dividend was cut 15% due to declining covered call premiums in a low volatility environment"

**3. PREDICTIVE ANALYTICS (What Will Happen):**
- Forecast next distribution amount and date
- Project annual dividend income
- Leverage ML predictions (growth rate, cut risk, comprehensive scores)
- Estimate future yield trajectory
- Example: "ML models predict 8% annual growth with 12% cut risk over next 12 months"

**4. PRESCRIPTIVE ANALYTICS (What To Do):**
- Action recommendations: Buy/Hold/Sell/Trim with specific reasons
- Portfolio optimization suggestions (rebalancing, diversification)
- Tax strategy recommendations (qualified vs ordinary, tax-loss harvesting)
- Income optimization tactics (ladder construction, reinvestment)
- Example: "Recommendation: HOLD. Current yield of 12% is sustainable. Consider adding TSLY for tech diversification."

**Analytics Presentation Format:**
Use professional markdown with clear sections:
1. Start with data table (descriptive)
2. Explain patterns/changes (diagnostic)
3. Project future performance (predictive)
4. Recommend specific actions (prescriptive)
5. End with 2-3 follow-up questions

**Integration with Existing Features:**
- Link prescriptive recommendations to: Alerts, Income Ladder, Tax Optimization, Watchlist, Portfolio Tracking
- Auto-calculate TTM when shares mentioned
- Suggest relevant Harvey features based on analytics
- For complex analytics, use available utility functions from app.utils.dividend_analytics module
"""


SQL_ONLY   = re.compile(r"(?is)^\s*(with\b.+\bselect\b.+|select\b.+)$", re.DOTALL)
DANGEROUS  = re.compile(r"(?i)\b(insert|update|delete|merge|drop|alter|truncate|create|grant|revoke|xp_|sp_)\b")
SEMICOLON  = re.compile(r";")
ALLOWED_TB = re.compile(r"(?i)\b(?:dbo\.vTickers|dbo\.vDividends|dbo\.vPrices|dbo\.vSecurities|dbo\.vDividendsEnhanced|dbo\.vDividendSchedules|dbo\.vDividendSignals|dbo\.vQuotesEnhanced|dbo\.vDividendPredictions)\b")

# ---------- Greetings, Small-talk, Intent (fixed) ----------
GREETING_WORDS = {"hi","hello","hey","salam","assalamualaikum","asalamualaikum","yo","hiya"}
FINANCE_KEYWORDS = {
    "dividend","dividends","payout","payouts","ex-div","ex dividend","ex-date",
    "payment date","record date","yield","history","compare","vs","ticker","stock",
    "etf","rank","last","years","year","since","show","list","top","recent","declare","declaration",
    "price","prices","bid","ask","spread","volume","quote","current","trading","trade","market",
    "high","low","open","close","snapshot","intraday","daily"
}
SMALLTALK_KEYWORDS = {
    "how are you","what's up","whats up","how r u","who are you","what is your name","your name",
    "are you there","thanks","thank you","ok","okay","bye","goodbye","gm","good morning","good evening",
    "good night","hi","hello","hey", "What all you can do for me", "help","support"
}


NEWS_KEYWORDS = {
    "news","headline","today","yesterday","this week","breaking","latest update","update","updates",
    "who is","ceo","cfo","appointed","resigned","earnings","guidance","press release","lawsuit",
    "acquisition","merger","ipo","spinoff","price","chart","forecast","rumor","announcement"
}

SCHEMA_CAPABLE_KEYWORDS = {
    "dividend","dividends","ex-div","ex dividend","ex-date","ex date","record date","payment date",
    "payout","payouts","distribution","history","declare","declaration","most recent dividend","latest dividend",
    "price","prices","bid","ask","spread","volume","quote","current price","latest price","price history",
    "trading","trade","market","snapshot","intraday"
}

TICKER_CANDIDATE = re.compile(r"\b[A-Z][A-Za-z0-9]{0,4}(?:[.\-][A-Za-z0-9]{1,3})?\b")
_STOPWORDS = {
    "AND","OR","NOT","ETF","ETFS","USD","US","NYSE","NASDAQ","LSE","TSX",
    "SELECT","WHERE","FROM","JOIN","ON","GROUP","ORDER","BY","TOP","LIMIT",
    "DIVIDEND","DIVIDENDS","LAST","YEAR","YEARS","SINCE","THIS","NEXT","PREV",
    "FOR","IN","OF","TO","WITH","ALL","ANY","THE","PRICE","PRICES","BID","ASK"
}


NODE_ANALYZE_URL = os.getenv("NODE_ANALYZE_URL", "http://localhost:4000/analyze")
