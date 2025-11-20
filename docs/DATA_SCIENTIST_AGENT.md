# 🔬 Harvey AI - Data Scientist Agent

AI-powered agent that analyzes Harvey's Azure SQL database and recommends ML models, training improvements, and data optimization strategies.

---

## Overview

The Data Scientist Agent is an intelligent system that:
- **Analyzes** your entire Harvey database schema and data distribution
- **Identifies** gaps in training data and model performance
- **Recommends** specific ML models and improvements using Gemini 2.0 AI
- **Generates** actionable insights for advancing Harvey's intelligence

---

## Features

### 1. 📊 Database Schema Analysis
- Discovers all tables, columns, indexes, and relationships
- Maps the complete data structure
- Identifies schema design patterns

### 2. 📈 Data Distribution Analysis
- Counts rows across all key tables
- Identifies data volume patterns
- Detects missing or empty tables

### 3. 📚 Training Coverage Analysis
- Analyzes questions across all 10 categories
- Calculates processing rates
- Identifies underrepresented categories

### 4. 🎯 Model Performance Analysis
- Compares all 5 AI models (GPT-5, Grok-4, DeepSeek-R1, Gemini, FinGPT)
- Measures response time, quality, and confidence
- Ranks models by performance

### 5. 💬 Feedback Pattern Analysis
- Analyzes user ratings and sentiment
- Identifies satisfaction trends
- Highlights improvement opportunities

### 6. 🤖 AI-Powered Recommendations
Uses Gemini 2.0 to generate:
- **New ML models** to implement
- **Training data** improvements
- **Feature engineering** ideas
- **Model optimization** strategies
- **Data quality** enhancements
- **Performance** improvements

---

## Quick Start

### Run Full Analysis

```bash
# Complete analysis with all recommendations
python scripts/data_scientist_agent.py --analyze

# Save report to specific file
python scripts/data_scientist_agent.py --analyze --output my_analysis.json
```

**Output:**
- Console report with all findings
- JSON file with complete analysis data
- AI-generated ML recommendations

---

## Usage Examples

### 1. Schema Analysis Only
```bash
python scripts/data_scientist_agent.py --schema-only
```

**Shows:**
- Total tables in database
- Columns per table
- Indexes and foreign keys

---

### 2. Data Distribution Only
```bash
python scripts/data_scientist_agent.py --distribution-only
```

**Shows:**
- Row counts for all tables
- Total data points
- Data availability status

---

### 3. Training Coverage Only
```bash
python scripts/data_scientist_agent.py --coverage-only
```

**Shows:**
- Questions per category
- Processing rates
- Coverage gaps

---

### 4. Model Performance Only
```bash
python scripts/data_scientist_agent.py --performance-only
```

**Shows:**
- Model comparison stats
- Response times
- Quality scores
- Best performing model

---

### 5. AI Recommendations Only
```bash
python scripts/data_scientist_agent.py --recommendations-only
```

**Generates:**
- New ML model suggestions
- Training improvements
- Feature engineering ideas
- Optimization strategies

*Note: Requires GEMINI_API_KEY in .env*

---

## Sample Output

### Console Output

