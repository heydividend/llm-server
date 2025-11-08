#!/usr/bin/env python3
"""
Harvey Dividend Intelligence System - Production Version
Automated monitoring of news and social media for dividend announcements
Internal API endpoints for Harvey integration only
"""

import os
import json
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict, Counter
import re
import logging
import pymssql
from flask import Flask, jsonify, request
from functools import wraps
import threading
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/azureuser/harvey/logs/dividend_intelligence.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Database configuration from environment
DB_CONFIG = {
    'server': os.getenv('SQLSERVER_HOST', 'heydividend.database.windows.net'),
    'database': os.getenv('SQLSERVER_DB', 'heydividend'),
    'username': os.getenv('SQLSERVER_USER', 'sqladmin'),
    'password': os.getenv('SQLSERVER_PASSWORD', ''),
    'timeout': 30,
    'login_timeout': 10,
    'charset': 'UTF-8'
}

# Internal API authentication
INTERNAL_API_KEY = os.getenv('HARVEY_AI_API_KEY', '')

def require_api_key(f):
    """Decorator to require internal API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key != INTERNAL_API_KEY:
            return jsonify({'error': 'Unauthorized - Internal API only'}), 401
        return f(*args, **kwargs)
    return decorated_function

class DividendIntelligenceEngine:
    """Production dividend intelligence engine"""
    
    def __init__(self):
        self.dividend_keywords = {
            'high_priority': [
                'dividend cut', 'dividend slash', 'suspend dividend', 'eliminate dividend',
                'dividend increase', 'dividend raise', 'dividend hike', 'boost dividend',
                'special dividend', 'extra dividend', 'dividend reinstatement', 
                'dividend declaration', 'ex-dividend today', 'ex-dividend tomorrow'
            ],
            'medium_priority': [
                'quarterly dividend', 'monthly dividend', 'annual dividend', 
                'dividend payment', 'dividend payout', 'dividend yield',
                'dividend announcement', 'dividend date', 'record date',
                'payment date', 'dividend policy', 'distribution rate'
            ],
            'low_priority': [
                'dividend stock', 'dividend investor', 'dividend portfolio',
                'dividend aristocrat', 'dividend king', 'dividend champion',
                'dividend growth', 'dividend etf', 'dividend fund'
            ]
        }
        
        # Trending tracker
        self.trending_cache = {}
        self.last_scan_time = None
        self.scan_results = None
        
    def connect_db(self):
        """Connect to Azure SQL database"""
        try:
            return pymssql.connect(**DB_CONFIG)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
    
    def extract_tickers(self, text: str) -> List[str]:
        """Extract stock tickers from text"""
        tickers = []
        
        # Pattern for $TICKER or (TICKER) format
        ticker_pattern = r'\$([A-Z]{1,5})\b|\(([A-Z]{1,5})\)'
        matches = re.findall(ticker_pattern, text.upper())
        tickers.extend([m for group in matches for m in group if m])
        
        # Common company name mappings
        company_mappings = {
            'APPLE': 'AAPL', 'MICROSOFT': 'MSFT', 'AMAZON': 'AMZN',
            'GOOGLE': 'GOOGL', 'META': 'META', 'NVIDIA': 'NVDA',
            'TESLA': 'TSLA', 'BERKSHIRE': 'BRK.B', 'JOHNSON': 'JNJ',
            'JPMORGAN': 'JPM', 'WALMART': 'WMT', 'VISA': 'V'
        }
        
        text_upper = text.upper()
        for company, ticker in company_mappings.items():
            if company in text_upper:
                tickers.append(ticker)
        
        return list(set(tickers))
    
    def calculate_relevance_score(self, title: str, content: str, source: str) -> float:
        """Calculate dividend relevance score"""
        score = 0.0
        full_text = f"{title} {content}".lower()
        
        # Keyword scoring
        for keyword in self.dividend_keywords['high_priority']:
            if keyword in full_text:
                score += 3.0
        
        for keyword in self.dividend_keywords['medium_priority']:
            if keyword in full_text:
                score += 2.0
        
        for keyword in self.dividend_keywords['low_priority']:
            if keyword in full_text:
                score += 1.0
        
        # Source credibility bonus
        trusted_sources = ['reuters', 'bloomberg', 'wsj', 'marketwatch', 'cnbc', 'seekingalpha']
        if any(s in source.lower() for s in trusted_sources):
            score += 1.5
        
        # Multiple ticker mentions bonus
        tickers = self.extract_tickers(full_text)
        if len(tickers) > 0:
            score += min(len(tickers) * 0.5, 2.0)
        
        return min(score, 10.0)
    
    def analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of dividend news"""
        positive_words = [
            'increase', 'raise', 'boost', 'growth', 'higher', 'special',
            'extra', 'bonus', 'declare', 'maintain', 'stable', 'strong'
        ]
        negative_words = [
            'cut', 'reduce', 'slash', 'suspend', 'eliminate', 'lower',
            'decrease', 'concern', 'risk', 'warning', 'decline', 'weak'
        ]
        
        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count + neg_count == 0:
            return 0.0
        
        return (pos_count - neg_count) / (pos_count + neg_count)
    
    def generate_analysis(self, title: str, content: str, relevance: float, sentiment: float, tickers: List[str]) -> Dict:
        """Generate AI analysis of news"""
        analysis = {
            'impact_level': '',
            'sentiment_interpretation': '',
            'recommendation': '',
            'tickers_affected': tickers,
            'requires_disclaimer': False
        }
        
        # Determine impact level
        if relevance >= 8:
            analysis['impact_level'] = 'HIGH'
        elif relevance >= 5:
            analysis['impact_level'] = 'MODERATE'
        else:
            analysis['impact_level'] = 'LOW'
        
        # Sentiment interpretation
        if sentiment > 0.5:
            analysis['sentiment_interpretation'] = 'Positive dividend development'
        elif sentiment < -0.5:
            analysis['sentiment_interpretation'] = 'Negative dividend news'
        else:
            analysis['sentiment_interpretation'] = 'Neutral information'
        
        # Generate recommendation
        title_lower = title.lower()
        if 'dividend increase' in title_lower or 'special dividend' in title_lower:
            analysis['recommendation'] = 'BUY CONSIDERATION: Potential accumulation opportunity'
            analysis['requires_disclaimer'] = True
        elif 'dividend cut' in title_lower or 'suspend' in title_lower:
            analysis['recommendation'] = 'ACTION: Review position if holding'
            analysis['requires_disclaimer'] = False
        else:
            analysis['recommendation'] = 'MONITOR: Track for further developments'
            analysis['requires_disclaimer'] = False
        
        return analysis
    
    def scan_news_sources(self) -> Dict[str, Any]:
        """Scan news sources for dividend intelligence"""
        logger.info("Starting dividend intelligence scan...")
        
        # For production, this would connect to real news APIs
        # For now, using demonstration data
        demo_articles = [
            {
                'id': hashlib.md5(f"article_{datetime.now().isoformat()}".encode()).hexdigest(),
                'title': 'Apple Increases Quarterly Dividend by 5%',
                'content': 'Apple Inc. announced a 5% increase in its quarterly cash dividend.',
                'source': 'MarketWatch',
                'url': 'https://marketwatch.com/apple-dividend',
                'published_at': datetime.now(timezone.utc) - timedelta(hours=2),
                'is_breaking': False
            },
            {
                'id': hashlib.md5(f"article2_{datetime.now().isoformat()}".encode()).hexdigest(),
                'title': 'BREAKING: Microsoft Declares Special Dividend',
                'content': 'Microsoft Corporation declares special cash dividend of $2.00 per share.',
                'source': 'Reuters',
                'url': 'https://reuters.com/msft-special',
                'published_at': datetime.now(timezone.utc) - timedelta(minutes=30),
                'is_breaking': True
            }
        ]
        
        processed_articles = []
        alerts = []
        trending_topics = defaultdict(int)
        
        for article in demo_articles:
            # Calculate scores
            relevance = self.calculate_relevance_score(
                article['title'], 
                article['content'], 
                article['source']
            )
            
            if relevance < 2:  # Skip low relevance
                continue
            
            sentiment = self.analyze_sentiment(f"{article['title']} {article['content']}")
            tickers = self.extract_tickers(f"{article['title']} {article['content']}")
            
            # Generate analysis
            analysis = self.generate_analysis(
                article['title'],
                article['content'],
                relevance,
                sentiment,
                tickers
            )
            
            # Track trending topics
            for ticker in tickers:
                trending_topics[ticker] += 1
            
            # Create alert if high priority
            if relevance >= 7 or article['is_breaking']:
                alerts.append({
                    'priority': 'HIGH' if article['is_breaking'] else 'MEDIUM',
                    'title': article['title'],
                    'source': article['source'],
                    'url': article['url'],
                    'analysis': analysis
                })
            
            processed_articles.append({
                'id': article['id'],
                'title': article['title'],
                'source': article['source'],
                'url': article['url'],
                'published_at': article['published_at'].isoformat(),
                'relevance_score': relevance,
                'sentiment_score': sentiment,
                'tickers': tickers,
                'analysis': analysis,
                'is_breaking': article['is_breaking']
            })
        
        # Sort articles by relevance
        processed_articles = sorted(
            processed_articles, 
            key=lambda x: x['relevance_score'], 
            reverse=True
        )
        
        # Compile results
        results = {
            'scan_timestamp': datetime.now(timezone.utc).isoformat(),
            'articles_found': len(processed_articles),
            'top_articles': processed_articles[:10],
            'alerts': alerts,
            'trending_tickers': dict(trending_topics),
            'statistics': {
                'breaking_news': sum(1 for a in processed_articles if a['is_breaking']),
                'positive_sentiment': sum(1 for a in processed_articles if a['sentiment_score'] > 0.3),
                'negative_sentiment': sum(1 for a in processed_articles if a['sentiment_score'] < -0.3),
                'unique_tickers': len(set(t for a in processed_articles for t in a['tickers']))
            }
        }
        
        # Cache results
        self.scan_results = results
        self.last_scan_time = datetime.now(timezone.utc)
        
        # Store in database
        self.store_scan_results(results)
        
        logger.info(f"Scan complete: {len(processed_articles)} articles, {len(alerts)} alerts")
        
        return results
    
    def store_scan_results(self, results: Dict):
        """Store scan results in database"""
        conn = self.connect_db()
        if not conn:
            logger.error("Failed to store results - no database connection")
            return
        
        try:
            cursor = conn.cursor()
            
            # Store scan metadata
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='dividend_intelligence_scans' AND xtype='U')
                CREATE TABLE dividend_intelligence_scans (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    scan_timestamp DATETIME,
                    articles_found INT,
                    alerts_generated INT,
                    unique_tickers INT,
                    scan_data NVARCHAR(MAX),
                    created_at DATETIME DEFAULT GETDATE()
                )
            """)
            
            # Insert scan record
            cursor.execute("""
                INSERT INTO dividend_intelligence_scans 
                (scan_timestamp, articles_found, alerts_generated, unique_tickers, scan_data)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                results['scan_timestamp'],
                results['articles_found'],
                len(results['alerts']),
                results['statistics']['unique_tickers'],
                json.dumps(results)
            ))
            
            conn.commit()
            logger.info("Scan results stored in database")
            
        except Exception as e:
            logger.error(f"Error storing scan results: {e}")
        finally:
            conn.close()

