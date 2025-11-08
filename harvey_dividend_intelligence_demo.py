#!/usr/bin/env python3
"""
Harvey Dividend Intelligence System - Demo Version
Demonstrates the architecture for monitoring news and social media for dividend announcements
"""

import json
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Tuple
from collections import defaultdict, Counter
import re
import random

class HarveyDividendIntelligence:
    """Harvey's dividend news intelligence system"""
    
    def __init__(self):
        self.dividend_keywords = {
            'high_priority': ['dividend cut', 'dividend increase', 'special dividend', 'dividend suspension'],
            'medium_priority': ['quarterly dividend', 'monthly dividend', 'dividend yield', 'ex-dividend'],
            'low_priority': ['dividend stock', 'dividend investor', 'dividend portfolio']
        }
        
        # Simulated news data for demo
        self.demo_articles = [
            {
                'title': 'Apple Announces Special Dividend of $0.50 Per Share',
                'description': 'Apple Inc. (AAPL) declared a special cash dividend of $0.50 per share, payable to shareholders of record.',
                'source': 'MarketWatch',
                'url': 'https://example.com/apple-special-dividend',
                'published': datetime.now(timezone.utc) - timedelta(hours=1)
            },
            {
                'title': 'Microsoft Increases Quarterly Dividend by 10%',
                'description': 'Microsoft Corporation (MSFT) announced a 10% increase in its quarterly dividend to $0.75 per share.',
                'source': 'Reuters',
                'url': 'https://example.com/msft-dividend-increase',
                'published': datetime.now(timezone.utc) - timedelta(hours=2)
            },
            {
                'title': 'BREAKING: Ford Suspends Dividend Amid Market Challenges',
                'description': 'Ford Motor Company (F) has announced the suspension of its dividend to preserve cash.',
                'source': 'CNBC',
                'url': 'https://example.com/ford-dividend-suspension',
                'published': datetime.now(timezone.utc) - timedelta(minutes=30)
            },
            {
                'title': 'Trending on Reddit: NVIDIA Dividend Speculation Heats Up',
                'description': 'Multiple posts on r/dividends discussing potential NVDA dividend announcement gaining traction.',
                'source': 'Reddit r/dividends',
                'url': 'https://reddit.com/r/dividends/nvda-speculation',
                'published': datetime.now(timezone.utc) - timedelta(hours=3)
            },
            {
                'title': 'Johnson & Johnson Maintains Dividend for 60th Consecutive Year',
                'description': 'JNJ continues its dividend aristocrat status with maintained quarterly payment.',
                'source': 'Seeking Alpha',
                'url': 'https://example.com/jnj-dividend-maintained',
                'published': datetime.now(timezone.utc) - timedelta(hours=5)
            }
        ]
    
    def extract_tickers(self, text: str) -> List[str]:
        """Extract stock tickers from text"""
        ticker_pattern = r'\b([A-Z]{1,5})\b'
        text_upper = text.upper()
        
        # Known ticker mappings
        known_tickers = {
            'APPLE': 'AAPL', 'MICROSOFT': 'MSFT', 'NVIDIA': 'NVDA',
            'FORD': 'F', 'JOHNSON': 'JNJ', 'AMAZON': 'AMZN'
        }
        
        tickers = []
        # Check for company names
        for company, ticker in known_tickers.items():
            if company in text_upper:
                tickers.append(ticker)
        
        # Check for ticker symbols in parentheses
        paren_tickers = re.findall(r'\(([A-Z]{1,5})\)', text)
        tickers.extend(paren_tickers)
        
        return list(set(tickers))
    
    def calculate_relevance_score(self, article: Dict) -> float:
        """Calculate relevance score for dividend news"""
        score = 0.0
        text = f"{article['title']} {article['description']}".lower()
        
        # Keyword scoring
        for keyword in self.dividend_keywords['high_priority']:
            if keyword in text:
                score += 3.0
        for keyword in self.dividend_keywords['medium_priority']:
            if keyword in text:
                score += 2.0
        for keyword in self.dividend_keywords['low_priority']:
            if keyword in text:
                score += 1.0
        
        # Recency bonus
        hours_old = (datetime.now(timezone.utc) - article['published']).total_seconds() / 3600
        if hours_old < 1:
            score += 2.0
        elif hours_old < 6:
            score += 1.0
        
        # Source credibility
        if article['source'] in ['Reuters', 'Bloomberg', 'MarketWatch', 'CNBC']:
            score += 1.0
        
        return min(score, 10.0)
    
    def analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of dividend news"""
        positive = ['increase', 'raise', 'boost', 'special', 'maintain', 'growth']
        negative = ['cut', 'suspend', 'reduce', 'slash', 'eliminate', 'concern']
        
        text_lower = text.lower()
        pos_count = sum(1 for word in positive if word in text_lower)
        neg_count = sum(1 for word in negative if word in text_lower)
        
        if pos_count + neg_count == 0:
            return 0.0
        
        return (pos_count - neg_count) / (pos_count + neg_count)
    
    def detect_trending_topics(self, articles: List[Dict]) -> List[Dict]:
        """Detect trending dividend topics"""
        ticker_counts = Counter()
        keyword_counts = Counter()
        
        for article in articles:
            # Count tickers
            tickers = self.extract_tickers(f"{article['title']} {article['description']}")
            ticker_counts.update(tickers)
            
            # Count keywords
            text_lower = f"{article['title']} {article['description']}".lower()
            for priority, keywords in self.dividend_keywords.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        keyword_counts[keyword] += 1
        
        trending = []
        
        # Trending tickers
        for ticker, count in ticker_counts.most_common(3):
            if count >= 1:
                trending.append({
                    'type': 'ticker',
                    'topic': ticker,
                    'count': count,
                    'trend_score': count * 2.5
                })
        
        # Trending keywords
        for keyword, count in keyword_counts.most_common(3):
            if count >= 1:
                trending.append({
                    'type': 'keyword',
                    'topic': keyword,
                    'count': count,
                    'trend_score': count * 1.5
                })
        
        return sorted(trending, key=lambda x: x['trend_score'], reverse=True)
    
    def generate_ai_analysis(self, article: Dict, relevance: float, sentiment: float) -> str:
        """Generate AI analysis of the news"""
        analysis = []
        
        # Impact assessment
        if relevance >= 8:
            analysis.append("🔴 HIGH IMPACT: Critical dividend news requiring immediate attention.")
        elif relevance >= 5:
            analysis.append("🟡 MODERATE IMPACT: Important dividend development to monitor.")
        else:
            analysis.append("🟢 LOW IMPACT: Informational update.")
        
        # Sentiment interpretation
        if sentiment > 0.5:
            analysis.append("Positive development for dividend investors.")
        elif sentiment < -0.5:
            analysis.append("Negative news - review portfolio exposure.")
        
        # Specific recommendations
        title_lower = article['title'].lower()
        if 'special dividend' in title_lower:
            analysis.append("BUY CONSIDERATION: Special dividend capture opportunity. ⚠️ DISCLAIMER: This is for educational purposes only, not financial advice. Please consult your trusted financial advisor before making investment decisions.")
        elif 'dividend cut' in title_lower or 'suspension' in title_lower:
            analysis.append("ACTION: Consider reviewing if holding this position.")
        elif 'dividend increase' in title_lower:
            analysis.append("BUY CONSIDERATION: Potential accumulation opportunity. ⚠️ DISCLAIMER: This is for educational purposes only, not financial advice. Please consult your trusted financial advisor before making investment decisions.")
        
        return " ".join(analysis)
    
    def process_articles(self) -> Dict[str, Any]:
        """Process all articles and generate intelligence report"""
        processed = []
        
        for article in self.demo_articles:
            # Calculate metrics
            relevance = self.calculate_relevance_score(article)
            sentiment = self.analyze_sentiment(f"{article['title']} {article['description']}")
            tickers = self.extract_tickers(f"{article['title']} {article['description']}")
            
            # Generate analysis
            analysis = self.generate_ai_analysis(article, relevance, sentiment)
            
            # Find keywords
            text_lower = f"{article['title']} {article['description']}".lower()
            found_keywords = []
            for priority, keywords in self.dividend_keywords.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        found_keywords.append(keyword)
            
            processed.append({
                'title': article['title'],
                'source': article['source'],
                'url': article['url'],
                'published': article['published'].isoformat(),
                'relevance_score': relevance,
                'sentiment_score': sentiment,
                'tickers': tickers,
                'keywords': found_keywords,
                'analysis': analysis,
                'is_breaking': (datetime.now(timezone.utc) - article['published']).total_seconds() < 3600
            })
        
        # Sort by relevance
        processed = sorted(processed, key=lambda x: x['relevance_score'], reverse=True)
        
        # Detect trends
        trending = self.detect_trending_topics(self.demo_articles)
        
        # Generate alerts
        alerts = []
        for article in processed:
            if article['relevance_score'] >= 8 or article['is_breaking']:
                priority = 'CRITICAL' if 'suspension' in article['title'].lower() or 'cut' in article['title'].lower() else 'HIGH'
                alerts.append({
                    'priority': priority,
                    'title': article['title'],
                    'message': article['analysis'],
                    'url': article['url']
                })
        
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'articles_processed': len(processed),
            'top_articles': processed[:5],
            'trending_topics': trending,
            'alerts': alerts,
            'statistics': {
                'breaking_news': sum(1 for a in processed if a['is_breaking']),
                'positive_sentiment': sum(1 for a in processed if a['sentiment_score'] > 0.3),
                'negative_sentiment': sum(1 for a in processed if a['sentiment_score'] < -0.3),
                'unique_tickers': len(set(t for a in processed for t in a['tickers']))
            }
        }
    
    def display_report(self, report: Dict):
        """Display the intelligence report"""
        print("\n" + "="*80)
        print("🤖 HARVEY DIVIDEND INTELLIGENCE REPORT")
        print("="*80)
        print(f"Generated: {report['timestamp']}")
        print(f"Articles Analyzed: {report['articles_processed']}")
        print(f"Breaking News: {report['statistics']['breaking_news']}")
        print(f"Unique Tickers: {report['statistics']['unique_tickers']}")
        
        if report['alerts']:
            print(f"\n🚨 ALERTS ({len(report['alerts'])})")
            print("-"*40)
            for alert in report['alerts']:
                icon = "🔴" if alert['priority'] == 'CRITICAL' else "🟡"
                print(f"{icon} [{alert['priority']}] {alert['title']}")
                print(f"   {alert['message']}")
                print(f"   📎 Link: {alert['url']}\n")
        
        if report['trending_topics']:
            print("\n🔥 TRENDING TOPICS")
            print("-"*40)
            for trend in report['trending_topics'][:5]:
                print(f"• {trend['topic']} ({trend['type']}) - Score: {trend['trend_score']:.1f}")
        
        print(f"\n📰 TOP DIVIDEND NEWS")
        print("-"*40)
        for i, article in enumerate(report['top_articles'][:5], 1):
            sentiment_icon = "📈" if article['sentiment_score'] > 0.3 else "📉" if article['sentiment_score'] < -0.3 else "➡️"
            print(f"\n{i}. {article['title']}")
            print(f"   Source: {article['source']} | Relevance: {article['relevance_score']:.1f}/10 {sentiment_icon}")
            if article['tickers']:
                print(f"   Tickers: {', '.join(article['tickers'])}")
            print(f"   Analysis: {article['analysis']}")
            print(f"   📎 Link: {article['url']}")

def main():
    """Run the dividend intelligence demo"""
    intelligence = HarveyDividendIntelligence()
    report = intelligence.process_articles()
    intelligence.display_report(report)
    
    # Save report
    with open('dividend_intelligence_demo.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print("\n" + "="*80)
    print("💡 FULL SYSTEM CAPABILITIES")
    print("="*80)
    print("""
