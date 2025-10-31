# Harvey - AI Financial Advisor (Harvey-1o)

## Overview
Harvey is a FastAPI-based intelligent financial assistant providing context-aware responses on dividends, stock prices, tickers, and company insights. Formerly known as AskHeyDividend, Harvey is a professional-grade, AI-powered tool for financial analysis and passive income planning, targeting users interested in dividend investing and market data. The project emphasizes real-time data, personalized recommendations, and a robust, self-healing architecture.

**Current Version:** Harvey-1o

**Default Market Focus:** US Markets Only
- All queries default to US markets (NYSE, NASDAQ, AMEX, ARCA, BATS, OTC)
- Excludes international tickers with foreign suffixes (.JK, .KS, .L, .T, .TO, .AX, .HK, .SA, etc.)
- After each response, Harvey asks: "📍 *Showing US markets only. Would you like to see international markets as well?*"
- Users can request international/global data by saying "global", "international", "worldwide", or mentioning specific foreign tickers

## User Preferences
I prefer iterative development and want to be involved in key decision-making processes. Please ask before making major changes or architectural shifts. I appreciate clear, concise explanations and direct answers, but also value detailed documentation for complex features. Ensure the coding style is clean, maintainable, and follows best practices.

## System Architecture
The backend is built with FastAPI (Python 3.11) and connects to an Azure SQL Server database containing comprehensive financial data. It leverages OpenAI GPT-4o for primary AI capabilities, with optional integration for local Ollama models. Web search enhances real-time data acquisition.

