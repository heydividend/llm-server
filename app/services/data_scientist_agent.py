"""
Harvey AI - Data Scientist Agent
Analyzes Azure SQL database and recommends ML models, training improvements,
and data optimization strategies using AI-powered insights.

Uses pymssql (no ODBC drivers required) with parameterized queries for security.
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any
import pymssql  # type: ignore[import-not-found]
from dotenv import load_dotenv

load_dotenv(override=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataScientistAgent:
    """
    AI-powered data scientist that analyzes Harvey's database and recommends
    ML improvements, training strategies, and data optimizations.
    """
    
    def __init__(self):
        """Initialize database connection with pymssql (no ODBC required)."""
        self.host = os.getenv("SQLSERVER_HOST")
        self.user = os.getenv("SQLSERVER_USER")
        self.password = os.getenv("SQLSERVER_PASSWORD")
        self.database = os.getenv("SQLSERVER_DB")
        
        if not all([self.host, self.user, self.password, self.database]):
            raise ValueError("Missing required database credentials in environment")
        
        self.analysis_results = {}
        logger.info("DataScientistAgent initialized successfully")
    
    def _get_connection(self):
        """Create database connection using pymssql."""
        return pymssql.connect(
            server=self.host,
            user=self.user,
            password=self.password,
            database=self.database
        )
    
    def analyze_database_schema(self) -> Dict[str, Any]:
        """Analyze complete database schema using parameterized queries."""
        logger.info("Analyzing database schema...")
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Use parameterized query to avoid quoting issues
            cursor.execute(
                "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = %s ORDER BY TABLE_NAME",
                ('BASE TABLE',)
            )
            
            tables = [row[0] for row in cursor.fetchall()]
            
            schema_info = {
                "total_tables": len(tables),
                "tables": {},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            for table in tables:
                # Parameterized query for columns
                cursor.execute(
                    "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = %s",
                    (table,)
                )
                columns = [row[0] for row in cursor.fetchall()]
                
                schema_info["tables"][table] = {
                    "columns": len(columns),
                    "column_names": columns
                }
            
            conn.close()
            self.analysis_results["schema"] = schema_info
            logger.info(f"Schema analysis complete: {len(tables)} tables found")
            return schema_info
            
        except Exception as e:
            logger.error(f"Schema analysis failed: {e}")
            return {"error": str(e)}
    
    def analyze_data_distribution(self) -> Dict[str, Any]:
        """Analyze data volume and distribution."""
        logger.info("Analyzing data distribution...")
        
        key_tables = [
            "training_questions",
            "training_responses",
            "harvey_training_data",
            "feedback_log",
            "model_audit",
            "conversation_history"
        ]
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            distribution = {
                "tables": {},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            total_rows = 0
            
            for table in key_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    row_count = cursor.fetchone()[0]
                    distribution["tables"][table] = {
                        "row_count": row_count,
                        "exists": True
                    }
                    total_rows += row_count
                except Exception as e:
                    distribution["tables"][table] = {
                        "row_count": 0,
                        "exists": False,
                        "error": str(e)
                    }
            
            distribution["total_rows"] = total_rows
            conn.close()
            
            self.analysis_results["distribution"] = distribution
            logger.info(f"Distribution analysis complete: {total_rows} total rows")
            return distribution
            
        except Exception as e:
            logger.error(f"Distribution analysis failed: {e}")
            return {"error": str(e)}
    
    def analyze_training_coverage(self) -> Dict[str, Any]:
        """Analyze training data coverage across categories."""
        logger.info("Analyzing training coverage...")
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    category,
                    COUNT(*) as question_count,
                    SUM(CASE WHEN processed = 1 THEN 1 ELSE 0 END) as processed_count
                FROM training_questions
                GROUP BY category
                ORDER BY question_count DESC
            """)
            
            categories = []
            for row in cursor.fetchall():
                categories.append({
                    "category": row[0],
                    "questions": row[1],
                    "processed": row[2],
                    "processing_rate": (row[2] / row[1] * 100) if row[1] > 0 else 0
                })
            
            coverage = {
                "categories": categories,
                "total_categories": len(categories),
                "total_questions": sum(c["questions"] for c in categories),
                "total_processed": sum(c["processed"] for c in categories),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            conn.close()
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
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    model_name,
                    COUNT(*) as response_count,
                    AVG(response_time_ms) as avg_response_time,
                    AVG(quality_score) as avg_quality_score,
                    AVG(confidence_score) as avg_confidence
                FROM training_responses
                GROUP BY model_name
                ORDER BY avg_quality_score DESC
            """)
            
            models = []
            for row in cursor.fetchall():
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
            
            conn.close()
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
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    rating,
                    COUNT(*) as feedback_count,
                    AVG(CASE WHEN sentiment = 'positive' THEN 1.0 ELSE 0.0 END) as positive_rate
                FROM feedback_log
                WHERE rating IS NOT NULL
                GROUP BY rating
                ORDER BY rating DESC
            """)
            
            ratings = []
            for row in cursor.fetchall():
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
            
            conn.close()
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
            import sys
            sys.path.insert(0, '/home/azureuser/harvey')
            from app.services.gemini_client import GeminiClient
            
            gemini = GeminiClient(model_name="gemini-2.0-flash-exp")
            
            analysis_summary = json.dumps(self.analysis_results, indent=2)
            
            prompt = f"""You are an expert ML engineer analyzing Harvey AI's dividend intelligence database.

**Database Analysis:**
{analysis_summary}

Provide detailed recommendations in JSON format with these keys:
- new_ml_models: Array of 3-5 ML models to implement (each with title, description, priority)
- training_improvements: Data quality and coverage improvements
- feature_engineering: New features to extract
- model_optimization: Strategies to improve existing models
- data_quality: Issues and fixes
- performance: Scalability improvements

Return only valid JSON."""
            
            response = gemini.generate_response(prompt)  # type: ignore[attr-defined]
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
            recommendations["model_used"] = "gemini-2.0-flash-exp"
            
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
        schema = self.analysis_results.get("schema", {})
        
        return {
            "total_tables": schema.get("total_tables", 0),
            "total_data_points": dist.get("total_rows", 0),
            "total_training_questions": coverage.get("total_questions", 0),
            "total_categories": coverage.get("total_categories", 0),
            "models_analyzed": perf.get("total_models", 0),
            "best_performing_model": perf.get("best_quality_model"),
            "analysis_status": "complete"
        }


# Global instance
data_scientist_agent = DataScientistAgent()
