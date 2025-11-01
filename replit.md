# Harvey - AI Financial Advisor (Harvey-1o)

## Overview
Harvey is a FastAPI-based intelligent financial assistant providing context-aware responses on dividends, stock prices, tickers, and company insights. It is an AI-powered tool for financial analysis and passive income planning, focusing on dividend investing and market data with an emphasis on real-time data, personalized recommendations, and a robust, self-healing architecture. The default market focus is US markets, with an option for users to request international data. Harvey aims to be a professional-grade solution for financial analysis.

## User Preferences
I prefer iterative development and want to be involved in key decision-making processes. Please ask before making major changes or architectural shifts. I appreciate clear, concise explanations and direct answers, but also value detailed documentation for complex features. Ensure the coding style is clean, maintainable, and follows best practices.

## System Architecture
The backend is built with FastAPI (Python 3.11) and connects to an Azure SQL Server database. It leverages OpenAI GPT-4o for primary AI capabilities, with optional integration for local Ollama models. Web search is used for real-time data acquisition.

**UI/UX Decisions:**
A separate Next.js frontend provides a professional, financial-grade chat interface with a dark blue theme, real-time streaming responses, interactive charts, and PDF export functionalities.

**Technical Implementations & Feature Specifications:**
- **Query Classification:** Routes queries to appropriate handlers (SQL, chat, web search, passive income planning, ML predictions, multipart).
- **SQL Generation:** Generates and executes SQL queries against the financial database.
- **Comprehensive ML API Integration:** Full integration with HeyDividend's Internal ML API offering 22+ endpoints for scoring, predictions, clustering, optimization, and advanced insights. ML intelligence is automatically added to dividend responses, and the system is designed for graceful degradation.
- **Conversational Memory:** Stores entire conversation history with automatic session and thread management, token-aware context loading, and integrates seamlessly with streaming chat responses.
- **Income Ladder Builder:** AI-powered algorithm to select diversified monthly dividend payers, calculate capital needs, and manage risk-adjusted portfolios.
- **Tax Optimization AI:** Provides intelligent tax strategies such as qualified vs. ordinary dividend analysis, tax-loss harvesting, and replacement ticker suggestions.
- **Natural Language Alerts:** Proactive market monitoring using GPT-4o for parsing natural language alerts, checking conditions with live market data, and scheduling background checks.
- **Proactive Insights:** Generates daily personalized portfolio digests with analysis of price changes, dividend news, and upcoming ex-dates.
- **Professional Markdown Formatting:** Ensures clean, business-grade response formatting with standardized tables and action prompts, compatible with streaming responses.
- **Conversational AI Training:** Enhances user interaction with proactive follow-up questions, share ownership detection, and personalized income messages to guide users toward valuable features.
- **4-Tier Dividend Analytics Framework:** Provides comprehensive descriptive, diagnostic, predictive, and prescriptive analytics, integrating ML predictions and streaming progressively during responses.
- **Streaming Responses:** Utilizes server-sent events for real-time progressive interaction.
- **Web Search Integration:** Fallback mechanism for data not present in the database.
- **File Processing:** Advanced document processing with triple extraction engines (PDF.co for complex PDFs, Node service for images/Office docs, Portfolio Parser for intelligent multi-format parsing). Supports CSV, Excel, PDF, images with flexible column recognition. Extracts portfolio holdings (ticker, shares, prices, dividends) from ANY format including Schwab/Robinhood/Fidelity statements, CSV exports, Excel trackers, and screenshots.
- **Passive Income Portfolio Builder:** AI-powered tool for personalized dividend portfolio recommendations, including capital needs calculation and income projections.
- **Azure VM Training Job Management:** Simple SSH client for managing ML training jobs on Azure VM, including status checks, starting jobs, log tailing, and file transfer.
- **Feedback-Driven Learning System:** Comprehensive user feedback collection with ratings, sentiment analysis, and comments. Tracks response quality, builds training datasets for GPT-4o fine-tuning, and provides analytics dashboard for continuous improvement. Includes pattern analysis, improvement suggestions, and automated training data export for OpenAI fine-tuning.
- **API Authentication:** All protected API endpoints require `HARVEY_AI_API_KEY` via Bearer token.
- **Self-Healing AI:** Automatic error detection, web search fallback, HTTP retry logic, database resilience, and intelligent handling of empty data.
- **Database Views:** Utilizes SQL views for enhanced financial data, with graceful degradation to legacy views and mock data.
- **Background Job Scheduler:** Thread-based scheduler for automated tasks like alert monitoring and daily portfolio digest generation.
- **Performance:** Configurable connection pooling, retry logic, and caching infrastructure.

**System Design Choices:**
- **Development Environment:** Replit (NixOS) for development with Python 3.11
- **Production Deployment:** Azure VM (Ubuntu) with Nginx reverse proxy
- **Microservices-oriented:** Clear separation between backend (FastAPI) and frontend (Next.js)
- **Security:** API key-based authentication
- **Resilience:** Extensive retry mechanisms, fallbacks, and error handling
- **Scalability:** Designed for streaming responses and efficient data retrieval

**Deployment Model:**
- **Development:** Replit environment for rapid iteration
- **Production:** Azure VM running Harvey backend + ML API behind Nginx
- **Deployment Method:** Azure Run Command (no SSH required) via `deploy/AZURE_RUN_COMMAND_DEPLOY.sh`
- **Infrastructure:** Single Azure VM hosts both Harvey backend (port 8000) and ML API (port 9000), fronted by Nginx on port 80/443

## External Dependencies
- **Database:** Azure SQL Server (all schemas are SQL Server-specific using DATEADD, BIT, DATETIME, GO batches)
- **AI Models:**
    - OpenAI (GPT-4o) - primary model, with fine-tuning support via feedback system
    - Ollama (for local Llama models, optional)
- **Document Processing:**
    - PDF.co API
    - Node.js text extraction service
- **Charting Library:** Highcharts (client-side JavaScript CDN)
- **Python Libraries:** `FastAPI`, `uvicorn`, `pyodbc`, `pandas`, `requests`, `sqlalchemy`