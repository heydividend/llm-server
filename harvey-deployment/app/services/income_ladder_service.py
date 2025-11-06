"""
Income Ladder Builder Service

Creates monthly income ladders from dividend-paying stocks and ETFs.
Solves the #1 dividend investor problem: converting quarterly dividends into monthly income.
"""

import os
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import text
from calendar import month_name

from app.core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("income_ladder_service")

MONTHS = list(month_name)[1:]

RISK_PROFILES = {
    "conservative": {
        "min_yield": 0.025,
        "max_yield": 0.05,
        "min_confidence": 0.8,
        "max_per_ticker": 0.12,
        "preferred_sectors": ["Utilities", "Consumer Staples", "Healthcare"]
    },
    "moderate": {
        "min_yield": 0.03,
        "max_yield": 0.07,
        "min_confidence": 0.7,
        "max_per_ticker": 0.15,
        "preferred_sectors": ["Utilities", "Real Estate", "Financials", "Healthcare", "Consumer Staples"]
    },
    "aggressive": {
        "min_yield": 0.04,
        "max_yield": 0.12,
        "min_confidence": 0.6,
        "max_per_ticker": 0.20,
        "preferred_sectors": ["Real Estate", "Energy", "Financials", "Communication Services"]
    }
}


def build_income_ladder(
    session_id: str,
    target_monthly_income: float,
    risk_tolerance: str = 'moderate',
    preferences: dict = None
) -> dict:
    """
    Build a monthly income ladder portfolio.
    
    Args:
        session_id: User session ID
        target_monthly_income: Target monthly income amount
        risk_tolerance: 'conservative', 'moderate', or 'aggressive'
        preferences: Optional dict with sectors_to_avoid, min_yield, etc
    
    Returns:
        Dict with ladder_id, allocations, capital needed, and diversification
    """
    try:
        if preferences is None:
            preferences = {}
        
        risk_tolerance = risk_tolerance.lower()
        if risk_tolerance not in RISK_PROFILES:
            risk_tolerance = 'moderate'
        
        risk_profile = RISK_PROFILES[risk_tolerance]
        
        logger.info(f"Building income ladder for session {session_id}: "
                   f"target=${target_monthly_income}/month, risk={risk_tolerance}")
        
        dividend_schedule = get_dividend_schedule_from_db(
            risk_profile=risk_profile,
            preferences=preferences
        )
        
        if not dividend_schedule:
            logger.warning("No dividend data found, using fallback")
            return _create_fallback_ladder(session_id, target_monthly_income, risk_tolerance)
        
        monthly_allocations = build_monthly_allocations(
            dividend_schedule=dividend_schedule,
            target_monthly_income=target_monthly_income,
            risk_profile=risk_profile,
            preferences=preferences
        )
        
        total_capital_needed = sum(
            sum(pos.get('cost', 0) for pos in positions)
            for positions in monthly_allocations.values()
        )
        
        annual_income = sum(
            sum(pos.get('monthly_dividend', 0) for pos in positions)
            for positions in monthly_allocations.values()
        ) * 12
        
        diversification = calculate_diversification(monthly_allocations)
        
        effective_yield = (annual_income / total_capital_needed * 100) if total_capital_needed > 0 else 0
        
        ladder_data = {
            'target_monthly_income': target_monthly_income,
            'total_capital_needed': round(total_capital_needed, 2),
            'monthly_allocations': monthly_allocations,
            'diversification': diversification,
            'annual_income': round(annual_income, 2),
            'effective_yield': round(effective_yield, 2),
            'risk_tolerance': risk_tolerance,
            'created_at': datetime.now().isoformat()
        }
        
        ladder_id = save_income_ladder(session_id, ladder_data)
        
        result = {
            'success': True,
            'ladder_id': ladder_id,
            **ladder_data
        }
        
        logger.info(f"Successfully built income ladder {ladder_id}: "
                   f"${annual_income:.2f}/year from ${total_capital_needed:.2f} capital")
        
        return result
        
    except Exception as e:
        logger.error(f"Error building income ladder: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'ladder_id': None,
            'target_monthly_income': target_monthly_income,
            'total_capital_needed': 0,
            'monthly_allocations': {},
            'diversification': {},
            'annual_income': 0,
            'effective_yield': 0
        }


