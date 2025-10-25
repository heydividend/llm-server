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
- `POST /v1/portfolio/save` - Save generated portfolio or watchlist to database

## Frontend
A simple, clean chat interface is available at the root URL (`/`) for testing the API. Features:
- Real-time streaming responses with markdown/HTML rendering
- Example queries for quick testing (including passive income portfolio builder)
- Support for displaying charts and tables
- Modern, responsive design with purple gradient theme
- Located in `static/index.html`

## Key Features
- **Query Classification**: Automatically routes queries to appropriate handlers (SQL, chat, web search, passive income planning, multipart)
- **SQL Generation**: Generates and executes SQL queries against financial database
- **Streaming Responses**: Real-time response streaming via server-sent events
- **Web Search Integration**: Falls back to web search for data not in database
- **File Processing**: Supports uploads for PDFs, images, and spreadsheets
- **Passive Income Portfolio Builder**: AI-powered retirement planning with personalized dividend portfolio recommendations, interactive charts, and portfolio persistence
- **Self-Healing AI**: Automatic error detection, recovery, and alternative solutions (see `SELF_HEALING.md`)

## Database Configuration
The application uses pyodbc to connect to Azure SQL Server. Database views and tables are created automatically on startup:

**Views (Financial Data):**
- `dbo.vTickers` - Ticker/company information (stocks & ETFs)
- `dbo.vDividends` - Dividend payment history
- `dbo.vPrices` - Current stock prices and volume

**Tables (Portfolio Management):**
- `dbo.user_profiles` - User account information
- `dbo.portfolio_groups` - Portfolio/watchlist definitions with metadata
- `dbo.portfolio_positions` - Individual stock positions within portfolios

**Note**: Database connection requires FreeTDS ODBC driver, configured at `/home/runner/.odbcinst.ini`

## Passive Income Portfolio Builder Feature

**NEW**: AI-powered passive income planning tool that generates personalized dividend portfolio strategies.

**How to Use:**
Query the AI with retirement income goals:
- "I want to build a passive income portfolio to replace my $300,000 income in 5 years"
- "Help me create a dividend portfolio for financial independence"
- "Build me a passive income strategy for retirement"

**What It Does:**
1. **Analyzes Requirements**: Parses target income, time horizon, and risk tolerance
2. **Calculates Capital Needs**: Determines required investment based on dividend yields (3.5%-5.5%)
3. **Builds Diversified Portfolio**: Selects 8-12 dividend stocks/ETFs across key sectors:
   - Utilities, Real Estate (REITs), Energy, Consumer Staples
   - Financials, Healthcare, Industrials, Communication Services
4. **Projects Income Growth**: 5-year dividend income projections with 3% annual growth
5. **Generates Visual Charts**:
   - Portfolio allocation pie chart
   - 5-year income projection timeline
   - Sector diversification breakdown
6. **Offers Portfolio Persistence**: Save plans as watchlists or portfolios for tracking

**Technical Implementation:**
- Service Layer: `app/services/passive_income_planner.py` - financial calculations and database queries
- Chart Rendering: Highcharts (client-side JavaScript) - professional financial charts
- Database Schema: `app/config/portfolio_schema.py` - portfolio/watchlist storage
- API Endpoint: `POST /v1/portfolio/save` - persist portfolios with metadata
- Frontend: Enhanced markdown/HTML rendering with Highcharts integration

**Dependencies:**
- `pandas` - Data manipulation for financial calculations
- Highcharts (CDN) - Client-side chart rendering (no server dependencies)

## Recent Changes (Oct 25, 2025)
- **Infrastructure Setup** (Oct 23):
  - Imported from GitHub and installed Python 3.11 + core dependencies
  - Configured environment variables for database and OpenAI
  - Set up FastAPI workflow on port 5000
  - Fixed Azure SQL Server hostname and connected successfully
  - Installed FreeTDS + unixODBC system packages
  - Configured ODBC driver at `/home/runner/.odbcinst.ini`

- **Security & Code Quality** (Oct 23):
  - Removed hard-coded Bing API key, moved to environment variables
  - Reduced helper.py from 1,108 to 390 lines (64.8% reduction)
  - Fixed OpenAI httpx client configuration (removed incompatible retries parameter)

- **Performance Optimizations** (Oct 23):
  - Database connection pool: 2.5x increase (40 max connections)
  - OpenAI API: 60s timeout + 3-retry logic with exponential backoff
  - Web search: HTTP connection pooling + retry strategy
  - Created caching infrastructure (5-min TTL, 1000 entry capacity)

- **Passive Income Portfolio Builder Feature** (Oct 25):
  - Built complete portfolio planning system with AI-powered recommendations
  - Created database schema: user_profiles, portfolio_groups, portfolio_positions tables
  - Implemented PassiveIncomePlanService with financial calculations (capital needs, dividend projections, sector diversification)
  - Switched to Highcharts for professional client-side financial chart rendering
  - Implemented 3 interactive charts: pie (allocation), line (income projection), column (sector breakdown)
  - Updated planner to detect passive income requests and route to dedicated handler
  - Created POST /v1/portfolio/save endpoint for portfolio persistence
  - Enhanced frontend with markdown/HTML rendering, Highcharts integration, image display, and table formatting
  - Added "Build passive income portfolio" example query button
  - Removed Plotly/Kaleido server-side dependencies for improved performance
  - All changes architect-reviewed and approved ✅

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

## Self-Healing Architecture

AskHeyDividend implements comprehensive self-healing mechanisms:

### Automatic Error Recovery
1. **Web Search Fallback**: If SQL fails or returns no data, automatically searches web
2. **HTTP Retry Logic**: 3 retries with exponential backoff for network errors (429, 500-504)
3. **Database Resilience**: Connection pooling, auto-retry, graceful degradation
4. **OpenAI API Resilience**: 60s timeout, 3 retries with backoff
5. **Empty Data Handling**: Explains failures and offers alternative approaches
6. **Chart Rendering Fallback**: Graceful error messages if visualization fails

### Error Detection & Communication
- Detects when database has insufficient data
- Explains WHY errors occurred (not just that they failed)
- Offers 3 alternative solutions for every failure
- Logs all errors for monitoring and analysis

**See `SELF_HEALING.md` for complete architecture documentation**

## Known Issues
- Minor LSP diagnostics present (type checking warnings) that don't affect runtime functionality

## Development Notes
- The app uses contextvars for per-request LLM selection (ChatGPT vs Llama)
- Extensive prompt engineering in settings.py for financial query handling
- Supports both ETF and Stock data with unified views
- Implements smart defaults to prevent data overload (e.g., TOP 1 for latest prices)
