# Harvey Complete System Documentation
**The Unified AI-Powered Dividend Intelligence Platform**

Version: 4.0.0  
Last Updated: November 2, 2025  
Status: Production-Ready for Azure VM Deployment

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Components](#system-components)
3. [Multi-Model AI Architecture](#multi-model-ai-architecture)
4. [Dividend Strategy Intelligence](#dividend-strategy-intelligence)
5. [Learning & Training System](#learning--training-system)
6. [API Reference](#api-reference)
7. [Azure VM Migration Guide](#azure-vm-migration-guide)

---

## Executive Summary

Harvey is a **unified AI-powered financial intelligence system** that combines:
- **5 specialized AI models** (GPT-5, Grok-4, DeepSeek-R1, Gemini 2.5 Pro, FinGPT)
- **22+ ML prediction endpoints** via Harvey Intelligence Engine
- **8 advanced dividend investment strategies**
- **Continuous learning system** that improves from user interactions
- **Cost optimization** achieving 46-70% savings vs. single-model approach

### Key Innovations

1. **Multi-Model Routing**: Automatically selects the optimal AI model based on query type
2. **Ensemble Learning**: Combines insights from multiple models for superior analysis
3. **Dividend Strategy Analyzer**: Understands margin buying, DRIP, dividend capture, ex-date strategies
4. **Model Audit System**: Logs all AI responses for continuous improvement
5. **Unified Intelligence**: Seamless integration between Replit VM (dev) and Azure VM (production)

---

## System Components

### 1. Harvey Intelligence Service
**Location**: `app/services/harvey_intelligence.py`  
**Purpose**: Unified coordinator for all AI and ML systems

**Features**:
- Orchestrates 5 AI models across multiple providers
- Supports single-model and ensemble modes
- Integrates with Harvey ML Engine (Azure VM:9000)
- Provides dividend-focused analysis
- System health monitoring

**Key Methods**:
```python
async def analyze_dividend(
    query: str,
    symbol: Optional[str],
    enable_ensemble: bool,
    include_strategies: bool
) -> Dict[str, Any]
```

### 2. Multi-Model Router
**Location**: `app/core/model_router.py`  
**Purpose**: Intelligently routes queries to optimal AI models

**Query Types**:
- `CHART_ANALYSIS` → Gemini 2.5 Pro
- `FX_TRADING` → Gemini 2.5 Pro
- `DIVIDEND_SCORING` → FinGPT (ML Engine)
- `DIVIDEND_STRATEGY` → GPT-5
- `QUANTITATIVE_ANALYSIS` → DeepSeek-R1
- `FAST_QUERY` → Grok-4
- `COMPLEX_ANALYSIS` → GPT-5
- `GENERAL_CHAT` → GPT-5 (default)

### 3. Model Audit Service
**Location**: `app/services/model_audit_service.py`  
**Purpose**: Logs AI responses for training and improvement

**Features**:
- Captures responses from all 5 models
- Extracts dividend-specific metrics
- Creates training samples for ML models
- Tracks model performance statistics
- Stores in Azure SQL for analysis

**Metrics Extracted**:
- Dividend yield
- Payout ratio
- Growth rate
- Safety scores
- Dividend dates
- Investment recommendations

### 4. Dividend Strategy Analyzer
**Location**: `app/services/dividend_strategy_analyzer.py`  
**Purpose**: Analyzes 8 advanced dividend investment strategies

**Strategies**:
1. **Margin Buying**: Leverage to amplify yield
2. **DRIP**: Automatic reinvestment for compounding
3. **Dividend Capture**: Buy before ex-date, sell after
4. **Ex-Date Dip Buying**: Buy on price drop
5. **Declaration Play**: Buy on announcement
6. **Covered Calls**: Dividends + option premiums
7. **Cash-Secured Puts**: Income while waiting to buy
8. **Long-Term Hold**: Traditional buy and hold

**Calculations Provided**:
- Expected returns (annualized)
- Risk assessment (LOW/MEDIUM/HIGH)
- Capital requirements
- Tax implications
- Break-even analysis
- Timeline-based recommendations

### 5. LLM Providers
**Location**: `app/core/llm_providers.py`  
**Purpose**: Unified interface for all AI model providers

**Supported Providers**:
- Azure OpenAI (GPT-5, Grok-4, DeepSeek-R1)
- Google Gemini (Gemini 2.5 Pro)
- ML API Client (FinGPT via Harvey Intelligence Engine)

---

## Multi-Model AI Architecture

### Model Specifications

| Model | Provider | Cost (per 1M tokens) | Context | Specialization |
|-------|----------|---------------------|---------|----------------|
| **GPT-5** | Azure OpenAI | $1.25 in / $10 out | 128K | Complex analysis, strategy |
| **Grok-4** | Azure OpenAI | $3 in / $15 out | 128K | Fast queries, real-time |
| **DeepSeek-R1** | Azure OpenAI | $0.55 in / $2.19 out ⭐ | 64K | Quantitative, calculations |
| **Gemini 2.5 Pro** | Google | $1.25 in / $5 out | 1M | Charts, FX, multimodal |
| **FinGPT** | Self-hosted | FREE | 8K | Dividend scoring, ML predictions |

### Cost Optimization Strategy

**Baseline (All GPT-5)**: $2,625/month  
**Optimized (Multi-Model)**: $1,411/month  
**Savings**: $1,214/month (46%)  

**Query Distribution**:
- 30% → Grok-4 (fast queries)
- 25% → DeepSeek-R1 (calculations)
- 20% → GPT-5 (complex analysis)
- 15% → FinGPT (dividend scoring)
- 10% → Gemini (charts/FX)

### Ensemble Mode

For complex dividend analysis, Harvey queries multiple models simultaneously:

```
User Query → Query Router → Parallel Model Execution
                ↓
    ┌──────────────────────────┐
    │  DeepSeek: Calculations   │
    │  GPT-5: Comprehensive     │
    │  Grok-4: Fast insights    │
    │  FinGPT: ML scoring       │
    └──────────────────────────┘
                ↓
    Ensemble Evaluator → Combined Response
```

---

## Dividend Strategy Intelligence

### Calendar-Based Strategy System

Harvey provides date-specific recommendations throughout the dividend cycle:

**Pre-Declaration Phase**:
- Accumulate shares gradually
- Sell cash-secured puts for income
- Monitor for dividend increase announcements

**Declaration to Ex-Date**:
- Execute declaration play (buy on announcement)
- Prepare for dividend capture (1-2 days before ex-date)
- Consider margin buying if rates favorable

**Ex-Dividend Date**:
- Monitor for dip buying opportunity (morning drop)
- Complete dividend capture strategy (sell if held)
- Assess recovery potential

**Post Ex-Date**:
- Hold for typical price recovery
- Sell covered calls for additional income
- Evaluate next dividend cycle

### Strategy Analysis Engine

For each strategy, Harvey calculates:

```python
{
    "expected_return": {
        "nominal": 5.2,
        "annualized": 18.3,
        "after_tax": 15.5
    },
    "risk_metrics": {
        "level": "MEDIUM",
        "volatility_impact": 0.15,
        "max_drawdown": -8.5
    },
    "capital_efficiency": {
        "required": 10000,
        "optimal": 25000,
        "leverage_available": true
    },
    "timing": {
        "entry": "2 days before ex-date",
        "hold_period": "5-7 days",
        "exit": "After price recovery"
    }
}
```

---

## Learning & Training System

### Continuous Improvement Pipeline

```
User Query → Multi-Model Analysis → Response Delivery
     ↓              ↓                      ↓
Query Logged    All Models          User Feedback
     ↓           Respond                  ↓
Training DB ← Model Audit ← Feedback Analysis
     ↓              ↓                      ↓
Nightly Training → Model Updates → Router Optimization
```

### Training Data Collection

**Dividend Metrics Extracted**:
- Yield accuracy
- Payout ratio predictions
- Growth rate calculations
- Safety score assessments
- Strategy recommendations
- User satisfaction ratings

**Model Performance Tracking**:
- Response time by model
- Accuracy by query type
- Cost per satisfied response
- Error rates and fallbacks

### Nightly Automation (Future)

**2 AM UTC Daily Process**:
1. Harvest high-rated responses (≥4 stars)
2. Extract best practices by query type
3. Update routing weights
4. Fine-tune FinGPT (if applicable)
5. Generate performance reports

---

## API Reference

### Core Endpoints

#### Harvey Intelligence
```
GET  /v1/harvey/status              # System-wide status
POST /v1/chat/completions           # Main chat interface
```

#### Dividend Strategies
```
POST /v1/dividend-strategies/analyze    # Full strategy analysis
POST /v1/dividend-strategies/calendar   # Date-specific strategies
GET  /v1/dividend-strategies/list       # List all strategies
POST /v1/dividend-strategies/compare    # Compare strategies
```

#### ML Intelligence (Azure VM:9000)
```
POST /api/internal/ml/score/symbol          # Dividend quality scoring
POST /api/internal/ml/predict/yield         # Yield forecasting
POST /api/internal/ml/predict/growth-rate   # Growth predictions
POST /api/internal/ml/predict/payout-ratio  # Payout analysis
POST /api/analysis/nav-erosion             # NAV erosion detection
```

#### Portfolio Analysis
```
POST /api/financial/portfolio/projection    # Income projections
POST /api/financial/watchlist/allocation    # Optimal allocation
POST /api/financial/dividend/sustainability # Payout health
```

### Authentication

All endpoints require:
```
Authorization: Bearer <HARVEY_AI_API_KEY>
```

ML endpoints additionally require:
```
X-Internal-API-Key: <INTERNAL_ML_API_KEY>
```

---

## Azure VM Migration Guide

### What's Already Deployed

✅ **Currently Running on Azure VM (20.81.210.213)**:
- Harvey Backend (port 8000)
- Harvey Intelligence Engine (port 9000)
- Azure SQL Database
- Nginx reverse proxy
- Systemd services

### What Needs Migration

The following components need to be deployed to Azure VM:

#### 1. Multi-Model AI Router
**Files to Deploy**:
- `app/core/model_router.py` (updated)
- `app/core/llm_providers.py` (updated)
- `app/services/harvey_intelligence.py` (new)
- `app/routes/harvey_status.py` (new)

#### 2. Model Audit Service
**Files to Deploy**:
- `app/services/model_audit_service.py` (new)

**Database Migration**:
```sql
CREATE TABLE dividend_model_audit_log (
    id INT IDENTITY(1,1) PRIMARY KEY,
    query NVARCHAR(1000),
    selected_model VARCHAR(50),
    routing_reason NVARCHAR(500),
    model_responses_json NVARCHAR(MAX),
    dividend_metrics_json NVARCHAR(MAX),
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    created_at DATETIME DEFAULT GETUTCDATE()
);
```

#### 3. Dividend Strategy Analyzer
**Files to Deploy**:
- `app/services/dividend_strategy_analyzer.py` (new)
- `app/routes/dividend_strategies.py` (new)

#### 4. Documentation
**Files to Deploy**:
- `HARVEY_UNIFIED_ARCHITECTURE.md`
- `HARVEY_COMPLETE_SYSTEM_DOCUMENTATION.md`
- `replit.md` (updated)

### Migration Steps

#### Step 1: SSH into Azure VM
```bash
ssh user@20.81.210.213
cd /path/to/harvey
```

#### Step 2: Pull Latest Code
```bash
git pull origin main
```

#### Step 3: Install New Dependencies
```bash
pip install google-generativeai  # For Gemini support
pip install azure-ai-documentintelligence  # Already done if previous deployment complete
```

#### Step 4: Set Environment Variables
Add to your environment configuration:
```bash
# Gemini API (if not already set)
export GEMINI_API_KEY="your-gemini-api-key"

# Verify existing variables
echo $AZURE_OPENAI_ENDPOINT
echo $AZURE_OPENAI_API_KEY
echo $ML_API_BASE_URL
echo $INTERNAL_ML_API_KEY
```

#### Step 5: Create Database Table
Run the SQL script above to create `dividend_model_audit_log` table in Azure SQL.

#### Step 6: Restart Services
```bash
sudo systemctl restart harvey-backend
sudo systemctl restart harvey-intelligence
sudo systemctl status harvey-backend
sudo systemctl status harvey-intelligence
```

#### Step 7: Verify Deployment
```bash
# Check Harvey status
curl http://localhost:8000/v1/harvey/status

# Check dividend strategies
curl http://localhost:8000/v1/dividend-strategies/list

# Check ML engine
curl http://localhost:9000/api/internal/ml/health
```

### Post-Migration Verification

1. **Test Multi-Model Routing**:
   - Ask questions that trigger different models
   - Verify model selection in logs

2. **Test Dividend Strategies**:
   - Call strategy analysis endpoint
   - Verify calculations are correct

3. **Test Model Auditing**:
   - Make several queries
   - Check if responses are logged in database

4. **Test Ensemble Mode**:
   - Ask complex dividend questions
   - Verify multiple models respond

### Configuration Files to Update

**main.py** - Ensure new routes are imported:
```python
from app.routes import harvey_status
from app.routes import dividend_strategies
```

**requirements.txt** - Ensure includes:
```
google-generativeai
azure-ai-documentintelligence
```

---

## System Health Monitoring

### Key Metrics to Track

**Model Performance**:
- Response time per model
- Error rates by model
- Cost per query
- User satisfaction by model

**Strategy Analysis**:
- Most requested strategies
- Strategy success rates
- User adoption of recommendations

**System Health**:
- API latency
- Database query performance
- Model availability
- Cache hit rates

### Monitoring Commands

```bash
# Check system status
curl http://20.81.210.213/v1/harvey/status

# View logs
sudo journalctl -u harvey-backend -f
sudo journalctl -u harvey-intelligence -f

# Database queries
SELECT COUNT(*) FROM dividend_model_audit_log WHERE created_at > DATEADD(day, -1, GETUTCDATE());
SELECT selected_model, COUNT(*) as count FROM dividend_model_audit_log GROUP BY selected_model;
```

---

## Troubleshooting

### Common Issues

**1. Gemini Not Working**:
- Install: `pip install google-generativeai`
- Set: `export GEMINI_API_KEY=...`
- Fallback: System gracefully degrades to other models

**2. Database Connection Issues**:
- Verify SQL Server credentials
- Check firewall rules
- Ensure pymssql installed

**3. Model Routing Errors**:
- Check Azure OpenAI deployments exist
- Verify API keys are set
- Review logs for specific errors

**4. High Costs**:
- Review model usage distribution
- Adjust routing weights
- Increase use of DeepSeek-R1 and FinGPT

---

## Future Enhancements

**Planned Features**:
1. Automated FinGPT fine-tuning
2. Real-time routing weight optimization
3. A/B testing for model selection
4. Advanced dividend prediction models
5. Options strategy integration
6. International dividend tax optimization

---

## Support & Documentation

**Primary Documentation**:
- `HARVEY_UNIFIED_ARCHITECTURE.md` - Complete system architecture
- `deploy/MULTI_MODEL_DEPLOYMENT.md` - Deployment guide
- `replit.md` - System configuration and preferences

**Log Locations**:
- Harvey Backend: `/var/log/harvey/backend.log`
- Intelligence Engine: `/var/log/harvey/ml-engine.log`
- Nginx: `/var/log/nginx/access.log`

---

**Document Version**: 4.0.0  
**Last Updated**: November 2, 2025  
**Status**: Production-Ready  
**Next Action**: Deploy to Azure VM following migration guide