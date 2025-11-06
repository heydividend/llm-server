# Harvey Financial Models

Custom financial computation engines for dividend and portfolio analysis.

## Overview

Harvey's **Portfolio and Watchlist Projection Engine** provides domain-specific financial computations (not generic ML) for comprehensive dividend investing analysis:

1. **Portfolio Projection Engine** - Projects 1/3/5/10 year dividend income using historical CAGR
2. **Watchlist Projection Engine** - Analyzes potential income and optimal allocations
3. **Dividend Sustainability Analyzer** - Assesses payout ratio health, assigns A-F grades
4. **Cash Flow Sensitivity Model** - Stress tests portfolio with dividend cut scenarios

## Architecture

```
financial_models/
├── engines/          # Financial computation engines
│   ├── portfolio_projection.py
│   ├── watchlist_projection.py
│   ├── sustainability_analyzer.py
│   └── cashflow_sensitivity.py
├── utils/            # Database extractors
│   └── database.py
└── api/              # FastAPI endpoints
    └── endpoints.py
```

## Key Features

### Portfolio Projection Engine
- **Real CAGR calculations** from historical dividend data (10 years)
- **Multi-year projections**: 1, 3, 5, and 10 year income forecasts
- **Growth modeling**: Individual growth rates per holding
- **Sector diversification** analysis
- **Cumulative dividend** tracking

### Watchlist Projection Engine
- **What-if analysis**: "What if I invest $10,000?"
- **Optimal allocation**: Achieve target monthly income with diversification
- **Sustainability scoring**: Grades stocks based on payout ratio, growth, yield
- **Top picks recommendations**: Best yield, best growth, most sustainable

### Dividend Sustainability Analyzer
- **Payout ratio health**: 0-100 score with A-F grade
- **Consistency score**: Payment frequency and reliability
- **Cut risk analysis**: Probability of dividend reduction
- **Portfolio-level**: Weighted average scores across holdings

### Cash Flow Sensitivity Model
- **Stress scenarios**: 10%/20%/40% dividend cuts
- **Sector-specific**: What if top sector cuts dividends 30%?
- **Top stock impact**: Analyze loss if highest-income stock cuts
- **Income stability score**: Portfolio resilience under stress
- **Diversification recommendations**

## Usage

### From Python

```python
from financial_models.utils.database import FinancialDataExtractor
from financial_models.engines.portfolio_projection import PortfolioProjectionEngine

# Initialize
data_extractor = FinancialDataExtractor()
portfolio_engine = PortfolioProjectionEngine(data_extractor)

# Analyze portfolio
result = portfolio_engine.analyze_portfolio(user_id="user123")

# Access projections
print(result['portfolio_projection']['projections'][10])
# {'annual_income': 45234.21, 'monthly_income': 3769.52, ...}
```

### From API

```bash
# Portfolio projection
curl -X POST http://localhost:8000/api/financial/portfolio/projection \
  -H "X-Internal-API-Key: ${INTERNAL_ML_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "years": 10}'

# Watchlist analysis
curl -X POST http://localhost:8000/api/financial/watchlist/analyze \
  -H "X-Internal-API-Key: ${INTERNAL_ML_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "investment_amount": 50000}'

# Sustainability analysis
curl -X POST http://localhost:8000/api/financial/sustainability/stock \
  -H "X-Internal-API-Key: ${INTERNAL_ML_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}'

# Cash flow sensitivity
curl -X POST http://localhost:8000/api/financial/cashflow/sensitivity \
  -H "X-Internal-API-Key: ${INTERNAL_ML_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123"}'
```

## Integration with Harvey Backend

Add to your FastAPI app:

```python
from financial_models.api.endpoints import router as financial_router

app.include_router(financial_router)
```

## Data Sources

All engines use **Azure SQL** data:
- `portfolio_holdings` - User's current positions
- `watchlist` - User's watchlist stocks
- `dividend_data` - Historical dividend payments
- `tickers` - Fundamental metrics
- `latest_prices` - Current market prices

## Environment Variables

Required:
- `INTERNAL_ML_API_KEY` - API authentication (no default, fail-fast if missing)
- `SQLSERVER_HOST` - Azure SQL server
- `SQLSERVER_DB` - Database name
- `SQLSERVER_USER` - Database user
- `SQLSERVER_PASSWORD` - Database password

## Response Formats

### Portfolio Projection
```json
{
  "success": true,
  "portfolio_projection": {
    "current_annual_income": 12450.00,
    "current_monthly_income": 1037.50,
    "projections": {
      "1": {"annual_income": 13102.50, "monthly_income": 1091.88},
      "10": {"annual_income": 24789.34, "monthly_income": 2065.78}
    },
    "holdings_detail": [...],
    "growth_assumptions": {...}
  }
}
```

### Sustainability Analysis
```json
{
  "success": true,
  "ticker": "AAPL",
  "sustainability_analysis": {
    "overall_score": 87.5,
    "grade": "A",
    "components": {
      "payout_ratio_health": {"score": 90, "status": "Excellent"},
      "consistency_score": 95.2,
      "growth_health": {"score": 85, "status": "Very Good"},
      "cut_risk_score": 12.5
    }
  }
}
```

## Security

- All API endpoints require `X-Internal-API-Key` header
- API key must be set via environment variable (no hardcoded defaults)
- Fail-fast if environment variable is missing

## Performance Considerations

- Database connections are opened per-call (acceptable for low traffic)
- For high traffic, implement connection pooling
- Consider caching for frequently-accessed ticker data

## Development

```bash
# Install dependencies
pip install fastapi pymssql python-dotenv

# Run tests (after implementation)
pytest financial_models/tests/

# Lint
pylint financial_models/
```

## Roadmap

- [ ] Connection pooling for database queries
- [ ] Caching layer for ticker fundamentals
- [ ] Integration tests with real Azure SQL
- [ ] Performance benchmarking
- [ ] Monte Carlo simulation for projections
