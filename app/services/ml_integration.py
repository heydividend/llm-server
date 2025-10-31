"""
ML Integration Service for Harvey

Provides high-level ML-powered features for conversational AI:
- Dividend quality scoring and grading
- ML-powered stock recommendations
- Portfolio optimization suggestions
- Similar stock discovery using clustering
- Predictive analytics (yield, growth, payout forecasts)
"""

import logging
from typing import List, Dict, Any, Optional
from app.services.ml_api_client import get_ml_client

logger = logging.getLogger("ml_integration")


class MLIntegration:
    """High-level ML integration for Harvey's conversational AI."""
    
    def __init__(self):
        try:
            self.client = get_ml_client()
            self.ml_available = bool(self.client.api_key)
        except Exception as e:
            logger.warning(f"ML API client initialization failed: {e}")
            self.client = None
            self.ml_available = False
    
    async def get_dividend_intelligence(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive ML intelligence for a dividend stock.
        
        Combines: scoring, predictions, clustering, and insights.
        Perfect for answering "Tell me about [TICKER]" queries.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Comprehensive ML intelligence
        """
        # Quick fail if ML not available
        if not self.ml_available or not self.client:
            logger.debug(f"ML API unavailable, skipping intelligence for {symbol}")
            return {"symbol": symbol, "ml_available": False}
        
        try:
            logger.info(f"Getting ML intelligence for {symbol}")
            
            intelligence = {
                "symbol": symbol,
                "ml_available": True,
                "score": None,
                "predictions": {},
                "cluster_info": None,
                "similar_stocks": [],
                "recommendation": None
            }
            
            # Get ML quality score (non-blocking)
            try:
                score_result = self.client.score_symbol(symbol)
                if score_result.get("success"):
                    intelligence["score"] = score_result.get("data", {})
            except ValueError as e:
                logger.debug(f"ML API key missing: {e}")
                return {"symbol": symbol, "ml_available": False}
            except Exception as e:
                logger.warning(f"ML scoring unavailable for {symbol}: {e}")
            
            # Get growth prediction (non-blocking)
            try:
                growth_result = self.client.predict_growth_rate(symbol)
                if growth_result.get("success"):
                    intelligence["predictions"]["growth_rate"] = growth_result.get("data", {})
            except Exception as e:
                logger.warning(f"ML growth prediction unavailable for {symbol}: {e}")
            
            # Get yield prediction (non-blocking)
            try:
                yield_result = self.client.predict_yield(symbol, horizon="12_months")
                if yield_result.get("success"):
                    intelligence["predictions"]["yield_12m"] = yield_result.get("data", {})
            except Exception as e:
                logger.warning(f"ML yield prediction unavailable for {symbol}: {e}")
            
            # Get cluster analysis (non-blocking)
            try:
                cluster_result = self.client.cluster_analyze_stock(symbol)
                if cluster_result.get("success"):
                    intelligence["cluster_info"] = cluster_result.get("data", {})
            except Exception as e:
                logger.warning(f"ML clustering unavailable for {symbol}: {e}")
            
            # Get similar stocks (non-blocking)
            try:
                similar_result = self.client.cluster_find_similar(symbol, limit=5)
                if similar_result.get("success"):
                    intelligence["similar_stocks"] = similar_result.get("data", {}).get("similar_stocks", [])
            except Exception as e:
                logger.warning(f"ML similar stocks unavailable for {symbol}: {e}")
            
            # Get comprehensive insights (non-blocking)
            try:
                insights_result = self.client.get_symbol_insights(symbol)
                if insights_result.get("success"):
                    intelligence["insights"] = insights_result.get("data", {}).get("ml_insights", {})
            except Exception as e:
                logger.warning(f"ML insights unavailable for {symbol}: {e}")
            
            logger.info(f"ML intelligence gathered for {symbol}")
            return intelligence
            
        except Exception as e:
            logger.error(f"Failed to get ML intelligence for {symbol}: {e}")
            return {
                "symbol": symbol,
                "ml_available": False,
                "error": str(e)
            }
    
    async def get_ml_recommendation(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Get ML-powered buy/hold/sell recommendations for securities.
        
        Intelligently uses single, watchlist, or batch endpoints based on count.
        
        Args:
            symbols: List of ticker symbols
            
        Returns:
            ML recommendations with scoring
        """
        # Quick fail if ML not available
        if not self.ml_available or not self.client:
            logger.debug(f"ML API unavailable, skipping recommendations for {len(symbols)} symbols")
            return {"success": False, "ml_available": False}
        
        try:
            logger.info(f"Getting ML recommendations for {len(symbols)} symbols")
            
            # Use appropriate endpoint based on symbol count
            if len(symbols) == 0:
                return {"success": False, "error": "No symbols provided"}
            elif len(symbols) == 1:
                # Single symbol scoring
                result = self.client.score_symbol(symbols[0])
            elif len(symbols) <= 10:
                # Watchlist scoring (optimized for small lists)
                result = self.client.score_watchlist(symbols)
            else:
                # Batch scoring (handles up to 100 symbols efficiently)
                result = self.client.score_batch(symbols[:100])
            
            if result.get("success"):
                data = result.get("data", {})
                
                # Add recommendation logic
                recommendations = []
                scores_list = data.get("scores", []) if "scores" in data else [data]
                
                for score_data in scores_list:
                    score = score_data.get("score", 0)
                    grade = score_data.get("grade", "N/A")
                    
                    # Simple recommendation logic based on ML score
                    if score >= 85:
                        recommendation = "Strong Buy"
                    elif score >= 75:
                        recommendation = "Buy"
                    elif score >= 60:
                        recommendation = "Hold"
                    elif score >= 50:
                        recommendation = "Trim"
                    else:
                        recommendation = "Sell"
                    
                    recommendations.append({
                        "symbol": score_data.get("symbol"),
                        "score": score,
                        "grade": grade,
                        "recommendation": recommendation
                    })
                
                # Add summary stats
                if recommendations:
                    scores = [r["score"] for r in recommendations]
                    summary = {
                        "total_symbols": len(recommendations),
                        "avg_score": sum(scores) / len(scores),
                        "best_symbol": max(recommendations, key=lambda x: x["score"])["symbol"],
                        "worst_symbol": min(recommendations, key=lambda x: x["score"])["symbol"]
                    }
                else:
                    summary = {}
                
                return {
                    "success": True,
                    "recommendations": recommendations,
                    "summary": summary
                }
            
            return {"success": False, "error": "ML scoring unavailable"}
            
        except ValueError as e:
            logger.debug(f"ML API key missing: {e}")
            return {"success": False, "ml_available": False}
        except Exception as e:
            logger.error(f"Failed to get ML recommendations: {e}")
            return {"success": False, "error": str(e)}
    
    async def optimize_portfolio(self, portfolio_id: int, goal: str = "maximize_yield") -> Dict[str, Any]:
        """
        Get ML-driven portfolio optimization suggestions.
        
        Args:
            portfolio_id: Portfolio ID
            goal: Optimization goal (maximize_yield, minimize_risk, etc.)
            
        Returns:
            Portfolio optimization suggestions
        """
        try:
            logger.info(f"Optimizing portfolio {portfolio_id} for {goal}")
            
            result = self.client.cluster_optimize_portfolio(
                portfolio_id=portfolio_id,
                optimization_goal=goal
            )
            
            if result.get("success"):
                return result.get("data", {})
            
            return {"error": "Portfolio optimization unavailable"}
            
        except Exception as e:
            logger.error(f"Failed to optimize portfolio: {e}")
            return {"error": str(e)}
    
    async def find_similar_stocks(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find stocks similar to a given symbol using ML clustering.
        
        Perfect for "stocks like [TICKER]" queries.
        
        Args:
            symbol: Stock ticker symbol
            limit: Maximum number of similar stocks
            
        Returns:
            List of similar stocks with similarity scores
        """
        try:
            logger.info(f"Finding stocks similar to {symbol}")
            
            result = self.client.cluster_find_similar(symbol, limit=limit)
            
            if result.get("success"):
                return result.get("data", {}).get("similar_stocks", [])
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to find similar stocks: {e}")
            return []
    
    async def get_portfolio_health(self, portfolio_id: int) -> Dict[str, Any]:
        """
        Get comprehensive ML health check for a portfolio.
        
        Includes: scoring, diversification, cluster analysis.
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            Portfolio health metrics
        """
        try:
            logger.info(f"Analyzing portfolio health for {portfolio_id}")
            
            health = {
                "portfolio_id": portfolio_id,
                "score": None,
                "diversification": None,
                "cluster_analysis": None
            }
            
            # Get portfolio score
            try:
                score_result = self.client.score_portfolio(portfolio_id)
                if score_result.get("success"):
                    health["score"] = score_result.get("data", {})
            except Exception as e:
                logger.warning(f"Portfolio scoring unavailable: {e}")
            
            # Get diversification analysis
            try:
                div_result = self.client.cluster_portfolio_diversification(portfolio_id)
                if div_result.get("success"):
                    health["diversification"] = div_result.get("data", {})
            except Exception as e:
                logger.warning(f"Diversification analysis unavailable: {e}")
            
            # Get cluster analysis
            try:
                cluster_result = self.client.get_cluster_portfolio_detail(portfolio_id)
                if cluster_result.get("success"):
                    health["cluster_analysis"] = cluster_result.get("data", {})
            except Exception as e:
                logger.warning(f"Cluster analysis unavailable: {e}")
            
            return health
            
        except Exception as e:
            logger.error(f"Failed to analyze portfolio health: {e}")
            return {"error": str(e)}
    
    async def get_yield_forecast(self, symbols: List[str], horizon: str = "12_months") -> Dict[str, Any]:
        """
        Get ML-powered yield forecasts for multiple symbols.
        
        Args:
            symbols: List of ticker symbols
            horizon: Prediction horizon (3_months, 6_months, 12_months, 24_months)
            
        Returns:
            Yield forecasts with confidence
        """
        try:
            logger.info(f"Getting yield forecasts for {len(symbols)} symbols")
            
            if len(symbols) == 1:
                result = self.client.predict_yield(symbols[0], horizon=horizon)
            else:
                result = self.client.predict_yield_batch(symbols, horizon=horizon)
            
            if result.get("success"):
                return result.get("data", {})
            
            return {"error": "Yield forecast unavailable"}
            
        except Exception as e:
            logger.error(f"Failed to get yield forecasts: {e}")
            return {"error": str(e)}
    
    async def get_payout_sustainability(self, symbols: List[str], horizon: str = "12_months") -> Dict[str, Any]:
        """
        Get ML-powered payout ratio sustainability analysis.
        
        Args:
            symbols: List of ticker symbols
            horizon: Prediction horizon
            
        Returns:
            Payout sustainability analysis
        """
        try:
            logger.info(f"Analyzing payout sustainability for {len(symbols)} symbols")
            
            if len(symbols) == 1:
                result = self.client.predict_payout_ratio(symbols[0], horizon=horizon)
            else:
                result = self.client.predict_payout_ratio_batch(symbols, horizon=horizon)
            
            if result.get("success"):
                return result.get("data", {})
            
            return {"error": "Payout analysis unavailable"}
            
        except Exception as e:
            logger.error(f"Failed to analyze payout sustainability: {e}")
            return {"error": str(e)}
    
    async def get_cluster_dashboard(self) -> Dict[str, Any]:
        """
        Get overview of all ML clusters and their characteristics.
        
        Perfect for "dividend market overview" or "what clusters exist" queries.
        
        Returns:
            Cluster dashboard with all cluster characteristics
        """
        if not self.ml_available or not self.client:
            logger.debug("ML API unavailable, skipping cluster dashboard")
            return {"success": False, "ml_available": False}
        
        try:
            logger.info("Getting cluster dashboard")
            
            result = self.client.get_cluster_dashboard()
            
            if result.get("success"):
                return result.get("data", {})
            
            return {"error": "Cluster dashboard unavailable"}
            
        except ValueError as e:
            logger.debug(f"ML API key missing: {e}")
            return {"success": False, "ml_available": False}
        except Exception as e:
            logger.error(f"Failed to get cluster dashboard: {e}")
            return {"error": str(e)}


# Global instance
_ml_integration = None


def get_ml_integration() -> MLIntegration:
    """Get or create global ML integration instance."""
    global _ml_integration
    if _ml_integration is None:
        _ml_integration = MLIntegration()
    return _ml_integration
