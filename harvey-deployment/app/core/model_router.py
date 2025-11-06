"""
Harvey Multi-Model AI Router
Intelligently routes queries to the optimal LLM model based on query type and complexity.

Model Pool:
- GPT-5 (Azure): Complex financial analysis, reasoning, general chat
- Grok-4 (Azure): Fast reasoning, real-time queries, quick responses
- DeepSeek-R1 (Azure): Quantitative analysis, mathematical modeling, complex calculations
- Gemini 2.5 Pro: Chart/graph analysis, FX trading, multimodal tasks
- FinGPT (Azure VM): Specialized dividend scoring and financial predictions

Cost Optimization: Targets 70% cost savings vs. all-GPT-5 approach
"""

import os
import re
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

class ModelType(Enum):
    """Available AI models in Harvey's fleet"""
    GPT5 = "gpt-5"  # Azure OpenAI: HarveyGPT-5 deployment
    GROK4 = "grok-4"  # Azure OpenAI: grok-4-fast-reasoning deployment
    DEEPSEEK = "deepseek-r1"  # Azure OpenAI: DeepSeek-R1-0528 deployment
    GEMINI = "gemini-2.5-pro"  # Google Gemini API
    FINGPT = "fingpt"  # Azure VM Intelligence Engine

@dataclass
class ModelConfig:
    """Configuration for each model"""
    name: str
    deployment: Optional[str]  # Azure deployment name
    endpoint: Optional[str]  # API endpoint
    cost_per_1m_input: float  # Cost in dollars
    cost_per_1m_output: float
    specialization: str
    max_tokens: int

class QueryType(Enum):
    """Query classification types"""
    CHART_ANALYSIS = "chart_analysis"
    FX_TRADING = "fx_trading"
    DIVIDEND_SCORING = "dividend_scoring"
    DIVIDEND_STRATEGY = "dividend_strategy"  # New: Advanced dividend strategies
    QUANTITATIVE_ANALYSIS = "quantitative_analysis"
    FAST_QUERY = "fast_query"
    COMPLEX_ANALYSIS = "complex_analysis"
    GENERAL_CHAT = "general_chat"
    MULTIMODAL = "multimodal"

# Model configurations
MODEL_CONFIGS = {
    ModelType.GPT5: ModelConfig(
        name="GPT-5",
        deployment="HarveyGPT-5",
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        cost_per_1m_input=1.25,
        cost_per_1m_output=10.0,
        specialization="Complex financial analysis, multi-step reasoning, comprehensive reports",
        max_tokens=128000
    ),
    ModelType.GROK4: ModelConfig(
        name="Grok-4 Fast",
        deployment="grok-4-fast-reasoning",
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        cost_per_1m_input=3.0,
        cost_per_1m_output=15.0,
        specialization="Fast reasoning, real-time queries, quick analysis",
        max_tokens=128000
    ),
    ModelType.DEEPSEEK: ModelConfig(
        name="DeepSeek-R1",
        deployment="DeepSeek-R1-0528",
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        cost_per_1m_input=0.55,
        cost_per_1m_output=2.19,
        specialization="Quantitative analysis, mathematical modeling, portfolio optimization, complex calculations",
        max_tokens=64000
    ),
    ModelType.GEMINI: ModelConfig(
        name="Gemini 2.5 Pro",
        deployment=None,
        endpoint="https://generativelanguage.googleapis.com",
        cost_per_1m_input=1.25,
        cost_per_1m_output=5.0,
        specialization="Chart analysis, FX data, multimodal (images+text), technical patterns",
        max_tokens=1048576  # 1M context
    ),
    ModelType.FINGPT: ModelConfig(
        name="FinGPT",
        deployment=None,
        endpoint=os.getenv("ML_API_BASE_URL", "http://localhost:9000"),
        cost_per_1m_input=0.0,  # Self-hosted
        cost_per_1m_output=0.0,
        specialization="Dividend scoring, financial sentiment, yield prediction, sector analysis",
        max_tokens=8192
    )
}

