# Harvey Enhanced File Processing System

## Overview
Harvey now supports comprehensive file processing for portfolio analysis from multiple sources:
- **Local uploads**: PDF, CSV, XLS, XLSX, JPG, PNG, JPEG
- **Cloud integrations**: Google Sheets, Google Drive, OneDrive

## 🎯 Features

### Supported File Types
| Type | Extension | Use Case |
|------|-----------|----------|
| PDF | .pdf | Brokerage statements, reports |
| CSV | .csv | Portfolio exports, spreadsheets |
| Excel (New) | .xlsx | Modern Excel files |
| Excel (Legacy) | .xls | Older Excel files |
| Images | .jpg, .jpeg, .png | Screenshots, scanned documents |

### Cloud Integrations
| Service | URL Format | Authentication |
|---------|------------|---------------|
| Google Sheets | `https://docs.google.com/spreadsheets/d/...` | Service Account |
| Google Drive | `https://drive.google.com/file/d/...` | Service Account |
| OneDrive | `https://onedrive.live.com/...` | OAuth 2.0 |

## 📡 API Endpoints

### 1. Upload Local Files
```bash
POST /files/upload

# Example with curl
curl -X POST "http://localhost:8000/files/upload" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@portfolio.xlsx" \
  -F "include_summary=true"
```

**Response:**
```json
{
  "success": true,
  "file_type": "xlsx",
  "source": "local",
  "holdings_count": 5,
  "tickers": ["HOOY", "MSTY", "SMCY", "MARO", "PLTY"],
  "portfolio_summary": "**PORTFOLIO ANALYSIS (5 holdings detected)**...",
  "metadata": {
    "row_count": 6,
    "column_count": 7
  }
}
```

### 2. Process Cloud Files
```bash
POST /files/cloud

# Example: Google Sheets
curl -X POST "http://localhost:8000/files/cloud" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://docs.google.com/spreadsheets/d/1ABC...xyz/edit",
    "include_summary": true
  }'
```

### 3. Check Service Health
```bash
GET /files/health

# Response
{
  "azure_document_intelligence": {
    "enabled": true,
    "status": "healthy"
  },
  "google_sheets": {
    "enabled": true,
    "status": "healthy"
  },
  "google_drive": {
    "enabled": true,
    "status": "healthy"
  },
  "onedrive": {
    "enabled": false,
    "status": "disabled"
  }
}
```

### 4. Get Supported Types
```bash
GET /files/supported-types
```

## 🔒 Security Features

### File Upload Validation
- **Max file size**: 50MB
- **Allowed extensions**: .pdf, .csv, .xlsx, .xls, .jpg, .jpeg, .png
- **MIME type validation**: Strict content type checking
- **Empty file detection**: Rejects zero-byte files

### Error Handling
- Sanitized error messages (no internal details leaked)
- Proper HTTP status codes:
  - `400` - Bad request (invalid file)
  - `413` - File too large
  - `422` - Processing error
  - `503` - Service unavailable

## 🛠️ Setup & Configuration

### Required Environment Variables

#### Azure Document Intelligence (for PDF/image OCR)
```bash
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-instance.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=your-key-here
```

#### Google Cloud (for Sheets and Drive)
```bash
# Option 1: Service account file path
GOOGLE_SERVICE_ACCOUNT_PATH=/path/to/service-account.json

# Option 2: Service account JSON string
GOOGLE_SERVICE_ACCOUNT_JSON='{"type": "service_account", ...}'
```

#### Microsoft OneDrive
```bash
ONEDRIVE_CLIENT_ID=your-client-id
ONEDRIVE_CLIENT_SECRET=your-client-secret
ONEDRIVE_TENANT_ID=common  # or your tenant ID
```

### Package Installation

Add to `requirements.txt`:
```txt
openpyxl>=3.1.0
xlrd==1.2.0
google-auth>=2.24.0
google-auth-oauthlib>=1.1.0
google-auth-httplib2>=0.1.1
google-api-python-client>=2.108.0
msal>=1.25.0
azure-ai-documentintelligence>=1.0.0
```

Then install:
```bash
pip install -r requirements.txt
```

## 🏗️ Architecture

### Service Components

1. **Enhanced File Processor** (`enhanced_file_processor.py`)
   - Unified entry point for all file processing
   - Automatic format detection
   - Source routing (local vs cloud)

2. **Google Sheets Service** (`google_sheets_service.py`)
   - OAuth service account authentication
   - Read spreadsheet data
   - Convert to CSV for parsing

3. **Google Drive Service** (`google_drive_service.py`)
   - Download files from Drive
   - Support for public and private files
   - Auto-detect file types

4. **OneDrive Service** (`onedrive_service.py`)
   - Microsoft Graph API integration
   - OAuth 2.0 client credentials flow
   - Support for personal and business accounts

5. **Portfolio Parser** (`portfolio_parser.py`)
   - Extract holdings from various formats
   - Normalize data structures
   - Generate summary reports

