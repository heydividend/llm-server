#!/usr/bin/env python3
"""
Monitoring Setup for Harvey AI New Features
Sets up logging and monitoring for Video, Education, and Dividend Lists features
"""

import logging
from datetime import datetime
import json

class FeatureMonitor:
    """Monitor new Harvey AI features"""
    
    def __init__(self):
        self.logger = logging.getLogger("harvey.feature_monitor")
        self.metrics = {
            "video_searches": 0,
            "dividend_list_queries": 0,
            "education_triggers": 0,
            "errors": 0
        }
    
    def log_video_search(self, query: str, results_count: int, duration_ms: int):
        """Log video search request"""
        self.metrics["video_searches"] += 1
        self.logger.info(
            f"[VIDEO_SEARCH] query='{query}' results={results_count} duration={duration_ms}ms"
        )
    
    def log_dividend_list_query(self, category: str, results_count: int, duration_ms: int):
        """Log dividend list query"""
        self.metrics["dividend_list_queries"] += 1
        self.logger.info(
            f"[DIVIDEND_LIST] category='{category}' results={results_count} duration={duration_ms}ms"
        )
    
    def log_education_trigger(self, misconception_type: str, user_query: str):
        """Log investor education trigger"""
        self.metrics["education_triggers"] += 1
        self.logger.info(
            f"[EDUCATION] type='{misconception_type}' query='{user_query[:50]}...'"
        )
    
    def log_error(self, feature: str, error: str):
        """Log feature error"""
        self.metrics["errors"] += 1
        self.logger.error(
            f"[ERROR] feature='{feature}' error='{error}'"
        )
    
    def get_metrics(self) -> dict:
        """Get current metrics"""
        return {
            **self.metrics,
            "timestamp": datetime.now().isoformat()
        }
    
    def print_metrics_summary(self):
        """Print metrics summary"""
        print("\n" + "=" * 60)
        print("Harvey AI New Features - Metrics Summary")
        print("=" * 60)
        print(f"Video Searches:        {self.metrics['video_searches']}")
        print(f"Dividend List Queries: {self.metrics['dividend_list_queries']}")
        print(f"Education Triggers:    {self.metrics['education_triggers']}")
        print(f"Errors:                {self.metrics['errors']}")
        print("=" * 60 + "\n")


def setup_monitoring():
    """Setup monitoring for new features"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
        handlers=[
            logging.FileHandler('/tmp/harvey_features.log'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger("harvey.feature_monitor")
    logger.info("Feature monitoring initialized")
    
    return FeatureMonitor()


# Example usage for monitoring dashboard
def generate_monitoring_queries():
    """Generate SQL queries for monitoring dashboards"""
    
    queries = {
        "video_engagement": """
            SELECT 
                video_id,
                COUNT(*) as view_count,
                SUM(CASE WHEN clicked = 1 THEN 1 ELSE 0 END) as click_count,
                SUM(CASE WHEN helpful = 1 THEN 1 ELSE 0 END) as helpful_count
            FROM video_engagement
            WHERE created_date >= DATEADD(day, -7, GETDATE())
            GROUP BY video_id
            ORDER BY view_count DESC
        """,
        
        "dividend_list_popularity": """
            SELECT 
                category_id,
                COUNT(*) as list_count,
                SUM(stock_count) as total_stocks
            FROM dividend_lists
            WHERE created_date >= DATEADD(day, -30, GETDATE())
            GROUP BY category_id
            ORDER BY list_count DESC
        """,
        
        "user_feedback_summary": """
            SELECT 
                feedback_type,
                AVG(rating) as avg_rating,
                COUNT(*) as feedback_count
            FROM user_feedback
            WHERE created_date >= DATEADD(day, -7, GETDATE())
            GROUP BY feedback_type
        """,
        
        "watchlist_growth": """
            SELECT 
                CONVERT(date, added_date) as date,
                COUNT(*) as stocks_added
            FROM user_watchlist
            WHERE added_date >= DATEADD(day, -30, GETDATE())
            GROUP BY CONVERT(date, added_date)
            ORDER BY date DESC
        """
    }
    
    return queries


if __name__ == "__main__":
    # Setup monitoring
    monitor = setup_monitoring()
    
    # Example usage
    monitor.log_video_search("dividend investing", 3, 45)
    monitor.log_dividend_list_query("dividend_aristocrats", 20, 120)
    monitor.log_education_trigger("cusip_vs_ticker", "What is CUSIP 037833100?")
    
    # Print summary
    monitor.print_metrics_summary()
    
    print("\n📊 Monitoring Queries for Dashboards:")
    print("=" * 60)
    queries = generate_monitoring_queries()
    for name, query in queries.items():
        print(f"\n{name.upper().replace('_', ' ')}:")
        print(query.strip())
