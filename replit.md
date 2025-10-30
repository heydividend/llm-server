# Harvey - AI Financial Advisor (Harvey-1o)

## Overview
Harvey is a FastAPI-based intelligent financial assistant providing context-aware responses on dividends, stock prices, tickers, and company insights. Formerly known as AskHeyDividend, Harvey is a professional-grade, AI-powered tool for financial analysis and passive income planning, targeting users interested in dividend investing and market data. The project emphasizes real-time data, personalized recommendations, and a robust, self-healing architecture.

**Current Version:** Harvey-1o

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
- **ML-Powered Predictions:** Integration with HeyDividend's Internal ML API (`INTERNAL_ML_API_KEY`) for advanced dividend analysis with progressive streaming:
  - **Payout Sustainability Ratings:** 0-100 scores with quality and NAV protection metrics
  - **Dividend Growth Forecasts:** Predicted annual growth rates with confidence levels
  - **Cut Risk Analysis:** 12-month dividend cut probability with risk factors
  - **Anomaly Detection:** Identifies unusual payout patterns and payment irregularities
  - **Comprehensive ML Scores:** Overall dividend quality scores with buy/sell recommendations
  - All ML predictions stream progressively for real-time user feedback
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
- **Streaming Responses:** Utilizes server-sent events for real-time progressive interaction (AI chat, SQL results, ML predictions).
- **Web Search Integration:** Fallback mechanism for data not present in the database.
- **File Processing:** Supports uploads for PDFs, images, and spreadsheets.
- **Passive Income Portfolio Builder:** AI-powered tool for personalized dividend portfolio recommendations, including capital needs calculation, diversified portfolio construction, 5-year income projections, and interactive charts. Portfolios can be saved and tracked.
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