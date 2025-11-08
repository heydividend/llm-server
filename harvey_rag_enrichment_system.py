#!/usr/bin/env python3
"""
Harvey Agentic RAG Enrichment System
Intelligent multi-source data orchestration with self-evaluation loops
"""

import os
import json
import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from enum import Enum
import logging
import re
import aiohttp
import pymssql
from concurrent.futures import ThreadPoolExecutor
import yfinance as yf
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
YAHOO_BATCH_SIZE = 50  # Max tickers per Yahoo Finance request
MASSIVE_API_URL = "https://api.massive.com/v1"
CACHE_TTL_SECONDS = {
    'quote': 60,        # 1 minute for real-time quotes
    'sentiment': 300,   # 5 minutes for sentiment
    'ml_ratings': 3600, # 1 hour for ML ratings (updated daily)
    'dividends': 1800   # 30 minutes for dividend data
}

class QueryIntent(Enum):
    """User query intent classification"""
    BUY_RECOMMENDATION = "buy"
    SELL_RECOMMENDATION = "sell"
    ANALYZE = "analyze"
    MONITOR = "monitor"
    SCREEN = "screen"
    COMPARE = "compare"
    FORECAST = "forecast"
    PORTFOLIO = "portfolio"

class DataSource(Enum):
    """Available data sources"""
    DATABASE = "database"
    YAHOO_FINANCE = "yahoo"
    MASSIVE = "massive"
    INTELLIGENCE = "intelligence"
    ML_SERVICE = "ml_service"

