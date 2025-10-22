AskHeyDividend — Intelligent Financial Assistant
Overview
AskHeyDividend is a FinTech-focused conversational AI platform that provides intelligent, dynamic, and context-aware responses about finance — including dividends, prices, tickers, and company insights.
The system combines a fine-tuned LLaMA model, real-time SQL data access, and an intelligent fallback model to ensure accuracy and reliability. It integrates with multiple Azure services and external APIs, giving users a seamless experience for both text and file-based queries.

System Architecture
AskHeyDividend follows a modular and scalable architecture where each layer has a well-defined role.
Core Flow
The user sends a query through the frontend.


The query reaches the FastAPI server via Azure Front Door.


The server classifies the query and routes it based on intent:


Simple or general queries are handled directly by the model.


Financial or data-related queries generate and execute SQL against the database.


Out-of-domain questions or explicit WEB: queries trigger a web search.


File or image uploads are sent to a Node.js module for parsing.


The system then generates a summarized response and streams it back to the user interface in real time.



Frontend
The frontend is built with Next.js and deployed on Azure Static Web Apps. It provides a conversational interface that supports both text queries and file uploads.
Hero Charts are used for dynamic visualizations such as dividend histories, stock trends, or performance charts. Responses are streamed to users using server-sent events or WebSockets for a smooth and responsive experience.

Backend (FastAPI Orchestrator)
The FastAPI backend acts as the central orchestrator. It manages all query logic, model communication, SQL generation, and file-handling coordination.
It is fully asynchronous and supports streaming responses, ensuring that users see results progressively as they are generated.
Query Classification Layer
A lightweight Python layer classifies every incoming query into one of several categories: conversational, general knowledge, data-driven, or web search.
It also includes a ticker extraction module that identifies company names and stock symbols using regular expressions and name mapping. This helps the model accurately link user queries to specific tickers when generating SQL.

AI Model Flow
At the core of AskHeyDividend is a fine-tuned LLaMA model, optimized for financial and market-related language.
When a query is received, the model determines the context and intent. If the request involves live financial data, the model generates a SQL query that retrieves the necessary information from the database. The results are then summarized into a human-friendly response.
If the primary model encounters an issue or produces invalid output, the system automatically switches to a fallback model (GPT-4o) to ensure a consistent and reliable response.

Dynamic Data Handling
The system connects to an Azure SQL Database that holds live and historical financial data.
Model-generated SQL statements are executed securely and efficiently to retrieve dividends, prices, tickers, or portfolio data. The results are passed back to the model, which summarizes them for the user in natural language or forwards them to the frontend for visualization.
This architecture allows the system to blend structured data retrieval with intelligent language understanding.

Web Search Integration
When a query cannot be answered using model knowledge or database data, AskHeyDividend triggers a web search automatically.
It uses Google or Bing APIs to collect relevant and up-to-date information from the internet. The model then summarizes the results and presents them to the user.
Users can also request a web search explicitly by prefixing their query with WEB:.

File and Image Processing
AskHeyDividend can process uploaded files and images to extract financial information.
The FastAPI server forwards uploads to a Node.js module that runs on the same Azure VM. This module uses Azure AI Document Intelligence, Azure AI Vision, and a custom CSV parser to extract structured data from PDFs, reports, images, and spreadsheets.
The processed data is returned as JSON to the FastAPI server, which integrates it into the model’s context for generating responses based on the extracted content.

 Structured Logging and Analytics
Every user query, model response, and data transaction is logged for debugging and analysis.
 Logs are stored in local files using a structured JSON format, ensuring each event includes timestamps, user context, request/response details, and error traces.
 These logs can be easily parsed or visualized using tools like Grafana Loki, ELK Stack (Elasticsearch, Logstash, Kibana), or simple file-based analysis scripts.
 This structured local logging setup ensures the system remains traceable, auditable, and easy to debug during operation or troubleshooting.


Infrastructure and Deployment
AskHeyDividend runs entirely on Azure, combining flexibility, reliability, and scalability.
Frontend: Deployed as an Azure Static Web App for fast, global delivery.


Backend and Node.js Module: Hosted together on a single Azure Virtual Machine, running both the FastAPI orchestrator and Node.js file parsing service.


Database: Managed through Azure SQL Database for secure and high-performance access to financial data.


Routing: Managed by Azure Front Door, which exposes the AI model endpoints securely and provides load balancing.



Key Strengths
AskHeyDividend stands out for its strong integration of financial reasoning, real-time data access, and Azure-native infrastructure.
FinTech-specific model fine-tuned for precision and context awareness.


Fully asynchronous architecture with real-time streaming.


Intelligent query classification and ticker extraction.


Reliable fallback system for fault tolerance.


Modular and scalable design for future growth.


Transparent web search and file handling capabilities.


Unified deployment and monitoring through Azure services.

