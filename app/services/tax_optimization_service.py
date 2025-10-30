"""
Tax Optimization Service

Helps dividend investors minimize tax burden through:
1. Identifying qualified vs ordinary dividends
2. Tax-loss harvesting opportunities
3. Tax-efficient portfolio positioning
4. Holding period optimization
"""

import os
import json
import uuid
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import text

from app.core.database import engine
from app.core.llm_providers import oai_client, CHAT_MODEL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tax_optimization_service")

TAX_RATES = {
    'qualified': {
        'low': 0.0,
        'medium': 0.15,
        'high': 0.20
    },
    'ordinary': {
        'low': 0.22,
        'medium': 0.24,
        'high': 0.37
    },
    'short_term_gains': {
        'low': 0.22,
        'medium': 0.24,
        'high': 0.37
    },
    'long_term_gains': {
        'low': 0.0,
        'medium': 0.15,
        'high': 0.20
    }
}


def is_qualified_dividend(ticker: str, holding_days: Optional[int] = None) -> tuple[bool, str]:
    """
    Check if a dividend is qualified based on ticker and holding period.
    
    Qualified dividend requirements:
    - US company or qualified foreign corporation
    - Held for >60 days during 121-day period around ex-dividend date
    
    Args:
        ticker: Stock ticker symbol
        holding_days: Days held (if available)
    
    Returns:
        (is_qualified, reason)
    """
    try:
        query = text("""
            SELECT TOP 1 
                s.Ticker,
                s.Company_Name,
                s.Country,
                s.Exchange,
                s.Security_Type
            FROM dbo.vSecurities s
            WHERE s.Ticker = :ticker
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {'ticker': ticker})
            row = result.fetchone()
        
        if not row:
            return False, f"Ticker {ticker} not found in database"
        
        country = row[2] or ""
        exchange = row[3] or ""
        security_type = row[4] or ""
        
        if security_type.upper() in ['ETF', 'MUTUAL FUND', 'INDEX FUND']:
            return True, "ETFs typically pay qualified dividends if underlying holdings meet requirements"
        
        is_us_or_qualified = (
            country.upper() == 'USA' or
            country.upper() == 'UNITED STATES' or
            exchange.upper() in ['NYSE', 'NASDAQ', 'AMEX', 'NYSEArca']
        )
        
        if not is_us_or_qualified:
            return False, f"Foreign company not in qualified foreign corporation list"
        
        if holding_days is not None and holding_days < 60:
            return False, f"Held for only {holding_days} days (need >60 days)"
        
        return True, "US company, meets qualified dividend requirements"
        
    except Exception as e:
        logger.error(f"Error checking qualified dividend for {ticker}: {e}")
        return False, f"Error: {str(e)}"


def calculate_holding_period(purchase_date: date) -> int:
    """Calculate days held from purchase date to today."""
    if not purchase_date:
        return 0
    
    if isinstance(purchase_date, str):
        purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d').date()
    
    today = date.today()
    delta = today - purchase_date
    return delta.days


def calculate_tax_savings(loss_amount: float, tax_bracket: float) -> float:
    """Calculate tax savings from harvesting a loss."""
    return abs(loss_amount) * tax_bracket


def find_similar_tickers(ticker: str, sector: str, limit: int = 5) -> List[str]:
    """
    Find similar tickers in the same sector for replacement recommendations.
    Avoids suggesting the exact same ticker (wash sale rule).
    
    Args:
        ticker: Original ticker to replace
        sector: Sector to search within
        limit: Maximum number of suggestions
    
    Returns:
        List of ticker symbols
    """
    try:
        query = text("""
            SELECT TOP (:limit)
                s.Ticker,
                s.Company_Name,
                q.Market_Cap,
                d.annual_dividend
            FROM dbo.vSecurities s
            LEFT JOIN (
                SELECT 
                    Ticker,
                    Price,
                    Market_Cap,
                    ROW_NUMBER() OVER (PARTITION BY Ticker ORDER BY Last_Updated DESC) AS rn
                FROM dbo.vQuotesEnhanced
            ) q ON s.Ticker = q.Ticker AND q.rn = 1
            LEFT JOIN (
                SELECT 
                    Ticker,
                    SUM(AdjDividend_Amount) AS annual_dividend
                FROM dbo.vDividendsEnhanced
                WHERE Payment_Date >= DATEADD(year, -1, CAST(GETDATE() AS DATE))
                GROUP BY Ticker
            ) d ON s.Ticker = d.Ticker
            WHERE s.Sector = :sector
                AND s.Ticker != :ticker
                AND q.Price > 0
            ORDER BY q.Market_Cap DESC, d.annual_dividend DESC
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {
                'ticker': ticker,
                'sector': sector or 'Technology',
                'limit': limit
            })
            rows = result.fetchall()
        
        return [row[0] for row in rows if row[0]]
        
    except Exception as e:
        logger.error(f"Error finding similar tickers: {e}")
        return []