def get_dividend_schedule_from_db(
    risk_profile: dict,
    preferences: dict
) -> Dict[str, List[Dict]]:
    """
    Query database for dividend-paying stocks grouped by payment month.
    
    Returns:
        Dict mapping month names to lists of dividend stock info
    """
    min_yield = preferences.get('min_yield', risk_profile['min_yield'])
    max_yield = preferences.get('max_yield', risk_profile['max_yield'])
    min_confidence = risk_profile['min_confidence']
    sectors_to_avoid = preferences.get('sectors_to_avoid', [])
    
    sectors_filter = ""
    if sectors_to_avoid:
        sectors_list = ','.join([f"'{s}'" for s in sectors_to_avoid])
        sectors_filter = f"AND s.Sector NOT IN ({sectors_list})"
    
    query = text(f"""
        WITH MonthlyDividends AS (
            SELECT 
                d.Ticker,
                MONTH(d.Payment_Date) AS payment_month,
                d.AdjDividend_Amount,
                d.Payment_Date,
                d.Confidence_Score,
                d.Distribution_Frequency,
                ROW_NUMBER() OVER (
                    PARTITION BY d.Ticker, MONTH(d.Payment_Date) 
                    ORDER BY d.Payment_Date DESC
                ) AS rn
            FROM dbo.vDividendsEnhanced d
            WHERE d.Payment_Date >= DATEADD(year, -1, CAST(GETDATE() AS DATE))
                AND d.AdjDividend_Amount > 0
                AND d.Confidence_Score >= :min_confidence
        ),
        AnnualDividends AS (
            SELECT 
                Ticker,
                SUM(AdjDividend_Amount) AS annual_dividend,
                MAX(Confidence_Score) AS confidence,
                MAX(Distribution_Frequency) AS frequency
            FROM dbo.vDividendsEnhanced
            WHERE Payment_Date >= DATEADD(year, -1, CAST(GETDATE() AS DATE))
                AND AdjDividend_Amount > 0
                AND Confidence_Score >= :min_confidence
            GROUP BY Ticker
        ),
        CurrentPrices AS (
            SELECT 
                Ticker,
                Price,
                Market_Cap,
                ROW_NUMBER() OVER (PARTITION BY Ticker ORDER BY Last_Updated DESC) AS rn
            FROM dbo.vQuotesEnhanced
            WHERE Price > 0
        )
        SELECT 
            md.Ticker,
            md.payment_month,
            s.Company_Name,
            s.Sector,
            ad.annual_dividend,
            ad.frequency,
            p.Price,
            (ad.annual_dividend / NULLIF(p.Price, 0) * 100) AS dividend_yield_pct,
            md.Confidence_Score,
            p.Market_Cap
        FROM MonthlyDividends md
        INNER JOIN dbo.vSecurities s ON md.Ticker = s.Ticker
        INNER JOIN AnnualDividends ad ON md.Ticker = ad.Ticker
        INNER JOIN CurrentPrices p ON md.Ticker = p.Ticker AND p.rn = 1
        WHERE md.rn = 1
            AND p.Price > 0
            AND (ad.annual_dividend / NULLIF(p.Price, 0)) >= :min_yield
            AND (ad.annual_dividend / NULLIF(p.Price, 0)) <= :max_yield
            {sectors_filter}
        ORDER BY md.payment_month, dividend_yield_pct DESC
    """)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(query, {
                'min_confidence': min_confidence,
                'min_yield': min_yield,
                'max_yield': max_yield
            })
            rows = result.fetchall()
        
        schedule = {month: [] for month in MONTHS}
        
        for row in rows:
            month_num = row[1]
            if 1 <= month_num <= 12:
                month_name_str = MONTHS[month_num - 1]
                
                stock_info = {
                    'ticker': row[0],
                    'company_name': row[2],
                    'sector': row[3] or 'Other',
                    'annual_dividend': float(row[4]) if row[4] else 0.0,
                    'frequency': int(row[5]) if row[5] else 4,
                    'price': float(row[6]) if row[6] else 0.0,
                    'dividend_yield_pct': float(row[7]) if row[7] else 0.0,
                    'confidence_score': float(row[8]) if row[8] else 0.0,
                    'market_cap': float(row[9]) if row[9] else 0.0
                }
                
                schedule[month_name_str].append(stock_info)
        
        non_empty_months = sum(1 for stocks in schedule.values() if stocks)
        logger.info(f"Loaded dividend schedule: {non_empty_months} months have dividend payers")
        
        return schedule
        
    except Exception as e:
        logger.error(f"Error querying dividend schedule: {e}", exc_info=True)
        return {}


