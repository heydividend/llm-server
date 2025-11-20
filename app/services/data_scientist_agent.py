"""
Harvey AI - Data Scientist Agent
Analyzes Azure SQL database and recommends ML models, training improvements,
and data optimization strategies using AI-powered insights.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.pool import NullPool
import json

logger = logging.getLogger("data_scientist_agent")


class DataScientistAgent:
    """
    AI-powered data scientist that analyzes Harvey's database and recommends
    ML improvements, training strategies, and data optimizations.
    """
    
    def __init__(self):
        """Initialize the Data Scientist Agent."""
        self.db_connection_string = self._build_connection_string()
        self.engine = None
        self.analysis_results = {}
        
        if self.db_connection_string:
            try:
                self.engine = create_engine(
                    self.db_connection_string,
                    poolclass=NullPool,
                    pool_pre_ping=True
                )
                logger.info("Data Scientist Agent initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")
    
    def _build_connection_string(self) -> Optional[str]:
        """Build SQL Server connection string from environment variables."""
        host = os.getenv("SQLSERVER_HOST")
        user = os.getenv("SQLSERVER_USER")
        password = os.getenv("SQLSERVER_PASSWORD")
        db = os.getenv("SQLSERVER_DB")
        
        if not all([host, user, password, db]):
            logger.warning("Missing database credentials")
            return None
        
        return f"mssql+pyodbc://{user}:{password}@{host}/{db}?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
    
    def analyze_database_schema(self) -> Dict[str, Any]:
        """Analyze database schema and structure."""
        logger.info("Analyzing database schema...")
        
        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            
            schema_info = {
                "total_tables": len(tables),
                "tables": {},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            for table in tables:
                columns = inspector.get_columns(table)
                indexes = inspector.get_indexes(table)
                foreign_keys = inspector.get_foreign_keys(table)
                
                schema_info["tables"][table] = {
                    "columns": len(columns),
                    "column_details": [
                        {
                            "name": col["name"],
                            "type": str(col["type"]),
                            "nullable": col["nullable"]
                        }
                        for col in columns
                    ],
                    "indexes": len(indexes),
                    "foreign_keys": len(foreign_keys)
                }
            
            self.analysis_results["schema"] = schema_info
            logger.info(f"Schema analysis complete: {len(tables)} tables found")
            return schema_info
            
        except Exception as e:
            logger.error(f"Schema analysis failed: {e}")
            return {"error": str(e)}
    
    def analyze_data_distribution(self) -> Dict[str, Any]:
        """Analyze data distribution and quality across key tables."""
        logger.info("Analyzing data distribution...")
        
        distribution = {}
        
        key_tables = [
            "training_questions",
            "training_responses",
            "harvey_training_data",
            "feedback_log",
            "model_audit",
            "learning_metrics"
        ]
        
        try:
            with self.engine.connect() as conn:
                for table in key_tables:
                    try:
                        result = conn.execute(text(
                            f"SELECT COUNT(*) as row_count FROM {table}"
                        ))
                        row = result.fetchone()
                        distribution[table] = {
                            "row_count": row[0] if row else 0,
                            "exists": True
                        }
                    except Exception as e:
                        distribution[table] = {
                            "row_count": 0,
                            "exists": False,
                            "error": str(e)
                        }
                
                distribution["timestamp"] = datetime.now(timezone.utc).isoformat()
                distribution["total_rows"] = sum(
                    t.get("row_count", 0) for t in distribution.values() 
                    if isinstance(t, dict) and "row_count" in t
                )
            
            self.analysis_results["distribution"] = distribution
            logger.info(f"Distribution analysis complete: {distribution['total_rows']} total rows")
            return distribution
            
        except Exception as e:
            logger.error(f"Distribution analysis failed: {e}")
            return {"error": str(e)}
    
    def analyze_training_coverage(self) -> Dict[str, Any]:
        """Analyze training data coverage across categories."""
        logger.info("Analyzing training data coverage...")
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT 
                        category,
                        COUNT(*) as question_count,
                        AVG(CASE WHEN processed = 1 THEN 1.0 ELSE 0.0 END) as processed_rate
                    FROM training_questions
                    GROUP BY category
                    ORDER BY question_count DESC
                """))
                
                categories = []
                for row in result:
                    categories.append({
                        "category": row[0],
                        "question_count": row[1],
                        "processed_rate": float(row[2]) if row[2] else 0.0
                    })
                
                coverage = {
                    "categories": categories,
                    "total_categories": len(categories),
                    "total_questions": sum(c["question_count"] for c in categories),
                    "average_questions_per_category": sum(c["question_count"] for c in categories) / len(categories) if categories else 0,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                self.analysis_results["training_coverage"] = coverage
                logger.info(f"Coverage analysis complete: {coverage['total_categories']} categories, {coverage['total_questions']} questions")
                return coverage
                
        except Exception as e:
            logger.error(f"Training coverage analysis failed: {e}")
            return {"error": str(e)}
    
    def analyze_model_performance(self) -> Dict[str, Any]:
        """Analyze multi-model performance metrics."""
        logger.info("Analyzing model performance...")
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT 
                        model_name,
                        COUNT(*) as response_count,
                        AVG(response_time_ms) as avg_response_time,
                        AVG(quality_score) as avg_quality_score,
                        AVG(confidence_score) as avg_confidence
                    FROM training_responses
                    GROUP BY model_name
                    ORDER BY avg_quality_score DESC
                """))
                
                models = []
                for row in result:
                    models.append({
                        "model": row[0],
                        "response_count": row[1],
                        "avg_response_time_ms": float(row[2]) if row[2] else 0.0,
                        "avg_quality_score": float(row[3]) if row[3] else 0.0,
                        "avg_confidence": float(row[4]) if row[4] else 0.0
                    })
                
                performance = {
                    "models": models,
                    "total_models": len(models),
                    "total_responses": sum(m["response_count"] for m in models),
                    "best_quality_model": models[0]["model"] if models else None,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                self.analysis_results["model_performance"] = performance
                logger.info(f"Performance analysis complete: {len(models)} models analyzed")
                return performance
                
        except Exception as e:
            logger.error(f"Model performance analysis failed: {e}")
            return {"error": str(e)}
    
    def analyze_feedback_patterns(self) -> Dict[str, Any]:
        """Analyze user feedback patterns and sentiment."""
        logger.info("Analyzing feedback patterns...")
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT 
                        rating,
                        COUNT(*) as feedback_count,
                        AVG(CASE WHEN sentiment = 'positive' THEN 1.0 ELSE 0.0 END) as positive_rate
                    FROM feedback_log
                    WHERE rating IS NOT NULL
                    GROUP BY rating
                    ORDER BY rating DESC
                """))
                
                ratings = []
                for row in result:
                    ratings.append({
                        "rating": row[0],
                        "count": row[1],
                        "positive_rate": float(row[2]) if row[2] else 0.0
                    })
                
                total_feedback = sum(r["count"] for r in ratings)
                avg_rating = sum(r["rating"] * r["count"] for r in ratings) / total_feedback if total_feedback > 0 else 0
                
                feedback = {
                    "rating_distribution": ratings,
                    "total_feedback": total_feedback,
                    "average_rating": avg_rating,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                self.analysis_results["feedback_patterns"] = feedback
                logger.info(f"Feedback analysis complete: {total_feedback} feedback entries")
                return feedback
                
        except Exception as e:
            logger.error(f"Feedback analysis failed: {e}")
            return {"error": str(e)}
    
    def generate_ml_recommendations(self) -> Dict[str, Any]:
        """Generate ML model and training recommendations using Gemini 2.0."""
        logger.info("Generating ML recommendations...")
        
        try:
            from app.services.gemini_client import GeminiClient
            
            gemini = GeminiClient(model_name="gemini-2.0-flash")
            
            analysis_summary = json.dumps(self.analysis_results, indent=2)
            
            prompt = f"""You are an expert ML engineer and data scientist analyzing Harvey AI's dividend intelligence database.

**Database Analysis:**
{analysis_summary}

Based on this analysis, provide detailed recommendations in the following categories:

**1. NEW ML MODELS TO IMPLEMENT**
- Suggest 3-5 specific ML models that would enhance Harvey's dividend predictions
- For each model, explain: use case, expected benefits, implementation complexity, required data

**2. TRAINING DATA IMPROVEMENTS**
- Identify gaps in training data coverage
- Recommend new categories or question types to add
- Suggest strategies to improve data quality and diversity

**3. FEATURE ENGINEERING IDEAS**
- Propose new features to extract from existing dividend data
- Suggest external data sources to integrate
- Recommend feature combinations for better predictions

**4. MODEL OPTIMIZATION**
- Identify underperforming models that need tuning
- Suggest hyperparameter optimization strategies
- Recommend ensemble techniques to improve accuracy

**5. DATA QUALITY ISSUES**
- Highlight potential data quality problems
- Suggest data cleaning and validation strategies
- Recommend monitoring metrics for data drift

**6. PERFORMANCE IMPROVEMENTS**
- Identify bottlenecks in model inference
- Suggest caching or optimization strategies
- Recommend scalability improvements

Format your response as structured JSON with these exact keys:
{{
  "new_ml_models": [...],
  "training_improvements": [...],
  "feature_engineering": [...],
  "model_optimization": [...],
  "data_quality": [...],
  "performance": [...]
}}

Be specific, actionable, and prioritize recommendations by impact."""

            response = gemini.generate_text(
                prompt=prompt,
                temperature=0.3,
                max_tokens=4096
            )
            
            recommendations_text = response.get("text", "")
            
            try:
                start_idx = recommendations_text.find("{")
                end_idx = recommendations_text.rfind("}") + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = recommendations_text[start_idx:end_idx]
                    recommendations = json.loads(json_str)
                else:
                    recommendations = {"raw_text": recommendations_text}
            except json.JSONDecodeError:
                recommendations = {"raw_text": recommendations_text}
            
            recommendations["timestamp"] = datetime.now(timezone.utc).isoformat()
            recommendations["model_used"] = "gemini-2.0-flash"
            
            self.analysis_results["recommendations"] = recommendations
            logger.info("ML recommendations generated successfully")
            return recommendations
            
        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            return {"error": str(e)}
    
    def run_full_analysis(self) -> Dict[str, Any]:
        """Run complete database analysis and generate recommendations."""
        logger.info("Starting full database analysis...")
        
        start_time = datetime.now(timezone.utc)
        
        self.analyze_database_schema()
        self.analyze_data_distribution()
        self.analyze_training_coverage()
        self.analyze_model_performance()
        self.analyze_feedback_patterns()
        self.generate_ml_recommendations()
        
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        full_report = {
            "analysis_timestamp": start_time.isoformat(),
            "analysis_duration_seconds": duration,
            "schema_analysis": self.analysis_results.get("schema", {}),
            "data_distribution": self.analysis_results.get("distribution", {}),
            "training_coverage": self.analysis_results.get("training_coverage", {}),
            "model_performance": self.analysis_results.get("model_performance", {}),
            "feedback_patterns": self.analysis_results.get("feedback_patterns", {}),
            "ml_recommendations": self.analysis_results.get("recommendations", {}),
            "summary": self._generate_summary()
        }
        
        logger.info(f"Full analysis complete in {duration:.2f}s")
        return full_report
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate executive summary of findings."""
        dist = self.analysis_results.get("distribution", {})
        coverage = self.analysis_results.get("training_coverage", {})
        perf = self.analysis_results.get("model_performance", {})
        
        return {
            "total_data_points": dist.get("total_rows", 0),
            "total_training_questions": coverage.get("total_questions", 0),
            "total_categories": coverage.get("total_categories", 0),
            "models_analyzed": perf.get("total_models", 0),
            "best_performing_model": perf.get("best_quality_model"),
            "analysis_status": "complete"
        }


data_scientist_agent = DataScientistAgent()