def analyze_qualified_dividends(
    session_id: str,
    portfolio_tickers: Optional[List[str]] = None,
    user_tax_bracket: str = 'medium'
) -> dict:
    """
    Analyze which dividends are qualified vs ordinary.
    
    Args:
        session_id: User session ID
        portfolio_tickers: Optional list of tickers to analyze (if None, gets from user_portfolios)
        user_tax_bracket: Tax bracket ('low', 'medium', 'high')
    
    Returns:
        Dict with qualified percentage, tax savings estimate, and breakdown
    """
    try:
        logger.info(f"Analyzing qualified dividends for session {session_id}")
        
        if portfolio_tickers:
            tickers = portfolio_tickers
            portfolio_data = {}
        else:
            portfolio_query = text("""
                SELECT 
                    ticker,
                    shares,
                    cost_basis,
                    purchase_date,
                    annual_dividend
                FROM dbo.user_portfolios
                WHERE session_id = :session_id
            """)
            
            with engine.connect() as conn:
                result = conn.execute(portfolio_query, {'session_id': session_id})
                rows = result.fetchall()
            
            if not rows:
                return {
                    'success': False,
                    'error': 'No portfolio found for this session',
                    'qualified_percentage': 0,
                    'tax_savings_estimate': 0,
                    'breakdown': []
                }
            
            tickers = [row[0] for row in rows]
            portfolio_data = {
                row[0]: {
                    'shares': float(row[1]) if row[1] else 0,
                    'cost_basis': float(row[2]) if row[2] else 0,
                    'purchase_date': row[3],
                    'annual_dividend': float(row[4]) if row[4] else 0
                }
                for row in rows
            }
        
        dividend_query = text("""
            SELECT 
                d.Ticker,
                s.Company_Name,
                SUM(d.AdjDividend_Amount) AS annual_dividend,
                s.Sector,
                s.Country
            FROM dbo.vDividendsEnhanced d
            INNER JOIN dbo.vSecurities s ON d.Ticker = s.Ticker
            WHERE d.Payment_Date >= DATEADD(year, -1, CAST(GETDATE() AS DATE))
                AND d.Ticker IN :tickers
            GROUP BY d.Ticker, s.Company_Name, s.Sector, s.Country
        """)
        
        breakdown = []
        total_dividend_income = 0
        qualified_dividend_income = 0
        
        with engine.connect() as conn:
            result = conn.execute(dividend_query, {'tickers': tuple(tickers) if tickers else ('',)})
            dividend_rows = result.fetchall()
        
        for row in dividend_rows:
            ticker = row[0]
            company_name = row[1]
            annual_div_per_share = float(row[2]) if row[2] else 0
            sector = row[3]
            
            shares = portfolio_data.get(ticker, {}).get('shares', 1)
            purchase_date = portfolio_data.get(ticker, {}).get('purchase_date')
            
            total_annual_dividend = annual_div_per_share * shares
            
            holding_days = calculate_holding_period(purchase_date) if purchase_date else None
            is_qualified, reason = is_qualified_dividend(ticker, holding_days)
            
            dividend_type = 'qualified' if is_qualified else 'ordinary'
            
            tax_rate_qualified = TAX_RATES['qualified'][user_tax_bracket]
            tax_rate_ordinary = TAX_RATES['ordinary'][user_tax_bracket]
            
            tax_on_qualified = total_annual_dividend * tax_rate_qualified
            tax_on_ordinary = total_annual_dividend * tax_rate_ordinary
            tax_difference = tax_on_ordinary - tax_on_qualified
            
            breakdown.append({
                'ticker': ticker,
                'company_name': company_name,
                'sector': sector,
                'dividend_type': dividend_type,
                'annual_dividend': round(total_annual_dividend, 2),
                'tax_rate_qualified': tax_rate_qualified,
                'tax_rate_ordinary': tax_rate_ordinary,
                'tax_difference': round(tax_difference, 2),
                'holding_days': holding_days,
                'qualification_reason': reason
            })
            
            total_dividend_income += total_annual_dividend
            if is_qualified:
                qualified_dividend_income += total_annual_dividend
        
        if not breakdown:
            return {
                'success': False,
                'error': 'No dividend data found for provided tickers',
                'qualified_percentage': 0,
                'tax_savings_estimate': 0,
                'breakdown': []
            }
        
        qualified_percentage = (qualified_dividend_income / total_dividend_income * 100) if total_dividend_income > 0 else 0
        
        tax_savings_estimate = sum(item['tax_difference'] for item in breakdown if item['dividend_type'] == 'qualified')
        
        recommendations = []
        if qualified_percentage < 70:
            recommendations.append("Consider replacing ordinary dividend stocks with qualified dividend payers to reduce tax burden")
        
        for item in breakdown:
            if item['holding_days'] and item['holding_days'] < 60:
                recommendations.append(f"Hold {item['ticker']} for {60 - item['holding_days']} more days to qualify for lower tax rate")
        
        result = {
            'success': True,
            'qualified_percentage': round(qualified_percentage, 2),
            'total_dividend_income': round(total_dividend_income, 2),
            'qualified_dividends': round(qualified_dividend_income, 2),
            'ordinary_dividends': round(total_dividend_income - qualified_dividend_income, 2),
            'tax_savings_estimate': round(tax_savings_estimate, 2),
            'recommendations': recommendations,
            'breakdown': breakdown,
            'user_tax_bracket': user_tax_bracket
        }
        
        logger.info(f"Qualified dividend analysis complete: {qualified_percentage:.1f}% qualified, ${tax_savings_estimate:.2f} savings")
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing qualified dividends: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'qualified_percentage': 0,
            'tax_savings_estimate': 0,
            'breakdown': []
        }


