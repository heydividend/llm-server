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
from app.services.investment_explanation_service import (
    InvestmentExplanationService,
    ExplanationContext,
    enhance_response
)
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
        self.explanation_service = InvestmentExplanationService()
        
        logger.info("Harvey Intelligence Service initialized")
        logger.info("  - Multi-model router: READY")
        logger.info("  - ML integration (Azure VM): READY" if self.ml_integration.ml_available else "  - ML integration: UNAVAILABLE")
        logger.info("  - Model audit logging: READY")
        logger.info("  - ETF provider service: READY")
        logger.info("  - Investment explanation service: READY (Why/How/What)")
    
    def _enhance_query_with_context(self, query: str, research_context: Optional[str] = None) -> str:
        """
        Enhance query with sub-agent context to ensure comprehensive explanations.
        Makes Harvey act as an investment research sub-agent that explains Why/How/What.
        """
        base_context = """
## Role
You are an investment research sub-agent specializing in dividend analysis and passive income strategies.
Your responses must ALWAYS explain:
1. WHAT - Clear definition of concepts and data
2. HOW - Methodology and calculations used
3. WHY - Reasoning and importance for investment decisions

## Instructions
- Provide educational context for all financial metrics
- Explain calculations step-by-step
- Connect analysis to practical investment implications
- Use examples when helpful
- Cite specific data points to support conclusions

## Query
"""
        
        if research_context:
            enhanced = f"{base_context}\n## Research Context\n{research_context}\n\n{query}"
        else:
            enhanced = f"{base_context}\n{query}"
        
        return enhanced
    
    async def analyze_dividend(
        self,
        query: str,
        symbol: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        enable_ensemble: bool = False,
        include_strategies: bool = True,
        research_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Complete dividend analysis using all available intelligence:
        1. Multi-model AI responses (GPT-5, Grok-4, DeepSeek, Gemini, FinGPT)
        2. Harvey ML predictions (yield, growth, payout, scoring)
        3. Ensemble evaluation (combine best insights)
        4. ETF Provider analysis (comprehensive provider-level data)
        5. Investment explanations (Why/How/What)
        
        Args:
            query: User's dividend-related question
            symbol: Optional stock ticker
            user_id: Optional user ID for tracking
            session_id: Optional session ID for tracking
            enable_ensemble: If True, queries multiple models and combines responses
            research_context: Optional research initiative context
        
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
            result = await self._ensemble_analysis(query, symbol, user_id, session_id, query_type, research_context)
        else:
            # Single model mode: Route to optimal model
            model_type, routing_reason = self.router.route(query)
            result["model_used"] = model_type.value
            result["routing_reason"] = routing_reason
            
            # Get AI response with sub-agent context
            enhanced_query = self._enhance_query_with_context(query, research_context)
            ai_response = await self._get_ai_response(enhanced_query, model_type)
            
            # Enhance response with Why/How/What explanations
            ai_response = self.explanation_service.enhance_response_with_explanations(
                ai_response, 
                query, 
                {"symbol": symbol} if symbol else None
            )
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
        query_type: QueryType,
        research_context: Optional[str] = None
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
        
        # Enhance query with sub-agent context
        enhanced_query = self._enhance_query_with_context(query, research_context)
        
        # Query all models concurrently
        tasks = []
        for model_type in models:
            tasks.append(self._get_ai_response(enhanced_query, model_type))
        
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
        
        # Enhance combined response with explanations
        combined_response = self.explanation_service.enhance_response_with_explanations(
            combined_response,
            query,
            {"symbol": symbol} if symbol else None
        )
        
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
        # We'll construct a dividend-focused response
        return f"FinGPT Analysis: This query requires dividend scoring and financial analysis. {query}"
    
    def _combine_responses(self, model_responses: Dict[str, str], query_type: QueryType) -> str:
        """
        Intelligently combine responses from multiple models.
        
        Strategy varies by query type:
        - Quantitative: Prioritize DeepSeek's calculations
        - Dividend Scoring: Combine scores and explanations
        - Complex Analysis: Synthesize all perspectives
        """
        combined = []
        
        # Header
        combined.append(f"## Ensemble Analysis (Query Type: {query_type.value})\n")
        
        # Add responses based on query type priority
        if query_type == QueryType.QUANTITATIVE_ANALYSIS:
            # Prioritize DeepSeek for calculations
            if "DeepSeek-R1" in model_responses:
                combined.append("### Quantitative Analysis (DeepSeek-R1):")
                combined.append(model_responses["DeepSeek-R1"])
            if "GPT-5" in model_responses:
                combined.append("\n### Comprehensive Context (GPT-5):")
                combined.append(model_responses["GPT-5"])
        
        elif query_type == QueryType.DIVIDEND_SCORING:
            # Combine scoring insights
            if "FinGPT" in model_responses:
                combined.append("### Dividend Scoring (FinGPT ML):")
                combined.append(model_responses["FinGPT"])
            if "GPT-5" in model_responses:
                combined.append("\n### Analysis (GPT-5):")
                combined.append(model_responses["GPT-5"])
            if "DeepSeek-R1" in model_responses:
                combined.append("\n### Quantitative Factors (DeepSeek-R1):")
                combined.append(model_responses["DeepSeek-R1"])
        
        else:
            # Complex analysis: Show all perspectives
            for model, response in model_responses.items():
                if "Error" not in response:
                    combined.append(f"\n### {model} Perspective:")
                    combined.append(response)
        
        # Summary
        combined.append("\n## Ensemble Summary")
        combined.append(f"Combined insights from {len(model_responses)} models for comprehensive analysis.")
        
        return "\n".join(combined)
    
    async def analyze_etf_provider(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze ETF provider-level queries with comprehensive distribution data.
        """
        # Extract provider name from query
        provider_name = self.etf_provider_service.extract_provider_name(query)
        
        if not provider_name:
            return {
                "error": "Could not identify ETF provider in query",
                "query": query
            }
        
        # Get all ETFs for this provider
        etfs = self.etf_provider_service.get_provider_etfs(provider_name)
        
        logger.info(f"Fetching distribution data for {len(etfs)} {provider_name} ETFs")
        
        # Get distribution data for all ETFs
        distribution_data = []
        for etf in etfs:
            # This would normally fetch from database
            # For now, return mock data
            distribution_data.append({
                "ticker": etf,
                "distribution_amount": f"${self._mock_distribution(etf)}",
                "ex_dividend_date": "2025-11-05",  # Mock date
                "yield": f"{self._mock_yield(etf)}%",
                "frequency": self.etf_provider_service.get_provider_info(provider_name).get(
                    "distribution_frequency", "monthly"
                )
            })
        
        # Format response
        provider_info = self.etf_provider_service.get_provider_info(provider_name)
        
        response_text = f"""## {provider_name} ETF Distributions
**Provider Description:** {provider_info.get('description', 'ETF Provider')}
**Distribution Frequency:** {provider_info.get('distribution_frequency', 'monthly').title()}
**Total ETFs Tracked:** {len(etfs)}

### Latest Distribution Data

| Ticker | Distribution Amount | Ex-Dividend Date | Yield | Frequency |
|--------|-------------------|------------------|-------|-----------|
"""
        
        for data in distribution_data[:10]:  # Show first 10
            response_text += f"| {data['ticker']} | {data['distribution_amount']} | {data['ex_dividend_date']} | {data['yield']} | {data['frequency']} |\n"
        
        if len(distribution_data) > 10:
            response_text += f"\n*... and {len(distribution_data) - 10} more {provider_name} ETFs*\n"
        
        # Add investment context
        response_text += f"""
### Investment Context
- {provider_name} ETFs are known for {provider_info.get('focus', 'dividend distributions')}
- Distribution frequency: {provider_info.get('distribution_frequency', 'monthly').title()}
- Consider tax implications of {provider_info.get('distribution_frequency', 'monthly')} distributions
"""
        
        return {
            "query": query,
            "provider_detected": True,
            "provider_name": provider_name,
            "etfs_count": len(etfs),
            "distribution_frequency": provider_info.get("distribution_frequency", "monthly"),
            "ai_response": response_text,
            "distribution_data": distribution_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _mock_distribution(self, ticker: str) -> str:
        """Generate mock distribution amount based on ticker"""
        # Simple mock logic - would be replaced with database query
        import random
        random.seed(hash(ticker))
        return f"{random.uniform(0.10, 2.50):.4f}"
    
    def _mock_yield(self, ticker: str) -> str:
        """Generate mock yield based on ticker"""
        # Simple mock logic - would be replaced with database query
        import random
        random.seed(hash(ticker) + 1)
        return f"{random.uniform(2, 50):.0f}"
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get complete Harvey Intelligence system status"""
        return {
            "status": "operational",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "multi_model_router": "active",
                "ml_integration": "connected" if self.ml_integration.ml_available else "unavailable",
                "model_audit": "active",
                "etf_provider_service": "active",
                "investment_explanations": "active"
            },
            "models_available": [
                "GPT-5 (Azure OpenAI)",
                "Grok-4 (Azure OpenAI)",
                "DeepSeek-R1 (Azure OpenAI)",
                "Gemini 2.5 Pro (Google)",
                "FinGPT (ML Engine)"
            ],
            "ml_endpoints": 22 if self.ml_integration.ml_available else 0,
            "etf_providers_supported": len(self.etf_provider_service.providers)
        }


# Global instance
harvey = HarveyIntelligence()