```
================================================================================
🔬 Harvey AI - Data Scientist Agent
================================================================================

────────────────────────────────────────────────────────────────────────────────
📊 Database Schema Analysis
────────────────────────────────────────────────────────────────────────────────
Total Tables: 15

  📁 training_questions
     Columns: 7
     Indexes: 2
     Foreign Keys: 0
  
  📁 training_responses
     Columns: 9
     Indexes: 3
     Foreign Keys: 1

────────────────────────────────────────────────────────────────────────────────
📊 Data Distribution Analysis
────────────────────────────────────────────────────────────────────────────────
Total Rows Across All Tables: 15,437

  ✓ training_questions........................          250 rows
  ✓ training_responses........................        1,250 rows
  ✓ harvey_training_data......................          875 rows
  ✓ feedback_log..............................          342 rows
  ✓ model_audit...............................        8,720 rows

────────────────────────────────────────────────────────────────────────────────
📊 Training Data Coverage
────────────────────────────────────────────────────────────────────────────────
Total Categories: 10
Total Questions: 250
Avg Questions/Category: 25.0

Category Breakdown:
  dividend_analysis...................    45 ( 88.9% processed)
  income_strategies...................    38 ( 92.1% processed)
  technical_timing....................    22 ( 68.2% processed)
  etf_funds...........................    18 ( 77.8% processed)

────────────────────────────────────────────────────────────────────────────────
📊 Model Performance Analysis
────────────────────────────────────────────────────────────────────────────────
Total Models: 5
Total Responses: 1,250
Best Quality Model: gpt-5

Model                Responses    Avg Time (ms)   Quality    Confidence
────────────────────────────────────────────────────────────────────────────────
gpt-5                     312          2,145.32      8.76        0.89
grok-4                    298          1,234.21      8.42        0.85
deepseek-r1               285          3,456.78      8.31        0.87
gemini-2.5-pro            203          2,987.45      8.18        0.82
fingpt                    152          1,876.54      7.94        0.79

────────────────────────────────────────────────────────────────────────────────
📊 AI-Powered ML Recommendations
────────────────────────────────────────────────────────────────────────────────
Generated by: gemini-2.0-flash

🤖 New ML Models to Implement:
  1. Dividend Cut Risk Predictor
     → XGBoost model to predict dividend suspension probability
     Priority: High

  2. Yield Curve Analyzer
     → LSTM model for dividend growth trajectory forecasting
     Priority: Medium

  3. Sector Rotation Recommender
     → Random Forest for optimal sector allocation timing
     Priority: Medium

📚 Training Data Improvements:
  1. Add 100+ questions on international dividends
  2. Include more edge cases (dividend cuts, special dividends)
  3. Expand ETF coverage to 50+ popular dividend ETFs

🔧 Feature Engineering Ideas:
  1. Calculate 5-year dividend CAGR as feature
  2. Add payout ratio momentum (3-month change)
  3. Integrate analyst consensus on dividend safety

⚡ Model Optimization:
  1. Implement ensemble voting across top 3 models
  2. Add confidence thresholding (reject < 0.75)
  3. Fine-tune GPT-5 on 1000+ Harvey responses

================================================================================
✅ Analysis Complete!
================================================================================
```

---

## Report Format (JSON)

The agent generates a comprehensive JSON report with this structure:

```json
{
  "analysis_timestamp": "2025-11-20T01:00:00.000000+00:00",
  "analysis_duration_seconds": 45.23,
  "schema_analysis": {
    "total_tables": 15,
    "tables": {...}
  },
  "data_distribution": {
    "total_rows": 15437,
    "training_questions": {"row_count": 250, "exists": true},
    "training_responses": {"row_count": 1250, "exists": true}
  },
  "training_coverage": {
    "total_categories": 10,
    "total_questions": 250,
    "categories": [...]
  },
  "model_performance": {
    "total_models": 5,
    "best_quality_model": "gpt-5",
    "models": [...]
  },
  "ml_recommendations": {
    "new_ml_models": [...],
    "training_improvements": [...],
    "feature_engineering": [...],
    "model_optimization": [...],
    "data_quality": [...],
    "performance": [...]
  },
  "summary": {
    "total_data_points": 15437,
    "total_training_questions": 250,
    "models_analyzed": 5,
    "analysis_status": "complete"
  }
}
```

---

## Integration with Existing Systems

The Data Scientist Agent integrates with:

### Harvey Database Tables
- `training_questions` - Question inventory
- `training_responses` - Multi-model responses
- `harvey_training_data` - Fine-tuning datasets
- `feedback_log` - User feedback
- `model_audit` - Model performance tracking
- `learning_metrics` - Continuous learning data

### AI Models
- Uses **Gemini 2.0 Flash** for recommendation generation
- Analyzes performance of all 5 Harvey models
- Provides comparative insights

---

## Scheduled Analysis (Optional)

Add monthly automated analysis:

