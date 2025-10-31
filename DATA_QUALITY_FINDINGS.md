# Harvey Data Quality Report - Key Findings

**Generated:** October 31, 2025  
**Database:** Azure SQL Server (HeyDividend Production)

---

## Executive Summary

Analysis of **433,185 dividend records** across **9,658 unique tickers** revealed significant data quality issues that explain the incorrect dividend totals you reported.

### Critical Issues Found

| Issue Type | Count | Severity |
|------------|-------|----------|
| **Unrealistic Amounts** (>$1,000/share) | 170 | 🔴 **CRITICAL** |
| **Zero Dividends** | 34 | 🟡 Medium |
| **Missing Payment Dates** | 3,028 | 🟡 Medium |

---

## Detailed Findings

### 1. Unrealistic Dividend Amounts (170 issues)

**Root Cause:** Database contains total corporate payouts instead of per-share amounts for certain tickers.

#### Top Offenders:
| Ticker | Amount | Ex-Date | Issue |
|--------|--------|---------|-------|
| **ASII.JK** | $5,017,628.00 | 2025-05-21 | Indonesian stock - likely total company payout |
| **PGAS.JK** | $2,966,282.00 | 2025-06-12 | Indonesian stock - likely total company payout |
| **AKR** | $2,642,823.53 | Multiple dates (1993-1997) | 15 identical entries - data corruption |

**Pattern Identified:**
- **AKR:** 46 duplicate entries with identical unrealistic amounts from 1993-2008
- **Indonesian stocks (.JK):** Foreign exchange or data source issues
- **Korean stocks (.KS):** Similar currency conversion problems

---

### 2. AKR Specific Analysis

**Total Bad Records:** 46 entries  
**Date Range:** 1993-2008  
**Pattern:** Multiple duplicate amounts repeated across quarters

| Amount | Occurrences | Date Range |
|--------|-------------|------------|
| $2,642,823.53 | 15x | 1993-1997 |
| $1,468,235.29 | 2x | 1997 |
| $954,352.94 | 3x | 2002 |
| $880,941.18 | 13x | 1999-2002 |
| $234,917.65 | 4x | 2003-2004 |

**Conclusion:** AKR data is severely corrupted with what appears to be total quarterly distributions rather than per-share amounts.

---

### 3. Data Source Analysis

**All problematic records:** Source = "Legacy"

This indicates the issues originate from your legacy data migration, not from the new Canonical_Dividends or distribution_schedules tables.

---

## Immediate Recommendations

### ✅ Production Fixes (Apply Now)

1. **Add Amount Filter to All Queries**
   ```sql
   WHERE Dividend_Amount > 0 
     AND Dividend_Amount <= 1000
   ```

2. **Update vDividendsEnhanced View**
   ```sql
   -- Add realistic amount filter
   WHERE Dividend_Amount > 0 
     AND Dividend_Amount <= 1000
     AND Confidence_Score >= 0.7
   ```

3. **Add Data Validation Layer**
   - Reject dividends >$1,000/share on ingestion
   - Flag foreign tickers (.JK, .KS) for manual review
   - Add currency normalization for international stocks

---

## Database Cleanup Required

### Priority 1: Delete Corrupted AKR Records (46 records)
```sql
DELETE FROM vDividends 
WHERE Ticker = 'AKR' 
  AND Dividend_Amount > 1000
```

### Priority 2: Review Indonesian/Korean Stocks
```sql
-- Flag for manual review
SELECT Ticker, Dividend_Amount, Ex_Dividend_Date, Data_Source
FROM vDividends
WHERE (Ticker LIKE '%.JK' OR Ticker LIKE '%.KS')
  AND Dividend_Amount > 100
```

### Priority 3: Fix Missing Payment Dates (3,028 records)
```sql
-- Update NULL payment dates based on typical T+3 settlement
UPDATE vDividends
SET Payment_Date = DATEADD(DAY, 3, Ex_Dividend_Date)
WHERE Payment_Date IS NULL 
  AND Ex_Dividend_Date IS NOT NULL
  AND Data_Source = 'Legacy'
```

---

## Implementation Plan

### Phase 1: Immediate Protection (Today)
- [x] Add data quality endpoint to Harvey API
- [ ] Update SQL generation prompt with amount filter
- [ ] Add validation to markdown formatter

### Phase 2: Data Cleanup (This Week)
- [ ] Delete AKR corrupted records
- [ ] Review and fix international stock amounts
- [ ] Populate missing payment dates

### Phase 3: Prevention (Ongoing)
- [ ] Add pre-ingestion validation for new data
- [ ] Implement currency normalization
- [ ] Add automated data quality alerts

---

## Using the Data Quality API

### Generate Report:
```bash
curl http://your-domain/v1/data-quality/report
```

### Get JSON Format:
```bash
curl http://your-domain/v1/data-quality/issues/json
```

---

## Statistics

| Metric | Value |
|--------|-------|
| Total Dividend Records | 433,185 |
| Unique Tickers | 9,658 |
| Average Dividend | $151.36 |
| **Max Dividend** | **$5,017,628.00** ⚠️ |
| Min Dividend | $0.00 |
| Average Confidence Score | 100.00% |

---

## Next Steps

1. **Review this report** and approve cleanup plan
2. **Apply immediate filters** to protect users from bad data
3. **Schedule database cleanup** to permanently fix corrupted records
4. **Monitor data quality** using the new `/v1/data-quality/report` endpoint

---

**Full Report Available:** `data_quality_report_YYYYMMDD.txt`