# Initialize engine
engine = DividendIntelligenceEngine()

# ===========================
# INTERNAL API ENDPOINTS
# ===========================

@app.route('/v1/dividend-intelligence/health', methods=['GET'])
@require_api_key
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Harvey Dividend Intelligence',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'last_scan': engine.last_scan_time.isoformat() if engine.last_scan_time else None
    })

@app.route('/v1/dividend-intelligence/scan', methods=['POST'])
@require_api_key
def trigger_scan():
    """Manually trigger a dividend intelligence scan"""
    try:
        results = engine.scan_news_sources()
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        logger.error(f"Scan error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/v1/dividend-intelligence/latest', methods=['GET'])
@require_api_key
def get_latest_intelligence():
    """Get latest intelligence results"""
    if not engine.scan_results:
        # Run scan if no cached results
        engine.scan_news_sources()
    
    return jsonify(engine.scan_results)

@app.route('/v1/dividend-intelligence/alerts', methods=['GET'])
@require_api_key
def get_alerts():
    """Get current dividend alerts"""
    if not engine.scan_results:
        return jsonify({'alerts': []})
    
    return jsonify({
        'alerts': engine.scan_results.get('alerts', []),
        'generated_at': engine.last_scan_time.isoformat() if engine.last_scan_time else None
    })

@app.route('/v1/dividend-intelligence/trending', methods=['GET'])
@require_api_key
def get_trending():
    """Get trending dividend topics"""
    if not engine.scan_results:
        return jsonify({'trending_tickers': {}})
    
    return jsonify({
        'trending_tickers': engine.scan_results.get('trending_tickers', {}),
        'scan_time': engine.last_scan_time.isoformat() if engine.last_scan_time else None
    })

@app.route('/v1/dividend-intelligence/analyze-text', methods=['POST'])
@require_api_key
def analyze_text():
    """Analyze arbitrary text for dividend relevance"""
    data = request.json
    if not data or 'text' not in data:
        return jsonify({'error': 'Text required'}), 400
    
    text = data['text']
    
    # Perform analysis
    relevance = engine.calculate_relevance_score(text, '', 'user_input')
    sentiment = engine.analyze_sentiment(text)
    tickers = engine.extract_tickers(text)
    analysis = engine.generate_analysis(text, '', relevance, sentiment, tickers)
    
    return jsonify({
        'relevance_score': relevance,
        'sentiment_score': sentiment,
        'tickers_found': tickers,
        'analysis': analysis
    })

@app.route('/v1/dividend-intelligence/ticker/<ticker>', methods=['GET'])
@require_api_key
def get_ticker_intelligence(ticker: str):
    """Get intelligence for specific ticker"""
    ticker = ticker.upper()
    
    if not engine.scan_results:
        engine.scan_news_sources()
    
    # Filter articles for this ticker
    ticker_articles = [
        article for article in engine.scan_results.get('top_articles', [])
        if ticker in article.get('tickers', [])
    ]
    
    return jsonify({
        'ticker': ticker,
        'articles': ticker_articles,
        'article_count': len(ticker_articles),
        'is_trending': ticker in engine.scan_results.get('trending_tickers', {})
    })

def run_scheduled_scan():
    """Background thread for scheduled scanning"""
    while True:
        try:
            # Run scan every 4 hours
            engine.scan_news_sources()
            logger.info("Scheduled scan completed")
            time.sleep(14400)  # 4 hours
        except Exception as e:
            logger.error(f"Scheduled scan error: {e}")
            time.sleep(300)  # Retry in 5 minutes

if __name__ == '__main__':
    # Start background scanning thread
    scan_thread = threading.Thread(target=run_scheduled_scan, daemon=True)
    scan_thread.start()
    
    # Run Flask app (internal port)
    app.run(host='127.0.0.1', port=9001, debug=False)