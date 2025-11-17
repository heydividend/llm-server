## File Processing

Harvey's enhanced file processing system supports 7 file types and 3 cloud storage platforms for comprehensive portfolio analysis.

### Supported File Types

- **PDF** - Brokerage statements, reports (.pdf)
- **CSV** - Portfolio exports (.csv)
- **Excel (Modern)** - .xlsx files
- **Excel (Legacy)** - .xls files  
- **Images** - Screenshots, scanned documents (.jpg, .jpeg, .png)

### Supported Cloud Storage

- **Google Sheets** - Direct spreadsheet URL processing
- **Google Drive** - Download and analyze files from Drive
- **OneDrive** - Microsoft cloud file access

---

### POST /files/upload

Upload a local file for portfolio analysis.

**Request Headers:**
```
Content-Type: multipart/form-data
Authorization: Bearer YOUR_API_KEY
```

**Request Body (Form Data):**
- `file` (required): File to upload
- `include_summary` (optional): Return formatted summary (default: false)

**cURL Example:**
```bash
curl -X POST http://localhost:8001/files/upload \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@portfolio.xlsx" \
  -F "include_summary=true"
```

**Response (Success):**
```json
{
  "success": true,
  "file_type": "xlsx",
  "source": "local",
  "holdings_count": 5,
  "tickers": ["AAPL", "MSFT", "JNJ", "KO", "PEP"],
  "portfolio_summary": "**PORTFOLIO ANALYSIS (5 holdings detected)**\n\n...",
  "metadata": {
    "row_count": 6,
    "column_count": 7,
    "detected_columns": ["Symbol", "Shares", "Price", "Value"]
  }
}
```

**Error Responses:**
```json
// File too large (>50MB)
{
  "detail": "File too large. Maximum size is 50MB"
}

// Unsupported file type
{
  "detail": "Unsupported file type. Allowed: .pdf, .csv, .xlsx, .xls, .jpg, .jpeg, .png"
}

// Processing error
{
  "detail": "Error processing file"
}
```

---

### POST /files/cloud

Process a file from cloud storage (Google Sheets, Drive, OneDrive).

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY
```

**Request Body:**
```json
{
  "url": "https://docs.google.com/spreadsheets/d/1ABC...xyz/edit",
  "include_summary": true
}
```

**Supported URL Formats:**
- **Google Sheets**: `https://docs.google.com/spreadsheets/d/{id}/edit`
- **Google Drive**: `https://drive.google.com/file/d/{id}/view`
- **OneDrive**: `https://onedrive.live.com/...`

**cURL Example:**
```bash
curl -X POST http://localhost:8001/files/cloud \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://docs.google.com/spreadsheets/d/1ABC...xyz/edit",
    "include_summary": true
  }'
```

**Response (Success):**
```json
{
  "success": true,
  "file_type": "google_sheets",
  "source": "cloud",
  "holdings_count": 8,
  "tickers": ["HOOY", "MSTY", "SMCY", "MARO", "PLTY", "CVNY", "YETH", "CONY"],
  "portfolio_summary": "**PORTFOLIO ANALYSIS (8 holdings detected)**\n\n...",
  "metadata": {
    "sheet_name": "Portfolio",
    "row_count": 9,
    "column_count": 6
  }
}
```

**Error Responses:**
```json
// Invalid URL
{
  "detail": "Invalid cloud storage URL"
}

// Service not available
{
  "detail": "Cloud service not enabled or credentials not configured"
}
```

---

### GET /files/health

Check the health status of all file processing services.

**Request Headers:**
```
Authorization: Bearer YOUR_API_KEY
```

**cURL Example:**
```bash
curl -X GET http://localhost:8001/files/health \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Response:**
```json
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
    "status": "disabled",
    "reason": "Credentials not configured"
  }
}
```

---

### GET /files/supported-types

Get a list of all supported file types and cloud sources.

**cURL Example:**
```bash
curl -X GET http://localhost:8001/files/supported-types \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Response:**
```json
{
  "local_files": [
    {
      "type": "pdf",
      "extension": ".pdf",
      "description": "PDF documents (brokerage statements, reports)"
    },
    {
      "type": "csv",
      "extension": ".csv",
      "description": "CSV files (portfolio exports)"
    },
    {
      "type": "xlsx",
      "extension": ".xlsx",
      "description": "Excel files (modern format)"
    },
    {
      "type": "xls",
      "extension": ".xls",
      "description": "Excel files (legacy format)"
    },
    {
      "type": "image",
      "extension": ".jpg, .jpeg, .png",
      "description": "Images (screenshots, scans)"
    }
  ],
  "cloud_sources": [
    {
      "source": "google_sheets",
      "enabled": true,
      "description": "Google Sheets spreadsheets"
    },
    {
      "source": "google_drive",
      "enabled": true,
      "description": "Google Drive files"
    },
    {
      "source": "onedrive",
      "enabled": false,
      "description": "Microsoft OneDrive files"
    }
  ]
}
```

