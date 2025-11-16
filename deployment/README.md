# Harvey Deployment Scripts

This directory contains deployment scripts and migrations for the Harvey AI backend.

## Database Migrations

### 001_add_new_features.sql
Creates database tables for new Harvey features:
- User watchlists and portfolios
- Dividend lists management
- Video engagement tracking
- User feedback collection
- Investor education tracking

**To run:**
```bash
python3 run_migration.py
```

## Data Seeding

### seed_stock_profiles.py
Populates the `stock_profiles` table with sample dividend stocks for testing the Dividend Lists feature.

**Stocks included:**
- 5 Dividend Aristocrats (25+ years of growth)
- 3 Dividend Kings (50+ years of growth)
- 3 High Yield stocks (>5% yield)
- 3 Monthly payers (REITs)
- 6 Additional quality dividend stocks

**To run:**
```bash
cd /home/azureuser/harvey
python3 deployment/seed_stock_profiles.py
```

**Features enabled after seeding:**
- Dividend Lists API will return real stock data
- Category filtering (Aristocrats, Kings, High Yield, etc.)
- Watchlist and portfolio integration

## Deployment Checklist

1. **Pull latest code:** `git pull origin main`
2. **Run migrations:** `python3 run_migration.py`
3. **Seed data:** `python3 deployment/seed_stock_profiles.py`
4. **Restart service:** `sudo systemctl restart harvey-backend`
5. **Verify:** Check `/healthz` endpoint

## Monitoring

Monitor the new features at:
- `/api/videos/*` - Video search endpoints
- `/api/dividend-lists/*` - Dividend lists endpoints
- Harvey backend logs: `journalctl -u harvey-backend -f`