def find_tax_loss_harvest_opportunities(
    session_id: str,
    min_loss_threshold: float = 1000,
    user_tax_bracket: str = 'medium'
) -> dict:
    """
    Identify tax-loss harvesting opportunities from user's portfolio.
    
    Analyzes user_portfolios table for:
    - Positions with unrealized losses
    - Replacement ticker suggestions (similar but not wash sale)
    - Potential tax savings
    
    Args:
        session_id: User session ID
        min_loss_threshold: Minimum loss amount to consider
        user_tax_bracket: Tax bracket for savings calculation
    
    Returns:
        Dict with opportunities, total harvestable losses, and estimated tax savings
    """
    try:
        logger.info(f"Finding tax-loss harvest opportunities for session {session_id}")
        
        portfolio_query = text("""
            SELECT 
                p.ticker,
                p.shares,
                p.cost_basis,
                p.current_price,
                p.current_value,
                p.unrealized_gain_loss,
                p.purchase_date,
                s.Sector,
                s.Company_Name
            FROM dbo.user_portfolios p
            LEFT JOIN dbo.vSecurities s ON p.ticker = s.Ticker
            WHERE p.session_id = :session_id
                AND p.unrealized_gain_loss < 0
            ORDER BY p.unrealized_gain_loss ASC
        """)
        
        with engine.connect() as conn:
            result = conn.execute(portfolio_query, {'session_id': session_id})
            rows = result.fetchall()
        
        if not rows:
            return {
                'success': True,
                'opportunities': [],
                'total_harvestable_losses': 0,
                'estimated_tax_savings': 0,
                'message': 'No positions with unrealized losses found'
            }
        
        opportunities = []
        total_harvestable_losses = 0
        
        tax_rate = TAX_RATES['short_term_gains'][user_tax_bracket]
        
        for row in rows:
            ticker = row[0]
            shares = float(row[1]) if row[1] else 0
            cost_basis = float(row[2]) if row[2] else 0
            current_price = float(row[3]) if row[3] else 0
            current_value = float(row[4]) if row[4] else 0
            unrealized_loss = float(row[5]) if row[5] else 0
            purchase_date = row[6]
            sector = row[7] or 'Unknown'
            company_name = row[8] or ticker
            
            if abs(unrealized_loss) < min_loss_threshold:
                continue
            
            holding_days = calculate_holding_period(purchase_date) if purchase_date else None
            
            wash_sale_warning = holding_days is not None and holding_days < 30
            
            replacement_suggestions = find_similar_tickers(ticker, sector, limit=3)
            
            tax_savings = calculate_tax_savings(unrealized_loss, tax_rate)
            
            opportunities.append({
                'ticker': ticker,
                'company_name': company_name,
                'sector': sector,
                'unrealized_loss': round(unrealized_loss, 2),
                'shares': shares,
                'cost_basis': round(cost_basis, 2),
                'current_price': round(current_price, 2),
                'current_value': round(current_value, 2),
                'tax_savings': round(tax_savings, 2),
                'replacement_suggestions': replacement_suggestions,
                'wash_sale_warning': wash_sale_warning,
                'holding_days': holding_days
            })
            
            total_harvestable_losses += abs(unrealized_loss)
        
        estimated_tax_savings = calculate_tax_savings(total_harvestable_losses, tax_rate)
        
        recommendations = []
        if opportunities:
            recommendations.append(f"Consider harvesting ${total_harvestable_losses:,.2f} in losses for ${estimated_tax_savings:,.2f} in tax savings")
            recommendations.append("Wait 31 days before repurchasing sold securities to avoid wash sale")
            recommendations.append("Use replacement tickers to maintain market exposure during waiting period")
        
        result = {
            'success': True,
            'opportunities': opportunities,
            'total_harvestable_losses': round(total_harvestable_losses, 2),
            'estimated_tax_savings': round(estimated_tax_savings, 2),
            'user_tax_bracket': user_tax_bracket,
            'tax_rate_used': tax_rate,
            'recommendations': recommendations
        }
        
        logger.info(f"Found {len(opportunities)} tax-loss harvest opportunities totaling ${total_harvestable_losses:.2f}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error finding tax-loss harvest opportunities: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'opportunities': [],
            'total_harvestable_losses': 0,
            'estimated_tax_savings': 0
        }


