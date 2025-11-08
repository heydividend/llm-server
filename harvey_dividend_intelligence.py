#!/usr/bin/env python3
"""
Harvey Dividend Intelligence System
Automated monitoring of news, social media, and RSS feeds for dividend announcements
Identifies trending dividend topics before they become mainstream
"""

import os
import json
import hashlib
import asyncio
import aiohttp
import feedparser
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
import re
import logging
from dataclasses import dataclass, asdict
import sqlite3
from urllib.parse import urlparse
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class NewsArticle:
    """Structured news article data"""
    id: str
    title: str
    description: str
    url: str
    source: str
    published_at: datetime
    relevance_score: float
    sentiment_score: float
    tickers_mentioned: List[str]
    dividend_keywords: List[str]
    trend_score: float
    is_breaking: bool
    analysis: str = ""
    category: str = ""

class DividendIntelligenceSystem:
    """Harvey's automated dividend news intelligence system"""
    
    def __init__(self):
        # API keys from environment
        self.newsapi_key = os.getenv('NEWSAPI_KEY', 'demo_key')
        self.reddit_client_id = os.getenv('REDDIT_CLIENT_ID', '')
        self.reddit_client_secret = os.getenv('REDDIT_CLIENT_SECRET', '')
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_KEY', '')
        
        # Initialize database
        self.db_path = 'dividend_intelligence.db'
        self._init_database()
        
        # Dividend-related keywords for scoring
        self.dividend_keywords = {
            'high_priority': ['dividend cut', 'dividend increase', 'dividend raise', 'special dividend', 
                            'dividend suspension', 'dividend reinstatement', 'ex-dividend', 'dividend declaration'],
            'medium_priority': ['quarterly dividend', 'monthly dividend', 'annual dividend', 'dividend yield',
                              'dividend payout', 'dividend payment', 'dividend announcement', 'dividend date'],
            'low_priority': ['dividend stock', 'dividend investor', 'dividend portfolio', 'dividend strategy',
                           'dividend aristocrat', 'dividend king', 'dividend growth']
        }
        
        # Financial news RSS feeds
        self.rss_feeds = [
            {'name': 'MarketWatch Dividends', 'url': 'https://feeds.marketwatch.com/marketwatch/dividends/'},
            {'name': 'Yahoo Finance', 'url': 'https://finance.yahoo.com/rss/headline'},
            {'name': 'Seeking Alpha Dividends', 'url': 'https://seekingalpha.com/feed.xml'},
            {'name': 'Bloomberg Markets', 'url': 'https://feeds.bloomberg.com/markets/news.rss'},
            {'name': 'Reuters Business', 'url': 'https://feeds.reuters.com/reuters/businessNews'},
            {'name': 'WSJ Markets', 'url': 'https://feeds.a.dj.com/rss/RSSMarketsMain.xml'},
            {'name': 'CNBC Top News', 'url': 'https://www.cnbc.com/id/100003114/device/rss/rss.html'},
            {'name': 'Financial Times', 'url': 'https://www.ft.com/?format=rss'}
        ]
        
        # Social media sources
        self.social_sources = {
            'reddit': ['dividends', 'stocks', 'investing', 'SecurityAnalysis', 'ValueInvesting'],
            'stocktwits': ['trending'],  # Would need StockTwits API
            'twitter_keywords': ['$DIV', '#dividends', '#dividendinvesting', '#exdividend']
        }
        
        # Trending topics tracker
        self.trending_tracker = defaultdict(lambda: {'count': 0, 'first_seen': None, 'sources': set()})
        
    def _init_database(self):
        """Initialize SQLite database for storing news and trends"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # News articles table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS news_articles (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            url TEXT UNIQUE NOT NULL,
            source TEXT,
            published_at TIMESTAMP,
            relevance_score REAL,
            sentiment_score REAL,
            tickers_mentioned TEXT,
            dividend_keywords TEXT,
            trend_score REAL,
            is_breaking BOOLEAN,
            analysis TEXT,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Trending topics table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS trending_topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            count INTEGER,
            trend_score REAL,
            first_seen TIMESTAMP,
            last_updated TIMESTAMP,
            sources TEXT,
            related_articles TEXT
        )
        ''')
        
        # Alerts table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id TEXT,
            alert_type TEXT,
            priority TEXT,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sent BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (article_id) REFERENCES news_articles(id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    async def fetch_newsapi_articles(self, query: str = "dividend") -> List[Dict]:
        """Fetch articles from NewsAPI"""
        articles = []
        try:
            url = f"https://newsapi.org/v2/everything"
            params = {
                'q': query,
                'apiKey': self.newsapi_key,
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': 100,
                'domains': 'reuters.com,bloomberg.com,wsj.com,cnbc.com,marketwatch.com,seekingalpha.com'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        articles = data.get('articles', [])
                        logger.info(f"Fetched {len(articles)} articles from NewsAPI")
        except Exception as e:
            logger.error(f"Error fetching NewsAPI articles: {e}")
        
        return articles
    
    def fetch_rss_feeds(self) -> List[Dict]:
        """Fetch articles from RSS feeds"""
        all_articles = []
        
        for feed_info in self.rss_feeds:
            try:
                feed = feedparser.parse(feed_info['url'])
                for entry in feed.entries[:20]:  # Limit to 20 latest per feed
                    article = {
                        'title': entry.get('title', ''),
                        'description': entry.get('summary', ''),
                        'url': entry.get('link', ''),
                        'source': feed_info['name'],
                        'published': entry.get('published', '')
                    }
                    all_articles.append(article)
                logger.info(f"Fetched {len(feed.entries[:20])} articles from {feed_info['name']}")
            except Exception as e:
                logger.error(f"Error fetching RSS feed {feed_info['name']}: {e}")
        
        return all_articles
    
    async def fetch_reddit_posts(self) -> List[Dict]:
        """Fetch dividend-related posts from Reddit"""
        posts = []
        
        if not (self.reddit_client_id and self.reddit_client_secret):
            logger.warning("Reddit credentials not configured")
            return posts
        
        try:
            # Get Reddit access token
            auth = aiohttp.BasicAuth(self.reddit_client_id, self.reddit_client_secret)
            data = {'grant_type': 'client_credentials'}
            headers = {'User-Agent': 'HarveyDividendBot/1.0'}
            
            async with aiohttp.ClientSession() as session:
                async with session.post('https://www.reddit.com/api/v1/access_token', 
                                       auth=auth, data=data, headers=headers) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        token = token_data['access_token']
                        
                        # Fetch posts from dividend subreddits
                        headers['Authorization'] = f'Bearer {token}'
                        
                        for subreddit in self.social_sources['reddit']:
                            url = f'https://oauth.reddit.com/r/{subreddit}/hot'
                            async with session.get(url, headers=headers, params={'limit': 25}) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    for post in data['data']['children']:
                                        post_data = post['data']
                                        if any(kw in post_data['title'].lower() for kw in ['dividend', 'div', 'yield']):
                                            posts.append({
                                                'title': post_data['title'],
                                                'description': post_data.get('selftext', '')[:500],
                                                'url': f"https://reddit.com{post_data['permalink']}",
                                                'source': f'Reddit r/{subreddit}',
                                                'published': datetime.fromtimestamp(post_data['created_utc']),
                                                'upvotes': post_data['ups'],
                                                'comments': post_data['num_comments']
                                            })
                        
                        logger.info(f"Fetched {len(posts)} relevant Reddit posts")
        except Exception as e:
            logger.error(f"Error fetching Reddit posts: {e}")
        
        return posts
    
    def extract_tickers(self, text: str) -> List[str]:
        """Extract stock tickers from text"""
        # Common patterns: $TICKER, TICKER:, (TICKER), NYSE:TICKER
        ticker_pattern = r'\$([A-Z]{1,5})\b|(?:NYSE|NASDAQ|NYSE|LSE|TSX):([A-Z]{1,5})\b|\(([A-Z]{1,5})\)'
        matches = re.findall(ticker_pattern, text.upper())
        tickers = [match for group in matches for match in group if match]
        
        # Also check for common dividend stocks without symbols
        common_dividend_stocks = {
            'APPLE': 'AAPL', 'MICROSOFT': 'MSFT', 'JOHNSON': 'JNJ', 
            'COCA-COLA': 'KO', 'PEPSI': 'PEP', 'WALMART': 'WMT',
            'AMAZON': 'AMZN', 'GOOGLE': 'GOOGL', 'META': 'META'
        }
        
        for company, ticker in common_dividend_stocks.items():
            if company in text.upper():
                tickers.append(ticker)
        
        return list(set(tickers))
    
    def calculate_relevance_score(self, article: Dict) -> float:
        """Calculate dividend relevance score for an article"""
        score = 0.0
        text = f"{article.get('title', '')} {article.get('description', '')}".lower()
        
        # Check keyword presence and weight
        for keyword in self.dividend_keywords['high_priority']:
            if keyword in text:
                score += 3.0
        
        for keyword in self.dividend_keywords['medium_priority']:
            if keyword in text:
                score += 2.0
        
        for keyword in self.dividend_keywords['low_priority']:
            if keyword in text:
                score += 1.0
        
        # Bonus for multiple tickers mentioned
        tickers = self.extract_tickers(text)
        if tickers:
            score += min(len(tickers) * 0.5, 2.0)
        
        # Recency bonus
        try:
            if 'published' in article:
                pub_time = article['published']
                if isinstance(pub_time, str):
                    pub_time = datetime.fromisoformat(pub_time.replace('Z', '+00:00'))
                
                hours_old = (datetime.now(timezone.utc) - pub_time).total_seconds() / 3600
                if hours_old < 1:
                    score += 2.0  # Very recent
                elif hours_old < 6:
                    score += 1.0  # Recent
                elif hours_old < 24:
                    score += 0.5  # Today
        except:
            pass
        
        # Source credibility bonus
        credible_sources = ['reuters', 'bloomberg', 'wsj', 'marketwatch', 'seeking alpha']
        if any(source in article.get('source', '').lower() for source in credible_sources):
            score += 1.0
        
        # Normalize score to 0-10 range
        return min(score, 10.0)
    
    def analyze_sentiment(self, text: str) -> float:
        """Simple sentiment analysis for dividend news"""
        positive_words = ['increase', 'raise', 'boost', 'growth', 'higher', 'special', 
                         'reinstate', 'declare', 'maintain', 'stable', 'aristocrat', 'king']
        negative_words = ['cut', 'reduce', 'slash', 'suspend', 'eliminate', 'lower',
                         'decrease', 'concern', 'risk', 'warning', 'decline']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count + negative_count == 0:
            return 0.0  # Neutral
        
        sentiment = (positive_count - negative_count) / (positive_count + negative_count)
        return sentiment  # Range: -1 (negative) to +1 (positive)
    
    def detect_trending_topics(self, articles: List[NewsArticle]) -> List[Dict]:
        """Detect emerging trending topics in dividend space"""
        trending = []
        
        # Extract topics from recent articles
        recent_articles = [a for a in articles 
                          if (datetime.now(timezone.utc) - a.published_at).days < 2]
        
        # Count ticker mentions
        ticker_counts = Counter()
        for article in recent_articles:
            ticker_counts.update(article.tickers_mentioned)
        
        # Count keyword combinations
        keyword_combinations = Counter()
        for article in recent_articles:
            keywords = article.dividend_keywords
            if len(keywords) >= 2:
                for i in range(len(keywords)):
                    for j in range(i+1, len(keywords)):
                        combination = tuple(sorted([keywords[i], keywords[j]]))
                        keyword_combinations[combination] += 1
        
        # Identify trending tickers
        for ticker, count in ticker_counts.most_common(10):
            if count >= 3:  # Mentioned in at least 3 articles
                trend_score = count * 2  # Simple scoring
                trending.append({
                    'type': 'ticker',
                    'topic': ticker,
                    'count': count,
                    'trend_score': trend_score,
                    'description': f"{ticker} mentioned in {count} recent articles"
                })
        
        # Identify trending topics
        for combination, count in keyword_combinations.most_common(5):
            if count >= 2:
                trending.append({
                    'type': 'topic',
                    'topic': ' + '.join(combination),
                    'count': count,
                    'trend_score': count * 1.5,
                    'description': f"Topic combination appearing in {count} articles"
                })
        
        return sorted(trending, key=lambda x: x['trend_score'], reverse=True)
    
    def generate_ai_analysis(self, article: NewsArticle, trending: List[Dict]) -> str:
        """Generate AI-powered analysis of the news"""
        # This would integrate with Harvey's multi-model AI system
        # For demo, using template-based analysis
        
        analysis_parts = []
        
        # Headline analysis
        if article.relevance_score >= 8:
            analysis_parts.append("🔴 HIGH IMPACT: This news could significantly affect dividend payments.")
        elif article.relevance_score >= 5:
            analysis_parts.append("🟡 MODERATE IMPACT: This news may influence dividend decisions.")
        else:
            analysis_parts.append("🟢 LOW IMPACT: Informational update with limited immediate dividend impact.")
        
        # Sentiment interpretation
        if article.sentiment_score > 0.5:
            analysis_parts.append("Positive sentiment suggests favorable dividend outlook.")
        elif article.sentiment_score < -0.5:
            analysis_parts.append("Negative sentiment indicates potential dividend concerns.")
        
        # Ticker analysis
        if article.tickers_mentioned:
            tickers_str = ', '.join(article.tickers_mentioned[:3])
            analysis_parts.append(f"Key stocks affected: {tickers_str}")
        
        # Trending context
        if article.trend_score > 5:
            analysis_parts.append("📈 This topic is trending - early signal detection successful!")
        
        # Action recommendation
        if 'dividend cut' in article.title.lower():
            analysis_parts.append("ACTION: Review exposure and consider rebalancing.")
        elif 'dividend increase' in article.title.lower():
            analysis_parts.append("ACTION: Potential accumulation opportunity if fundamentals support.")
        elif 'special dividend' in article.title.lower():
            analysis_parts.append("ACTION: Note ex-dividend date for capture opportunity.")
        
        return " ".join(analysis_parts)
    
    def should_send_alert(self, article: NewsArticle) -> Tuple[bool, str, str]:
        """Determine if article warrants an alert"""
        # High priority alerts
        if article.relevance_score >= 8 or article.is_breaking:
            if 'dividend cut' in article.title.lower():
                return True, 'CRITICAL', 'Dividend cut detected - immediate attention required'
            elif 'special dividend' in article.title.lower():
                return True, 'HIGH', 'Special dividend announced - capture opportunity'
            elif article.trend_score > 7:
                return True, 'HIGH', 'Trending topic detected before mainstream coverage'
        
        # Medium priority
        if article.relevance_score >= 5:
            if any(kw in article.title.lower() for kw in ['dividend increase', 'dividend raise']):
                return True, 'MEDIUM', 'Positive dividend action detected'
        
        return False, '', ''
    
    async def process_all_sources(self) -> Dict[str, Any]:
        """Main processing pipeline for all news sources"""
        logger.info("Starting dividend intelligence scan...")
        
        all_articles = []
        
        # Fetch from all sources
        # NewsAPI
        newsapi_articles = await self.fetch_newsapi_articles("dividend OR dividends OR yield")
        for article in newsapi_articles:
            all_articles.append({
                'title': article.get('title', ''),
                'description': article.get('description', ''),
                'url': article.get('url', ''),
                'source': article.get('source', {}).get('name', 'NewsAPI'),
                'published': article.get('publishedAt', '')
            })
        
        # RSS Feeds
        rss_articles = self.fetch_rss_feeds()
        all_articles.extend(rss_articles)
        
        # Reddit
        reddit_posts = await self.fetch_reddit_posts()
        all_articles.extend(reddit_posts)
        
        # Process and score articles
        processed_articles = []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for article_data in all_articles:
            try:
                # Skip if already processed
                url_hash = hashlib.md5(article_data['url'].encode()).hexdigest()
                cursor.execute("SELECT id FROM news_articles WHERE id = ?", (url_hash,))
                if cursor.fetchone():
                    continue
                
                # Calculate scores
                relevance_score = self.calculate_relevance_score(article_data)
                if relevance_score < 2:  # Skip low relevance
                    continue
                
                sentiment_score = self.analyze_sentiment(
                    f"{article_data['title']} {article_data.get('description', '')}"
                )
                
                tickers = self.extract_tickers(
                    f"{article_data['title']} {article_data.get('description', '')}"
                )
                
                # Extract dividend keywords found
                text_lower = f"{article_data['title']} {article_data.get('description', '')}".lower()
                found_keywords = []
                for priority, keywords in self.dividend_keywords.items():
                    for keyword in keywords:
                        if keyword in text_lower:
                            found_keywords.append(keyword)
                
                # Parse published date
                published_at = datetime.now(timezone.utc)
                if article_data.get('published'):
                    if isinstance(article_data['published'], datetime):
                        published_at = article_data['published']
                    else:
                        try:
                            published_at = datetime.fromisoformat(
                                article_data['published'].replace('Z', '+00:00')
                            )
                        except:
                            pass
                
                # Create NewsArticle object
                article = NewsArticle(
                    id=url_hash,
                    title=article_data['title'][:500],
                    description=article_data.get('description', '')[:2000],
                    url=article_data['url'],
                    source=article_data.get('source', 'Unknown'),
                    published_at=published_at,
                    relevance_score=relevance_score,
                    sentiment_score=sentiment_score,
                    tickers_mentioned=tickers,
                    dividend_keywords=found_keywords[:5],  # Top 5 keywords
                    trend_score=0.0,  # Will calculate after
                    is_breaking=(datetime.now(timezone.utc) - published_at).total_seconds() < 3600
                )
                
                processed_articles.append(article)
                
            except Exception as e:
                logger.error(f"Error processing article: {e}")
        
        # Detect trending topics
        trending_topics = self.detect_trending_topics(processed_articles)
        
        # Update trend scores
        for article in processed_articles:
            for trend in trending_topics:
                if trend['type'] == 'ticker' and trend['topic'] in article.tickers_mentioned:
                    article.trend_score += trend['trend_score'] * 0.5
                elif trend['type'] == 'topic':
                    topic_keywords = trend['topic'].split(' + ')
                    if any(kw in article.dividend_keywords for kw in topic_keywords):
                        article.trend_score += trend['trend_score'] * 0.3
        
        # Generate AI analysis for top articles
        top_articles = sorted(processed_articles, 
                             key=lambda x: x.relevance_score + x.trend_score, 
                             reverse=True)[:10]
        
        alerts_to_send = []
        for article in top_articles:
            article.analysis = self.generate_ai_analysis(article, trending_topics)
            
            # Check for alerts
            should_alert, priority, message = self.should_send_alert(article)
            if should_alert:
                alerts_to_send.append({
                    'article': article,
                    'priority': priority,
                    'message': message
                })
            
            # Save to database
            cursor.execute('''
            INSERT OR IGNORE INTO news_articles 
            (id, title, description, url, source, published_at, relevance_score, 
             sentiment_score, tickers_mentioned, dividend_keywords, trend_score, 
             is_breaking, analysis, category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                article.id, article.title, article.description, article.url,
                article.source, article.published_at, article.relevance_score,
                article.sentiment_score, json.dumps(article.tickers_mentioned),
                json.dumps(article.dividend_keywords), article.trend_score,
                article.is_breaking, article.analysis, article.category
            ))
        
        # Save trending topics
        for trend in trending_topics:
            cursor.execute('''
            INSERT INTO trending_topics 
            (topic, count, trend_score, first_seen, last_updated, sources)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                trend['topic'], trend['count'], trend['trend_score'],
                datetime.now(timezone.utc), datetime.now(timezone.utc),
                json.dumps([])
            ))
        
        conn.commit()
        conn.close()
        
        # Prepare summary
        summary = {
            'scan_time': datetime.now(timezone.utc).isoformat(),
            'total_articles_scanned': len(all_articles),
            'relevant_articles_found': len(processed_articles),
            'top_articles': [
                {
                    'title': a.title,
                    'source': a.source,
                    'relevance': a.relevance_score,
                    'sentiment': a.sentiment_score,
                    'tickers': a.tickers_mentioned,
                    'analysis': a.analysis,
                    'url': a.url
                } for a in top_articles
            ],
            'trending_topics': trending_topics[:5],
            'alerts': [
                {
                    'priority': alert['priority'],
                    'message': alert['message'],
                    'article_title': alert['article'].title
                } for alert in alerts_to_send
            ],
            'statistics': {
                'breaking_news_count': sum(1 for a in processed_articles if a.is_breaking),
                'positive_sentiment_count': sum(1 for a in processed_articles if a.sentiment_score > 0.3),
                'negative_sentiment_count': sum(1 for a in processed_articles if a.sentiment_score < -0.3),
                'unique_tickers_mentioned': len(set(t for a in processed_articles for t in a.tickers_mentioned))
            }
        }
        
        logger.info(f"Scan complete: {len(processed_articles)} relevant articles, {len(alerts_to_send)} alerts")
        
        return summary

async def main():
    """Run the dividend intelligence system"""
    intelligence = DividendIntelligenceSystem()
    
    print("\n" + "="*80)
    print("🤖 HARVEY DIVIDEND INTELLIGENCE SYSTEM")
    print("="*80)
    print("\n📡 Monitoring news sources, social media, and RSS feeds...")
    print("🔍 Detecting dividend announcements before they trend...\n")
    
    # Run the scan
    results = await intelligence.process_all_sources()
    
    # Display results
    print(f"\n📊 SCAN RESULTS - {results['scan_time']}")
    print("="*80)
    print(f"Total articles scanned: {results['total_articles_scanned']}")
    print(f"Relevant articles found: {results['relevant_articles_found']}")
    print(f"Breaking news detected: {results['statistics']['breaking_news_count']}")
    print(f"Unique tickers mentioned: {results['statistics']['unique_tickers_mentioned']}")
    
    if results['trending_topics']:
        print(f"\n🔥 TRENDING TOPICS (Early Detection)")
        print("-"*40)
        for trend in results['trending_topics'][:5]:
            print(f"• {trend['topic']} - Score: {trend['trend_score']:.1f} ({trend['description']})")
    
    if results['alerts']:
        print(f"\n🚨 ALERTS GENERATED")
        print("-"*40)
        for alert in results['alerts']:
            icon = "🔴" if alert['priority'] == 'CRITICAL' else "🟡" if alert['priority'] == 'HIGH' else "🟢"
            print(f"{icon} [{alert['priority']}] {alert['message']}")
            print(f"   Article: {alert['article_title']}")
    
    if results['top_articles']:
        print(f"\n📰 TOP DIVIDEND NEWS")
        print("-"*40)
        for i, article in enumerate(results['top_articles'][:5], 1):
            sentiment_icon = "📈" if article['sentiment'] > 0.3 else "📉" if article['sentiment'] < -0.3 else "➡️"
            print(f"\n{i}. {article['title'][:80]}...")
            print(f"   Source: {article['source']} | Relevance: {article['relevance']:.1f}/10 {sentiment_icon}")
            if article['tickers']:
                print(f"   Tickers: {', '.join(article['tickers'][:5])}")
            print(f"   Analysis: {article['analysis'][:200]}...")
    
    # Save full report
    with open('dividend_intelligence_report.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print("\n✅ Full report saved to dividend_intelligence_report.json")
    print("\n💡 This system can be deployed to run every 15 minutes on Azure VM")
    print("   providing real-time dividend intelligence to Harvey users!")
    
    return results

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())