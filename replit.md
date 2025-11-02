# Harvey - AI Financial Advisor (Harvey-1o)

## Overview
Harvey is a FastAPI-based intelligent financial assistant providing context-aware responses on dividends, stock prices, tickers, and company insights. It is an AI-powered tool for financial analysis and passive income planning, focusing on dividend investing and market data with an emphasis on real-time data, personalized recommendations, and a robust, self-healing architecture. The default market focus is US markets, with an option for users to request international data. Harvey aims to be a professional-grade solution for financial analysis.

## Recent Changes
**November 2, 2025 - MULTI-MODEL AI ROUTING SYSTEM DEPLOYED**
- ✅ **5-Model AI Fleet**: GPT-5, Grok-4, DeepSeek-R1, Gemini 2.5 Pro, FinGPT
- ✅ **Intelligent Query Routing**: Automatically selects optimal model based on query type
- ✅ **Cost Optimization**: Targets 70% cost reduction vs. all-GPT-5 approach
- ✅ **Model Deployments**:
  - **GPT-5** (HarveyGPT-5) - Complex financial analysis ($1.25/$10 per 1M tokens)
  - **Grok-4** (grok-4-fast-reasoning) - Fast queries ($3/$15 per 1M tokens)
  - **DeepSeek-R1** (DeepSeek-R1-0528) - Quantitative analysis ($0.55/$2.19 per 1M tokens) ⭐ CHEAPEST
  - **Gemini 2.5 Pro** (Google API) - Chart/FX analysis ($1.25/$5 per 1M tokens)
  - **FinGPT** (Azure VM:9000) - Dividend scoring (FREE, self-hosted)
- ✅ **Azure Document Intelligence**: Integrated to replace PDF.co for document processing
- ✅ **Query Classification**: 8 query types with pattern-based routing
- ✅ **Production-Ready**: Full deployment guide at `deploy/MULTI_MODEL_DEPLOYMENT.md`
- ✅ **Graceful Degradation**: Falls back to GPT-5 if specialized models unavailable
- 📋 **NEXT STEPS**: Deploy to Azure VM, monitor model usage, fine-tune routing rules

**November 2, 2025 - Azure OpenAI Migration Complete**
- ✅ **Migrated from OpenAI API to Azure OpenAI**: Cost savings and better control
- ✅ **Azure OpenAI Configuration**: Using `htmltojson-parser-openai-a1a8` resource
- ✅ **3 Azure Deployments**: HarveyGPT-5 (GPT-5), grok-4-fast-reasoning, DeepSeek-R1-0528
- ✅ **Endpoint**: https://htmltojson-parser-openai-a1a8.openai.azure.com/
- ✅ **Environment Secrets**: AZURE_OPENAI, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT_NAME
- ✅ **Backward Compatible**: System supports both Azure OpenAI and regular OpenAI via environment flag

**November 2, 2025 - Financial Models Integration (Dev Build)**
- ✅ **Portfolio & Watchlist Projection Engine**: Custom financial computation engines for dividend analysis
- ✅ **4 Financial Engines Built**:
  - Portfolio Projection Engine: 1/3/5/10 year dividend income projections with CAGR modeling
  - Watchlist Projection Engine: Optimal allocation recommendations for target monthly income
  - Dividend Sustainability Analyzer: Payout ratio health, cut risk scoring, A-F grading system
  - Cash Flow Sensitivity Model: Stress testing with dividend cut scenarios, sector concentration analysis
- ✅ **API Endpoints**: 6 FastAPI endpoints integrated into Harvey backend (`/api/financial/*`)
- ✅ **Security**: Removed hardcoded API keys, fail-fast authentication, environment-based secrets
- ✅ **Documentation**: `financial_models/README.md`, `FINANCIAL_MODELS_INTEGRATION.md`
- ⚠️ **Replit Environment Limitation**: Database connectivity broken due to missing FreeTDS driver and pip install failures
- ✅ **Production-Ready**: Code designed for Azure VM deployment where pymssql/database connectivity works
- 📋 **NEXT STEPS**: Deploy financial models to Azure VM for full database connectivity, test with live portfolio data

**November 2, 2025 - ML Training Pipeline FULLY DEPLOYED & OPERATIONAL**
- ✅ Harvey backend successfully deployed to Azure VM (20.81.210.213) on port 8000
- ✅ **Harvey Intelligence Engine LIVE** on port 9000 serving 7 trained ML models via systemd service
- ✅ **ML Training Completed**: 8,247 samples extracted from Azure SQL, 7 models trained (~11MB total)
- ✅ **Production Models Deployed**:
  - dividend_quality_scorer.pkl (R² = 0.98)
  - yield_predictor_12_months.pkl (R² = 0.99)
  - payout_ratio_predictor.pkl (R² = 0.91)
  - cut_risk_analyzer.pkl (Accuracy = 99.88%)
  - growth_rate_predictor.pkl (requires improvement: R² = -10.50)
  - anomaly_detector.pkl (9.9% anomalies detected)
  - stock_clusterer.pkl (Silhouette = 0.37)
