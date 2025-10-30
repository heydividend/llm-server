# AskHeyDividend - Financial AI Assistant Backend

## Overview
AskHeyDividend is a FastAPI-based intelligent financial assistant providing context-aware responses on dividends, stock prices, tickers, and company insights. It aims to offer a professional-grade, AI-powered tool for financial analysis and passive income planning, targeting users interested in dividend investing and market data. The project emphasizes real-time data, personalized recommendations, and a robust, self-healing architecture.

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
- **Streaming Responses:** Utilizes server-sent events for real-time progressive interaction (AI chat, SQL results, ML predictions).
- **Web Search Integration:** Fallback mechanism for data not present in the database.
- **File Processing:** Supports uploads for PDFs, images, and spreadsheets.
- **Passive Income Portfolio Builder:** AI-powered tool for personalized dividend portfolio recommendations, including capital needs calculation, diversified portfolio construction, 5-year income projections, and interactive charts. Portfolios can be saved and tracked.
- **API Authentication:** All protected API endpoints require authentication using a `HARVEY_AI_API_KEY` via a Bearer token in the Authorization header. Public endpoints (`/` and `/healthz`) do not require authentication.
- **Self-Healing AI:** Automatic error detection, web search fallback, HTTP retry logic, database resilience (connection pooling, graceful degradation), OpenAI API resilience, and intelligent handling of empty data.
- **Database Views:** Utilizes a robust system of SQL views (`vSecurities`, `vDividendsEnhanced`, `vDividendSchedules`, `vDividendSignals`, `vQuotesEnhanced`, `vDividendPredictions`) for enhanced financial data, with a graceful degradation mechanism to legacy views and mock data if production tables are unavailable.
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