class QueryAnalyzer:
    """Analyzes and rewrites user queries for optimal retrieval"""
    
    def __init__(self):
        self.intent_keywords = {
            QueryIntent.BUY_RECOMMENDATION: ['buy', 'purchase', 'invest', 'accumulate', 'add'],
            QueryIntent.SELL_RECOMMENDATION: ['sell', 'exit', 'dump', 'reduce', 'trim'],
            QueryIntent.ANALYZE: ['analyze', 'evaluate', 'assess', 'review', 'examine'],
            QueryIntent.MONITOR: ['watch', 'track', 'follow', 'monitor', 'alert'],
            QueryIntent.SCREEN: ['find', 'search', 'screen', 'filter', 'list'],
            QueryIntent.COMPARE: ['compare', 'versus', 'vs', 'against', 'better'],
            QueryIntent.FORECAST: ['predict', 'forecast', 'expect', 'project', 'future'],
            QueryIntent.PORTFOLIO: ['portfolio', 'holdings', 'positions', 'allocation']
        }
        
        self.ticker_pattern = re.compile(r'\b[A-Z]{1,5}\b')
        
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze user query and determine retrieval strategy"""
        query_lower = query.lower()
        
        # Detect intent
        intent = QueryIntent.ANALYZE  # default
        for intent_type, keywords in self.intent_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                intent = intent_type
                break
        
        # Extract tickers
        tickers = self._extract_tickers(query)
        
        # Determine required data sources
        required_sources = self._determine_sources(query_lower, intent)
        
        # Generate rewritten queries for better retrieval
        rewritten_queries = self._rewrite_queries(query, intent, tickers)
        
        # Determine if disclaimer needed
        needs_disclaimer = intent in [QueryIntent.BUY_RECOMMENDATION, QueryIntent.SELL_RECOMMENDATION]
        
        return {
            'original_query': query,
            'intent': intent.value,
            'tickers': tickers,
            'required_sources': required_sources,
            'rewritten_queries': rewritten_queries,
            'needs_disclaimer': needs_disclaimer,
            'confidence': self._calculate_confidence(query, tickers, intent)
        }
    
    def _extract_tickers(self, query: str) -> List[str]:
        """Extract stock tickers from query"""
        # Find uppercase words that look like tickers
        potential_tickers = self.ticker_pattern.findall(query)
        
        # Filter common words that aren't tickers
        non_tickers = {'I', 'A', 'THE', 'AND', 'OR', 'BUT', 'NOT', 'ETF', 'REIT'}
        tickers = [t for t in potential_tickers if t not in non_tickers]
        
        # Add common company name mappings
        query_upper = query.upper()
        company_map = {
            'APPLE': 'AAPL', 'MICROSOFT': 'MSFT', 'AMAZON': 'AMZN',
            'GOOGLE': 'GOOGL', 'NVIDIA': 'NVDA', 'TESLA': 'TSLA',
            'BERKSHIRE': 'BRK.B', 'JOHNSON': 'JNJ', 'WALMART': 'WMT'
        }
        
        for company, ticker in company_map.items():
            if company in query_upper and ticker not in tickers:
                tickers.append(ticker)
        
        return list(set(tickers))
    
    def _determine_sources(self, query_lower: str, intent: QueryIntent) -> List[str]:
        """Determine which data sources are needed"""
        sources = [DataSource.DATABASE.value]  # Always use database
        
        # Add sources based on keywords and intent
        if any(word in query_lower for word in ['price', 'current', 'today', 'now', 'real-time']):
            sources.append(DataSource.YAHOO_FINANCE.value)
        
        if any(word in query_lower for word in ['sentiment', 'social', 'trending', 'buzz']):
            sources.append(DataSource.MASSIVE.value)
        
        if any(word in query_lower for word in ['news', 'announcement', 'alert', 'latest']):
            sources.append(DataSource.INTELLIGENCE.value)
        
        if any(word in query_lower for word in ['predict', 'forecast', 'rating', 'score']):
            sources.append(DataSource.ML_SERVICE.value)
        
        # Intent-based source selection
        if intent in [QueryIntent.BUY_RECOMMENDATION, QueryIntent.SELL_RECOMMENDATION]:
            # Need all sources for recommendations
            sources.extend([DataSource.YAHOO_FINANCE.value, DataSource.MASSIVE.value, 
                          DataSource.ML_SERVICE.value])
        elif intent == QueryIntent.SCREEN:
            sources.extend([DataSource.YAHOO_FINANCE.value, DataSource.ML_SERVICE.value])
        
        return list(set(sources))
    
    def _rewrite_queries(self, query: str, intent: QueryIntent, tickers: List[str]) -> List[str]:
        """Generate rewritten queries for better retrieval"""
        rewrites = [query]  # Include original
        
        if intent == QueryIntent.BUY_RECOMMENDATION:
            rewrites.extend([
                f"high dividend yield stocks with A+ safety rating",
                f"undervalued dividend stocks with growing payouts",
                f"dividend aristocrats near 52-week lows"
            ])
        elif intent == QueryIntent.SELL_RECOMMENDATION:
            rewrites.extend([
                f"dividend stocks with declining payout ratios",
                f"companies at risk of dividend cuts",
                f"overvalued dividend stocks with negative momentum"
            ])
        elif intent == QueryIntent.SCREEN:
            rewrites.extend([
                f"dividend stocks meeting criteria: {query}",
                f"filter dividend paying companies by {query}",
                f"screen for high quality dividend stocks"
            ])
        
        # Add ticker-specific queries
        for ticker in tickers[:3]:  # Limit to avoid too many queries
            rewrites.append(f"{ticker} dividend history safety rating forecast")
        
        return rewrites[:5]  # Return max 5 queries
    
    def _calculate_confidence(self, query: str, tickers: List[str], intent: QueryIntent) -> float:
        """Calculate confidence score for query analysis"""
        score = 0.5  # Base score
        
        # Clear intent boosts confidence
        if intent != QueryIntent.ANALYZE:
            score += 0.2
        
        # Having tickers boosts confidence
        if tickers:
            score += min(0.2, len(tickers) * 0.05)
        
        # Query length and specificity
        if len(query.split()) > 5:
            score += 0.1
        
        return min(1.0, score)


class DatabaseRetriever:
    """Retrieves data from Azure SQL database"""
    
    def __init__(self):
        self.config = {
            'server': os.getenv('SQLSERVER_HOST', 'heydividend.database.windows.net'),
            'database': os.getenv('SQLSERVER_DB', 'heydividend'),
            'user': os.getenv('SQLSERVER_USER', 'sqladmin'),
            'password': os.getenv('SQLSERVER_PASSWORD', ''),
            'timeout': 30,
            'login_timeout': 10
        }
        self.executor = ThreadPoolExecutor(max_workers=3)
    
    def _connect(self):
        """Create database connection"""
        return pymssql.connect(**self.config)
    
    async def get_ml_ratings(self, tickers: List[str] = None) -> Dict[str, Any]:
        """Get ML payout ratings for tickers or top-rated stocks if no tickers specified"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self._get_ml_ratings_sync, tickers)
    
    def _get_ml_ratings_sync(self, tickers: List[str] = None) -> Dict[str, Any]:
        """Synchronous database query for ML ratings"""
        conn = self._connect()
        cursor = conn.cursor(as_dict=True)
        
        if tickers:
            # Query for specific tickers
            placeholders = ','.join(['%s'] * len(tickers))
            query = f"""
                SELECT ticker, rating, confidence_score, updated_at
                FROM ml_payout_ratings
                WHERE ticker IN ({placeholders})
                AND updated_at >= DATEADD(day, -7, GETDATE())
                ORDER BY ticker, updated_at DESC
            """
            cursor.execute(query, tickers)
        else:
            # No tickers specified - get top-rated stocks for screening
            query = """
                SELECT TOP 20 ticker, rating, confidence_score, updated_at
                FROM ml_payout_ratings
                WHERE rating IN ('A+', 'A', 'B')
                AND updated_at >= DATEADD(day, -7, GETDATE())
                ORDER BY 
                    CASE rating 
                        WHEN 'A+' THEN 1 
                        WHEN 'A' THEN 2 
                        WHEN 'B' THEN 3 
                    END, 
                    confidence_score DESC
            """
            cursor.execute(query)
        
        results = cursor.fetchall()
        conn.close()
        
        # Group by ticker, taking most recent
        ratings = {}
        for row in results:
            ticker = row['ticker']
            if ticker not in ratings:
                ratings[ticker] = {
                    'rating': row['rating'],
                    'confidence': row['confidence_score'],
                    'updated': row['updated_at'].isoformat() if row['updated_at'] else None
                }
        
        return ratings
    
    async def get_dividend_history(self, tickers: List[str], limit: int = 10) -> Dict[str, Any]:
        """Get dividend payment history"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self._get_dividend_history_sync, tickers, limit)
    
    def _get_dividend_history_sync(self, tickers: List[str], limit: int) -> Dict[str, Any]:
        """Synchronous query for dividend history"""
        if not tickers:
            return {}
        
        conn = self._connect()
        cursor = conn.cursor(as_dict=True)
        
        placeholders = ','.join(['%s'] * len(tickers))
        query = f"""
            SELECT ticker, ex_date, payment_date, amount, frequency
            FROM dividends
            WHERE ticker IN ({placeholders})
            ORDER BY ticker, ex_date DESC
        """
        
        cursor.execute(query, tickers)
        results = cursor.fetchall()
        conn.close()
        
        # Group by ticker
        history = defaultdict(list)
        for row in results:
            history[row['ticker']].append({
                'ex_date': row['ex_date'].isoformat() if row['ex_date'] else None,
                'payment_date': row['payment_date'].isoformat() if row['payment_date'] else None,
                'amount': float(row['amount']) if row['amount'] else 0,
                'frequency': row['frequency']
            })
        
        # Limit results per ticker
        return {ticker: divs[:limit] for ticker, divs in history.items()}
    
    async def get_intelligence_alerts(self, tickers: List[str] = None) -> List[Dict[str, Any]]:
        """Get latest dividend intelligence alerts"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self._get_intelligence_alerts_sync, tickers)
    
    def _get_intelligence_alerts_sync(self, tickers: List[str] = None) -> List[Dict[str, Any]]:
        """Synchronous query for intelligence alerts"""
        conn = self._connect()
        cursor = conn.cursor(as_dict=True)
        
        query = """
            SELECT TOP 10 scan_data
            FROM dividend_intelligence
            WHERE scan_timestamp >= DATEADD(day, -1, GETDATE())
            ORDER BY scan_timestamp DESC
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        
        alerts = []
        for row in results:
            try:
                data = json.loads(row['scan_data'])
                if 'alerts' in data:
                    for alert in data['alerts']:
                        # Filter by tickers if provided
                        if not tickers or any(t in alert.get('tickers', []) for t in tickers):
                            alerts.append(alert)
            except:
                pass
        
        return alerts[:10]  # Return top 10 alerts


class YahooFinanceRetriever:
    """Retrieves real-time data from Yahoo Finance"""
    
    def __init__(self):
        self.cache = {}  # Simple in-memory cache
    
    async def get_quotes(self, tickers: List[str]) -> Dict[str, Any]:
        """Get real-time quotes for tickers"""
        if not tickers:
            return {}
        
        # Check cache
        quotes = {}
        fetch_tickers = []
        now = time.time()
        
        for ticker in tickers:
            cache_key = f"quote_{ticker}"
            if cache_key in self.cache:
                cached, timestamp = self.cache[cache_key]
                if now - timestamp < CACHE_TTL_SECONDS['quote']:
                    quotes[ticker] = cached
                    continue
            fetch_tickers.append(ticker)
        
        # Fetch missing quotes
        if fetch_tickers:
            loop = asyncio.get_event_loop()
            new_quotes = await loop.run_in_executor(None, self._fetch_quotes_sync, fetch_tickers)
            quotes.update(new_quotes)
            
            # Update cache
            for ticker, data in new_quotes.items():
                self.cache[f"quote_{ticker}"] = (data, now)
        
        return quotes
    
    def _fetch_quotes_sync(self, tickers: List[str]) -> Dict[str, Any]:
        """Synchronously fetch quotes from Yahoo Finance"""
        quotes = {}
        
        try:
            # Batch fetch for efficiency
            ticker_str = ' '.join(tickers[:YAHOO_BATCH_SIZE])
            data = yf.download(ticker_str, period='1d', interval='1d', 
                             progress=False)
            
            if len(tickers) == 1:
                # Single ticker result
                ticker = tickers[0]
                if not data.empty:
                    quotes[ticker] = self._extract_quote_data(data, ticker)
            else:
                # Multiple tickers
                for ticker in tickers:
                    if ticker in data.columns.levels[1]:
                        ticker_data = data.xs(ticker, level=1, axis=1)
                        quotes[ticker] = self._extract_quote_data(ticker_data, ticker)
            
            # Get additional info for each ticker
            for ticker in tickers:
                try:
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    
                    if ticker in quotes:
                        quotes[ticker].update({
                            'dividend_yield': info.get('dividendYield', 0),
                            'forward_yield': info.get('trailingAnnualDividendYield', 0),
                            'payout_ratio': info.get('payoutRatio', 0),
                            'pe_ratio': info.get('forwardPE', info.get('trailingPE', 0)),
                            'market_cap': info.get('marketCap', 0),
                            '52_week_high': info.get('fiftyTwoWeekHigh', 0),
                            '52_week_low': info.get('fiftyTwoWeekLow', 0)
                        })
                except:
                    pass  # Continue if individual ticker fails
                    
        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance data: {e}")
        
        return quotes
    
    def _extract_quote_data(self, data, ticker: str) -> Dict[str, Any]:
        """Extract quote data from DataFrame"""
        try:
            latest = data.iloc[-1] if not data.empty else None
            if latest is not None:
                return {
                    'ticker': ticker,
                    'price': float(latest.get('Close', 0)),
                    'volume': int(latest.get('Volume', 0)),
                    'open': float(latest.get('Open', 0)),
                    'high': float(latest.get('High', 0)),
                    'low': float(latest.get('Low', 0)),
                    'timestamp': datetime.now().isoformat()
                }
        except:
            pass
        
        return {
            'ticker': ticker,
            'price': 0,
            'error': 'Data unavailable'
        }


class MassiveAPIClient:
    """Client for Massive.com sentiment API"""
    
    def __init__(self):
        self.api_key = os.getenv('MASSIVE_API_KEY', '')
        self.base_url = MASSIVE_API_URL
        self.cache = {}
        
    async def get_sentiment(self, tickers: List[str]) -> Dict[str, Any]:
        """Get sentiment scores for tickers"""
        if not self.api_key or not tickers:
            return {}
        
        sentiments = {}
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for ticker in tickers:
                # Check cache first
                cache_key = f"sentiment_{ticker}"
                if cache_key in self.cache:
                    cached, timestamp = self.cache[cache_key]
                    if time.time() - timestamp < CACHE_TTL_SECONDS['sentiment']:
                        sentiments[ticker] = cached
                        continue
                
                tasks.append(self._fetch_sentiment(session, ticker))
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for ticker, result in zip([t for t in tickers if f"sentiment_{t}" not in self.cache], results):
                    if not isinstance(result, Exception):
                        sentiments[ticker] = result
                        self.cache[f"sentiment_{ticker}"] = (result, time.time())
        
        return sentiments
    
    async def _fetch_sentiment(self, session: aiohttp.ClientSession, ticker: str) -> Dict[str, Any]:
        """Fetch sentiment for a single ticker"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            async with session.get(
                f"{self.base_url}/sentiment/{ticker}",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'sentiment_score': data.get('score', 0),
                        'sentiment_label': data.get('label', 'neutral'),
                        'buzz_volume': data.get('buzz', 0),
                        'momentum': data.get('momentum', 0),
                        'sources': data.get('sources', 0)
                    }
                else:
                    return {'error': f'API returned {response.status}'}
        except Exception as e:
            logger.error(f"Error fetching Massive sentiment for {ticker}: {e}")
            return {'error': str(e)}


