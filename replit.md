# Harvey - AI Financial Advisor

## Overview
Harvey is a FastAPI-based intelligent financial assistant designed for context-aware responses on dividends, stock prices, tickers, and company insights. Its primary purpose is to serve as an AI-powered tool for financial analysis and passive income planning, with a focus on dividend investing and real-time market data. Harvey aims to provide personalized recommendations and a robust, self-healing architecture, catering to US markets by default with options for international data. The project's ambition is to deliver a professional-grade solution for financial analysis, leveraging a unified intelligence system of multiple AI models for superior performance and cost optimization.

### ML Services on Azure VM (20.81.210.213) ✅
**Active ML Schedulers (heydividend-ml-schedulers service):**
- 🤖 **Payout Rating ML** - Daily 1:00 AM - Generates A+/A/B/C dividend safety ratings
- 🤖 **Dividend Calendar ML** - Sunday 2:00 AM - Predicts next dividend payment dates  
- 🤖 **ML Training** - Sunday 3:00 AM - Trains all 5 core ML models

**ML Infrastructure:**
- Training scripts location: `server/ml/training/`
- Service name: `heydividend-ml-schedulers`
- Database: Azure SQL Server with pymssql driver
- Models: Dividend predictions, payout ratings, yield forecasting, growth analysis, cut risk detection

## User Preferences
I prefer iterative development and want to be involved in key decision-making processes. Please ask before making major changes or architectural shifts. I appreciate clear, concise explanations and direct answers, but also value detailed documentation for complex features. Ensure the coding style is clean, maintainable, and follows best practices.

## System Architecture

**UI/UX Decisions:**
A separate Next.js frontend provides a professional, financial-grade chat interface with a dark blue theme, real-time streaming responses, interactive charts, and PDF export functionalities.

**Technical Implementations & Feature Specifications:**
- **Harvey Unified Intelligence System:** Coordinates 5 specialized AI models (GPT-5, Grok-4, DeepSeek-R1, Gemini 2.5 Pro, FinGPT) across Replit and Azure VMs. It features intelligent query routing (8 types), ensemble learning, model audit logging, and continuous dividend-focused learning, achieving significant cost savings.
- **Multi-Model AI Routing:** Automatically selects the optimal AI model based on query type (e.g., Grok-4 for fast queries, DeepSeek-R1 for quantitative analysis, GPT-5 for complex analysis, Gemini for charts, FinGPT for dividend scoring).
- **Harvey Intelligence Engine Integration:** Integrates with Harvey's internal Intelligence Engine, offering 22+ ML endpoints for scoring, predictions, clustering, and advanced insights, automatically enhancing dividend responses.
- **Portfolio & Watchlist Projection Engine:** Custom financial computation engines providing domain-specific dividend analysis, including portfolio projection (income forecasts with CAGR), watchlist projection (optimal allocation for target income), dividend sustainability analysis (payout health, cut risk, A-F grading), and cash flow sensitivity modeling.
- **Conversational Memory:** Manages entire conversation history with token-aware context loading and seamless integration with streaming chat responses.
- **Financial AI Tools:** Includes an Income Ladder Builder for diversified monthly dividend portfolios and a Tax Optimization AI for intelligent tax strategies.
- **Proactive Insights & Alerts:** Generates daily personalized portfolio digests and utilizes natural language AI for proactive market monitoring and alerts.
- **Professional Markdown Formatting:** Ensures clean, business-grade response formatting with standardized tables.
- **4-Tier Dividend Analytics Framework:** Provides descriptive, diagnostic, predictive, and prescriptive analytics, integrating ML predictions and streaming progressively.
- **Enhanced File Processing & Cloud Integrations:** Comprehensive file processing supporting 7 file types (PDF, CSV, XLS, XLSX, JPG, PNG, JPEG) with Azure Document Intelligence OCR. Includes cloud integrations for Google Sheets, Google Drive, and OneDrive, enabling users to analyze portfolios directly from spreadsheets and cloud storage. Features secure file upload validation, automated format detection, and unified API endpoints.
- **Feedback-Driven Learning System:** Collects user feedback for sentiment analysis, response quality tracking, and building training datasets for continuous improvement and fine-tuning.
- **Self-Healing AI:** Implements automatic error detection, web search fallback, HTTP retry logic, and database resilience.

**System Design Choices:**
- **Backend:** FastAPI (Python 3.11)
- **Development Environment:** Replit (NixOS)
- **Production Deployment:** Azure VM (Ubuntu) with Nginx reverse proxy.
- **Architecture:** Microservices-oriented with clear separation between backend and frontend.
- **Security:** API key-based authentication.
- **Resilience:** Extensive retry mechanisms, fallbacks, and error handling.
- **Scalability:** Designed for streaming responses and efficient data retrieval.

## External Dependencies
- **Database:** Azure SQL Server (using pymssql driver - no ODBC required)
- **AI Models:**
    - **Azure OpenAI:** HarveyGPT-5 (GPT-5), Grok-4, DeepSeek-R1.
    - **Google Gemini 2.5 Pro:** For chart analysis, FX trading, and multimodal queries.
    - **FinGPT:** Self-hosted on Azure VM for dividend scoring and financial sentiment.
    - **OpenAI:** GPT-4o (legacy fallback, optional).
    - **Ollama:** For optional local Llama models.
- **Document Processing:** Azure Document Intelligence (primary for PDF/image OCR), openpyxl (Excel XLSX), xlrd (Excel XLS), Google Sheets API, Google Drive API, Microsoft OneDrive API (Graph), PDF.co API (legacy fallback).
- **Charting Library:** Highcharts (client-side JavaScript CDN).
- **Python Libraries:** FastAPI, uvicorn, pyodbc, pandas, requests, sqlalchemy, google-generativeai, azure-ai-documentintelligence.