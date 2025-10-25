import os, re, json, time, math, datetime as dt

from zoneinfo import ZoneInfo

DEFAULT_TZ   = ZoneInfo("Asia/Karachi")
TODAY        = dt.datetime.now(DEFAULT_TZ).date()
TODAY_ISO    = TODAY.isoformat()  # e.g., '2025-10-08'


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

Views (preferred):
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
"""


# ---------- Ensure views (idempotent) ----------
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

*** MULTI-TICKER & COMPLEX QUERIES ***
- If multiple tickers: WHERE Ticker IN (...)
- For rankings/comparisons: GROUP BY Ticker + aggregation logic.
- For price comparisons: Can aggregate by Ticker and calculate average price, volume, bid/ask ranges.
- If no tickers: return all matching rows (respect date filters).

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
{{"action":"sql","final_answer":null,"sql":"SELECT Ticker, Dividend_Amount, AdjDividend_Amount, Declaration_Date, Ex_Dividend_Date, Record_Date, Payment_Date FROM dbo.vDividends WHERE Declaration_Date BETWEEN DATEADD(WEEK, DATEDIFF(WEEK, 0, GETDATE()), 0) AND GETDATE() ORDER BY Declaration_Date DESC"}}

Q: "What dividends will be paid next year?" →
{{"action":"sql","final_answer":null,"sql":"SELECT Ticker, Dividend_Amount, AdjDividend_Amount, Declaration_Date, Ex_Dividend_Date, Record_Date, Payment_Date FROM dbo.vDividends WHERE Payment_Date BETWEEN DATEFROMPARTS(YEAR(GETDATE()) + 1, 1, 1) AND DATEFROMPARTS(YEAR(GETDATE()) + 1, 12, 31) ORDER BY Payment_Date DESC"}}
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
"""


SQL_ONLY   = re.compile(r"(?is)^\s*(with\b.+\bselect\b.+|select\b.+)$", re.DOTALL)
DANGEROUS  = re.compile(r"(?i)\b(insert|update|delete|merge|drop|alter|truncate|create|grant|revoke|xp_|sp_)\b")
SEMICOLON  = re.compile(r";")
ALLOWED_TB = re.compile(r"(?i)\b(?:dbo\.vTickers|dbo\.vDividends|dbo\.vPrices)\b")

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
