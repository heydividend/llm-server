#!/usr/bin/env python3
"""
Harvey Dividend Intelligence System - Cron Version
Runs daily to scan for dividend news and store results in database
"""

import os
import json
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any
from collections import defaultdict, Counter
import re
import logging
import pymssql

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'server': os.getenv('SQLSERVER_HOST', 'heydividend.database.windows.net'),
    'database': os.getenv('SQLSERVER_DB', 'heydividend'),
    'username': os.getenv('SQLSERVER_USER', 'sqladmin'),
    'password': os.getenv('SQLSERVER_PASSWORD', ''),
    'timeout': 30,
    'login_timeout': 10,
    'charset': 'UTF-8'
}

class DividendIntelligenceScanner:
    """Daily dividend intelligence scanner"""
    
    def __init__(self):
        self.dividend_keywords = {
            'high_priority': [
                'dividend cut', 'dividend slash', 'suspend dividend', 
                'dividend increase', 'dividend raise', 'special dividend'
            ],
            'medium_priority': [
                'quarterly dividend', 'monthly dividend', 'dividend payment',
                'ex-dividend', 'dividend yield', 'dividend date'
            ],
            'low_priority': [
                'dividend stock', 'dividend aristocrat', 'dividend portfolio'
            ]
        }
    
    def connect_db(self):
        """Connect to Azure SQL database"""
        try:
            logger.info("Connecting to database...")
            return pymssql.connect(**DB_CONFIG)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
    
    def extract_tickers(self, text: str) -> List[str]:
        """Extract stock tickers from text"""
        tickers = []
        ticker_pattern = r'\$([A-Z]{1,5})\b|\(([A-Z]{1,5})\)'
        matches = re.findall(ticker_pattern, text.upper())
        tickers.extend([m for group in matches for m in group if m])
        
        # Common mappings
        company_map = {
            'APPLE': 'AAPL', 'MICROSOFT': 'MSFT', 'AMAZON': 'AMZN',
            'GOOGLE': 'GOOGL', 'NVIDIA': 'NVDA', 'TESLA': 'TSLA'
        }
        
        text_upper = text.upper()
        for company, ticker in company_map.items():
            if company in text_upper:
                tickers.append(ticker)
        
        return list(set(tickers))
    
    def calculate_relevance(self, text: str) -> float:
        """Calculate relevance score"""
        score = 0.0
        text_lower = text.lower()
        
        for keyword in self.dividend_keywords['high_priority']:
            if keyword in text_lower:
                score += 3.0
        
        for keyword in self.dividend_keywords['medium_priority']:
            if keyword in text_lower:
                score += 2.0
        
        for keyword in self.dividend_keywords['low_priority']:
            if keyword in text_lower:
                score += 1.0
        
        return min(score, 10.0)
    
    def analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment"""
        positive = ['increase', 'raise', 'boost', 'special', 'growth']
        negative = ['cut', 'reduce', 'slash', 'suspend', 'eliminate']
        
        text_lower = text.lower()
        pos_count = sum(1 for word in positive if word in text_lower)
        neg_count = sum(1 for word in negative if word in text_lower)
        
        if pos_count + neg_count == 0:
            return 0.0
        
        return (pos_count - neg_count) / (pos_count + neg_count)
    
    def run_scan(self) -> Dict[str, Any]:
        """Run dividend intelligence scan"""
        logger.info("Starting dividend intelligence scan...")
        
        # Simulated articles for demo (would connect to real news APIs)
        demo_articles = [
            {
                'title': f'Market Update: Dividend Stocks Show Strength',
                'content': 'Several dividend aristocrats announced increases today.',
                'source': 'MarketWatch',
                'published': datetime.now(timezone.utc) - timedelta(hours=3)
            },
            {
                'title': f'Apple Maintains Quarterly Dividend at $0.25',
                'content': 'Apple (AAPL) announced maintaining its dividend.',
                'source': 'Reuters',
                'published': datetime.now(timezone.utc) - timedelta(hours=1)
            }
        ]
        
        processed = []
        alerts = []
        trending = defaultdict(int)
        
        for article in demo_articles:
            text = f"{article['title']} {article['content']}"
            relevance = self.calculate_relevance(text)
            
            if relevance < 2:
                continue
            
            sentiment = self.analyze_sentiment(text)
            tickers = self.extract_tickers(text)
            
            for ticker in tickers:
                trending[ticker] += 1
            
            # Generate recommendation
            recommendation = ""
            requires_disclaimer = False
            
            if 'dividend increase' in article['title'].lower():
                recommendation = "BUY CONSIDERATION: Potential accumulation opportunity"
                requires_disclaimer = True
            elif 'dividend cut' in article['title'].lower():
                recommendation = "ACTION: Review position if holding"
            else:
                recommendation = "MONITOR: Track for developments"
            
            processed.append({
                'title': article['title'],
                'source': article['source'],
                'published': article['published'].isoformat(),
                'relevance_score': relevance,
                'sentiment_score': sentiment,
                'tickers': tickers,
                'recommendation': recommendation,
                'requires_disclaimer': requires_disclaimer
            })
            
            # Create alerts for high relevance
            if relevance >= 7:
                alerts.append({
                    'title': article['title'],
                    'priority': 'HIGH' if relevance >= 8 else 'MEDIUM',
                    'recommendation': recommendation
                })
        
        results = {
            'scan_timestamp': datetime.now(timezone.utc).isoformat(),
            'articles_processed': len(processed),
            'articles': processed[:10],
            'alerts': alerts,
            'trending_tickers': dict(trending),
            'statistics': {
                'positive_sentiment': sum(1 for a in processed if a['sentiment_score'] > 0.3),
                'negative_sentiment': sum(1 for a in processed if a['sentiment_score'] < -0.3),
                'unique_tickers': len(set(t for a in processed for t in a['tickers']))
            }
        }
        
        logger.info(f"Scan complete: {len(processed)} articles, {len(alerts)} alerts")
        return results
    
    def store_results(self, results: Dict):
        """Store scan results in database"""
        conn = self.connect_db()
        if not conn:
            logger.error("Cannot store results - no database connection")
            return
        
        try:
            cursor = conn.cursor()
            
            # Create table if not exists
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='dividend_intelligence' AND xtype='U')
                CREATE TABLE dividend_intelligence (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    scan_timestamp DATETIME,
                    articles_count INT,
                    alerts_count INT,
                    scan_data NVARCHAR(MAX),
                    created_at DATETIME DEFAULT GETDATE()
                )
            """)
            
            # Insert scan results
            cursor.execute("""
                INSERT INTO dividend_intelligence 
                (scan_timestamp, articles_count, alerts_count, scan_data)
                VALUES (%s, %s, %s, %s)
            """, (
                results['scan_timestamp'],
                results['articles_processed'],
                len(results['alerts']),
                json.dumps(results)
            ))
            
            conn.commit()
            logger.info("Results stored in database successfully")
            
            # Clean up old records (keep 30 days)
            cursor.execute("""
                DELETE FROM dividend_intelligence 
                WHERE created_at < DATEADD(day, -30, GETDATE())
            """)
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error storing results: {e}")
        finally:
            conn.close()
    
    def generate_summary(self, results: Dict) -> str:
        """Generate text summary of scan results"""
        summary = f"""
========================================
HARVEY DIVIDEND INTELLIGENCE REPORT
{results['scan_timestamp']}
========================================

📊 SCAN SUMMARY
Articles Processed: {results['articles_processed']}
Alerts Generated: {len(results['alerts'])}
Unique Tickers: {results['statistics']['unique_tickers']}

📈 SENTIMENT ANALYSIS
Positive: {results['statistics']['positive_sentiment']}
Negative: {results['statistics']['negative_sentiment']}
"""
        
        if results['alerts']:
            summary += "\n🚨 ALERTS:\n"
            for alert in results['alerts']:
                summary += f"• [{alert['priority']}] {alert['title']}\n"
                summary += f"  {alert['recommendation']}\n"
        
        if results['trending_tickers']:
            summary += "\n🔥 TRENDING TICKERS:\n"
            for ticker, count in sorted(results['trending_tickers'].items(), 
                                       key=lambda x: x[1], reverse=True)[:5]:
                summary += f"• {ticker}: {count} mentions\n"
        
        summary += """
========================================
This analysis is for educational purposes only.
Not financial advice. Consult your advisor.
========================================
"""
        return summary

def main():
    """Main execution function"""
    try:
        scanner = DividendIntelligenceScanner()
        
        # Run the scan
        results = scanner.run_scan()
        
        # Store in database
        scanner.store_results(results)
        
        # Generate and print summary
        summary = scanner.generate_summary(results)
        print(summary)
        
        # Save to file for Harvey API to read
        output_file = '/home/azureuser/harvey/dividend_intelligence/latest_scan.json'
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to {output_file}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())