The production Harvey Dividend Intelligence System will include:

📡 DATA SOURCES
• NewsAPI: Real-time financial news from 100+ sources
• RSS Feeds: MarketWatch, Bloomberg, Reuters, WSJ, CNBC, FT
• Reddit API: r/dividends, r/stocks, r/investing sentiment analysis  
• Twitter/X API: Tracking $DIV hashtags and dividend influencers
• StockTwits: Social sentiment on dividend stocks

🤖 ML FEATURES
• Relevance Scoring: ML model trained on 100K+ dividend articles
• Trend Detection: Identify topics 6-12 hours before mainstream
• Entity Recognition: Extract tickers, dates, amounts automatically
• Sentiment Analysis: Advanced NLP for nuanced market sentiment
• Deduplication: Smart clustering to avoid duplicate alerts

🎯 INTELLIGENCE ENGINE
• Multi-Model AI: GPT-5, Grok-4, DeepSeek-R1 for analysis
• Pattern Recognition: Detect dividend cut warnings early
• Correlation Analysis: Link news to stock price movements
• Risk Assessment: Evaluate dividend sustainability impacts
• Opportunity Scoring: Rank capture opportunities

📊 DELIVERY CHANNELS
• Real-time API: Stream to Harvey chat interface
• Email Alerts: Priority-based notifications to dev@heydividend.com
• Database Storage: Historical trend analysis
• Dashboard: Web interface for monitoring trends
• Webhooks: Integration with trading platforms

⏰ SCHEDULING
• Every 15 minutes: News and RSS feed scanning
• Every 30 minutes: Social media sentiment check
• Every hour: Trend analysis and ML predictions
• Daily: Comprehensive intelligence digest

✅ DEPLOYMENT
• Azure VM Integration: Runs alongside ML schedulers
• API Endpoints: /v1/dividend-intelligence/*
• Cron Jobs: Automated monitoring schedule
• State Management: Track processed articles
• Performance: Process 1000+ articles/hour
    """)
    
    print("\n✅ Demo report saved to dividend_intelligence_demo.json")
    print("🚀 This system will give Harvey users a competitive edge in dividend investing!")

if __name__ == "__main__":
    main()