**UI/UX Decisions:**
A separate Next.js frontend (not part of this backend repository but referenced) offers a professional, financial-grade chat interface with a dark blue (#1a1d29) theme. Key UI/UX features include:
- Real-time streaming responses with markdown/HTML rendering.
- Interactive charts (Highcharts) for portfolio visualization.
- "New Chat," "Global Print to PDF," and "Per-message Save as PDF" functionalities with professional branding.

**Technical Implementations & Feature Specifications:**
- **Query Classification:** Routes queries to appropriate handlers (SQL, chat, web search, passive income planning, ML predictions, multipart).
- **SQL Generation:** Generates and executes SQL queries against the financial database.
- **Comprehensive ML API Integration (EXPANDED):** Full integration with HeyDividend's Internal ML API (`INTERNAL_ML_API_KEY`) providing 22+ ML endpoints across scoring, predictions, clustering, and optimization:
  
  **ML Scoring & Quality Assessment:**
  - **Single Stock Scoring:** Real-time dividend quality scores (0-100) with letter grades (A+ to F)
  - **Portfolio Scoring:** Aggregated ML metrics with risk assessment and diversification scores
  - **Watchlist Scoring:** Batch scoring for multiple symbols with comparative analysis
  - **Batch Processing:** Efficiently score up to 100 symbols in a single request
  
  **ML Predictions & Forecasting:**
  - **Yield Forecasting:** ML-powered yield predictions with 3/6/12/24-month horizons
  - **Growth Rate Predictions:** Dividend growth rate forecasts with confidence levels
  - **Payout Ratio Forecasting:** Future payout sustainability with risk levels (EXCELLENT/GOOD/MODERATE/POOR)
  - **Batch Predictions:** Batch yield and payout forecasts for portfolio-wide analysis
  
  **ML Clustering & Similarity Analysis:**
  - **Stock Clustering:** K-means clustering identifies dividend stock categories (Dividend Aristocrats, High Yield Growth, etc.)
  - **Similar Stock Discovery:** Find stocks similar to any ticker using ML clustering (similarity scores 0-1)
  - **Cluster Dashboard:** Overview of all ML clusters with characteristics and member counts
  - **Portfolio Cluster Analysis:** Detailed cluster breakdown for diversification insights
  
  **ML-Powered Portfolio Optimization:**
  - **Portfolio Optimization:** ML-driven buy/sell/reduce suggestions with optimization goals (maximize_yield, minimize_risk)
  - **Diversification Analysis:** ML-assessed diversification scores across clusters
  - **Portfolio Health Metrics:** Comprehensive ML health checks combining scoring, diversification, and cluster analysis
  
  **Advanced ML Insights:**
  - **Symbol Insights:** Deep ML-powered insights combining all ML models for comprehensive analysis
  - **Prediction History:** Historical prediction tracking with accuracy metrics
  - **Model Performance:** Access to ML model performance metrics (MAE, RMSE, R² scores)
  - **Usage Statistics:** ML API usage tracking with tier-based limits
  
  **Integration Architecture:**
  - **MLAPIClient:** 22 endpoints for scoring, predictions, clustering, optimization, monitoring
  - **MLIntegration Service:** High-level wrapper providing conversation-friendly ML features
  - **Automatic Enrichment:** ML intelligence automatically added to dividend responses
  - **Graceful Degradation:** All ML calls non-blocking; continues with standard analytics if ML unavailable
  - **Progressive Streaming:** ML predictions stream progressively for real-time user feedback
  - **Conversational AI Integration:** ML insights seamlessly woven into Harvey's responses
- **Conversational Memory (NEW):** Makes Harvey feel like a real financial advisor through intelligent context retention:
  - Stores entire conversation history with automatic session and thread management
  - Token-aware context loading (4000 token budget) for continuous conversations
  - Uses tiktoken for accurate GPT-4o token counting
  - Seamlessly integrates with streaming chat responses
  - Returns session_id and conversation_id for frontend state management
- **Income Ladder Builder (NEW):** Solves the #1 dividend investor problem - monthly income from quarterly payers:
  - AI-powered algorithm selects diversified monthly dividend payers
  - Calculates exact shares needed and total capital required
  - Risk-adjusted portfolios (conservative, moderate, aggressive)
  - Sector diversification with visual breakdowns
  - Stores and tracks multiple ladder plans per user
  - RESTful API endpoints for ladder creation and retrieval
- **Tax Optimization AI (NEW):** Saves users real money through intelligent tax strategies:
  - Qualified vs ordinary dividend analysis with tax savings estimates
  - Tax-loss harvesting opportunity detection
  - Replacement ticker suggestions (wash sale avoidance)
  - Multi-scenario tax modeling (current, optimized, harvest)
  - AI-powered recommendations using GPT-4o
  - Holding period tracking for qualified dividend status
- **Natural Language Alerts (NEW):** "Tell me when X happens" - proactive market monitoring:
  - Natural language parsing using GPT-4o function calling
  - Multiple alert types: price targets, dividend cuts, yield changes
  - Background scheduler checks alerts every 5 minutes
  - Alert event tracking with read/unread status
  - Real-time condition evaluation using live market data
- **Proactive Insights (NEW):** Daily portfolio digests delivered automatically:
  - Background generation at 8 AM daily for active users
  - Portfolio analysis: price changes, dividend news, upcoming ex-dates
  - AI-generated personalized summaries using GPT-4o
  - Priority-based insight delivery
  - Manual digest generation on-demand
- **Professional Markdown Formatting (NEW):** Clean, business-grade response formatting:
  - Uses mdformat and py-markdown-table for consistent professional styling
  - Standardized 8-column dividend tables (Ticker, Price, Distribution Amount, Yield, Payout Ratio, Declaration Date, Ex-Date, Pay Date)
  - Automatic removal of emojis and icons for business-appropriate output
  - Action prompts for watchlist, portfolio tracking, alerts, and income ladder features
  - Formatted tables work seamlessly with streaming responses
- **Conversational AI Training (NEW):** Makes Harvey feel like a real financial advisor:
  - Proactive follow-up questions suggesting relevant next steps (forecasting, watchlist, portfolio tracking, alerts, income ladder, tax optimization)
  - Share ownership detection using natural language patterns ("I own 200 shares of YMAX", "my 100 TSLY shares")
  - Automatic TTM (trailing twelve months) income calculator
  - Personalized income messages with historical distribution data
  - Intelligent conversation flow that guides users toward valuable features
- **4-Tier Dividend Analytics Framework (NEW):** Comprehensive analytics across all dimensions:
  - **Descriptive Analytics:** Historical payment patterns, consistency scores, yield trends, distribution frequency
  - **Diagnostic Analytics:** Dividend cut analysis, yield change diagnosis, payment irregularity detection, variance explanations
  - **Predictive Analytics:** Next distribution forecasts, annual income projections, ML API integration, yield trajectory modeling
  - **Prescriptive Analytics:** Buy/Hold/Sell/Trim recommendations, portfolio optimization suggestions, tax strategies, risk mitigation actions
  - All analytics stream progressively during dividend responses
  - 17 specialized analytics functions covering every aspect of dividend analysis
  - Integration with existing ML predictions API for comprehensive forecasting
- **Streaming Responses:** Utilizes server-sent events for real-time progressive interaction (AI chat, SQL results, ML predictions, analytics).
- **Web Search Integration:** Fallback mechanism for data not present in the database.
- **File Processing:** Supports uploads for PDFs, images, and spreadsheets.
- **Passive Income Portfolio Builder:** AI-powered tool for personalized dividend portfolio recommendations, including capital needs calculation, diversified portfolio construction, 5-year income projections, and interactive charts. Portfolios can be saved and tracked.
- **Azure VM Training Job Management (NEW):** Simple SSH client for managing ML training jobs on Azure VM:
  - Execute arbitrary shell commands remotely via API
  - Check GPU status (nvidia-smi) and system resources (CPU, memory, disk)
  - List running training jobs (Python processes)
  - Start training jobs in background with nohup
  - Tail training logs remotely
  - File upload/download capabilities (SFTP)
  - All operations secured with API key authentication
  - Environment-based configuration (AZURE_VM_IP, AZURE_VM_USER, AZURE_VM_PASSWORD)
- **API Authentication:** All protected API endpoints require authentication using a `HARVEY_AI_API_KEY` via a Bearer token in the Authorization header. Public endpoints (`/` and `/healthz`) do not require authentication.
- **Self-Healing AI:** Automatic error detection, web search fallback, HTTP retry logic, database resilience (connection pooling, graceful degradation), OpenAI API resilience, and intelligent handling of empty data.
- **Database Views:** Utilizes a robust system of SQL views (`vSecurities`, `vDividendsEnhanced`, `vDividendSchedules`, `vDividendSignals`, `vQuotesEnhanced`, `vDividendPredictions`) for enhanced financial data, with a graceful degradation mechanism to legacy views and mock data if production tables are unavailable.
- **Background Job Scheduler:** Thread-based scheduler for automated tasks:
  - Alert condition monitoring (every 5 minutes)
  - Daily portfolio digest generation (8 AM daily)
  - Graceful startup/shutdown with application lifecycle
  - Comprehensive error handling and logging
- **Performance:** Configurable connection pooling for database and HTTP requests, retry logic for OpenAI and web search APIs, and a caching infrastructure.

**System Design Choices:**
- **Containerized Development:** Replit (NixOS) environment with Python 3.11.
- **Microservices-oriented:** Clear separation between backend (FastAPI) and frontend (Next.js).
- **Security:** API key-based authentication for critical endpoints.
- **Resilience:** Extensive retry mechanisms, fallbacks, and error handling.
- **Scalability:** Designed for streaming responses and efficient data retrieval.

## External Dependencies
- **Database:** Azure SQL Server
- **AI Models:**
    - OpenAI (GPT-4o)
    - Ollama (for local Llama models, optional)
- **Charting Library:** Highcharts (client-side JavaScript CDN)
- **Python Libraries:** `FastAPI`, `uvicorn`, `pyodbc`, `pandas`

## API Documentation
Comprehensive API reference for all Harvey endpoints is available in **`API_DOCUMENTATION.md`**. This single source of truth covers:
- Core Chat API with JSON and multipart/form-data support (file uploads)
- All 5 Harvey-1o features: Conversational Memory, Income Ladder Builder, Tax Optimization AI, Natural Language Alerts, Proactive Insights
- **Comprehensive ML API Integration:** All 22+ ML endpoints automatically integrated into dividend responses:
  - ML Scoring (single stock, portfolio, watchlist, batch)
  - ML Predictions (yield forecasts, growth rates, payout sustainability)
  - ML Clustering (stock similarity, cluster analysis, portfolio diversification)
  - ML Portfolio Optimization (buy/sell suggestions, health metrics)
  - ML Monitoring (model performance, usage stats, prediction history)
- Complete request/response schemas with code examples in JavaScript/TypeScript and Python
- Authentication, error handling, and streaming response patterns

Frontend teams should refer to `API_DOCUMENTATION.md` for integration guidance.