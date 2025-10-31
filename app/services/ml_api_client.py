"""
ML API Client Service for HeyDividend Internal ML API.

Provides ML-powered dividend predictions and analysis including:
- Payout ratings
- Yield forecasts
- Cut risk analysis
- Anomaly detection
- Comprehensive scores
"""

import os
import logging
from typing import List, Optional, Dict, Any
import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("ml_api_client")

DEV_BASE_URL = "https://2657f601-b8fe-40bd-8b9b-bdce950dabad-00-3ihusjg16z2it.janeway.replit.dev/api/internal/ml"
PROD_BASE_URL = "https://hd-test.replit.app/api/internal/ml"


class MLAPIClient:
    """Client for HeyDividend Internal ML API with connection pooling and retry logic."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize ML API client.
        
        Args:
            api_key: API key for authentication (defaults to INTERNAL_ML_API_KEY env var)
            base_url: Base URL for API (defaults to ML_API_BASE_URL env var or DEV URL)
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum number of retries for failed requests (default: 3)
        """
        self.api_key = api_key or os.getenv("INTERNAL_ML_API_KEY")
        self.base_url = base_url or os.getenv("ML_API_BASE_URL") or DEV_BASE_URL
        self.timeout = timeout
        self.max_retries = max_retries
        
        if not self.api_key:
            logger.warning("ML API key not found. Set INTERNAL_ML_API_KEY environment variable.")
        
        self.client = httpx.Client(
            timeout=timeout,
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
            transport=httpx.HTTPTransport(retries=max_retries)
        )
        
        logger.info(f"ML API client initialized with base URL: {self.base_url}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        if not self.api_key:
            raise ValueError("ML API key is required but not set. Set INTERNAL_ML_API_KEY environment variable.")
        return {
            "X-Internal-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make POST request to ML API endpoint.
        
        Args:
            endpoint: API endpoint path (e.g., "/payout-rating")
            payload: Request payload
            
        Returns:
            Parsed JSON response
            
        Raises:
            Exception: On API errors
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.info(f"ML API request: {endpoint} with {len(payload.get('symbols', []))} symbols")
            
            response = self.client.post(
                url,
                json=payload,
                headers=self._get_headers()
            )
            
            if response.status_code == 401:
                logger.error("ML API: Unauthorized - Invalid or missing API key")
                raise Exception("ML API authentication failed: Invalid or missing API key")
            
            elif response.status_code == 403:
                logger.error("ML API: Forbidden - API key does not have access")
                raise Exception("ML API access denied: API key does not have permission")
            
            elif response.status_code == 429:
                logger.error("ML API: Rate limit exceeded")
                raise Exception("ML API rate limit exceeded. Please try again later.")
            
            elif response.status_code >= 500:
                logger.error(f"ML API: Server error ({response.status_code})")
                raise Exception(f"ML API server error: {response.status_code}")
            
            elif response.status_code != 200:
                logger.error(f"ML API: Unexpected error ({response.status_code})")
                raise Exception(f"ML API error: {response.status_code}")
            
            data = response.json()
            
            if not data.get("success"):
                error_msg = data.get("error", "Unknown error")
                logger.error(f"ML API returned error: {error_msg}")
                raise Exception(f"ML API error: {error_msg}")
            
            logger.info(f"ML API request successful: {endpoint}")
            return data
            
        except httpx.TimeoutException:
            logger.error(f"ML API timeout for {endpoint}")
            raise Exception("ML API request timed out. Please try again.")
        
        except httpx.RequestError as e:
            logger.error(f"ML API request error: {e}")
            raise Exception(f"ML API connection error: {str(e)}")
        
        except Exception as e:
            if "ML API" in str(e):
                raise
            logger.error(f"Unexpected error in ML API request: {e}")
            raise Exception(f"ML API error: {str(e)}")
    
    def get_payout_rating(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Get dividend payout sustainability ratings (0-100 scale).
        
        Args:
            symbols: List of ticker symbols (max 100)
            
        Returns:
            Response with payout ratings for each symbol
            
        Example:
            >>> client.get_payout_rating(["AAPL", "MSFT"])
            {
                "success": true,
                "data": [
                    {
                        "symbol": "AAPL",
                        "payout_rating": 92.5,
                        "rating_label": "Excellent",
                        "confidence": 0.87
                    }
                ]
            }
        """
        if len(symbols) > 100:
            raise ValueError("Maximum 100 symbols allowed per request")
        
        return self._make_request("/payout-rating", {"symbols": symbols})
    
    def get_yield_forecast(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Predict future dividend growth rates.
        
        Args:
            symbols: List of ticker symbols (max 100)
            
        Returns:
            Response with growth rate predictions for each symbol
            
        Example:
            >>> client.get_yield_forecast(["AAPL", "MSFT"])
            {
                "success": true,
                "data": [
                    {
                        "symbol": "AAPL",
                        "current_yield": 0.52,
                        "predicted_growth_rate": 8.5,
                        "confidence": 0.82
                    }
                ]
            }
        """
        if len(symbols) > 100:
            raise ValueError("Maximum 100 symbols allowed per request")
        
        return self._make_request("/yield-forecast", {"symbols": symbols})
    
    def get_cut_risk(
        self,
        symbols: List[str],
        include_earnings: bool = True
    ) -> Dict[str, Any]:
        """
        Predict probability of dividend cuts in the next 12 months.
        
        Args:
            symbols: List of ticker symbols (max 100)
            include_earnings: Include earnings analysis (default: True)
            
        Returns:
            Response with cut risk scores for each symbol
            
        Example:
            >>> client.get_cut_risk(["AAPL", "TSLY"], include_earnings=True)
            {
                "success": true,
                "data": [
                    {
                        "symbol": "TSLY",
                        "cut_risk_score": 0.67,
                        "risk_level": "high",
                        "confidence": 0.84,
                        "risk_factors": ["high_payout_ratio", "declining_nav"]
                    }
                ]
            }
        """
        if len(symbols) > 100:
            raise ValueError("Maximum 100 symbols allowed per request")
        
        return self._make_request("/cut-risk", {
            "symbols": symbols,
            "include_earnings": include_earnings
        })
    
    def check_anomalies(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Detect unusual dividend payment patterns, cuts, or suspensions.
        
        Args:
            symbols: List of ticker symbols (max 100)
            
        Returns:
            Response with anomaly detection results for each symbol
            
        Example:
            >>> client.check_anomalies(["AAPL", "TSLY"])
            {
                "success": true,
                "data": [
                    {
                        "symbol": "TSLY",
                        "has_anomaly": true,
                        "anomaly_score": 0.89,
                        "anomaly_type": "unusual_payout_pattern",
                        "confidence": 0.91
                    }
                ]
            }
        """
        if len(symbols) > 100:
            raise ValueError("Maximum 100 symbols allowed per request")
        
        return self._make_request("/anomaly-check", {"symbols": symbols})
    
    def get_comprehensive_score(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Get overall dividend quality score combining all ML models.
        
        Args:
            symbols: List of ticker symbols (max 50)
            
        Returns:
            Response with comprehensive scores for each symbol
            
        Example:
            >>> client.get_comprehensive_score(["AAPL", "JNJ"])
            {
                "success": true,
                "data": [
                    {
                        "symbol": "AAPL",
                        "overall_score": 87.5,
                        "recommendation": "strong_buy",
                        "confidence": 0.85
                    }
                ]
            }
        """
        if len(symbols) > 50:
            raise ValueError("Maximum 50 symbols allowed per request (compute-intensive)")
        
        return self._make_request("/score", {"symbols": symbols})
    
    def batch_predict(
        self,
        symbols: List[str],
        models: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run multiple ML models in a single request for efficiency.
        
        Args:
            symbols: List of ticker symbols (max 50)
            models: List of model names to run (default: all models)
                   Available: ["payout_rating", "yield_forecast", "cut_risk", "anomaly"]
            
        Returns:
            Response with predictions from all requested models
            
        Example:
            >>> client.batch_predict(["AAPL", "MSFT"], models=["payout_rating", "cut_risk"])
            {
                "success": true,
                "data": {
                    "symbols": ["AAPL", "MSFT"],
                    "payout_ratings": [...],
                    "cut_risks": [...]
                }
            }
        """
        if len(symbols) > 50:
            raise ValueError("Maximum 50 symbols allowed per request")
        
        payload = {"symbols": symbols}
        if models:
            payload["models"] = models
        
        return self._make_request("/batch-predict", payload)
    
    def score_symbol(self, symbol: str) -> Dict[str, Any]:
        """
        Score a single stock for dividend quality and sustainability.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dividend quality score with breakdown
            
        Example:
            >>> client.score_symbol("AAPL")
            {
                "symbol": "AAPL",
                "score": 87.5,
                "factors": {
                    "payout_sustainability": 92,
                    "growth_consistency": 85,
                    "yield_stability": 88,
                    "financial_health": 95
                },
                "grade": "A"
            }
        """
        return self._make_request("/score/symbol", {"symbol": symbol})
    
    def score_portfolio(self, portfolio_id: int) -> Dict[str, Any]:
        """
        Score an entire portfolio with aggregated ML metrics.
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            Portfolio score with risk metrics
        """
        return self._make_request("/score/portfolio", {"portfolio_id": portfolio_id})
    
    def score_watchlist(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Score all symbols in a watchlist.
        
        Args:
            symbols: List of ticker symbols
            
        Returns:
            Scores for all symbols with summary
        """
        return self._make_request("/score/watchlist", {"symbols": symbols})
    
    def score_batch(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Batch score up to 100 symbols in a single request.
        
        Args:
            symbols: List of ticker symbols (max 100)
            
        Returns:
            Batch scoring results
        """
        if len(symbols) > 100:
            raise ValueError("Maximum 100 symbols allowed per batch request")
        
        return self._make_request("/score/batch", {"symbols": symbols})
    
    def predict_yield(self, symbol: str, horizon: str = "12_months") -> Dict[str, Any]:
        """
        Predict future dividend yield using ML regression models.
        
        Args:
            symbol: Stock ticker symbol
            horizon: Prediction horizon (3_months, 6_months, 12_months, 24_months)
            
        Returns:
            Yield prediction with confidence
        """
        return self._make_request("/predict/yield", {
            "symbol": symbol,
            "horizon": horizon
        })
    
    def predict_growth_rate(self, symbol: str) -> Dict[str, Any]:
        """
        Predict dividend growth rate.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Growth rate prediction with confidence
        """
        return self._make_request("/predict/growth-rate", {"symbol": symbol})
    
    def predict_payout_ratio(self, symbol: str, horizon: str = "12_months") -> Dict[str, Any]:
        """
        Forecast future payout ratio sustainability.
        
        Args:
            symbol: Stock ticker symbol
            horizon: Prediction horizon (3_months, 6_months, 12_months, 24_months)
            
        Returns:
            Payout ratio prediction with sustainability rating
        """
        return self._make_request("/predict/payout-ratio", {
            "symbol": symbol,
            "horizon": horizon
        })
    
    def predict_yield_batch(self, symbols: List[str], horizon: str = "12_months") -> Dict[str, Any]:
        """
        Batch yield predictions for multiple symbols.
        
        Args:
            symbols: List of ticker symbols
            horizon: Prediction horizon
            
        Returns:
            Batch yield predictions
        """
        return self._make_request("/predict/yield/batch", {
            "symbols": symbols,
            "horizon": horizon
        })
    
    def predict_payout_ratio_batch(self, symbols: List[str], horizon: str = "12_months") -> Dict[str, Any]:
        """
        Batch payout ratio predictions.
        
        Args:
            symbols: List of ticker symbols
            horizon: Prediction horizon
            
        Returns:
            Batch payout ratio predictions
        """
        return self._make_request("/predict/payout-ratio/batch", {
            "symbols": symbols,
            "horizon": horizon
        })
    
    def cluster_analyze_stock(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze stock characteristics using K-means clustering.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Cluster analysis with peers
        """
        return self._make_request("/cluster/analyze-stock", {"symbol": symbol})
    
    def cluster_find_similar(self, symbol: str, limit: int = 10) -> Dict[str, Any]:
        """
        Find stocks similar to a given symbol using ML clustering.
        
        Args:
            symbol: Stock ticker symbol
            limit: Maximum number of similar stocks to return
            
        Returns:
            Similar stocks with similarity scores
        """
        return self._make_request("/cluster/find-similar", {
            "symbol": symbol,
            "limit": limit
        })
    
    def cluster_optimize_portfolio(
        self,
        portfolio_id: int,
        optimization_goal: str = "maximize_yield",
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get ML-driven portfolio optimization suggestions.
        
        Args:
            portfolio_id: Portfolio ID
            optimization_goal: Goal (maximize_yield, minimize_risk, etc.)
            constraints: Optimization constraints
            
        Returns:
            Portfolio optimization suggestions
        """
        payload = {
            "portfolio_id": portfolio_id,
            "optimization_goal": optimization_goal
        }
        if constraints:
            payload["constraints"] = constraints
        
        return self._make_request("/cluster/optimize-portfolio", payload)
    
    def cluster_portfolio_diversification(self, portfolio_id: int) -> Dict[str, Any]:
        """
        Analyze portfolio diversification across ML clusters.
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            Diversification analysis with recommendations
        """
        return self._make_request("/cluster/portfolio-diversification", {
            "portfolio_id": portfolio_id
        })
    
    def get_cluster_dashboard(self) -> Dict[str, Any]:
        """
        Get overview of all ML clusters and their characteristics.
        
        Returns:
            Cluster dashboard data
        """
        try:
            url = f"{self.base_url}/cluster/dashboard"
            response = self.client.get(url, headers=self._get_headers())
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Cluster dashboard request failed: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to get cluster dashboard: {e}")
            raise
    
    def get_cluster_portfolio_detail(self, portfolio_id: int) -> Dict[str, Any]:
        """
        Get cluster analysis for a specific portfolio.
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            Detailed cluster breakdown
        """
        try:
            url = f"{self.base_url}/cluster/portfolio/{portfolio_id}"
            response = self.client.get(url, headers=self._get_headers())
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Cluster portfolio detail request failed: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to get cluster portfolio detail: {e}")
            raise
    
    def get_models_regression_performance(self) -> Dict[str, Any]:
        """
        Get performance metrics for ML regression models.
        
        Returns:
            Regression model performance metrics
        """
        try:
            url = f"{self.base_url}/models/regression/performance"
            response = self.client.get(url, headers=self._get_headers())
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Model performance request failed: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to get model performance: {e}")
            raise
    
    def get_models_timeseries_performance(self) -> Dict[str, Any]:
        """
        Get performance metrics for time-series models.
        
        Returns:
            Time-series model performance metrics
        """
        try:
            url = f"{self.base_url}/models/timeseries/performance"
            response = self.client.get(url, headers=self._get_headers())
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Model performance request failed: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to get model performance: {e}")
            raise
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get ML API usage statistics for the current user.
        
        Returns:
            Usage statistics and limits
        """
        try:
            url = f"{self.base_url}/usage-stats"
            response = self.client.get(url, headers=self._get_headers())
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Usage stats request failed: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}")
            raise
    
    def get_symbol_insights(self, symbol: str) -> Dict[str, Any]:
        """
        Get advanced ML-powered insights for a specific symbol.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Comprehensive ML insights
        """
        try:
            url = f"{self.base_url}/insights/{symbol}"
            response = self.client.get(url, headers=self._get_headers())
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Symbol insights request failed: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to get symbol insights: {e}")
            raise
    
    def get_prediction_history(self, symbol: str) -> Dict[str, Any]:
        """
        Get recent prediction history for a symbol.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Recent prediction history with accuracy metrics
        """
        try:
            url = f"{self.base_url}/predictions/{symbol}/recent"
            response = self.client.get(url, headers=self._get_headers())
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Prediction history request failed: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to get prediction history: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if the ML service is available and healthy.
        
        Returns:
            Health status response
            
        Example:
            >>> client.health_check()
            {
                "success": true,
                "status": "healthy",
                "service": "HeyDividend ML API"
            }
        """
        try:
            url = f"{self.base_url}/health"
            response = self.client.get(url)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "success": False,
                    "status": "unhealthy",
                    "error": f"Health check failed with status {response.status_code}"
                }
        except Exception as e:
            logger.error(f"ML API health check failed: {e}")
            return {
                "success": False,
                "status": "unhealthy",
                "error": str(e)
            }
    
    def close(self):
        """Close the HTTP client connection pool."""
        self.client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close client."""
        self.close()


_global_client = None


def get_ml_client() -> MLAPIClient:
    """
    Get or create a global ML API client instance (singleton pattern).
    
    Returns:
        MLAPIClient instance
    """
    global _global_client
    if _global_client is None:
        _global_client = MLAPIClient()
    return _global_client