### Processing Flow

```
User Upload/URL
    ↓
Enhanced File Processor
    ↓
Source Detection → Local File | Google Sheets | Google Drive | OneDrive
    ↓                    ↓              ↓              ↓
File Type Detection → PDF/Image → Azure DI OCR
                   → CSV → Direct Parse
                   → Excel → Pandas Read → CSV
                   → Sheets → API Read → CSV
    ↓
Portfolio Parser
    ↓
Holdings Extraction
    ↓
API Response
```

## 📊 Usage Examples

### Example 1: Upload Excel Portfolio
```python
import requests

url = "http://localhost:8000/files/upload"
headers = {"Authorization": "Bearer YOUR_API_KEY"}
files = {"file": open("portfolio.xlsx", "rb")}
data = {"include_summary": True}

response = requests.post(url, headers=headers, files=files, data=data)
result = response.json()

print(f"Holdings: {result['holdings_count']}")
print(f"Tickers: {', '.join(result['tickers'])}")
print(result['portfolio_summary'])
```

### Example 2: Process Google Sheets
```python
url = "http://localhost:8000/files/cloud"
headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}
data = {
    "url": "https://docs.google.com/spreadsheets/d/1ABC...xyz/edit",
    "include_summary": True
}

response = requests.post(url, headers=headers, json=data)
result = response.json()

for ticker in result['tickers']:
    print(f"Ticker: {ticker}")
```

### Example 3: Analyze PDF Statement
```python
url = "http://localhost:8000/files/upload"
headers = {"Authorization": "Bearer YOUR_API_KEY"}
files = {"file": open("statement.pdf", "rb")}

response = requests.post(url, headers=headers, files=files)
result = response.json()

if result['success']:
    print(f"Extracted {result['holdings_count']} holdings from PDF")
    print(f"Confidence: {result['metadata'].get('confidence', 'N/A')}")
```

## 🚀 Deployment to Azure VM

### 1. Update Requirements on VM
```bash
ssh azureuser@20.81.210.213
cd ~/harvey
nano requirements.txt  # Verify new packages are present
```

### 2. Install Packages
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Set Environment Variables
```bash
sudo nano /etc/systemd/system/harvey-backend.service

# Add under [Service]
Environment="GOOGLE_SERVICE_ACCOUNT_JSON={...}"
Environment="ONEDRIVE_CLIENT_ID=your-id"
Environment="ONEDRIVE_CLIENT_SECRET=your-secret"
```

### 4. Restart Service
```bash
sudo systemctl daemon-reload
sudo systemctl restart harvey-backend
sudo systemctl status harvey-backend
```

### 5. Test Endpoints
```bash
# Health check
curl "http://localhost:8001/files/health" -H "Authorization: Bearer $HARVEY_AI_API_KEY"

# Test upload
curl -X POST "http://localhost:8001/files/upload" \
  -H "Authorization: Bearer $HARVEY_AI_API_KEY" \
  -F "file=@test.csv"
```

## 🧪 Testing

### Test Script
```bash
python test_file_processing.py
```

### Manual Testing
1. **PDF**: Upload brokerage statement
2. **CSV**: Upload portfolio export
3. **Excel**: Upload .xlsx or .xls file
4. **Image**: Upload screenshot of holdings
5. **Google Sheets**: Process shared spreadsheet URL

## 🐛 Troubleshooting

### Issue: "Package not installed"
**Solution**: Install missing packages
```bash
pip install google-api-python-client google-auth msal openpyxl xlrd==1.2.0
```

### Issue: "Google Sheets service not enabled"
**Solution**: Set service account credentials
```bash
export GOOGLE_SERVICE_ACCOUNT_PATH=/path/to/credentials.json
```

### Issue: "File too large"
**Solution**: Current limit is 50MB. Compress or split the file.

### Issue: "Unsupported file type"
**Solution**: Verify file extension is in supported list:
- .pdf, .csv, .xlsx, .xls, .jpg, .jpeg, .png

## 📝 Changelog

### Version 1.0.0 (2025-11-17)
- ✅ Added support for XLS/XLSX files
- ✅ Integrated Google Sheets API
- ✅ Integrated Google Drive API
- ✅ Integrated Microsoft OneDrive API
- ✅ Added comprehensive file validation
- ✅ Implemented secure error handling
- ✅ Created unified processing pipeline
- ✅ Added health check endpoints

## 🔗 Related Documentation
- [Harvey File Processing Capabilities](../HARVEY_FILE_PROCESSING_CAPABILITIES.md)
- [Portfolio Upload Capabilities](../PORTFOLIO_UPLOAD_CAPABILITIES.md)
- [Azure Document Intelligence](https://docs.microsoft.com/azure/ai-services/document-intelligence/)
- [Google Sheets API](https://developers.google.com/sheets/api)
- [Microsoft Graph API](https://docs.microsoft.com/graph/)
