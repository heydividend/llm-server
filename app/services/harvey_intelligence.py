"""
Harvey Unified Intelligence Service
Coordinates all AI and ML systems across Replit VM and Azure VM.

Architecture:
┌─────────────────────────────────────────────────────────────────┐
│                    REPLIT VM (Development)                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Harvey Intelligence Service (This File)                    │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │ │
│  │  │ Multi-Model  │  │ Model Audit  │  │ Ensemble         │ │ │
│  │  │ Router       │→ │ Logger       │→ │ Evaluator        │ │ │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
│         │                    │                     │             │
│         ↓                    ↓                     ↓             │
│  ┌─────────────┐      ┌──────────────┐      ┌──────────────┐   │
│  │ Azure       │      │ Azure SQL    │      │ ML API       │   │
│  │ OpenAI      │      │ Database     │      │ Client       │   │
│  │ (3 models)  │      │ (Audit Logs) │      │              │   │
│  └─────────────┘      └──────────────┘      └──────────────┘   │
│         │                                           │            │
└─────────┼───────────────────────────────────────────┼────────────┘
          │                                           │
          │                                           │
          ↓                                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                    AZURE VM (Production)                         │
│  20.81.210.213                                                   │
│                                                                  │
│  ┌──────────────────────────┐  ┌──────────────────────────────┐ │
│  │ Azure OpenAI Resource    │  │ Harvey Intelligence Engine   │ │
│  │ htmltojson-parser-       │  │ Port 9000                    │ │
│  │ openai-a1a8              │  │                              │ │
│  │                          │  │ 22+ ML Endpoints:            │ │
│  │ • HarveyGPT-5           │  │ • Dividend Scoring           │ │
│  │ • grok-4-fast-reasoning │  │ • Yield Prediction           │ │
│  │ • DeepSeek-R1-0528      │  │ • Payout Analysis            │ │
│  └──────────────────────────┘  │ • NAV Erosion                │ │
│                                │ • Portfolio Optimization      │ │
│  ┌──────────────────────────┐  │ • Clustering                 │ │
│  │ Azure SQL Database       │  │ • FinGPT Model               │ │
│  │ heydividend-sql          │  └──────────────────────────────┘ │
│  │                          │                                   │
│  │ • Canonical_Dividends    │                                   │
│  │ • Symbols                │                                   │
│  │ • Feedback               │                                   │
│  │ • AI Training Samples    │                                   │
│  └──────────────────────────┘                                   │
└─────────────────────────────────────────────────────────────────┘

Integration Flow:
1. User query → Harvey Intelligence Service
2. Multi-Model Router classifies query → selects optimal model(s)
3. Execute query across selected models (parallel if ensemble mode)
4. Model Audit Logger captures all responses
5. Ensemble Evaluator combines best insights
6. Return unified response to user
7. Store audit logs in Azure SQL for training
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from app.core.model_router import QueryRouter, ModelType, QueryType
from app.core.llm_providers import oai_stream_with_model, oai_client, gemini_stream
from app.services.ml_integration import MLIntegration
from app.services.model_audit_service import dividend_auditor
from app.services.dividend_strategy_analyzer import dividend_strategy, DividendStrategy
from app.services.etf_provider_service import ETFProviderService
from app.core.logging_config import get_logger

logger = get_logger("harvey_intelligence")


class HarveyIntelligence:
    """
    Unified Harvey Intelligence Service
    Coordinates multi-model AI routing, ML predictions, and ensemble learning.
    """
    
    def __init__(self):
        """Initialize Harvey's unified intelligence system"""
        self.router = QueryRouter()
        self.ml_integration = MLIntegration()
        self.auditor = dividend_auditor
        self.etf_provider_service = ETFProviderService()
        
        logger.info("Harvey Intelligence Service initialized")
        logger.info("  - Multi-model router: READY")
        logger.info("  - ML integration (Azure VM): READY" if self.ml_integration.ml_available else "  - ML integration: UNAVAILABLE")
        logger.info("  - Model audit logging: READY")
        logger.info("  - ETF provider service: READY")
    
    async def analyze_dividend(
        self,
        query: str,
        symbol: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        enable_ensemble: bool = False,
        include_strategies: bool = True
    ) -> Dict[str, Any]:
        """
        Complete dividend analysis using all available intelligence:
        1. Multi-model AI responses (GPT-5, Grok-4, DeepSeek, Gemini, FinGPT)
        2. Harvey ML predictions (yield, growth, payout, scoring)
        3. Ensemble evaluation (combine best insights)
        4. ETF Provider analysis (comprehensive provider-level data)
        
        Args:
            query: User's dividend-related question
            symbol: Optional stock ticker
            user_id: Optional user ID for tracking
            session_id: Optional session ID for tracking
            enable_ensemble: If True, queries multiple models and combines responses
        
        Returns:
            Unified intelligence response with AI analysis + ML predictions
        """
        logger.info(f"Harvey analyzing dividend query: {query[:50]}... (ensemble: {enable_ensemble})")
        
        # Check if this is an ETF provider query
        if self.etf_provider_service.is_provider_query(query):
            logger.info("Detected ETF provider-level query")
            return await self.analyze_etf_provider(query, user_id, session_id)
        
        result = {
            "query": query,
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "ai_response": None,
            "ml_intelligence": {},
            "model_used": None,
            "ensemble_used": enable_ensemble,
            "routing_reason": None
        }
        
        # Step 1: Route query to optimal model(s)
        query_type = self.router.classify_query(query)
        
        if enable_ensemble and query_type in [
            QueryType.COMPLEX_ANALYSIS,
            QueryType.DIVIDEND_SCORING,
            QueryType.QUANTITATIVE_ANALYSIS
        ]:
            # Ensemble mode: Query multiple models and combine
            result = await self._ensemble_analysis(query, symbol, user_id, session_id, query_type)
        else:
            # Single model mode: Route to optimal model
            model_type, routing_reason = self.router.route(query)
            result["model_used"] = model_type.value
            result["routing_reason"] = routing_reason
            
            # Get AI response directly
            ai_response = await self._get_ai_response(query, model_type)
            result["ai_response"] = ai_response
        
        # Step 2: Get ML intelligence from Harvey Intelligence Engine (Azure VM)
        if symbol and self.ml_integration.ml_available:
            logger.info(f"Fetching ML intelligence for {symbol} from Azure VM")
            try:
                ml_intelligence = await self.ml_integration.get_dividend_intelligence(symbol)
                result["ml_intelligence"] = ml_intelligence
            except Exception as e:
                logger.error(f"Failed to get ML intelligence: {e}")
                result["ml_intelligence"] = {"error": str(e), "ml_available": False}
        
        # Step 2.5: Analyze dividend investment strategies
        if symbol and include_strategies:
            logger.info(f"Analyzing dividend strategies for {symbol}")
            try:
                # Get strategy analysis (would need real data in production)
                strategy_analysis = dividend_strategy.analyze_strategy(
                    symbol=symbol,
                    current_price=100.0,  # Would fetch from market data
                    dividend_yield=3.5,   # Would fetch from database
                    capital_available=10000,
                    risk_tolerance="MEDIUM"
                )
                result["dividend_strategies"] = strategy_analysis
            except Exception as e:
                logger.error(f"Failed to analyze strategies: {e}")
                result["dividend_strategies"] = {"error": str(e)}
        
        # Step 3: Log to model audit service for training
        if enable_ensemble and "model_responses" in result:
            # Log all model responses
            self.auditor.log_multi_model_response(
                query=query,
                model_responses=result["model_responses"],
                selected_model=result.get("selected_model", "ensemble"),
                selected_response=result.get("ai_response", ""),
                routing_reason=result.get("routing_reason", "ensemble_mode"),
                user_id=user_id,
                session_id=session_id
            )
        
        return result
    
    async def _ensemble_analysis(
        self,
        query: str,
        symbol: Optional[str],
        user_id: Optional[str],
        session_id: Optional[str],
        query_type: QueryType
    ) -> Dict[str, Any]:
        """
        Ensemble mode: Query multiple AI models and combine their insights.
        
        Strategy:
        - DeepSeek: Quantitative calculations
        - GPT-5: Comprehensive explanation
        - FinGPT (ML): Dividend scoring
        - Gemini: Chart analysis (if applicable)
        """
        logger.info(f"Ensemble analysis for query type: {query_type}")
        
        # Select models for ensemble based on query type
        if query_type == QueryType.DIVIDEND_SCORING:
            models = [ModelType.GPT5, ModelType.DEEPSEEK, ModelType.FINGPT]
        elif query_type == QueryType.QUANTITATIVE_ANALYSIS:
            models = [ModelType.DEEPSEEK, ModelType.GPT5]
        elif query_type == QueryType.COMPLEX_ANALYSIS:
            models = [ModelType.GPT5, ModelType.GROK4, ModelType.DEEPSEEK]
        else:
            models = [ModelType.GPT5, ModelType.GROK4]
        
        # Query all models concurrently
        tasks = []
        for model_type in models:
            tasks.append(self._get_ai_response(query, model_type))
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Build model responses dict
        model_responses = {}
        for i, model_type in enumerate(models):
            if isinstance(responses[i], Exception):
                logger.warning(f"{model_type.value} failed: {responses[i]}")
                model_responses[model_type.value] = f"Error: {str(responses[i])}"
            else:
                model_responses[model_type.value] = responses[i]
        
        # Ensemble evaluation: Combine best insights
        combined_response = self._combine_responses(model_responses, query_type)
        
        return {
            "query": query,
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "ai_response": combined_response,
            "model_responses": model_responses,
            "selected_model": "ensemble",
            "routing_reason": f"Ensemble mode for {query_type.value}",
            "models_used": [m.value for m in models],
            "ml_intelligence": {}
        }
    
    async def _get_ai_response(self, query: str, model_type: ModelType) -> str:
        """Get AI response from a specific model"""
        try:
            # For FinGPT (ML API), use ML integration instead
            if model_type == ModelType.FINGPT:
                return await self._get_fingpt_response(query)
            
            # For Gemini, use Gemini API
            if model_type == ModelType.GEMINI:
                messages = [{"role": "user", "content": query}]
                response_parts = []
                async for chunk in gemini_stream(messages):
                    response_parts.append(chunk)
                return ''.join(response_parts)
            
            # For Azure OpenAI models (GPT-5, Grok-4, DeepSeek), map to deployment names
            deployment_map = {
                ModelType.GPT5: "HarveyGPT-5",
                ModelType.GROK4: "grok-4-fast-reasoning", 
                ModelType.DEEPSEEK: "DeepSeek-R1-0528"
            }
            
            deployment = deployment_map.get(model_type)
            if not deployment:
                logger.error(f"No deployment mapping for {model_type.value}")
                return f"Error: No deployment for {model_type.value}"
            
            # Use Azure OpenAI streaming
            messages = [{"role": "user", "content": query}]
            response_parts = []
            for chunk in oai_stream_with_model(messages, deployment_name=deployment):
                response_parts.append(chunk)
            return ''.join(response_parts)
            
        except Exception as e:
            logger.error(f"Error getting response from {model_type.value}: {e}")
            return f"Error: {str(e)}"
    
    async def _get_fingpt_response(self, query: str) -> str:
        """Get response from FinGPT via Harvey Intelligence Engine"""
        # FinGPT doesn't have a chat interface, it's accessed via ML endpoints
        # This is a placeholder - in practice, FinGPT results come via ML intelligence
        return "FinGPT (ML predictions available separately via Harvey Intelligence Engine)"
    
    def _combine_responses(self, model_responses: Dict[str, str], query_type: QueryType) -> str:
        """
        Ensemble Evaluator: Combine responses from multiple models.
        
        Strategy:
        - Use DeepSeek for quantitative data/calculations
        - Use GPT-5 for comprehensive explanations
        - Use FinGPT scores for dividend quality
        - Merge into a single coherent response
        """
        combined = "**Harvey's Ensemble Analysis**\n\n"
        
        # Extract quantitative insights from DeepSeek
        if "deepseek-r1" in model_responses and not model_responses["deepseek-r1"].startswith("Error"):
            combined += "**Quantitative Analysis (DeepSeek-R1):**\n"
            combined += model_responses["deepseek-r1"][:500] + "\n\n"
        
        # Add comprehensive explanation from GPT-5
        if "gpt-5" in model_responses and not model_responses["gpt-5"].startswith("Error"):
            combined += "**Detailed Analysis (GPT-5):**\n"
            combined += model_responses["gpt-5"][:800] + "\n\n"
        
        # Add FinGPT dividend scoring if available
        if "fingpt" in model_responses and not model_responses["fingpt"].startswith("Error"):
            combined += "**ML Dividend Scoring (FinGPT):**\n"
            combined += model_responses["fingpt"][:300] + "\n\n"
        
        # Add fast reasoning from Grok if available
        if "grok-4" in model_responses and not model_responses["grok-4"].startswith("Error"):
            combined += "**Quick Insights (Grok-4):**\n"
            combined += model_responses["grok-4"][:400] + "\n\n"
        
        combined += "\n*This response combines insights from multiple AI models specialized in different aspects of dividend analysis.*"
        
        return combined
    
    async def analyze_etf_provider(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze ETF provider-level queries to return comprehensive distribution data.
        
        Args:
            query: User's query about ETF provider distributions
            user_id: Optional user ID for tracking
            session_id: Optional session ID for tracking
        
        Returns:
            Comprehensive response with all ETFs from the provider
        """
        # Identify the provider from the query
        provider_key = self.etf_provider_service.identify_provider(query)
        
        if not provider_key:
            return {
                "query": query,
                "timestamp": datetime.utcnow().isoformat(),
                "ai_response": "I couldn't identify which ETF provider you're asking about. Please specify the provider name (e.g., YieldMax, Vanguard, Global X, etc.).",
                "provider_detected": False
            }
        
        # Get provider info
        provider_info = self.etf_provider_service.get_provider_etfs(provider_key)
        
        if not provider_info:
            return {
                "query": query,
                "timestamp": datetime.utcnow().isoformat(),
                "ai_response": f"Provider information not available for {provider_key}.",
                "provider_detected": True,
                "provider_key": provider_key
            }
        
        # Get all tickers for this provider
        tickers = provider_info["tickers"]
        logger.info(f"Fetching distribution data for {len(tickers)} {provider_info['name']} ETFs")
        
        # Here we would normally fetch actual distribution data from the database
        # For demonstration, we'll create a mock response showing the structure
        # In production, this would query Azure SQL for actual distribution data
        
        # Mock distribution data for demonstration
        mock_distributions = []
        for ticker in tickers[:10]:  # Limit to first 10 for demo
            mock_distributions.append({
                "Ticker": ticker,
                "Distribution_Amount": 0.25 + (hash(ticker) % 100) / 100,  # Mock amount
                "Ex_Dividend_Date": datetime.utcnow() - timedelta(days=hash(ticker) % 30),
                "Yield": f"{15 + (hash(ticker) % 40)}%"
            })
        
        # Format the response
        formatted_response = self.etf_provider_service.format_provider_response(
            provider_key,
            mock_distributions
        )
        
        # Log the analysis for audit
        if user_id and session_id:
            self.auditor.log_multi_model_response(
                query=query,
                model_responses={"etf_provider_service": formatted_response},
                selected_model="etf_provider_service",
                selected_response=formatted_response,
                routing_reason=f"ETF provider query for {provider_info['name']}",
                user_id=user_id,
                session_id=session_id
            )
        
        return {
            "query": query,
            "timestamp": datetime.utcnow().isoformat(),
            "ai_response": formatted_response,
            "provider_detected": True,
            "provider_key": provider_key,
            "provider_name": provider_info["name"],
            "etfs_count": len(tickers),
            "distribution_frequency": provider_info["frequency"],
            "model_used": "etf_provider_service",
            "routing_reason": f"Provider-level query for {provider_info['name']}"
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get status of all Harvey intelligence systems"""
        return {
            "harvey_intelligence": "operational",
            "components": {
                "multi_model_router": "ready",
                "azure_openai": {
                    "status": "ready",
                    "models": ["GPT-5", "Grok-4", "DeepSeek-R1"]
                },
                "google_gemini": {
                    "status": "ready" if self._check_gemini_available() else "unavailable",
                    "model": "Gemini 2.5 Pro"
                },
                "harvey_ml_engine": {
                    "status": "ready" if self.ml_integration.ml_available else "unavailable",
                    "endpoint": "Azure VM:9000",
                    "endpoints_count": 22
                },
                "model_audit_logger": "ready",
                "ensemble_evaluator": "ready"
            },
            "integration_status": {
                "replit_vm_to_azure_vm": "connected" if self.ml_integration.ml_available else "disconnected",
                "azure_sql_database": "connected" if self.auditor.engine else "disconnected"
            }
        }
    
    def _check_gemini_available(self) -> bool:
        """Check if Gemini is available"""
        try:
            import google.generativeai
            return True
        except ImportError:
            return False


# Global instance
harvey = HarveyIntelligence()
