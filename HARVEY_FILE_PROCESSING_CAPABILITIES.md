# Harvey's File Processing & Portfolio Analysis Capabilities

## Overview
Harvey can analyze financial documents, portfolio statements, and dividend reports uploaded as PDFs or images. The system uses multiple extraction methods to ensure comprehensive data capture.

---

## 📄 Supported File Types

### PDF Documents
- ✅ Brokerage statements (Robinhood, Fidelity, Charles Schwab, etc.)
- ✅ Portfolio reports
- ✅ Dividend payment history reports
- ✅ Tax documents (1099-DIV, etc.)
- ✅ Financial statements with tables
- ✅ Scanned documents (with OCR)

### Image Files
- ✅ Screenshots of portfolio holdings
- ✅ Photos of financial documents
- ✅ Charts and graphs
- ✅ Tables and spreadsheets (PNG, JPG, JPEG)

### Office Documents
- ✅ Excel spreadsheets (.xlsx - modern format)
- ✅ Excel legacy files (.xls - older format)
- ✅ CSV files with portfolio data

### Cloud Storage (NEW - 2025)
- ✅ **Google Sheets** - Direct URL processing
- ✅ **Google Drive** - Download and analyze files
- ✅ **OneDrive** - Microsoft cloud file access

---

## 🔧 Processing Technologies

### 1. **Enhanced File Processor** (NEW - Unified System)
**Technology:** Multi-source file processing pipeline  
**Capabilities:**
- Automatic file type detection
- Cloud source routing (Sheets, Drive, OneDrive)
- Secure file validation (50MB limit, type checking)
- Format normalization
- Portfolio data extraction from any source

**Supported Sources:**
- Local uploads (PDF, CSV, XLS, XLSX, images)
- Google Sheets URLs
- Google Drive URLs
- OneDrive URLs

**Security Features:**
- 50MB file size limit
- MIME type validation
- File extension whitelisting
- Sanitized error messages

### 2. **PDF.co Advanced Processing** (NEW - Enhanced)
**Technology:** PDF.co cloud API  
**API Key:** `PDFCO_API_KEY` (configured)  
**Capabilities:**
- ✅ **Advanced OCR** with 95%+ accuracy
- ✅ **Table Extraction** - Preserves table structure from financial statements
- ✅ **PDF to Excel Conversion** - Extract tabular data directly to spreadsheet format
- ✅ **PDF to CSV Conversion** - Export specific pages as CSV
- ✅ **Multi-page Processing** - Handle complex documents efficiently
- ✅ **Financial Document Parser** - Specialized extraction for:
  - Portfolio holdings (Ticker, Shares, Value)
  - Dividend payments (Ticker, Amount, Dates)
  - Account balances
  - Transaction history

**Use Cases:**
- Complex brokerage statements with multiple tables
- Scanned documents requiring high-accuracy OCR
- Bulk portfolio data extraction
- Financial reports with structured data

### 3. **Azure Document Intelligence** (PDF/Image OCR)
**Technology:** Azure AI Document Intelligence (formerly Form Recognizer)  
**Integration:** JSON response flattening via `_maybe_flatten_vision_json()`  
**Capabilities:**
- High-accuracy OCR for PDFs and images
- Multi-page document analysis
- Layout-aware text extraction
- Table structure preservation

### 4. **Excel Processing**
**Technology:** openpyxl (XLSX) + xlrd 1.2.0 (XLS)  
**Capabilities:**
- Modern Excel (.xlsx) via openpyxl
- Legacy Excel (.xls) via xlrd 1.2.0
- Automatic format detection
- Column name recognition
- Data normalization

### 5. **Cloud Integrations**
**Google Sheets:**
- Service account authentication
- Read spreadsheet data
- Convert to CSV for parsing

**Google Drive:**
- Download files from Drive
- Support for public and private files
- Auto-detect file types

**OneDrive:**
- Microsoft Graph API integration
- OAuth 2.0 client credentials
- Personal and business accounts

---

## 🎯 Portfolio Analysis Workflow

### Step 1: File Upload
User uploads a file via the `/chat` endpoint using `multipart/form-data`:

```bash
curl -X POST https://harvey-api.com/chat \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "question=Analyze my portfolio" \
  -F "file=@portfolio.pdf"
```

### Step 2: Automatic Detection & Extraction
Harvey automatically:
1. **Detects file type** (PDF, image, Excel, etc.)
2. **Chooses extraction method**:
   - PDF.co for PDFs with tables/complex data
   - Node service for images and basic PDFs
   - Direct parsing for CSV/Excel files
3. **Extracts data** with OCR and table detection

### Step 3: Intelligent Data Parsing
Harvey identifies and extracts:

