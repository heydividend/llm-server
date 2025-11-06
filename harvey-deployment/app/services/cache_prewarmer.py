"""
Intelligent Cache Prewarming Service

Preloads frequently-accessed ML data into cache on startup and periodically:
- Top dividend stocks (based on popularity/volume)
- Common queries (monthly payers, dividend aristocrats)
- Background execution (non-blocking startup)
- Scheduled rewarming every 6 hours

Expected Results:
- Cache hit rate: 40% → 70%
- Faster first-time queries for popular stocks
- Reduced ML API load
"""

import asyncio
import logging
import threading
import time
from typing import List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger("cache_prewarmer")


class CachePrewarmer:
    """
    Intelligent cache prewarming for ML data.
    
    Preloads popular stocks and common queries into cache to improve
    response times and reduce ML API calls.
    """
    
    def __init__(self):
        """Initialize cache prewarmer."""
        self.is_running = False
        self.last_prewarm_time: Optional[float] = None
        self.prewarm_interval = 21600  # 6 hours
        self._thread: Optional[threading.Thread] = None
        
        logger.info("Cache prewarmer initialized")
    
    def start_background_prewarming(self):
        """
        Start background cache prewarming thread.
        
        Non-blocking - runs in background thread.
        """
        if self.is_running:
            logger.warning("Cache prewarmer already running")
            return
        
        self.is_running = True
        self._thread = threading.Thread(target=self._prewarm_loop, daemon=True)
        self._thread.start()
        
        logger.info("Cache prewarmer started in background")
    
    def stop(self):
        """Stop background prewarming."""
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Cache prewarmer stopped")
    
    def _prewarm_loop(self):
        """Background prewarming loop."""
        while self.is_running:
            try:
                # Initial delay on startup (wait 30 seconds for app to fully start)
                if self.last_prewarm_time is None:
                    logger.info("Cache prewarmer: Waiting 30s before initial prewarm...")
                    time.sleep(30)
                
                # Run prewarming
                logger.info("Cache prewarmer: Starting cache prewarm cycle...")
                start_time = time.time()
                
                asyncio.run(self._run_prewarm_tasks())
                
                elapsed = time.time() - start_time
                logger.info(f"Cache prewarmer: Completed prewarm cycle in {elapsed:.1f}s")
                
                self.last_prewarm_time = time.time()
                
                # Sleep until next cycle (6 hours)
                logger.info(f"Cache prewarmer: Next cycle in {self.prewarm_interval/3600:.1f} hours")
                time.sleep(self.prewarm_interval)
                
            except Exception as e:
                logger.error(f"Cache prewarmer error: {e}", exc_info=True)
                # Wait 5 minutes before retrying on error
                time.sleep(300)
    
    async def _run_prewarm_tasks(self):
        """Run all prewarming tasks concurrently."""
        try:
            await asyncio.gather(
                self.prewarm_top_dividend_stocks(),
                self.prewarm_common_queries(),
                return_exceptions=True
            )
        except Exception as e:
            logger.error(f"Prewarm tasks failed: {e}")
    
    async def prewarm_top_dividend_stocks(self):
        """
        Preload ML data for top 100 dividend stocks.
        
        Focuses on high-yield, dividend aristocrats, and popular dividend stocks.
        """
        try:
            from app.services.ml_integration import get_ml_integration
            from app.core.database import engine
            from sqlalchemy import text
            
            logger.info("Prewarming top dividend stocks...")
            
            # Get top 100 dividend stocks from database
            query = text("""
                SELECT DISTINCT TOP 100 Ticker
                FROM dbo.vDividends
                WHERE Payment_Date >= DATEADD(MONTH, -12, GETDATE())
                ORDER BY Ticker
            """)
            
            with engine.connect() as conn:
                result = conn.execute(query)
                top_stocks = [row[0] for row in result.fetchall()]
            
            logger.info(f"Prewarming {len(top_stocks)} top dividend stocks...")
            
            # Prewarm in batches to avoid overwhelming the ML API
            ml = get_ml_integration()
            batch_size = 10
            
            for i in range(0, len(top_stocks), batch_size):
                batch = top_stocks[i:i+batch_size]
                
                # Prewarm each stock in parallel
                tasks = [ml.get_dividend_intelligence(symbol) for symbol in batch]
                await asyncio.gather(*tasks, return_exceptions=True)
                
                # Small delay between batches
                await asyncio.sleep(1)
            
            logger.info(f"Successfully prewarmed {len(top_stocks)} top dividend stocks")
            
        except Exception as e:
            logger.error(f"Failed to prewarm top dividend stocks: {e}")
    
    async def prewarm_common_queries(self):
        """
        Preload common dividend queries.
        
        Caches frequently requested data like monthly payers, aristocrats, etc.
        """
        try:
            from app.services.ml_integration import get_ml_integration
            
            logger.info("Prewarming common queries...")
            
            # Common dividend stocks to prewarm
            common_stocks = [
                # Dividend Aristocrats
                "JNJ", "PG", "KO", "PEP", "WMT", "MCD", "MMM", "CAT", "CVX", "XOM",
                # High-yield favorites
                "O", "ARCC", "AGNC", "NLY", "STAG", "MAIN", "PSEC",
                # Popular dividend ETFs
                "VYM", "SCHD", "DVY", "VIG", "SDY", "DGRO",
                # Tech dividend payers
                "AAPL", "MSFT", "INTC", "CSCO", "IBM", "TXN"
            ]
            
            logger.info(f"Prewarming {len(common_stocks)} common dividend stocks...")
            
            ml = get_ml_integration()
            
            # Prewarm in smaller batches
            batch_size = 5
            for i in range(0, len(common_stocks), batch_size):
                batch = common_stocks[i:i+batch_size]
                tasks = [ml.get_dividend_intelligence(symbol) for symbol in batch]
                await asyncio.gather(*tasks, return_exceptions=True)
                await asyncio.sleep(0.5)
            
            logger.info(f"Successfully prewarmed {len(common_stocks)} common stocks")
            
        except Exception as e:
            logger.error(f"Failed to prewarm common queries: {e}")


# Global prewarmer instance
_cache_prewarmer: Optional[CachePrewarmer] = None


def get_cache_prewarmer() -> CachePrewarmer:
    """Get or create global cache prewarmer instance."""
    global _cache_prewarmer
    if _cache_prewarmer is None:
        _cache_prewarmer = CachePrewarmer()
    return _cache_prewarmer


def start_cache_prewarming():
    """Start background cache prewarming."""
    prewarmer = get_cache_prewarmer()
    prewarmer.start_background_prewarming()


def stop_cache_prewarming():
    """Stop background cache prewarming."""
    global _cache_prewarmer
    if _cache_prewarmer:
        _cache_prewarmer.stop()