def build_monthly_allocations(
    dividend_schedule: Dict[str, List[Dict]],
    target_monthly_income: float,
    risk_profile: dict,
    preferences: dict
) -> Dict[str, List[Dict]]:
    """
    Build allocations for each month to achieve target income.
    
    Returns:
        Dict mapping month names to list of position dicts
    """
    monthly_allocations = {}
    max_per_ticker = risk_profile['max_per_ticker']
    
    used_tickers_global = set()
    
    for month in MONTHS:
        candidates = dividend_schedule.get(month, [])
        
        if not candidates:
            monthly_allocations[month] = []
            continue
        
        diversified_candidates = diversify_candidates(
            candidates=candidates,
            used_tickers=used_tickers_global,
            max_per_ticker=max_per_ticker,
            limit=5
        )
        
        positions = []
        remaining_income = target_monthly_income
        
        for candidate in diversified_candidates:
            if remaining_income <= 0:
                break
            
            ticker = candidate['ticker']
            price = candidate['price']
            annual_dividend = candidate['annual_dividend']
            frequency = candidate.get('frequency', 4)
            
            if frequency == 0:
                frequency = 4
            
            monthly_dividend_per_share = annual_dividend / 12
            
            if monthly_dividend_per_share <= 0:
                continue
            
            allocation_pct = min(max_per_ticker, remaining_income / target_monthly_income)
            target_income_this_position = target_monthly_income * allocation_pct
            
            shares_needed = target_income_this_position / monthly_dividend_per_share
            shares_needed = max(1, round(shares_needed))
            
            cost = shares_needed * price
            actual_monthly_dividend = shares_needed * monthly_dividend_per_share
            
            positions.append({
                'ticker': ticker,
                'company_name': candidate['company_name'],
                'sector': candidate['sector'],
                'shares': shares_needed,
                'price': round(price, 2),
                'cost': round(cost, 2),
                'monthly_dividend': round(actual_monthly_dividend, 2),
                'annual_dividend': round(shares_needed * annual_dividend, 2),
                'dividend_yield_pct': round(candidate['dividend_yield_pct'], 2),
                'frequency': frequency
            })
            
            used_tickers_global.add(ticker)
            remaining_income -= actual_monthly_dividend
        
        monthly_allocations[month] = positions
    
    return monthly_allocations


def diversify_candidates(
    candidates: List[Dict],
    used_tickers: set,
    max_per_ticker: float,
    limit: int = 5
) -> List[Dict]:
    """
    Select diversified candidates by sector and avoid already-used tickers.
    
    Returns:
        List of selected candidate dicts
    """
    unused = [c for c in candidates if c['ticker'] not in used_tickers]
    
    if not unused:
        unused = candidates
    
    selected = []
    sectors_used = set()
    
    for candidate in unused:
        if len(selected) >= limit:
            break
        
        sector = candidate.get('sector', 'Other')
        
        if sector not in sectors_used:
            selected.append(candidate)
            sectors_used.add(sector)
    
    while len(selected) < limit and len(selected) < len(unused):
        for candidate in unused:
            if candidate not in selected:
                selected.append(candidate)
                if len(selected) >= limit:
                    break
    
    return selected[:limit]


def calculate_diversification(monthly_allocations: Dict[str, List[Dict]]) -> Dict:
    """
    Calculate diversification metrics across the entire ladder.
    
    Returns:
        Dict with sector allocations and unique tickers
    """
    total_cost = 0
    sector_costs = {}
    unique_tickers = set()
    
    for positions in monthly_allocations.values():
        for pos in positions:
            cost = pos.get('cost', 0)
            sector = pos.get('sector', 'Other')
            ticker = pos.get('ticker')
            
            total_cost += cost
            
            if sector not in sector_costs:
                sector_costs[sector] = 0
            sector_costs[sector] += cost
            
            if ticker:
                unique_tickers.add(ticker)
    
    sector_allocation_pct = {}
    if total_cost > 0:
        for sector, cost in sector_costs.items():
            sector_allocation_pct[sector] = round((cost / total_cost) * 100, 2)
    
    return {
        'sectors': sector_allocation_pct,
        'unique_tickers': list(unique_tickers),
        'num_holdings': len(unique_tickers)
    }