**Portfolio Holdings:**
```
AAPL    100 shares    $15,000
MSFT     50 shares    $12,500
GOOGL    25 shares    $3,750
```

**Dividend Payments:**
```
AAPL - $0.24 per share (Ex-date: 2024-11-08)
MSFT - $0.75 per share (Ex-date: 2024-11-15)
```

**Account Information:**
- Total portfolio value
- Cash balance
- Unrealized gains/losses

### Step 4: Contextual Analysis
Harvey provides:
- ✅ **Portfolio Summary** - Total value, allocation by sector
- ✅ **Dividend Analysis** - Annual income, yield by ticker
- ✅ **Income Calculator** - TTM (trailing twelve months) income
- ✅ **Actionable Recommendations** - Based on extracted holdings

---

## 💡 Example Use Cases

### Use Case 1: Brokerage Statement Analysis
**User Action:** Upload Robinhood PDF statement  
**Harvey Response:**
```markdown
I found 12 holdings in your portfolio:

| Ticker | Shares | Current Value | Annual Dividend | Yield |
|--------|--------|---------------|-----------------|-------|
| AAPL   | 100    | $15,000       | $96.00          | 0.64% |
| MSFT   | 50     | $12,500       | $150.00         | 1.20% |
...

**Portfolio Metrics:**
- Total Value: $50,000
- Annual Dividend Income: $1,250
- Average Yield: 2.5%

Would you like me to:
1. Create a watchlist to monitor these holdings?
2. Calculate your TTM income with historical distributions?
3. Set up alerts for dividend cuts or price targets?
```

### Use Case 2: Dividend History Screenshot
**User Action:** Upload screenshot of dividend payment history  
**Harvey Response:**
```markdown
I extracted your dividend payments:

**AAPL Dividends (Last 4 Quarters):**
- Q4 2024: $24.00 (100 shares × $0.24)
- Q3 2024: $23.00 (100 shares × $0.23)
- Q2 2024: $24.00 (100 shares × $0.24)
- Q1 2024: $23.00 (100 shares × $0.23)

**TTM Income: $94.00** from AAPL

Would you like to see growth forecasts for this dividend stream?
```

### Use Case 3: Excel Portfolio Tracker
**User Action:** Upload Excel file with portfolio holdings  
**Harvey Response:**
```markdown
I've analyzed your Excel portfolio:

**15 Holdings Detected:**
- High Yield: QYLD (10.5%), JEPI (8.2%), SCHD (3.5%)
- Growth: AAPL (0.64%), MSFT (1.2%), GOOGL (0%)
- REITs: O (5.2%), STAG (4.8%)

**Diversification Score: 72/100**
- Technology: 40% (overweight)
- REITs: 15%
- Financials: 10%
- Other: 35%

Recommendations:
1. Consider reducing tech exposure (currently 40%)
2. Add international dividend growers for diversification
3. Your REIT allocation is healthy for income generation
```

---

## 🔍 What Harvey Can Extract

### Financial Data Points
✅ **Ticker Symbols** - Detects 1-5 character stock tickers  
✅ **Share Quantities** - Parses numbers with commas and decimals  
✅ **Dollar Values** - Handles $15,000.00 format  
✅ **Dividend Amounts** - Extracts per-share distributions  
✅ **Dates** - Declaration, ex-dividend, payment dates  
✅ **Percentages** - Yields, allocation percentages  
✅ **Account Numbers** - For context (never stored)  

### Table Structures
✅ **Multi-column tables** - Preserves structure  
✅ **Nested tables** - From complex statements  
✅ **Header rows** - Identifies column names  
✅ **Summary rows** - Totals and subtotals  

---

## 🚀 Advanced Features

### 1. **TTM Income Calculator** (Automatic)
When Harvey detects portfolio holdings, it automatically:
- Queries the dividend database for each ticker
- Calculates TTM (trailing twelve months) income
- Shows personalized income messages

**Example:**
```markdown
Based on your 100 shares of AAPL:
- Latest distribution: $0.24 per share
- TTM distributions: $0.96 total
- **Your annual income from AAPL: $96.00**
```

### 2. **Portfolio Tracking Integration**
Harvey can save extracted portfolios:
```markdown
Would you like me to save this portfolio for ongoing tracking?

I can:
- Monitor price changes daily
- Alert you to dividend cuts or increases
- Calculate updated income projections
- Track your total returns
```

### 3. **ML-Enhanced Analysis**
Extracted portfolios get ML intelligence:
- **ML Scoring** - Quality scores for each holding
- **Risk Assessment** - Portfolio-wide risk metrics
- **Diversification Analysis** - Cluster-based insights
- **Optimization Suggestions** - Buy/sell/trim recommendations

---

## 📊 Processing Capabilities Matrix