def calculate_tax_scenario(
    session_id: str,
    scenario_type: str,
    user_tax_bracket: str = 'medium',
    harvest_losses: bool = False
) -> dict:
    """
    Calculate tax implications of different scenarios.
    
    Args:
        session_id: User session ID
        scenario_type: 'current', 'optimized', or 'harvest'
        user_tax_bracket: Tax bracket ('low', 'medium', 'high')
        harvest_losses: Whether to include tax-loss harvesting
    
    Returns:
        Dict with scenario analysis including taxes owed and recommendations
    """
    try:
        logger.info(f"Calculating tax scenario '{scenario_type}' for session {session_id}")
        
        qualified_analysis = analyze_qualified_dividends(session_id, user_tax_bracket=user_tax_bracket)
        
        if not qualified_analysis.get('success'):
            return {
                'success': False,
                'error': qualified_analysis.get('error', 'Failed to analyze dividends')
            }
        
        annual_dividend_income = qualified_analysis['total_dividend_income']
        qualified_dividends = qualified_analysis['qualified_dividends']
        ordinary_dividends = qualified_analysis['ordinary_dividends']
        
        qualified_tax_rate = TAX_RATES['qualified'][user_tax_bracket]
        ordinary_tax_rate = TAX_RATES['ordinary'][user_tax_bracket]
        
        tax_on_qualified = qualified_dividends * qualified_tax_rate
        tax_on_ordinary = ordinary_dividends * ordinary_tax_rate
        total_tax_owed = tax_on_qualified + tax_on_ordinary
        
        capital_gains_harvested = 0
        capital_gains_tax = 0
        
        if harvest_losses or scenario_type == 'harvest':
            harvest_analysis = find_tax_loss_harvest_opportunities(
                session_id,
                min_loss_threshold=500,
                user_tax_bracket=user_tax_bracket
            )
            
            if harvest_analysis.get('success'):
                capital_gains_harvested = harvest_analysis['total_harvestable_losses']
                tax_on_gains = harvest_analysis['estimated_tax_savings']
                total_tax_owed -= tax_on_gains
        
        effective_tax_rate = (total_tax_owed / annual_dividend_income * 100) if annual_dividend_income > 0 else 0
        
        recommendations = []
        
        if scenario_type == 'current':
            recommendations.extend(qualified_analysis.get('recommendations', []))
            if qualified_analysis['qualified_percentage'] < 80:
                recommendations.append("Your portfolio could benefit from tax optimization")
        
        elif scenario_type == 'optimized':
            potential_savings = ordinary_dividends * (ordinary_tax_rate - qualified_tax_rate)
            recommendations.append(f"Converting ordinary dividends to qualified could save ${potential_savings:,.2f} annually")
            recommendations.append("Focus on US dividend stocks held >60 days")
            recommendations.append("Consider dividend-focused ETFs for automatic qualified status")
        
        elif scenario_type == 'harvest':
            if capital_gains_harvested > 0:
                recommendations.append(f"Harvesting ${capital_gains_harvested:,.2f} in losses can offset dividend taxes")
                recommendations.append("Replace sold positions with similar securities after 31 days")
            else:
                recommendations.append("No significant tax-loss harvesting opportunities at this time")
        
        scenario_id = str(uuid.uuid4())
        
        scenario_data = {
            'scenario_id': scenario_id,
            'session_id': session_id,
            'scenario_type': scenario_type,
            'annual_dividend_income': round(annual_dividend_income, 2),
            'qualified_dividends': round(qualified_dividends, 2),
            'ordinary_dividends': round(ordinary_dividends, 2),
            'capital_gains_harvested': round(capital_gains_harvested, 2),
            'total_tax_owed': round(total_tax_owed, 2),
            'effective_tax_rate': round(effective_tax_rate, 2),
            'user_tax_bracket': user_tax_bracket,
            'recommendations': recommendations,
            'created_at': datetime.now().isoformat()
        }
        
        save_tax_scenario(session_id, scenario_type, scenario_data)
        
        logger.info(f"Tax scenario '{scenario_type}' calculated: ${total_tax_owed:.2f} tax on ${annual_dividend_income:.2f} income")
        
        return {
            'success': True,
            **scenario_data
        }
        
    except Exception as e:
        logger.error(f"Error calculating tax scenario: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def get_tax_efficient_recommendations(session_id: str, user_tax_bracket: str = 'medium') -> dict:
    """
    AI-powered tax optimization recommendations using OpenAI.
    
    Uses GPT-4o to analyze:
    - Portfolio composition
    - Dividend types
    - Holding periods
    - Tax bracket optimization
    
    Args:
        session_id: User session ID
        user_tax_bracket: Tax bracket ('low', 'medium', 'high')
    
    Returns:
        Dict with AI-generated markdown recommendations
    """
    try:
        logger.info(f"Generating AI tax recommendations for session {session_id}")
        
        qualified_analysis = analyze_qualified_dividends(session_id, user_tax_bracket=user_tax_bracket)
        harvest_analysis = find_tax_loss_harvest_opportunities(session_id, min_loss_threshold=500, user_tax_bracket=user_tax_bracket)
        current_scenario = calculate_tax_scenario(session_id, 'current', user_tax_bracket=user_tax_bracket)
        
        context = {
            'qualified_analysis': qualified_analysis,
            'harvest_opportunities': harvest_analysis,
            'current_scenario': current_scenario
        }
        
        system_prompt = """You are a tax optimization expert specializing in dividend investing.
Analyze the provided portfolio data and generate actionable tax-saving recommendations.

Focus on:
1. Qualified vs ordinary dividend optimization
2. Tax-loss harvesting opportunities
3. Holding period strategies
4. Specific ticker recommendations

Format your response as clear, actionable markdown with dollar amounts for estimated savings."""
        
        user_prompt = f"""Analyze this dividend investor's tax situation and provide specific recommendations:

**Portfolio Tax Analysis:**
- Total Dividend Income: ${qualified_analysis.get('total_dividend_income', 0):,.2f}/year
- Qualified Dividends: ${qualified_analysis.get('qualified_dividends', 0):,.2f} ({qualified_analysis.get('qualified_percentage', 0):.1f}%)
- Ordinary Dividends: ${qualified_analysis.get('ordinary_dividends', 0):,.2f}
- Current Tax Owed: ${current_scenario.get('total_tax_owed', 0):,.2f}

**Tax-Loss Harvest Opportunities:**
- Total Harvestable Losses: ${harvest_analysis.get('total_harvestable_losses', 0):,.2f}
- Potential Tax Savings: ${harvest_analysis.get('estimated_tax_savings', 0):,.2f}
- Number of Opportunities: {len(harvest_analysis.get('opportunities', []))}

**Tax Bracket:** {user_tax_bracket} (Qualified rate: {TAX_RATES['qualified'][user_tax_bracket]*100}%, Ordinary rate: {TAX_RATES['ordinary'][user_tax_bracket]*100}%)

Provide 3-5 specific, actionable recommendations with estimated dollar savings."""
        
        response = oai_client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        
        ai_recommendations = (response.choices[0].message.content or "").strip()
        
        result = {
            'success': True,
            'session_id': session_id,
            'recommendations_markdown': ai_recommendations,
            'context': context,
            'generated_at': datetime.now().isoformat()
        }
        
        logger.info(f"AI tax recommendations generated for session {session_id}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating AI tax recommendations: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'recommendations_markdown': "Unable to generate AI recommendations at this time."
        }


def save_tax_scenario(session_id: str, scenario_type: str, scenario_data: dict) -> str:
    """
    Save tax scenario to database.
    
    Args:
        session_id: User session ID
        scenario_type: Type of scenario
        scenario_data: Full scenario data
    
    Returns:
        scenario_id
    """
    scenario_id = scenario_data.get('scenario_id', str(uuid.uuid4()))
    
    try:
        analysis_json = json.dumps({
            'annual_dividend_income': scenario_data.get('annual_dividend_income', 0),
            'qualified_dividends': scenario_data.get('qualified_dividends', 0),
            'ordinary_dividends': scenario_data.get('ordinary_dividends', 0),
            'capital_gains_harvested': scenario_data.get('capital_gains_harvested', 0),
            'total_tax_owed': scenario_data.get('total_tax_owed', 0),
            'effective_tax_rate': scenario_data.get('effective_tax_rate', 0)
        })
        
        recommendations_json = json.dumps(scenario_data.get('recommendations', []))
        
        potential_savings = scenario_data.get('capital_gains_harvested', 0) * 0.24
        
        tax_year = datetime.now().year
        
        query = text("""
            INSERT INTO dbo.tax_scenarios 
            (scenario_id, session_id, scenario_type, ticker, analysis_data, 
             recommendations, potential_savings, tax_year, created_at)
            VALUES 
            (:scenario_id, :session_id, :scenario_type, NULL, :analysis_data,
             :recommendations, :potential_savings, :tax_year, GETDATE());
        """)
        
        with engine.begin() as conn:
            conn.execute(query, {
                'scenario_id': scenario_id,
                'session_id': session_id,
                'scenario_type': scenario_type,
                'analysis_data': analysis_json,
                'recommendations': recommendations_json,
                'potential_savings': potential_savings,
                'tax_year': tax_year
            })
        
        logger.info(f"Saved tax scenario {scenario_id} to database")
        return scenario_id
        
    except Exception as e:
        logger.error(f"Error saving tax scenario: {e}", exc_info=True)
        raise


def format_tax_report_markdown(
    qualified_analysis: dict,
    harvest_analysis: Optional[dict] = None,
    scenario: Optional[dict] = None
) -> str:
    """
    Format tax analysis as markdown for display.
    
    Args:
        qualified_analysis: Qualified dividend analysis results
        harvest_analysis: Optional tax-loss harvest analysis
        scenario: Optional scenario analysis
    
    Returns:
        Formatted markdown string
    """
    md = "## 💰 Tax Optimization Analysis\n\n"
    
    md += "### Current Tax Situation\n"
    md += f"- **Annual Dividend Income:** ${qualified_analysis.get('total_dividend_income', 0):,.2f}\n"
    md += f"- **Qualified Dividends:** ${qualified_analysis.get('qualified_dividends', 0):,.2f} ({qualified_analysis.get('qualified_percentage', 0):.1f}%)\n"
    md += f"- **Ordinary Dividends:** ${qualified_analysis.get('ordinary_dividends', 0):,.2f}\n"
    
    if scenario:
        md += f"- **Est. Tax Owed:** ${scenario.get('total_tax_owed', 0):,.2f}\n"
        md += f"- **Effective Tax Rate:** {scenario.get('effective_tax_rate', 0):.2f}%\n"
    
    md += "\n"
    
    if harvest_analysis and harvest_analysis.get('opportunities'):
        md += "### Tax-Loss Harvesting Opportunities\n\n"
        
        for i, opp in enumerate(harvest_analysis['opportunities'][:5], 1):
            ticker = opp['ticker']
            loss = opp['unrealized_loss']
            savings = opp['tax_savings']
            replacements = ', '.join(opp['replacement_suggestions'][:3]) if opp['replacement_suggestions'] else 'N/A'
            holding_days = opp.get('holding_days', 'Unknown')
            
            md += f"{i}. **{ticker}** - Unrealized Loss: ${abs(loss):,.2f}\n"
            md += f"   - Tax Savings: ${savings:,.2f}\n"
            md += f"   - Replacement: {replacements}\n"
            
            if opp.get('wash_sale_warning'):
                md += f"   - ⚠️ Hold Period: {holding_days} days - Wash sale risk\n"
            
            md += "\n"
        
        md += f"**Total Harvestable:** ${harvest_analysis.get('total_harvestable_losses', 0):,.2f}\n"
        md += f"**Total Tax Savings:** ${harvest_analysis.get('estimated_tax_savings', 0):,.2f}\n\n"
    
    md += "### Recommendations\n\n"
    
    recommendations = qualified_analysis.get('recommendations', [])
    if harvest_analysis:
        recommendations.extend(harvest_analysis.get('recommendations', []))
    if scenario:
        recommendations.extend(scenario.get('recommendations', []))
    
    seen = set()
    for rec in recommendations:
        if rec not in seen:
            md += f"- {rec}\n"
            seen.add(rec)
    
    md += "\n"
    
    if scenario:
        md += "### Optimized Scenario\n"
        optimized_tax = scenario.get('total_tax_owed', 0)
        md += f"- After Optimization Tax: ${optimized_tax:,.2f}\n"
        
        if harvest_analysis:
            savings = harvest_analysis.get('estimated_tax_savings', 0)
            md += f"- **Tax Savings: ${savings:,.2f}/year**\n"
    
    return md