```bash
# Create monthly analysis cron job
0 0 1 * * cd /home/azureuser/harvey && python scripts/data_scientist_agent.py --analyze --output /var/log/harvey/monthly_analysis_$(date +\%Y\%m).json
```

---

## Environment Variables Required

```bash
# Azure SQL Database
SQLSERVER_HOST=your-server.database.windows.net
SQLSERVER_USER=your-username
SQLSERVER_PASSWORD=your-password
SQLSERVER_DB=your-database

# Gemini API (for recommendations)
GEMINI_API_KEY=AIzaSy...
```

---

## Use Cases

### 1. Monthly Performance Review
Run comprehensive analysis to:
- Track model performance trends
- Identify training data gaps
- Get AI-recommended improvements

### 2. Pre-Deployment Validation
Before major releases:
- Verify data quality
- Check model consistency
- Ensure adequate training coverage

### 3. Research & Development
For ML improvements:
- Discover feature engineering opportunities
- Identify new ML model candidates
- Optimize existing models

### 4. Data Quality Audits
Regular data health checks:
- Monitor data drift
- Detect anomalies
- Validate data completeness

---

## Advanced Options

### Quiet Mode (No Console Output)
```bash
python scripts/data_scientist_agent.py --analyze --quiet --output report.json
```

### Custom Analysis Pipelines
```python
from app.services.data_scientist_agent import data_scientist_agent

# Run specific analyses
schema = data_scientist_agent.analyze_database_schema()
coverage = data_scientist_agent.analyze_training_coverage()
recommendations = data_scientist_agent.generate_ml_recommendations()

# Custom processing
process_recommendations(recommendations)
```

---

## Performance

- **Schema Analysis:** ~2 seconds
- **Data Distribution:** ~3 seconds
- **Training Coverage:** ~4 seconds
- **Model Performance:** ~5 seconds
- **AI Recommendations:** ~15-20 seconds (Gemini API call)

**Total Full Analysis:** ~30-40 seconds

---

## Troubleshooting

### Database Connection Failed
```bash
# Verify credentials
python -c "
import os
from dotenv import load_dotenv
load_dotenv(override=True)
print('Host:', os.getenv('SQLSERVER_HOST'))
print('User:', os.getenv('SQLSERVER_USER'))
print('DB:', os.getenv('SQLSERVER_DB'))
"
```

### Gemini API Error
```bash
# Check API key
python -c "
import os
from dotenv import load_dotenv
load_dotenv(override=True)
key = os.getenv('GEMINI_API_KEY')
print('API Key:', 'OK' if key and len(key) == 39 else 'INVALID')
"
```

### ODBC Driver Not Found
```bash
# Install ODBC Driver 18
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

---

## Roadmap

Future enhancements:
- [ ] Automated monthly email reports
- [ ] Trend analysis across multiple time periods
- [ ] Interactive web dashboard
- [ ] Slack/Teams integration for alerts
- [ ] A/B testing recommendation engine
- [ ] Auto-implementation of low-risk improvements

---

## Example Recommendations

The AI generates specific, actionable recommendations like:

### New ML Models
- **Dividend Aristocrat Predictor**: Forecast which companies will join the aristocrats list (25+ year streaks)
- **Payout Sustainability Score**: Ensemble model combining FCF, earnings, and debt metrics
- **Sector Rotation Timer**: Optimize sector allocation based on economic cycles

### Training Improvements
- Add 200+ questions on dividend ETF strategies
- Include edge cases: dividend cuts, suspensions, special dividends
- Expand international dividend coverage (UK, Canada, Australia)

### Feature Engineering
- Calculate dividend momentum (3-month vs 12-month growth)
- Add analyst upgrade/downgrade sentiment
- Integrate insider buying activity as dividend confidence signal

---

## Support

For issues or questions:
- Check logs: `/var/log/harvey/data_scientist_agent.log`
- Review output: `attached_assets/data_scientist_report_*.json`
- Documentation: This file

---

**Last Updated:** November 20, 2025  
**Version:** 1.0.0  
**Status:** Production Ready ✅
