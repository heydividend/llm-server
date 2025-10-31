# US Market Filtering Implementation

**Date:** October 31, 2025  
**Feature:** Default US Market Filtering with International Option

---

## Overview

Harvey now defaults to **US markets only** for all dividend and stock queries, with an optional prompt to view international markets. This prevents users from seeing corrupted international data and provides a cleaner, more focused experience.

---

## Implementation Details

### 1. **SQL Query Filtering**

All dividend queries now include these filters by default:

```sql
WHERE Ticker NOT LIKE '%.%'        -- Excludes foreign tickers (.JK, .KS, .L, etc.)
  AND Dividend_Amount > 0          -- Excludes zero/negative amounts
  AND Dividend_Amount <= 1000      -- Excludes corrupted data (>$1,000/share)
  AND Confidence_Score >= 0.7      -- High-quality data only
```

### 2. **US Market Definition**

**Included Markets:**
- NYSE (New York Stock Exchange)
- NASDAQ
- AMEX (American Stock Exchange)
- ARCA (NYSE Arca)
- BATS
- OTC (Over-the-Counter)
- PINK (Pink Sheets)

**Excluded Markets (by default):**
- Indonesian stocks (.JK suffix)
- Korean stocks (.KS suffix)
- UK stocks (.L suffix)
- Japanese stocks (.T suffix)
- Canadian stocks (.TO suffix)
- Australian stocks (.AX suffix)
- Hong Kong stocks (.HK suffix)
- Brazilian stocks (.SA suffix)
- All other international exchanges

---

## User Experience

### Default Behavior

**User Query:** "What are the top dividend paying stocks?"

**Harvey Response:**
1. Shows dividend table (US stocks only)
2. Provides analysis and recommendations
3. **Adds follow-up:** "📍 *Showing US markets only. Would you like to see international markets as well?*"

### International Data Access

Users can request international data by:

1. **Explicit keywords:**
   - "Show me **global** dividend stocks"
   - "What are the **international** high-yield ETFs?"
   - "Give me **worldwide** dividend data"

2. **Specific foreign tickers:**
   - "Tell me about **ASII.JK** dividends"
   - "Show **BP.L** dividend history"

3. **Country-specific queries:**
   - "Japanese dividend stocks"
   - "UK dividend aristocrats"

---

## Data Quality Protection

This filtering also protects users from seeing corrupted data:

| Issue | Filter Protection |
|-------|------------------|
| Unrealistic amounts (>$1,000) | `Dividend_Amount <= 1000` |
| Zero/negative amounts | `Dividend_Amount > 0` |
| Low-confidence data | `Confidence_Score >= 0.7` |
| Foreign corrupted data | `Ticker NOT LIKE '%.%'` |

**Example of protected corruption:**
- ASII.JK: $5,017,628.00 (excluded by both foreign ticker and amount filters)
- AKR: $2,642,823.53 (excluded by amount filter)

---

## Technical Changes

### Files Modified

1. **`app/config/settings.py`**
   - Added US market filtering section to `PLANNER_SYSTEM_DEFAULT`
   - Updated SQL examples to include filters
   - Added data quality filtering rules
   - Added international market follow-up to `ANSWER_SYSTEM_DEFAULT`

2. **`replit.md`**
   - Documented default US market focus
   - Added user instructions for accessing international data

---

## Example Queries

### Query 1: Top Dividend Stocks (Default US)

**User:** "What are the top dividend paying stocks?"

**Generated SQL:**
```sql
SELECT TOP 10 
  d.Ticker, 
  q.Price, 
  d.Dividend_Amount AS Distribution, 
  ROUND((d.Dividend_Amount * ISNULL(d.Distribution_Frequency, 4) / NULLIF(q.Price, 0)) * 100, 2) AS Yield
FROM dbo.vDividendsEnhanced d 
LEFT JOIN dbo.vQuotesEnhanced q ON d.Ticker = q.Ticker 
WHERE d.Ticker NOT LIKE '%.%'           -- US only
  AND d.Dividend_Amount > 0 
  AND d.Dividend_Amount <= 1000
  AND d.Confidence_Score >= 0.7
  AND q.Price IS NOT NULL
ORDER BY Yield DESC
```

**Result:** US stocks only (YMAX, TSLY, NVDY, MSTY, etc.)

---

### Query 2: Global Dividend Stocks (User Requested)

**User:** "Show me **global** high dividend stocks"

**Generated SQL:**
```sql
SELECT TOP 10 
  d.Ticker, 
  q.Price, 
  d.Dividend_Amount AS Distribution, 
  ROUND((d.Dividend_Amount * ISNULL(d.Distribution_Frequency, 4) / NULLIF(q.Price, 0)) * 100, 2) AS Yield
FROM dbo.vDividendsEnhanced d 
LEFT JOIN dbo.vQuotesEnhanced q ON d.Ticker = q.Ticker 
WHERE d.Dividend_Amount > 0              -- Data quality filter
  AND d.Dividend_Amount <= 1000          -- Data quality filter  
  AND d.Confidence_Score >= 0.7          -- Data quality filter
  AND q.Price IS NOT NULL
ORDER BY Yield DESC
```

**Note:** `Ticker NOT LIKE '%.%'` filter is **removed** when user requests global data.

---

## Benefits

✅ **Cleaner Results** - No foreign ticker corruption (ASII.JK, PGAS.JK, etc.)  
✅ **Data Quality** - Automatic filtering of unrealistic amounts  
✅ **User Control** - Easy access to international data when needed  
✅ **Better UX** - Clear indication of market scope with optional expansion  
✅ **Reduced Confusion** - US investors see relevant data first  

---

## Future Enhancements

1. **Regional Filters** - Allow users to filter by specific regions (Europe, Asia, Latin America)
2. **Exchange-Level Filtering** - Filter by specific exchanges (NYSE only, NASDAQ only)
3. **User Preferences** - Remember user's preferred market scope
4. **Currency Normalization** - Convert foreign dividends to USD for comparison

---

## Testing

Test the feature with these queries:

```
1. "What are the top dividend paying stocks?"
   → Should show US stocks only + international prompt

2. "Show me global dividend stocks"
   → Should include international stocks

3. "Tell me about ASII.JK dividends"
   → Should specifically query the Indonesian stock

4. "Compare YMAX and TSLY dividends"
   → Should show both US ETFs (no international prompt needed)
```

---

**Implementation Status:** ✅ Complete  
**Server Restart Required:** Yes (already done)  
**Documentation Updated:** Yes