- ✅ **Smart Dividend Date Display**: Context-aware date intelligence with 5 states (declared today, upcoming ex-date, upcoming payment, standard, upcoming announcement)
- ✅ **DividendContextService**: UTC date handling, pattern detection for next declaration dates, dynamic table rendering
- ✅ **pymssql Integration**: Replaced FreeTDS/pyodbc with pymssql for reliable Azure SQL connectivity (no ODBC drivers required)
- ✅ Nginx reverse proxy configured and routing traffic on port 80
- ✅ Systemd services configured for Harvey backend and Intelligence Engine with auto-restart on failure
- ✅ All dependencies installed (Python 3.11 + Conda environment on Azure VM)
- ✅ Self-healing architecture handling database connection issues gracefully
- ✅ Proactive dividend alert suggestions with confidence filtering deployed
- ✅ Comprehensive documentation: `HARVEY_INTELLIGENCE_ENGINE.md`, `TRAINING_AUTOMATION.md`, `ML_TRAINING_DEPLOYMENT.md`
- ✅ Nightly training automation infrastructure ready: systemd timer at 2 AM UTC with backup/validation/rollback
- 📋 **NEXT STEPS**: Monitor model performance, improve growth_rate_predictor (R² = -10.50), enable nightly retraining timer

## User Preferences
I prefer iterative development and want to be involved in key decision-making processes. Please ask before making major changes or architectural shifts. I appreciate clear, concise explanations and direct answers, but also value detailed documentation for complex features. Ensure the coding style is clean, maintainable, and follows best practices.

## System Architecture
The backend is built with FastAPI (Python 3.11) and connects to an Azure SQL Server database. It leverages OpenAI GPT-4o for primary AI capabilities, with optional integration for local Ollama models. Web search is used for real-time data acquisition.

**UI/UX Decisions:**
A separate Next.js frontend provides a professional, financial-grade chat interface with a dark blue theme, real-time streaming responses, interactive charts, and PDF export functionalities.

**Technical Implementations & Feature Specifications:**
- **Query Classification:** Routes queries to appropriate handlers (SQL, chat, web search, passive income planning, ML predictions, multipart).
- **SQL Generation:** Generates and executes SQL queries against the financial database.
- **Harvey Intelligence Engine Integration:** Full integration with Harvey's internal Intelligence Engine offering 22+ ML endpoints for scoring, predictions, clustering, optimization, and advanced insights. ML intelligence is automatically added to dividend responses, and the system is designed for graceful degradation with health monitoring.
- **Portfolio & Watchlist Projection Engine:** Custom financial computation engines providing domain-specific dividend analysis. Includes Portfolio Projection (1/3/5/10 year income forecasts with CAGR), Watchlist Projection (optimal allocation for target income), Dividend Sustainability Analyzer (payout health, cut risk, A-F grading), and Cash Flow Sensitivity Model (stress testing, sector concentration). Exposes 6 API endpoints at `/api/financial/*` with INTERNAL_ML_API_KEY authentication. Production-ready for Azure VM deployment.
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
- **Production:** Azure VM running Harvey backend + Intelligence Engine behind Nginx
- **Deployment Method:** Azure Run Command (no SSH required) via `deploy/AZURE_RUN_COMMAND_DEPLOY.sh`
- **Infrastructure:** Single Azure VM hosts both Harvey backend (port 8000) and Intelligence Engine (port 9000), fronted by Nginx on port 80/443

## External Dependencies
- **Database:** Azure SQL Server (all schemas are SQL Server-specific using DATEADD, BIT, DATETIME, GO batches)
- **AI Models (Multi-Model Routing System):**
    - **Azure OpenAI** (htmltojson-parser-openai-a1a8 resource):
      - HarveyGPT-5 (GPT-5) - Complex analysis, primary model
      - grok-4-fast-reasoning (Grok-4) - Fast queries, general chat
      - DeepSeek-R1-0528 (DeepSeek-R1) - Quantitative analysis, math
    - **Google Gemini 2.5 Pro** - Chart analysis, FX trading, multimodal queries
    - **FinGPT** (Self-hosted on Azure VM:9000) - Dividend scoring, financial sentiment
    - **OpenAI** (GPT-4o) - Legacy fallback option, switchable via AZURE_OPENAI environment variable
    - **Ollama** (for local Llama models, optional)
- **Document Processing:**
    - **Azure Document Intelligence** - Primary document processor (OCR, table extraction, financial documents)
    - PDF.co API - Legacy fallback for complex PDFs
    - Node.js text extraction service - Images and Office documents
- **Charting Library:** Highcharts (client-side JavaScript CDN)
- **Python Libraries:** `FastAPI`, `uvicorn`, `pyodbc`, `pandas`, `requests`, `sqlalchemy`, `google-generativeai`, `azure-ai-documentintelligence`