---

### File Processing Workflow

```
┌─────────────────┐
│  User Upload    │
│  or Cloud URL   │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  File Type      │
│  Detection      │
└────────┬────────┘
         │
    ┌────┴─────┐
    │          │
    v          v
┌─────────┐  ┌──────────────┐
│ Local   │  │ Cloud Source │
│ File    │  │ (Sheets/     │
│         │  │  Drive/      │
│         │  │  OneDrive)   │
└────┬────┘  └──────┬───────┘
     │              │
     └──────┬───────┘
            │
            v
     ┌──────────────┐
     │  Format      │
     │  Processor   │
     │  (PDF/Excel/ │
     │   CSV/Image) │
     └──────┬───────┘
            │
            v
     ┌──────────────┐
     │  Portfolio   │
     │  Parser      │
     └──────┬───────┘
            │
            v
     ┌──────────────┐
     │  Extract     │
     │  Holdings    │
     └──────┬───────┘
            │
            v
     ┌──────────────┐
     │  Response    │
     └──────────────┘
```

---

### Security Features

**File Validation:**
- ✅ Maximum file size: 50MB
- ✅ MIME type validation
- ✅ File extension whitelisting
- ✅ Empty file detection

**Error Handling:**
- ✅ Sanitized error messages (no internal details leaked)
- ✅ Proper HTTP status codes
- ✅ Graceful service degradation

**Privacy:**
- ✅ Files processed in-memory only
- ✅ No permanent storage
- ✅ Automatic cleanup after processing

---

### Integration Examples

**JavaScript/React:**
```javascript
// Upload local file
async function uploadPortfolio(file) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('include_summary', 'true');
  
  const response = await fetch('http://localhost:8001/files/upload', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer YOUR_API_KEY'
    },
    body: formData
  });
  
  return await response.json();
}

// Process cloud file
async function processCloudFile(url) {
  const response = await fetch('http://localhost:8001/files/cloud', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer YOUR_API_KEY',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ 
      url: url,
      include_summary: true 
    })
  });
  
  return await response.json();
}

// Check health
async function checkFileServices() {
  const response = await fetch('http://localhost:8001/files/health', {
    headers: {
      'Authorization': 'Bearer YOUR_API_KEY'
    }
  });
  
  return await response.json();
}
```

**Python:**
```python
import requests

API_KEY = "your_api_key"
BASE_URL = "http://localhost:8001"

# Upload file
def upload_portfolio(file_path):
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {'include_summary': 'true'}
        headers = {'Authorization': f'Bearer {API_KEY}'}
        
        response = requests.post(
            f'{BASE_URL}/files/upload',
            headers=headers,
            files=files,
            data=data
        )
        return response.json()

# Process cloud file
def process_cloud_file(url):
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'url': url,
        'include_summary': True
    }
    
    response = requests.post(
        f'{BASE_URL}/files/cloud',
        headers=headers,
        json=data
    )
    return response.json()

# Check health
def check_file_services():
    headers = {'Authorization': f'Bearer {API_KEY}'}
    response = requests.get(
        f'{BASE_URL}/files/health',
        headers=headers
    )
    return response.json()
```

---

### Rate Limiting & Performance

**Performance:**
- Local file uploads: ~500ms - 2s (depending on file size)
- Cloud file processing: ~1s - 3s (includes download time)
- Health checks: <50ms

**Limits:**
- Max file size: 50MB
- Concurrent uploads: Recommended <10 simultaneous
- No explicit rate limiting (use responsibly)

---

### Environment Variables (Optional)

To enable cloud integrations, set these environment variables:

**Google Services:**
```bash
GOOGLE_SERVICE_ACCOUNT_PATH=/path/to/service-account.json
# OR
GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account", ...}'
```

**OneDrive:**
```bash
ONEDRIVE_CLIENT_ID=your-client-id
ONEDRIVE_CLIENT_SECRET=your-client-secret
ONEDRIVE_TENANT_ID=common
```

**Azure Document Intelligence:**
```bash
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-instance.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=your-key
```

---