class RetrievalOrchestrator:
    """Orchestrates parallel data retrieval from multiple sources"""
    
    def __init__(self):
        self.db_retriever = DatabaseRetriever()
        self.yahoo_retriever = YahooFinanceRetriever()
        self.massive_client = MassiveAPIClient()
        
    async def retrieve_data(self, query_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve data from all required sources in parallel"""
        tickers = query_analysis['tickers']
        sources = query_analysis['required_sources']
        intent = query_analysis.get('intent', 'analyze')
        
        # Initialize combined_data
        combined_data = {
            'timestamp': datetime.now().isoformat(),
            'query_analysis': query_analysis
        }
        
        # For screening queries without specific tickers, first get top candidates
        if not tickers and intent in ['screen', 'buy', 'sell']:
            # Get top-rated stocks first
            ml_ratings = await self.db_retriever.get_ml_ratings(None)
            tickers = list(ml_ratings.keys())[:10]  # Use top 10 for further analysis
            query_analysis['discovered_tickers'] = tickers
            combined_data['ml_ratings'] = ml_ratings  # Store the ratings we already fetched
            logger.info(f"Discovered {len(tickers)} tickers for screening query")
        
        tasks = []
        task_labels = []
        
        # Database tasks
        if DataSource.DATABASE.value in sources:
            # If we already fetched ML ratings for discovery, skip fetching again
            if 'ml_ratings' not in combined_data:
                tasks.append(self.db_retriever.get_ml_ratings(tickers))
                task_labels.append('ml_ratings')
            
            if tickers:  # Only get history if we have tickers
                tasks.append(self.db_retriever.get_dividend_history(tickers))
                task_labels.append('dividend_history')
            
            tasks.append(self.db_retriever.get_intelligence_alerts(tickers if tickers else None))
            task_labels.append('alerts')
        
        # Yahoo Finance tasks (only if we have tickers)
        if DataSource.YAHOO_FINANCE.value in sources and tickers:
            tasks.append(self.yahoo_retriever.get_quotes(tickers))
            task_labels.append('quotes')
        
        # Massive.com tasks (only if we have tickers)
        if DataSource.MASSIVE.value in sources and tickers:
            tasks.append(self.massive_client.get_sentiment(tickers))
            task_labels.append('sentiment')
        
        # Execute all tasks in parallel
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            results = []
        
        # Add results to combined_data
        for label, result in zip(task_labels, results):
            if isinstance(result, Exception):
                logger.error(f"Error retrieving {label}: {result}")
                combined_data[label] = {}
            else:
                combined_data[label] = result
        
        return combined_data


class IntelligentReranker:
    """Reranks and scores results based on multiple factors"""
    
    def __init__(self):
        self.weight_configs = {
            QueryIntent.BUY_RECOMMENDATION: {
                'safety': 0.4,
                'yield': 0.25,
                'sentiment': 0.15,
                'value': 0.1,
                'momentum': 0.1
            },
            QueryIntent.SELL_RECOMMENDATION: {
                'safety': 0.3,
                'sentiment': 0.3,
                'momentum': 0.2,
                'value': 0.1,
                'yield': 0.1
            },
            QueryIntent.ANALYZE: {
                'safety': 0.3,
                'yield': 0.3,
                'sentiment': 0.2,
                'value': 0.1,
                'momentum': 0.1
            }
        }
    
    async def rerank(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Rerank results based on intent and scoring"""
        query_analysis = data['query_analysis']
        intent = QueryIntent[query_analysis['intent'].upper()]
        
        # Extract all unique tickers from data
        all_tickers = set()
        if 'ml_ratings' in data:
            all_tickers.update(data['ml_ratings'].keys())
        if 'quotes' in data:
            all_tickers.update(data['quotes'].keys())
        if 'sentiment' in data:
            all_tickers.update(data['sentiment'].keys())
        
        # Score each ticker
        scored_results = []
        for ticker in all_tickers:
            score_components = self._calculate_scores(ticker, data)
            
            # Apply weights based on intent
            weights = self.weight_configs.get(intent, self.weight_configs[QueryIntent.ANALYZE])
            total_score = sum(
                score_components.get(factor, 0) * weight 
                for factor, weight in weights.items()
            )
            
            result = {
                'ticker': ticker,
                'total_score': total_score,
                'score_components': score_components,
                'data': self._aggregate_ticker_data(ticker, data)
            }
            
            scored_results.append(result)
        
        # Sort by total score
        scored_results.sort(key=lambda x: x['total_score'], reverse=True)
        
        return scored_results
    
    def _calculate_scores(self, ticker: str, data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate individual scoring components"""
        scores = {}
        
        # Safety score from ML ratings
        if 'ml_ratings' in data and ticker in data['ml_ratings']:
            rating = data['ml_ratings'][ticker]['rating']
            rating_scores = {'A+': 1.0, 'A': 0.8, 'B': 0.6, 'C': 0.4}
            scores['safety'] = rating_scores.get(rating, 0.3)
        else:
            scores['safety'] = 0.5  # Default neutral
        
        # Yield score
        if 'quotes' in data and ticker in data['quotes']:
            quote = data['quotes'][ticker]
            yield_val = quote.get('dividend_yield', 0) * 100  # Convert to percentage
            if yield_val > 0:
                # Score based on yield (cap at 10%)
                scores['yield'] = min(1.0, yield_val / 10)
            else:
                scores['yield'] = 0
        else:
            scores['yield'] = 0.3  # Default low
        
        # Sentiment score
        if 'sentiment' in data and ticker in data['sentiment']:
            sent = data['sentiment'][ticker]
            if 'sentiment_score' in sent:
                # Convert -1 to 1 range to 0 to 1
                scores['sentiment'] = (sent['sentiment_score'] + 1) / 2
            else:
                scores['sentiment'] = 0.5
        else:
            scores['sentiment'] = 0.5  # Default neutral
        
        # Value score (based on P/E ratio)
        if 'quotes' in data and ticker in data['quotes']:
            quote = data['quotes'][ticker]
            pe = quote.get('pe_ratio', 0)
            if pe > 0:
                # Lower P/E is better (inverse scoring)
                if pe < 15:
                    scores['value'] = 1.0
                elif pe < 20:
                    scores['value'] = 0.8
                elif pe < 25:
                    scores['value'] = 0.6
                elif pe < 30:
                    scores['value'] = 0.4
                else:
                    scores['value'] = 0.2
            else:
                scores['value'] = 0.5
        else:
            scores['value'] = 0.5
        
        # Momentum score (based on 52-week position)
        if 'quotes' in data and ticker in data['quotes']:
            quote = data['quotes'][ticker]
            price = quote.get('price', 0)
            high_52 = quote.get('52_week_high', 0)
            low_52 = quote.get('52_week_low', 0)
            
            if high_52 > low_52 and price > 0:
                # Position within 52-week range
                position = (price - low_52) / (high_52 - low_52)
                # Good momentum if in middle range (not too high, not too low)
                if 0.3 <= position <= 0.7:
                    scores['momentum'] = 0.8
                elif 0.2 <= position <= 0.8:
                    scores['momentum'] = 0.6
                else:
                    scores['momentum'] = 0.4
            else:
                scores['momentum'] = 0.5
        else:
            scores['momentum'] = 0.5
        
        return scores
    
    def _aggregate_ticker_data(self, ticker: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate all data for a ticker"""
        aggregated = {'ticker': ticker}
        
        # Add ML ratings
        if 'ml_ratings' in data and ticker in data['ml_ratings']:
            aggregated['ml_rating'] = data['ml_ratings'][ticker]
        
        # Add quotes
        if 'quotes' in data and ticker in data['quotes']:
            aggregated['quote'] = data['quotes'][ticker]
        
        # Add sentiment
        if 'sentiment' in data and ticker in data['sentiment']:
            aggregated['sentiment'] = data['sentiment'][ticker]
        
        # Add dividend history
        if 'dividend_history' in data and ticker in data['dividend_history']:
            aggregated['dividend_history'] = data['dividend_history'][ticker][:5]  # Last 5
        
        return aggregated


class ComplianceManager:
    """Manages disclaimers and compliance requirements"""
    
    DISCLAIMERS = {
        'buy': """
INVESTMENT DISCLAIMER: This analysis is for educational and informational purposes only and should not be considered as personalized investment advice. Past performance does not guarantee future results. Dividend payments are not guaranteed and can be reduced or eliminated at any time. Please consult with a qualified financial advisor before making any investment decisions. All investments carry risk, including potential loss of principal.
        """.strip(),
        
        'sell': """
TRADING DISCLAIMER: This analysis is for educational purposes only. The decision to sell any security should be based on your individual financial situation, investment objectives, and risk tolerance. Please consult with a qualified financial advisor before making any trading decisions. Tax implications may apply to the sale of securities.
        """.strip(),
        
        'general': """
DISCLAIMER: This information is provided for educational purposes only and does not constitute financial advice. Always conduct your own research and consult with qualified professionals before making investment decisions.
        """.strip()
    }
    
    def add_disclaimer(self, response: Dict[str, Any], intent: str) -> Dict[str, Any]:
        """Add appropriate disclaimer based on intent"""
        if intent in ['buy', 'sell']:
            response['disclaimer'] = self.DISCLAIMERS[intent]
            response['disclaimer_type'] = intent
        else:
            response['disclaimer'] = self.DISCLAIMERS['general']
            response['disclaimer_type'] = 'general'
        
        response['compliance_timestamp'] = datetime.now().isoformat()
        return response
    
    def add_source_attribution(self, response: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Add source attribution for transparency"""
        sources = []
        
        if 'ml_ratings' in data and data['ml_ratings']:
            sources.append("Harvey ML Models (updated daily)")
        
        if 'quotes' in data and data['quotes']:
            sources.append("Yahoo Finance (real-time)")
        
        if 'sentiment' in data and data['sentiment']:
            sources.append("Massive.com Sentiment Analysis")
        
        if 'dividend_history' in data and data['dividend_history']:
            sources.append("Harvey Database (historical data)")
        
        if 'alerts' in data and data['alerts']:
            sources.append("Harvey Intelligence Scanner (daily)")
        
        response['data_sources'] = sources
        response['data_freshness'] = {
            'retrieved_at': datetime.now().isoformat(),
            'cache_ttl_seconds': CACHE_TTL_SECONDS
        }
        
        return response


class SelfEvaluationLoop:
    """Self-evaluation and quality control loop"""
    
    def __init__(self):
        self.min_confidence_threshold = 0.6
        self.max_retries = 2
        
    async def evaluate(self, response: Dict[str, Any], original_query: str) -> Tuple[bool, Dict[str, Any]]:
        """Evaluate response quality and completeness"""
        evaluation = {
            'passed': True,
            'confidence': 0.0,
            'issues': [],
            'recommendations': []
        }
        
        # Check data freshness
        if 'data_freshness' in response:
            retrieved_at = datetime.fromisoformat(response['data_freshness']['retrieved_at'])
            age_minutes = (datetime.now() - retrieved_at).total_seconds() / 60
            if age_minutes > 30:
                evaluation['issues'].append(f"Data is {age_minutes:.0f} minutes old")
                evaluation['passed'] = False
        
        # Check compliance
        if 'needs_disclaimer' in response.get('query_analysis', {}):
            if response['query_analysis']['needs_disclaimer'] and 'disclaimer' not in response:
                evaluation['issues'].append("Missing required disclaimer")
                evaluation['passed'] = False
        
        # Check data completeness
        if 'ranked_results' in response:
            results = response['ranked_results']
            if not results:
                evaluation['issues'].append("No results found")
                evaluation['passed'] = False
            else:
                # Check if we have sufficient data for top results
                for result in results[:3]:
                    if 'data' not in result or not result['data']:
                        evaluation['issues'].append(f"Incomplete data for {result.get('ticker', 'unknown')}")
                        evaluation['recommendations'].append("Retry with additional data sources")
        
        # Calculate confidence
        confidence_factors = []
        
        # Query analysis confidence
        if 'query_analysis' in response:
            confidence_factors.append(response['query_analysis'].get('confidence', 0.5))
        
        # Data availability confidence
        data_sources_count = len(response.get('data_sources', []))
        confidence_factors.append(min(1.0, data_sources_count / 3))  # Expect at least 3 sources
        
        # Result quality confidence
        if 'ranked_results' in response and response['ranked_results']:
            top_score = response['ranked_results'][0].get('total_score', 0)
            confidence_factors.append(min(1.0, top_score))
        
        evaluation['confidence'] = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0
        
        # Check if confidence meets threshold
        if evaluation['confidence'] < self.min_confidence_threshold:
            evaluation['issues'].append(f"Low confidence: {evaluation['confidence']:.2f}")
            evaluation['recommendations'].append("Consider broadening search or using additional data sources")
            evaluation['passed'] = False
        
        # Add evaluation to response
        response['evaluation'] = evaluation
        
        return evaluation['passed'], response


class HarveyRAGEnrichmentSystem:
    """Main orchestrator for the Agentic RAG system"""
    
    def __init__(self):
        self.query_analyzer = QueryAnalyzer()
        self.orchestrator = RetrievalOrchestrator()
        self.reranker = IntelligentReranker()
        self.compliance = ComplianceManager()
        self.evaluator = SelfEvaluationLoop()
        
    async def process_query(self, query: str, retry_count: int = 0) -> Dict[str, Any]:
        """Process user query through the entire RAG pipeline"""
        
        try:
            # Step 1: Analyze query
            logger.info(f"Analyzing query: {query}")
            query_analysis = await self.query_analyzer.analyze_query(query)
            
            # Step 2: Retrieve data from multiple sources
            logger.info(f"Retrieving data from sources: {query_analysis['required_sources']}")
            data = await self.orchestrator.retrieve_data(query_analysis)
            
            # Step 3: Rerank results
            logger.info("Reranking results...")
            ranked_results = await self.reranker.rerank(data)
            
            # Step 4: Build response
            response = {
                'query': query,
                'query_analysis': query_analysis,
                'ranked_results': ranked_results[:10],  # Top 10 results
                'timestamp': datetime.now().isoformat()
            }
            
            # Step 5: Add compliance
            intent = query_analysis['intent']
            response = self.compliance.add_disclaimer(response, intent)
            response = self.compliance.add_source_attribution(response, data)
            
            # Step 6: Self-evaluation
            logger.info("Running self-evaluation...")
            passed, response = await self.evaluator.evaluate(response, query)
            
            if not passed and retry_count < self.evaluator.max_retries:
                logger.warning(f"Evaluation failed, retrying... (attempt {retry_count + 1})")
                # Modify query or strategy based on issues
                if "No results found" in response['evaluation']['issues']:
                    # Broaden search
                    modified_query = f"{query} dividend stocks high yield"
                    return await self.process_query(modified_query, retry_count + 1)
                elif "Low confidence" in str(response['evaluation']['issues']):
                    # Add more sources
                    query_analysis['required_sources'].extend([
                        DataSource.YAHOO_FINANCE.value,
                        DataSource.MASSIVE.value
                    ])
                    return await self.process_query(query, retry_count + 1)
            
            response['success'] = passed
            response['retry_count'] = retry_count
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                'error': str(e),
                'query': query,
                'success': False,
                'timestamp': datetime.now().isoformat()
            }
    
    async def generate_recommendation(self, response: Dict[str, Any]) -> str:
        """Generate human-readable recommendation from processed data"""
        if not response.get('success', False):
            return "Unable to generate recommendation due to insufficient data or system error."
        
        results = response.get('ranked_results', [])
        if not results:
            return "No suitable dividend stocks found matching your criteria."
        
        intent = response['query_analysis']['intent']
        
        # Build recommendation text
        lines = []
        
        if intent == 'buy':
            lines.append("📈 **BUY RECOMMENDATIONS**\n")
            lines.append("Based on comprehensive analysis of safety ratings, yields, and market sentiment:\n")
        elif intent == 'sell':
            lines.append("📉 **SELL ANALYSIS**\n")
            lines.append("Based on dividend sustainability and market conditions:\n")
        else:
            lines.append("📊 **DIVIDEND ANALYSIS**\n")
        
        # Add top 3 recommendations
        for i, result in enumerate(results[:3], 1):
            ticker = result['ticker']
            score = result['total_score']
            data = result['data']
            
            lines.append(f"\n**{i}. {ticker}** (Score: {score:.2f}/1.00)")
            
            # Add key metrics
            if 'ml_rating' in data:
                lines.append(f"   • Safety Rating: {data['ml_rating']['rating']}")
            
            if 'quote' in data and data['quote']:
                quote = data['quote']
                lines.append(f"   • Current Price: ${quote.get('price', 'N/A')}")
                if 'dividend_yield' in quote:
                    lines.append(f"   • Dividend Yield: {quote['dividend_yield']*100:.2f}%")
            
            if 'sentiment' in data and data['sentiment']:
                sent = data['sentiment']
                lines.append(f"   • Market Sentiment: {sent.get('sentiment_label', 'neutral').title()}")
            
            # Add brief recommendation
            components = result['score_components']
            if components.get('safety', 0) > 0.8 and components.get('yield', 0) > 0.5:
                lines.append(f"   ✓ Strong dividend safety with attractive yield")
            elif components.get('momentum', 0) > 0.7:
                lines.append(f"   ✓ Positive momentum with stable dividends")
            else:
                lines.append(f"   ✓ Established dividend payer")
        
        # Add data sources
        lines.append(f"\n**Data Sources:** {', '.join(response.get('data_sources', []))}")
        lines.append(f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC")
        
        # Add disclaimer if needed
        if 'disclaimer' in response:
            lines.append(f"\n---\n*{response['disclaimer']}*")
        
        return '\n'.join(lines)


# FastAPI Integration
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(title="Harvey RAG Enrichment API", version="1.0.0")

# Global RAG system instance
rag_system = None

class QueryRequest(BaseModel):
    query: str
    include_raw_data: bool = False

class QueryResponse(BaseModel):
    success: bool
    recommendation: str
    confidence: float = None
    data_sources: List[str] = None
    disclaimer: str = None
    raw_data: Dict = None

@app.on_event("startup")
async def startup_event():
    """Initialize RAG system on startup"""
    global rag_system
    rag_system = HarveyRAGEnrichmentSystem()
    logger.info("Harvey RAG Enrichment System initialized")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Harvey RAG Enrichment System"}

@app.post("/v1/rag/analyze", response_model=QueryResponse)
async def analyze_query(
    request: QueryRequest,
    x_api_key: str = Header(None, alias="X-API-Key")
):
    """
    Analyze a query using the Agentic RAG enrichment system
    """
    # Validate API key
    expected_key = os.getenv('HARVEY_AI_API_KEY', '')
    if not x_api_key or x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        # Process query through RAG pipeline
        result = await rag_system.process_query(request.query)
        
        # Generate recommendation
        recommendation = await rag_system.generate_recommendation(result)
        
        response = QueryResponse(
            success=result.get('success', False),
            recommendation=recommendation,
            confidence=result.get('evaluation', {}).get('confidence'),
            data_sources=result.get('data_sources', []),
            disclaimer=result.get('disclaimer')
        )
        
        # Include raw data if requested
        if request.include_raw_data:
            response.raw_data = result
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/rag/cache-stats")
async def get_cache_stats(x_api_key: str = Header(None, alias="X-API-Key")):
    """Get cache statistics"""
    expected_key = os.getenv('HARVEY_AI_API_KEY', '')
    if not x_api_key or x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    stats = {
        'yahoo_cache_size': len(rag_system.orchestrator.yahoo_retriever.cache),
        'massive_cache_size': len(rag_system.orchestrator.massive_client.cache),
        'cache_ttl': CACHE_TTL_SECONDS
    }
    return stats


if __name__ == "__main__":
    import uvicorn
    
    # For testing locally
    async def test_queries():
        """Test the RAG system with sample queries"""
        rag = HarveyRAGEnrichmentSystem()
        
        test_queries = [
            "What are the best dividend stocks to buy today?",
            "Should I sell AAPL?",
            "Analyze MSFT dividend safety",
            "Find high-yield dividend stocks with positive sentiment"
        ]
        
        for query in test_queries:
            print(f"\n{'='*60}")
            print(f"Query: {query}")
            print('='*60)
            
            result = await rag.process_query(query)
            recommendation = await rag.generate_recommendation(result)
            
            print(recommendation)
            
            if result.get('evaluation'):
                print(f"\nConfidence: {result['evaluation']['confidence']:.2%}")
                if result['evaluation']['issues']:
                    print(f"Issues: {', '.join(result['evaluation']['issues'])}")
    
    # Run test if executed directly
    # asyncio.run(test_queries())
    
    # Or run the API server
    uvicorn.run(app, host="0.0.0.0", port=8002)