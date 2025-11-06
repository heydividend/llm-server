"""
Model Audit Service - Dividend-Focused Learning System
Logs all 5 AI model responses for dividend queries to create training data.
Harvey learns which models excel at specific dividend analysis tasks.
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
import logging

logger = logging.getLogger(__name__)


class DividendModelAuditor:
    """
    Audits and logs AI model responses for dividend-focused queries.
    Creates training data to make Harvey the world's best dividend AI.
    """
    
    def __init__(self):
        self.db_connection_string = self._build_connection_string()
        self.engine = None
        if self.db_connection_string:
            try:
                self.engine = create_engine(
                    self.db_connection_string,
                    poolclass=NullPool,
                    pool_pre_ping=True
                )
            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")
    
    def _build_connection_string(self) -> Optional[str]:
        """Build SQL Server connection string from environment variables."""
        host = os.getenv("SQLSERVER_HOST")
        user = os.getenv("SQLSERVER_USER")
        password = os.getenv("SQLSERVER_PASSWORD")
        db = os.getenv("SQLSERVER_DB")
        
        if not all([host, user, password, db]):
            logger.warning("Missing database credentials for model auditing")
            return None
        
        return f"mssql+pyodbc://{user}:{password}@{host}/{db}?driver=ODBC+Driver+17+for+SQL+Server"
    
    def is_dividend_query(self, query: str) -> bool:
        """
        Determine if a query is dividend-related.
        Harvey's specialty: passive income and dividend investing.
        """
        dividend_keywords = [
            'dividend', 'yield', 'payout', 'income', 'passive',
            'distribution', 'ex-date', 'payment date', 'aristocrat',
            'monthly income', 'quarterly dividend', 'drip', 'reinvest',
            'tax efficient', 'qualified dividend', 'ordinary dividend',
            'dividend growth', 'dividend safety', 'payout ratio',
            'dividend cut', 'dividend king', 'dividend champion',
            'income ladder', 'cash flow', 'dividend coverage',
            'reit dividend', 'mlp distribution', 'bdc dividend'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in dividend_keywords)
    
    def extract_dividend_metrics(self, response: str, model_name: str) -> Dict[str, Any]:
        """
        Extract dividend-specific metrics from AI model response.
        Parses yield, payout ratio, growth rate, safety scores, etc.
        """
        metrics = {
            'model_name': model_name,
            'dividend_yield': None,
            'payout_ratio': None,
            'dividend_growth_rate': None,
            'safety_score': None,
            'forward_yield': None,
            'annual_dividend': None,
            'quarterly_dividend': None,
            'monthly_dividend': None,
            'ex_date': None,
            'payment_date': None,
            'has_income_projection': False,
            'mentions_aristocrat': False,
            'mentions_safety': False,
            'mentions_tax': False
        }
        
        # Extract dividend yield (e.g., "3.5%", "yield of 4.2%")
        yield_patterns = [
            r'yield[:\s]+(\d+\.?\d*)%',
            r'(\d+\.?\d*)%\s+yield',
            r'dividend yield[:\s]+(\d+\.?\d*)%'
        ]
        for pattern in yield_patterns:
            match = re.search(pattern, response.lower())
            if match:
                try:
                    metrics['dividend_yield'] = float(match.group(1))
                    break
                except:
                    pass
        
        # Extract payout ratio (e.g., "payout ratio: 45%", "45% payout")
        payout_patterns = [
            r'payout ratio[:\s]+(\d+\.?\d*)%',
            r'(\d+\.?\d*)%\s+payout',
            r'pays out (\d+\.?\d*)%'
        ]
        for pattern in payout_patterns:
            match = re.search(pattern, response.lower())
            if match:
                try:
                    metrics['payout_ratio'] = float(match.group(1))
                    break
                except:
                    pass
        
        # Extract dividend growth rate (e.g., "5% growth", "growing at 7%")
        growth_patterns = [
            r'dividend growth[:\s]+(\d+\.?\d*)%',
            r'growing at (\d+\.?\d*)%',
            r'(\d+\.?\d*)%\s+dividend growth'
        ]
        for pattern in growth_patterns:
            match = re.search(pattern, response.lower())
            if match:
                try:
                    metrics['dividend_growth_rate'] = float(match.group(1))
                    break
                except:
                    pass
        
        # Extract safety score (e.g., "A+", "B-", "safety score: 8/10")
        safety_patterns = [
            r'safety[:\s]+([A-F][+-]?)',
            r'grade[:\s]+([A-F][+-]?)',
            r'score[:\s]+(\d+)/10'
        ]
        for pattern in safety_patterns:
            match = re.search(pattern, response.lower())
            if match:
                metrics['safety_score'] = match.group(1)
                break
        
        # Extract annual dividend (e.g., "$4.50 annually", "$4.50/year")
        annual_patterns = [
            r'\$(\d+\.?\d*)\s+annual',
            r'\$(\d+\.?\d*)/year',
            r'annual dividend[:\s]+\$(\d+\.?\d*)'
        ]
        for pattern in annual_patterns:
            match = re.search(pattern, response.lower())
            if match:
                try:
                    metrics['annual_dividend'] = float(match.group(1))
                    break
                except:
                    pass
        
        # Detect key dividend features
        response_lower = response.lower()
        metrics['has_income_projection'] = any(term in response_lower for term in 
            ['income projection', 'monthly income', 'annual income', 'cash flow forecast'])
        metrics['mentions_aristocrat'] = any(term in response_lower for term in 
            ['dividend aristocrat', 'dividend king', 'dividend champion'])
        metrics['mentions_safety'] = any(term in response_lower for term in 
            ['dividend safety', 'cut risk', 'payout sustainable', 'dividend coverage'])
        metrics['mentions_tax'] = any(term in response_lower for term in 
            ['qualified dividend', 'tax efficient', 'withholding tax', 'ordinary dividend'])
        
        return metrics
    
    def log_multi_model_response(
        self,
        query: str,
        model_responses: Dict[str, str],
        selected_model: str,
        selected_response: str,
        routing_reason: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Optional[int]:
        """
        Log responses from all 5 models for a dividend query.
        Creates training data for Harvey's learning system.
        
        Args:
            query: User's dividend-related question
            model_responses: Dict of {model_name: response} from all available models
            selected_model: Which model was chosen by the router
            selected_response: The response that was shown to the user
            routing_reason: Why the router picked this model
            user_id: Optional user identifier
            session_id: Optional session identifier
        
        Returns:
            Audit log ID if successful, None otherwise
        """
        # Only log dividend-focused queries
        if not self.is_dividend_query(query):
            return None
        
        if not self.engine:
            logger.warning("No database connection for model auditing")
            return None
        
        try:
            # Extract dividend metrics from each model's response
            model_metrics = {}
            for model_name, response in model_responses.items():
                model_metrics[model_name] = self.extract_dividend_metrics(response, model_name)
            
            # Prepare data for storage
            audit_data = {
                'query': query[:1000],  # Limit length
                'selected_model': selected_model,
                'routing_reason': routing_reason[:500],
                'model_responses_json': json.dumps(model_responses),
                'dividend_metrics_json': json.dumps(model_metrics),
                'user_id': user_id,
                'session_id': session_id,
                'created_at': datetime.utcnow()
            }
            
            # Insert into database
            insert_sql = text("""
                INSERT INTO dividend_model_audit_log (
                    query, selected_model, routing_reason, 
                    model_responses_json, dividend_metrics_json,
                    user_id, session_id, created_at
                )
                OUTPUT INSERTED.id
                VALUES (
                    :query, :selected_model, :routing_reason,
                    :model_responses_json, :dividend_metrics_json,
                    :user_id, :session_id, :created_at
                )
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(insert_sql, audit_data)
                conn.commit()
                audit_id = result.scalar()
                
                logger.info(f"Logged multi-model dividend analysis (ID: {audit_id}) for query: {query[:50]}...")
                return audit_id
                
        except Exception as e:
            logger.error(f"Failed to log model audit: {e}")
            return None
    
    def get_training_samples(
        self,
        min_rating: float = 4.0,
        limit: int = 1000,
        dividend_focus: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve high-quality training samples for FinGPT fine-tuning.
        
        Args:
            min_rating: Minimum user rating (default: 4.0 stars)
            limit: Maximum samples to retrieve
            dividend_focus: Optional filter ('yield', 'safety', 'growth', 'income_planning')
        
        Returns:
            List of training samples with query, best_model, response, metrics
        """
        if not self.engine:
            return []
        
        try:
            # Build query with optional focus filter
            focus_filter = ""
            if dividend_focus == 'yield':
                focus_filter = "AND dm.dividend_yield IS NOT NULL"
            elif dividend_focus == 'safety':
                focus_filter = "AND (dm.mentions_safety = 1 OR dm.safety_score IS NOT NULL)"
            elif dividend_focus == 'growth':
                focus_filter = "AND dm.dividend_growth_rate IS NOT NULL"
            elif dividend_focus == 'income_planning':
                focus_filter = "AND dm.has_income_projection = 1"
            
            query_sql = text(f"""
                SELECT TOP :limit
                    a.id, a.query, a.selected_model, a.routing_reason,
                    a.model_responses_json, a.dividend_metrics_json,
                    f.rating, f.sentiment, f.comment,
                    a.created_at
                FROM dividend_model_audit_log a
                LEFT JOIN feedback f ON f.response_id = CAST(a.id AS VARCHAR(50))
                CROSS APPLY OPENJSON(a.dividend_metrics_json) 
                    WITH (
                        dividend_yield FLOAT,
                        mentions_safety BIT,
                        safety_score VARCHAR(10),
                        dividend_growth_rate FLOAT,
                        has_income_projection BIT
                    ) dm
                WHERE f.rating >= :min_rating {focus_filter}
                ORDER BY f.rating DESC, a.created_at DESC
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query_sql, {'limit': limit, 'min_rating': min_rating})
                samples = []
                
                for row in result:
                    samples.append({
                        'id': row.id,
                        'query': row.query,
                        'selected_model': row.selected_model,
                        'routing_reason': row.routing_reason,
                        'model_responses': json.loads(row.model_responses_json),
                        'dividend_metrics': json.loads(row.dividend_metrics_json),
                        'rating': row.rating,
                        'sentiment': row.sentiment,
                        'comment': row.comment,
                        'created_at': row.created_at
                    })
                
                logger.info(f"Retrieved {len(samples)} training samples (focus: {dividend_focus})")
                return samples
                
        except Exception as e:
            logger.error(f"Failed to retrieve training samples: {e}")
            return []
    
    def get_model_performance_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Get performance statistics for each model on dividend queries.
        Helps optimize routing and identify which models excel at what.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dict with per-model stats (avg_rating, query_count, specialties)
        """
        if not self.engine:
            return {}
        
        try:
            stats_sql = text("""
                SELECT 
                    a.selected_model,
                    COUNT(*) as query_count,
                    AVG(f.rating) as avg_rating,
                    SUM(CASE WHEN dm.dividend_yield IS NOT NULL THEN 1 ELSE 0 END) as yield_queries,
                    SUM(CASE WHEN dm.mentions_safety = 1 THEN 1 ELSE 0 END) as safety_queries,
                    SUM(CASE WHEN dm.dividend_growth_rate IS NOT NULL THEN 1 ELSE 0 END) as growth_queries,
                    SUM(CASE WHEN dm.has_income_projection = 1 THEN 1 ELSE 0 END) as income_queries
                FROM dividend_model_audit_log a
                LEFT JOIN feedback f ON f.response_id = CAST(a.id AS VARCHAR(50))
                CROSS APPLY OPENJSON(a.dividend_metrics_json) 
                    WITH (
                        dividend_yield FLOAT,
                        mentions_safety BIT,
                        dividend_growth_rate FLOAT,
                        has_income_projection BIT
                    ) dm
                WHERE a.created_at >= DATEADD(day, -:days, GETUTCDATE())
                GROUP BY a.selected_model
                ORDER BY avg_rating DESC
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(stats_sql, {'days': days})
                stats = {}
                
                for row in result:
                    stats[row.selected_model] = {
                        'query_count': row.query_count,
                        'avg_rating': float(row.avg_rating) if row.avg_rating else 0.0,
                        'specialties': {
                            'yield_analysis': row.yield_queries,
                            'safety_analysis': row.safety_queries,
                            'growth_analysis': row.growth_queries,
                            'income_planning': row.income_queries
                        }
                    }
                
                logger.info(f"Generated performance stats for {len(stats)} models")
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get model performance stats: {e}")
            return {}


# Global instance
dividend_auditor = DividendModelAuditor()