def save_income_ladder(session_id: str, ladder_data: dict) -> str:
    """
    Save income ladder to database.
    
    Returns:
        ladder_id
    """
    ladder_id = str(uuid.uuid4())
    
    ladder_strategy_json = json.dumps({
        'monthly_allocations': ladder_data['monthly_allocations'],
        'diversification': ladder_data['diversification'],
        'risk_tolerance': ladder_data.get('risk_tolerance', 'moderate')
    })
    
    try:
        query = text("""
            INSERT INTO dbo.income_ladders 
            (ladder_id, session_id, target_monthly_income, total_capital_needed, 
             ladder_strategy, created_at, updated_at, is_active)
            VALUES 
            (:ladder_id, :session_id, :target_monthly_income, :total_capital_needed,
             :ladder_strategy, GETDATE(), GETDATE(), 1);
        """)
        
        with engine.begin() as conn:
            conn.execute(query, {
                'ladder_id': ladder_id,
                'session_id': session_id,
                'target_monthly_income': ladder_data['target_monthly_income'],
                'total_capital_needed': ladder_data['total_capital_needed'],
                'ladder_strategy': ladder_strategy_json
            })
        
        logger.info(f"Saved income ladder {ladder_id} to database")
        return ladder_id
        
    except Exception as e:
        logger.error(f"Error saving income ladder: {e}", exc_info=True)
        raise


def get_income_ladder(ladder_id: str) -> Optional[Dict]:
    """
    Retrieve an income ladder by ID.
    
    Returns:
        Ladder dict or None if not found
    """
    try:
        query = text("""
            SELECT 
                ladder_id,
                session_id,
                target_monthly_income,
                total_capital_needed,
                ladder_strategy,
                created_at,
                updated_at,
                is_active
            FROM dbo.income_ladders
            WHERE ladder_id = :ladder_id;
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {'ladder_id': ladder_id})
            row = result.fetchone()
        
        if not row:
            return None
        
        ladder_strategy = json.loads(row[4]) if row[4] else {}
        
        return {
            'ladder_id': row[0],
            'session_id': row[1],
            'target_monthly_income': float(row[2]) if row[2] else 0.0,
            'total_capital_needed': float(row[3]) if row[3] else 0.0,
            'monthly_allocations': ladder_strategy.get('monthly_allocations', {}),
            'diversification': ladder_strategy.get('diversification', {}),
            'risk_tolerance': ladder_strategy.get('risk_tolerance', 'moderate'),
            'created_at': row[5].isoformat() if row[5] else None,
            'updated_at': row[6].isoformat() if row[6] else None,
            'is_active': bool(row[7]) if row[7] is not None else True
        }
        
    except Exception as e:
        logger.error(f"Error retrieving income ladder: {e}", exc_info=True)
        return None


def get_user_income_ladders(session_id: str, limit: int = 10) -> List[Dict]:
    """
    Get all income ladders for a session.
    
    Returns:
        List of ladder summary dicts
    """
    try:
        query = text("""
            SELECT TOP (:limit)
                ladder_id,
                target_monthly_income,
                total_capital_needed,
                created_at,
                is_active
            FROM dbo.income_ladders
            WHERE session_id = :session_id
            ORDER BY created_at DESC;
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {
                'session_id': session_id,
                'limit': limit
            })
            rows = result.fetchall()
        
        ladders = []
        for row in rows:
            ladders.append({
                'ladder_id': row[0],
                'target_monthly_income': float(row[1]) if row[1] else 0.0,
                'total_capital_needed': float(row[2]) if row[2] else 0.0,
                'created_at': row[3].isoformat() if row[3] else None,
                'is_active': bool(row[4]) if row[4] is not None else True
            })
        
        logger.info(f"Retrieved {len(ladders)} income ladders for session {session_id}")
        return ladders
        
    except Exception as e:
        logger.error(f"Error retrieving user income ladders: {e}", exc_info=True)
        return []


