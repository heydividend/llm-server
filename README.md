# AskHeyDividend — Intelligent Financial Assistant

## Overview
**AskHeyDividend** is a FinTech-focused conversational AI platform that delivers intelligent, dynamic, and context-aware responses about finance — including dividends, prices, tickers, and company insights.  

The system combines a fine-tuned **LLaMA model**, real-time SQL data access, and an intelligent **fallback model** to ensure accuracy and reliability. It integrates with multiple Azure services and external APIs, giving users a seamless experience for both text and file-based queries.

---

## System Architecture
AskHeyDividend follows a **modular and scalable architecture** where each layer has a well-defined role.

### Core Flow
1. User sends a query via the frontend.
2. Query reaches the FastAPI server through **Azure Front Door**.
3. Server classifies and routes the query:
   - **Simple/general queries:** handled directly by the model.
   - **Financial/data queries:** generate and execute SQL against the database.
   - **Out-of-domain or explicit `WEB:` queries:** trigger a web search.
   - **File/image uploads:** sent to a Node.js module for parsing.
4. Summarized response is generated and streamed back to the frontend in real time.

---

### Frontend
- Built with **Next.js** and deployed on **Azure Static Web Apps**.
- Provides a conversational interface supporting text queries and file uploads.
- Uses **Hero Charts** for visualizations (dividend histories, stock trends, performance charts).
- Responses are streamed using **server-sent events** or **WebSockets** for smooth UX.

### Backend (FastAPI Orchestrator)
- Central orchestrator managing:
  - Query logic
  - Model communication
  - SQL generation
  - File handling
- Fully asynchronous and supports streaming responses.

#### Query Classification Layer
- Classifies queries into:
  - Conversational
  - General knowledge
  - Data-driven
  - Web search
- Includes **ticker extraction module** using regex and name mapping to link queries to specific stock symbols.

---

### AI Model Flow
- **Fine-tuned LLaMA model** optimized for financial and market language.
- For live financial data:
  - Generates SQL queries
  - Retrieves data from Azure SQL Database
  - Summarizes results into human-friendly responses
- **Fallback Model:** GPT-4o ensures consistent responses if LLaMA fails.

### Dynamic Data Handling
- Connects to **Azure SQL Database** with live and historical financial data.
- Secure execution of SQL statements for dividends, prices, tickers, and portfolio data.
- Results are summarized or forwarded to frontend for visualization.

### Web Search Integration
- Automatically triggers web search if model/data cannot answer a query.
- Uses **Google or Bing APIs** to retrieve up-to-date information.
- Users can explicitly request a search with the prefix `WEB:`.

### File and Image Processing
- Processes uploaded PDFs, reports, images, and spreadsheets.
- FastAPI forwards uploads to a **Node.js module** using:
  - Azure AI Document Intelligence
  - Azure AI Vision
  - Custom CSV parser
- Extracted structured data returned as JSON for context-aware responses.

---

### Structured Logging and Analytics
- Logs every query, model response, and data transaction in **JSON format**.
- Includes timestamps, user context, request/response details, and error traces.
- Compatible with visualization and monitoring tools like **Grafana Loki** or **ELK Stack**.
- Ensures full traceability, auditability, and easy debugging.

---

## Infrastructure and Deployment
- **Frontend:** Azure Static Web App for global delivery.
- **Backend & Node.js Module:** Single **Azure VM** hosting FastAPI and Node.js services.
- **Database:** Azure SQL Database for secure, high-performance financial data access.
- **Routing:** Azure Front Door for secure endpoints and load balancing.

---

## Key Strengths
- **FinTech-specific model:** fine-tuned for precision and context awareness.
- **Asynchronous architecture:** real-time streaming.
- **Intelligent query classification:** including ticker extraction.
- **Reliable fallback system:** ensures fault tolerance.
- **Modular and scalable design:** supports future growth.
- **Transparent web search & file handling.**
- **Unified deployment & monitoring:** through Azure services.

---

## License
[MIT](LICENSE)  
