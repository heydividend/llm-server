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