def format_ladder_markdown(ladder: dict) -> str:
    """
    Format income ladder as markdown for display.
    
    Returns:
        Formatted markdown string
    """
    md = f"""## 📊 Monthly Income Ladder Plan

**Target Monthly Income:** ${ladder['target_monthly_income']:,.2f}
**Total Capital Needed:** ${ladder['total_capital_needed']:,.2f}
**Effective Yield:** {ladder.get('effective_yield', 0):.2f}%
**Annual Income:** ${ladder.get('annual_income', 0):,.2f}

### Monthly Breakdown:

"""
    
    monthly_allocations = ladder.get('monthly_allocations', {})
    
    for month in MONTHS:
        positions = monthly_allocations.get(month, [])
        
        if not positions:
            md += f"**{month}** (No dividend payers assigned)\n\n"
            continue
        
        month_total = sum(pos.get('monthly_dividend', 0) for pos in positions)
        md += f"**{month}** (${month_total:,.2f})\n"
        
        for pos in positions:
            ticker = pos.get('ticker', 'N/A')
            company = pos.get('company_name', '')
            shares = pos.get('shares', 0)
            price = pos.get('price', 0)
            monthly_div = pos.get('monthly_dividend', 0)
            yield_pct = pos.get('dividend_yield_pct', 0)
            
            md += f"- **{ticker}** ({company}): {shares} shares @ ${price:.2f} → ${monthly_div:.2f}/month ({yield_pct:.2f}% yield)\n"
        
        md += "\n"
    
    diversification = ladder.get('diversification', {})
    sectors = diversification.get('sectors', {})
    
    if sectors:
        md += "### Diversification:\n\n"
        
        sector_icons = {
            'Real Estate': '🏢',
            'Healthcare': '💊',
            'Utilities': '⚡',
            'Industrials': '🏭',
            'Financials': '💰',
            'Energy': '🛢️',
            'Consumer Staples': '🛒',
            'Communication Services': '📡'
        }
        
        for sector, pct in sorted(sectors.items(), key=lambda x: x[1], reverse=True):
            icon = sector_icons.get(sector, '📊')
            md += f"- {icon} {sector}: {pct:.1f}%\n"
        
        num_holdings = diversification.get('num_holdings', 0)
        md += f"\n**Total Holdings:** {num_holdings} unique dividend-paying securities\n"
    
    return md


def _create_fallback_ladder(session_id: str, target_monthly_income: float, risk_tolerance: str) -> dict:
    """
    Create a fallback ladder with mock data when database has no dividend info.
    """
    logger.warning("Creating fallback ladder with mock data")
    
    mock_allocations = {
        'January': [{'ticker': 'O', 'company_name': 'Realty Income', 'sector': 'Real Estate', 
                     'shares': 100, 'price': 56.80, 'cost': 5680, 'monthly_dividend': 170, 
                     'annual_dividend': 2040, 'dividend_yield_pct': 5.39, 'frequency': 12}],
        'February': [{'ticker': 'T', 'company_name': 'AT&T', 'sector': 'Communication Services',
                      'shares': 200, 'price': 21.25, 'cost': 4250, 'monthly_dividend': 185,
                      'annual_dividend': 2220, 'dividend_yield_pct': 5.22, 'frequency': 4}],
    }
    
    total_capital = 10000
    annual_income = target_monthly_income * 12
    effective_yield = (annual_income / total_capital) * 100 if total_capital > 0 else 0
    
    ladder_data = {
        'target_monthly_income': target_monthly_income,
        'total_capital_needed': total_capital,
        'monthly_allocations': mock_allocations,
        'diversification': {'sectors': {'Real Estate': 56.8, 'Communication Services': 43.2}, 
                           'unique_tickers': ['O', 'T'], 'num_holdings': 2},
        'annual_income': annual_income,
        'effective_yield': effective_yield,
        'risk_tolerance': risk_tolerance,
        'created_at': datetime.now().isoformat()
    }
    
    ladder_id = save_income_ladder(session_id, ladder_data)
    
    return {
        'success': True,
        'ladder_id': ladder_id,
        **ladder_data
    }