| Feature | Node Service | PDF.co | Combined |
|---------|--------------|--------|----------|
| Basic Text OCR | ✅ | ✅✅ (Better) | ✅✅ |
| Table Extraction | ❌ | ✅✅ | ✅✅ |
| PDF to Excel | ❌ | ✅ | ✅ |
| Multi-page PDFs | ✅ | ✅✅ | ✅✅ |
| Scanned Documents | ✅ (Basic) | ✅✅ (Advanced) | ✅✅ |
| Financial Parsing | ❌ | ✅ | ✅ |
| Image Files | ✅ | ❌ | ✅ |
| Office Documents | ✅ | ❌ | ✅ |

---

## 🔐 Security & Privacy

### Data Handling
- ✅ **No Permanent Storage** - Files are processed in-memory only
- ✅ **Encrypted Transmission** - HTTPS for all file uploads
- ✅ **API Key Authentication** - Required for all endpoints
- ✅ **Extraction-Only** - No file retention on Harvey servers
- ✅ **Third-Party Privacy** - PDF.co also doesn't retain files (per their policy)

### What Harvey Does NOT Store
- ❌ Account numbers
- ❌ Social Security Numbers
- ❌ Full names or addresses
- ❌ Password or login credentials
- ❌ Uploaded files or images

### What Harvey DOES Extract (Temporarily)
- ✅ Ticker symbols (for analysis)
- ✅ Share quantities (for income calculations)
- ✅ Dividend amounts (for forecasting)
- ✅ Public market data references

---

## 💻 API Integration

### Upload Endpoint
```http
POST /chat
Content-Type: multipart/form-data
Authorization: Bearer YOUR_HARVEY_API_KEY

Form Data:
  - question: "Analyze my portfolio"
  - file: [PDF/image/Excel file]
  - stream: true (optional)
```

### Response Format
```json
{
  "response": "I found 12 holdings in your portfolio...",
  "extracted_data": {
    "holdings": [
      {"ticker": "AAPL", "shares": 100, "value": 15000},
      {"ticker": "MSFT", "shares": 50, "value": 12500}
    ],
    "total_value": 27500,
    "processing_method": "pdfco_advanced"
  },
  "session_id": "sess_123",
  "conversation_id": "conv_456"
}
```

---

## 🎯 Best Practices for Users

### For Best Extraction Results:
1. **Upload Clear Documents** - High resolution PDFs or images
2. **Use Original Files** - Not photocopies when possible
3. **Include Full Pages** - Don't crop important data
4. **Multiple Files OK** - Upload statements one at a time for sequential analysis

### Optimal File Types:
- 🥇 **PDF** (digital/born-digital preferred over scanned)
- 🥈 **Excel/CSV** (for structured data)
- 🥉 **High-res PNG/JPG** (for screenshots)

### Questions to Ask Harvey:
- "Analyze my portfolio from this statement"
- "What's my total dividend income from this file?"
- "Extract all holdings and calculate my yield"
- "Create a watchlist from these tickers"
- "What are the dividend dates for my holdings?"

---

## 🔮 Future Enhancements

### Planned Features:
- 📊 **Automatic Chart Recognition** - Extract data from pie charts and bar graphs
- 📈 **Performance Tracking** - Compare uploaded statements month-over-month
- 🔔 **Statement Alerts** - Notify when new uploads show significant changes
- 🤖 **Smart Recommendations** - ML-driven suggestions based on extracted portfolios
- 📧 **Email Integration** - Forward statements directly to Harvey for analysis

---

## 📞 Support & Troubleshooting

### Common Issues:

**Problem:** "Harvey couldn't extract my portfolio"  
**Solution:** 
- Ensure the PDF contains actual text (not just an image)
- Try uploading as a high-res PNG screenshot instead
- Verify the file isn't password-protected

**Problem:** "Some tickers are missing"  
**Solution:**
- Non-standard tickers may need clarification (e.g., crypto symbols)
- International tickers may require explicit market specification

**Problem:** "Dividend amounts are incorrect"  
**Solution:**
- Verify the source document shows per-share amounts (not total)
- Some statements show net amounts (after tax) - clarify with Harvey

---

## 📚 Related Features

- **Conversational Memory** - Harvey remembers your uploaded portfolios across sessions
- **Income Ladder Builder** - Use extracted holdings to build monthly income streams
- **Tax Optimization** - Analyze qualified vs. ordinary dividends from statements
- **ML Predictions** - Get yield forecasts for extracted holdings
- **Natural Language Alerts** - "Alert me if any holding cuts dividends"

---

**Last Updated:** November 17, 2025  
**Harvey Version:** Harvey-1o  
**Enhanced File Processing:** v2.0 (Cloud Integrations + XLS Support)
