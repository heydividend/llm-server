# AskHeyDividend - Financial AI Assistant Backend

## Project Overview
This is a FastAPI backend for AskHeyDividend, an intelligent financial assistant that provides context-aware responses about dividends, stock prices, tickers, and company insights.

## Architecture
- **Backend Framework**: FastAPI (Python 3.11)
- **Database**: Azure SQL Server (with financial data: stocks, dividends, prices)
- **AI Models**: 
  - Primary: OpenAI GPT-4o
  - Optional: Local Llama models via Ollama
- **Web Search**: Enhanced search capabilities for real-time financial data
- **Frontend**: Separate Next.js application (deployed on Azure Static Web Apps)

## Current Setup
- **Environment**: Replit (NixOS)
- **Python Version**: 3.11
- **Port**: 5000 (FastAPI running on uvicorn)
- **Workflow**: "API Server" - uvicorn main:app --host 0.0.0.0 --port 5000 --reload

## Environment Variables
Required secrets (already configured):
- `OPENAI_API_KEY` - OpenAI API key for GPT-4o
- `SQLSERVER_HOST` - Azure SQL Server hostname
- `SQLSERVER_DB` - Database name
- `SQLSERVER_USER` - Database username
- `SQLSERVER_PASSWORD` - Database password

Optional:
- `AZURE_OPENAI` - Set to "true" to use Azure OpenAI instead of OpenAI
- `OLLAMA_BASE` - URL for local Ollama server (default: http://localhost:11434)
- `OLLAMA_MODEL` - Model name for Ollama (default: llama3.1:8b)

## API Endpoints
- `GET /` - Frontend chat interface (testing UI)
- `GET /healthz` - Health check endpoint
- `POST /v1/chat/completions` - Main chat completion endpoint (streaming responses)

## Frontend
A simple, clean chat interface is available at the root URL (`/`) for testing the API. Features:
- Real-time streaming responses
- Example queries for quick testing
- Modern, responsive design
- Located in `static/index.html`

## Key Features
- **Query Classification**: Automatically routes queries to appropriate handlers (SQL, chat, web search, multipart)
- **SQL Generation**: Generates and executes SQL queries against financial database
- **Streaming Responses**: Real-time response streaming via server-sent events
- **Web Search Integration**: Falls back to web search for data not in database
- **File Processing**: Supports uploads for PDFs, images, and spreadsheets

## Database Configuration
The application uses pyodbc to connect to Azure SQL Server. Database views are created automatically on startup:
- `dbo.vTickers` - Ticker/company information
- `dbo.vDividends` - Dividend payment data
- `dbo.vPrices` - Stock price data

**Note**: Database connection requires FreeTDS ODBC driver. Currently configured but may need additional setup for full functionality.

## Recent Changes (Oct 23, 2025)
- Imported from GitHub
- Installed Python 3.11 and core dependencies
- Configured environment variables for database and OpenAI
- Set up FastAPI workflow on port 5000
- Updated database configuration to use FreeTDS driver
- Fixed Azure SQL Server hostname issue (was truncated)
- Successfully connected to Azure SQL Server database
- Created simple frontend testing interface with streaming support
- **Security Fix**: Removed hard-coded Bing API key, moved to environment variables
- **Code Cleanup**: Reduced helper.py from 1,108 to 390 lines (64.8% reduction) by removing duplicate code
- **Performance Optimizations**:
  - Database connection pool increased to 40 max connections (2.5x improvement)
  - Added 60s timeout and 3-retry logic for OpenAI API calls
  - Implemented HTTP connection pooling for web search APIs
  - Created caching infrastructure with 5-minute TTL support
  - All external API calls now have proper timeout and retry mechanisms

## Database Connection

✅ **Successfully connected to Azure SQL Server**
- FreeTDS ODBC driver configured with TDS Version 7.3
- Database views created successfully on startup
- All database operations are functional

**Replit IP**: Run `curl -s https://api.ipify.org` to get the current IP (needed for Azure firewall rules)

## Performance Configuration

The application includes several performance optimizations configurable via environment variables:

**Database:**
- Connection pool: 20 connections, max 40 with overflow
- Auto-recycle: 3600s to prevent stale connections
- Pool timeout: 30s

**OpenAI API:**
- `OPENAI_TIMEOUT` (default: 60) - API request timeout in seconds
- `OPENAI_MAX_RETRIES` (default: 3) - Retry attempts with exponential backoff
- HTTP connection pooling: 20 keepalive, 100 max connections

**Caching:**
- `CACHE_TTL_SECONDS` (default: 300) - Cache time-to-live
- `CACHE_MAX_SIZE` (default: 1000) - Maximum cached entries

**Web Search:**
- Retry strategy: 3 attempts with backoff for rate limits (429) and server errors (500-504)
- Connection pooling: 20 pool connections, 20 max pool size

## Known Issues
- Minor LSP diagnostics present (type checking warnings) that don't affect runtime functionality

## Development Notes
- The app uses contextvars for per-request LLM selection (ChatGPT vs Llama)
- Extensive prompt engineering in settings.py for financial query handling
- Supports both ETF and Stock data with unified views
- Implements smart defaults to prevent data overload (e.g., TOP 1 for latest prices)
