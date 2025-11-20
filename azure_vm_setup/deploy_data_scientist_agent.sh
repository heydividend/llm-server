#!/bin/bash

echo "=================================================================="
echo "Harvey AI - Data Scientist Agent Deployment"
echo "=================================================================="
echo ""

HARVEY_DIR="/home/azureuser/harvey"
SCRIPTS_DIR="$HARVEY_DIR/scripts"
SERVICES_DIR="$HARVEY_DIR/app/services"

echo "📦 Creating directory structure..."
mkdir -p "$SCRIPTS_DIR"
mkdir -p "$SERVICES_DIR"

echo "📝 Deploying Data Scientist Agent Service..."
cat > "$SERVICES_DIR/data_scientist_agent.py" << 'AGENT_EOF'
import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

load_dotenv(override=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataScientistAgent:
    """AI-powered database analyst for Harvey's ML systems."""
    
    def __init__(self):
        """Initialize database connection with ODBC Driver 18."""
        self.host = os.getenv("SQLSERVER_HOST")
        self.user = os.getenv("SQLSERVER_USER")
        self.password = os.getenv("SQLSERVER_PASSWORD")
        self.database = os.getenv("SQLSERVER_DB")
        
        if not all([self.host, self.user, self.password, self.database]):
            raise ValueError("Missing required database credentials in environment")
        
        connection_string = (
            f"mssql+pyodbc://{self.user}:{self.password}@{self.host}/"
            f"{self.database}?driver=ODBC+Driver+18+for+SQL+Server"
            f"&TrustServerCertificate=yes"
        )
        
        self.engine = create_engine(connection_string, echo=False)
        self.analysis_results = {}
        logger.info("DataScientistAgent initialized successfully")
    
    def analyze_database_schema(self) -> Dict[str, Any]:
        """Analyze complete database schema."""
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
                    "column_names": [col["name"] for col in columns],
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
        """Analyze data volume and distribution."""
        logger.info("Analyzing data distribution...")
        
        key_tables = [
            "training_questions",
            "training_responses",
            "harvey_training_data",
            "feedback_log",
            "model_audit",
            "learning_metrics",
            "conversation_history"
        ]
        
        try:
            distribution = {"tables": {}, "timestamp": datetime.now(timezone.utc).isoformat()}
            total_rows = 0
            
            with self.engine.connect() as conn:
                for table in key_tables:
                    try:
                        result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        row_count = result.scalar()
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
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT 
                        category,
                        COUNT(*) as question_count,
                        SUM(CASE WHEN processed = 1 THEN 1 ELSE 0 END) as processed_count
                    FROM training_questions
                    GROUP BY category
                    ORDER BY question_count DESC
                """))
                
                categories = []
                for row in result:
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

Each array should contain objects with "title", "description", and "priority" (High/Medium/Low) fields."""
            
            response = gemini.generate_response(prompt)
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
AGENT_EOF

echo "✅ Service deployed: $SERVICES_DIR/data_scientist_agent.py"

echo ""
echo "📝 Deploying CLI Tool..."
cat > "$SCRIPTS_DIR/data_scientist_agent.py" << 'CLI_EOF'
#!/usr/bin/env python3
"""
Harvey AI - Data Scientist Agent CLI
Analyzes database and generates AI-powered ML recommendations.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.data_scientist_agent import data_scientist_agent


def format_table(headers, rows):
    """Format data as a pretty ASCII table."""
    col_widths = [len(h) for h in headers]
    
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    separator = "─" * (sum(col_widths) + len(headers) * 3 + 1)
    
    header_row = "  ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    print(header_row)
    print(separator)
    
    for row in rows:
        print("  ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)))


def print_section(title):
    """Print a section header."""
    print("\n" + "─" * 80)
    print(f"📊 {title}")
    print("─" * 80)


def print_schema_analysis(schema):
    """Print schema analysis."""
    print_section("Database Schema Analysis")
    print(f"Total Tables: {schema.get('total_tables', 0)}\n")
    
    for table_name, info in schema.get('tables', {}).items():
        print(f"  📁 {table_name}")
        print(f"     Columns: {info.get('columns', 0)}")
        print(f"     Indexes: {info.get('indexes', 0)}")
        print(f"     Foreign Keys: {info.get('foreign_keys', 0)}")
        print()


def print_distribution_analysis(dist):
    """Print data distribution."""
    print_section("Data Distribution Analysis")
    print(f"Total Rows Across All Tables: {dist.get('total_rows', 0):,}\n")
    
    for table_name, info in dist.get('tables', {}).items():
        status = "✓" if info.get('exists') else "✗"
        rows = info.get('row_count', 0)
        print(f"  {status} {table_name:.<50} {rows:>10,} rows")


def print_training_coverage(coverage):
    """Print training data coverage."""
    print_section("Training Data Coverage")
    print(f"Total Categories: {coverage.get('total_categories', 0)}")
    print(f"Total Questions: {coverage.get('total_questions', 0)}")
    avg_q = coverage.get('total_questions', 0) / max(coverage.get('total_categories', 1), 1)
    print(f"Avg Questions/Category: {avg_q:.1f}\n")
    
    print("Category Breakdown:")
    for cat in coverage.get('categories', []):
        rate = cat.get('processing_rate', 0)
        print(f"  {cat['category']:.<40} {cat['questions']:>5} ({rate:>5.1f}% processed)")


def print_model_performance(perf):
    """Print model performance."""
    print_section("Model Performance Analysis")
    print(f"Total Models: {perf.get('total_models', 0)}")
    print(f"Total Responses: {perf.get('total_responses', 0):,}")
    print(f"Best Quality Model: {perf.get('best_quality_model', 'N/A')}\n")
    
    headers = ["Model", "Responses", "Avg Time (ms)", "Quality", "Confidence"]
    rows = []
    
    for model in perf.get('models', []):
        rows.append([
            model['model'],
            f"{model['response_count']:,}",
            f"{model['avg_response_time_ms']:.2f}",
            f"{model['avg_quality_score']:.2f}",
            f"{model['avg_confidence']:.2f}"
        ])
    
    if rows:
        format_table(headers, rows)


def print_feedback_patterns(feedback):
    """Print feedback analysis."""
    print_section("Feedback Pattern Analysis")
    print(f"Total Feedback: {feedback.get('total_feedback', 0):,}")
    print(f"Average Rating: {feedback.get('average_rating', 0):.2f}\n")
    
    for rating_info in feedback.get('rating_distribution', []):
        rating = rating_info['rating']
        count = rating_info['count']
        positive = rating_info['positive_rate'] * 100
        print(f"  ⭐ {rating} stars: {count:>5,} ({positive:.1f}% positive)")


def print_recommendations(recs):
    """Print ML recommendations."""
    print_section("AI-Powered ML Recommendations")
    print(f"Generated by: {recs.get('model_used', 'N/A')}\n")
    
    sections = [
        ("new_ml_models", "🤖 New ML Models to Implement"),
        ("training_improvements", "📚 Training Data Improvements"),
        ("feature_engineering", "🔧 Feature Engineering Ideas"),
        ("model_optimization", "⚡ Model Optimization"),
        ("data_quality", "✨ Data Quality Issues"),
        ("performance", "🚀 Performance Improvements")
    ]
    
    for key, title in sections:
        items = recs.get(key, [])
        if items and not isinstance(items, str):
            print(f"\n{title}:")
            for i, item in enumerate(items[:5], 1):
                if isinstance(item, dict):
                    print(f"  {i}. {item.get('title', 'N/A')}")
                    print(f"     → {item.get('description', 'N/A')}")
                    if 'priority' in item:
                        print(f"     Priority: {item['priority']}")
                else:
                    print(f"  {i}. {item}")


def main():
    parser = argparse.ArgumentParser(
        description="Harvey AI Data Scientist Agent - Database Analysis & ML Recommendations"
    )
    
    parser.add_argument("--analyze", action="store_true", help="Run full analysis")
    parser.add_argument("--schema-only", action="store_true", help="Analyze schema only")
    parser.add_argument("--distribution-only", action="store_true", help="Analyze data distribution only")
    parser.add_argument("--coverage-only", action="store_true", help="Analyze training coverage only")
    parser.add_argument("--performance-only", action="store_true", help="Analyze model performance only")
    parser.add_argument("--feedback-only", action="store_true", help="Analyze feedback patterns only")
    parser.add_argument("--recommendations-only", action="store_true", help="Generate ML recommendations only")
    parser.add_argument("--output", "-o", help="Save report to JSON file")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode (no console output)")
    
    args = parser.parse_args()
    
    if not args.quiet:
        print("=" * 80)
        print("🔬 Harvey AI - Data Scientist Agent")
        print("=" * 80)
    
    try:
        if args.analyze:
            result = data_scientist_agent.run_full_analysis()
            
            if not args.quiet:
                print_schema_analysis(result.get('schema_analysis', {}))
                print_distribution_analysis(result.get('data_distribution', {}))
                print_training_coverage(result.get('training_coverage', {}))
                print_model_performance(result.get('model_performance', {}))
                print_feedback_patterns(result.get('feedback_patterns', {}))
                print_recommendations(result.get('ml_recommendations', {}))
        
        elif args.schema_only:
            result = data_scientist_agent.analyze_database_schema()
            if not args.quiet:
                print_schema_analysis(result)
        
        elif args.distribution_only:
            result = data_scientist_agent.analyze_data_distribution()
            if not args.quiet:
                print_distribution_analysis(result)
        
        elif args.coverage_only:
            result = data_scientist_agent.analyze_training_coverage()
            if not args.quiet:
                print_training_coverage(result)
        
        elif args.performance_only:
            result = data_scientist_agent.analyze_model_performance()
            if not args.quiet:
                print_model_performance(result)
        
        elif args.feedback_only:
            result = data_scientist_agent.analyze_feedback_patterns()
            if not args.quiet:
                print_feedback_patterns(result)
        
        elif args.recommendations_only:
            data_scientist_agent.run_full_analysis()
            result = data_scientist_agent.generate_ml_recommendations()
            if not args.quiet:
                print_recommendations(result)
        
        else:
            parser.print_help()
            return 1
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            if not args.quiet:
                print(f"\n✅ Report saved to: {args.output}")
        
        if not args.quiet:
            print("\n" + "=" * 80)
            print("✅ Analysis Complete!")
            print("=" * 80)
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
CLI_EOF

chmod +x "$SCRIPTS_DIR/data_scientist_agent.py"
echo "✅ CLI deployed: $SCRIPTS_DIR/data_scientist_agent.py"

echo ""
echo "=================================================================="
echo "✅ Data Scientist Agent Deployed Successfully!"
echo "=================================================================="
echo ""
echo "📚 Usage:"
echo "  cd $HARVEY_DIR"
echo "  python3 scripts/data_scientist_agent.py --analyze"
echo ""
echo "📖 Documentation: docs/DATA_SCIENTIST_AGENT.md"
echo "=================================================================="
AGENT_EOF

chmod +x "$SCRIPTS_DIR/data_scientist_agent.py"
chmod +x azure_vm_setup/deploy_data_scientist_agent.sh

echo "✅ Deployment script created: azure_vm_setup/deploy_data_scientist_agent.sh"