class QueryRouter:
    """Intelligent query router for multi-model AI system"""
    
    def __init__(self):
        self.models = MODEL_CONFIGS
        self._init_patterns()
    
    def _init_patterns(self):
        """Initialize regex patterns for query classification"""
        self.patterns = {
            QueryType.CHART_ANALYSIS: [
                r'\b(chart|graph|candlestick|pattern|technical\s+analysis|moving\s+average|rsi|macd|bollinger)\b',
                r'\b(support|resistance|trend\s+line|breakout|fibonacci)\b',
                r'\b(analyze\s+this\s+(chart|image|screenshot|graph))\b'
            ],
            QueryType.FX_TRADING: [
                r'\b(forex|fx|currency|eur/usd|gbp/usd|exchange\s+rate)\b',
                r'\b(pip|spread|currency\s+pair|cross\s+rate)\b'
            ],
            QueryType.DIVIDEND_SCORING: [
                r'\b(dividend\s+(quality|score|rating|grade|sustainability))\b',
                r'\b(payout\s+ratio|dividend\s+growth|yield\s+prediction)\b',
                r'\b(cut\s+risk|dividend\s+safety|income\s+reliability)\b',
                r'\b(rate\s+this\s+dividend|score\s+[A-Z]{1,5}\s+dividend)\b'
            ],
            QueryType.DIVIDEND_STRATEGY: [
                r'\b(margin\s+(buying|trading|leverage)|leverag(e|ing)\s+dividend)\b',
                r'\b(drip|dividend\s+reinvest|reinvestment\s+plan)\b',
                r'\b(dividend\s+capture|capture\s+strateg|ex(-|\s)date\s+play)\b',
                r'\b(ex(-|\s)dividend\s+(dip|drop|buying|strategy))\b',
                r'\b(declaration\s+(play|strateg|buying))\b',
                r'\b(covered\s+call|sell\s+call|option\s+income)\b',
                r'\b(cash(-|\s)secured\s+put|put\s+writing|sell\s+put)\b',
                r'\b(when\s+(to|should)\s+(buy|sell).*(dividend|ex(-|\s)date))\b',
                r'\b(buy\s+before\s+ex|sell\s+after\s+(ex|record))\b'
            ],
            QueryType.QUANTITATIVE_ANALYSIS: [
                r'\b(portfolio\s+optimization|optimize\s+my\s+portfolio)\b',
                r'\b(sharpe\s+ratio|sortino|alpha|beta|volatility)\b',
                r'\b(correlation|covariance|regression|backtest)\b',
                r'\b(calculate|compute|model|quantitative|quant)\b',
                r'\b(risk.*return|efficient\s+frontier|monte\s+carlo)\b',
                r'\b(tax\s+optimization|tax.*loss.*harvest)\b',
                r'\b(rebalance|asset\s+allocation|diversification\s+ratio)\b'
            ],
            QueryType.FAST_QUERY: [
                r'^\b(what|when|where|who|how\s+much|how\s+many)\b.*\?$',
                r'\b(price\s+of|current\s+price|latest\s+price|stock\s+price)\b',
                r'\b(quick|fast|simple|brief)\b',
                r'^.{0,50}$'  # Short queries (under 50 chars)
            ],
            QueryType.MULTIMODAL: [
                r'\b(analyze\s+this\s+(image|photo|screenshot|picture))\b',
                r'\b(what.*in\s+this\s+(image|chart|graph))\b'
            ]
        }
    
    def classify_query(self, query: str, has_image: bool = False) -> QueryType:
        """
        Classify query to determine optimal model routing.
        
        Args:
            query: User query text
            has_image: Whether the query includes an image/chart
            
        Returns:
            QueryType enum
        """
        query_lower = query.lower()
        
        # Multimodal takes priority if image is present
        if has_image:
            return QueryType.MULTIMODAL
        
        # Check quantitative analysis patterns (high priority)
        for pattern in self.patterns[QueryType.QUANTITATIVE_ANALYSIS]:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return QueryType.QUANTITATIVE_ANALYSIS
        
        # Check dividend scoring patterns
        for pattern in self.patterns[QueryType.DIVIDEND_SCORING]:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return QueryType.DIVIDEND_SCORING
        
        # Check chart analysis patterns
        for pattern in self.patterns[QueryType.CHART_ANALYSIS]:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return QueryType.CHART_ANALYSIS
        
        # Check FX trading patterns
        for pattern in self.patterns[QueryType.FX_TRADING]:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return QueryType.FX_TRADING
        
        # Check fast query patterns
        for pattern in self.patterns[QueryType.FAST_QUERY]:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return QueryType.FAST_QUERY
        
        # Complex analysis indicators
        complex_indicators = [
            len(query) > 200,  # Long query
            query.count('?') > 2,  # Multiple questions
            any(word in query_lower for word in [
                'analyze', 'compare', 'evaluate', 'portfolio', 'strategy',
                'comprehensive', 'detailed', 'explain', 'breakdown'
            ])
        ]
        
        if sum(complex_indicators) >= 2:
            return QueryType.COMPLEX_ANALYSIS
        
        # Default to general chat
        return QueryType.GENERAL_CHAT
    
    def route_query(
        self,
        query: str,
        has_image: bool = False,
        context: Optional[Dict] = None
    ) -> Tuple[ModelType, str]:
        """
        Route query to optimal model based on classification.
        
        Args:
            query: User query text
            has_image: Whether query includes image/chart
            context: Additional context (conversation history, etc.)
            
        Returns:
            Tuple of (ModelType, routing_reason)
        """
        query_type = self.classify_query(query, has_image)
        
        # Routing logic
        routing_map = {
            QueryType.CHART_ANALYSIS: (ModelType.GEMINI, "Chart/technical analysis → Gemini 2.5 Pro (multimodal expert)"),
            QueryType.FX_TRADING: (ModelType.GEMINI, "FX trading analysis → Gemini 2.5 Pro (financial data expert)"),
            QueryType.DIVIDEND_SCORING: (ModelType.FINGPT, "Dividend scoring → FinGPT (specialized dividend expert)"),
            QueryType.QUANTITATIVE_ANALYSIS: (ModelType.DEEPSEEK, "Quantitative analysis → DeepSeek-R1 (mathematical reasoning expert)"),
            QueryType.FAST_QUERY: (ModelType.GROK4, "Fast query → Grok-4 (optimized for speed)"),
            QueryType.COMPLEX_ANALYSIS: (ModelType.GPT5, "Complex analysis → GPT-5 (advanced reasoning)"),
            QueryType.GENERAL_CHAT: (ModelType.GROK4, "General chat → Grok-4 (cost-optimized)"),
            QueryType.MULTIMODAL: (ModelType.GEMINI, "Multimodal query → Gemini 2.5 Pro (image analysis)")
        }
        
        model, reason = routing_map.get(query_type, (ModelType.GPT5, "Default → GPT-5"))
        
        return model, reason
    
    def get_model_config(self, model_type: ModelType) -> ModelConfig:
        """Get configuration for a specific model"""
        return self.models[model_type]
    
    def estimate_cost(
        self,
        model_type: ModelType,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Estimate cost for a query with specific model.
        
        Returns:
            Cost in dollars
        """
        config = self.get_model_config(model_type)
        cost = (
            (input_tokens / 1_000_000) * config.cost_per_1m_input +
            (output_tokens / 1_000_000) * config.cost_per_1m_output
        )
        return round(cost, 6)
    
    def get_routing_stats(self) -> Dict:
        """Get router statistics and model information"""
        return {
            "available_models": [m.value for m in ModelType],
            "model_configs": {
                m.value: {
                    "name": cfg.name,
                    "specialization": cfg.specialization,
                    "cost_per_1m_input": cfg.cost_per_1m_input,
                    "cost_per_1m_output": cfg.cost_per_1m_output,
                    "max_tokens": cfg.max_tokens
                }
                for m, cfg in self.models.items()
            },
            "query_types": [qt.value for qt in QueryType]
        }


# Global router instance
router = QueryRouter()


def route_query(query: str, has_image: bool = False, context: Optional[Dict] = None):
    """
    Convenience function to route a query to the optimal model.
    
    Usage:
        model, reason = route_query("What's the dividend yield for AAPL?")
        config = router.get_model_config(model)
    """
    return router.route_query(query, has_image, context)


def get_router_stats():
    """Get router statistics"""
    return router.get_routing_stats()
