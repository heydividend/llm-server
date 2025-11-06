"""
Proactive Insights Service

Generates daily portfolio digests and proactive alerts using GPT-4o.
"""

import os
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy import text

from app.core.database import engine
from app.core.llm_providers import oai_client, CHAT_MODEL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("insights_service")


def generate_daily_digest(session_id: str) -> dict:
    """
    Generate daily portfolio digest for a session.
    
    Analyzes:
    1. Portfolio holdings (user_portfolios table)
    2. Price changes in last 24h
    3. Dividend announcements
    4. Upcoming ex-dividend dates
    5. ML predictions if available
    
    Uses GPT-4o to generate personalized summary.
    
    Args:
        session_id: User session ID
        
    Returns:
        {
            'insight_id': str,
            'title': str (e.g., "Your Daily Portfolio Update - Oct 30, 2025"),
            'content': str (markdown summary),
            'priority': int (1-10),
            'metadata': dict (tickers, changes, etc)
        }
    """
    try:
        logger.info(f"Generating daily digest for session {session_id}")
        
        portfolio_data = _get_portfolio_summary(session_id)
        
        if not portfolio_data or not portfolio_data.get("holdings"):
            logger.info(f"No portfolio holdings found for session {session_id}, skipping digest")
            return {
                "success": False,
                "message": "No portfolio holdings to analyze"
            }
        
        price_changes = _get_recent_price_changes(portfolio_data["tickers"])
        dividend_news = _get_recent_dividend_news(portfolio_data["tickers"])
        upcoming_dividends = _get_upcoming_dividends(portfolio_data["tickers"])
        
        digest_content = _generate_digest_with_gpt(
            session_id,
            portfolio_data,
            price_changes,
            dividend_news,
            upcoming_dividends
        )
        
        insight_id = str(uuid.uuid4())
        today = datetime.now().strftime("%b %d, %Y")
        title = f"Your Daily Portfolio Update - {today}"
        
        metadata = {
            "tickers": portfolio_data["tickers"],
            "significant_changes": [
                pc for pc in price_changes 
                if abs(pc.get("change_pct", 0)) >= 3
            ],
            "dividend_events": len(dividend_news) + len(upcoming_dividends)
        }
        
        query = text("""
            INSERT INTO dbo.proactive_insights
            (insight_id, session_id, insight_type, title, content, priority, created_at, 
             read_status, metadata)
            VALUES
            (:insight_id, :session_id, :insight_type, :title, :content, :priority, GETDATE(),
             0, :metadata);
        """)
        
        with engine.begin() as conn:
            conn.execute(query, {
                "insight_id": insight_id,
                "session_id": session_id,
                "insight_type": "daily_digest",
                "title": title,
                "content": digest_content,
                "priority": 5,
                "metadata": json.dumps(metadata)
            })
        
        logger.info(f"Created daily digest {insight_id} for session {session_id}")
        
        return {
            "success": True,
            "insight_id": insight_id,
            "title": title,
            "content": digest_content,
            "priority": 5,
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"Failed to generate daily digest: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


def _get_portfolio_summary(session_id: str) -> Optional[dict]:
    """Get portfolio holdings summary for a session."""
    try:
        query = text("""
            SELECT ticker, shares, cost_basis, current_price, 
                   current_value, unrealized_gain_loss, annual_dividend
            FROM dbo.user_portfolios
            WHERE session_id = :session_id;
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {"session_id": session_id})
            rows = result.fetchall()
        
        if not rows:
            return None
        
        holdings = []
        total_value = 0
        total_cost = 0
        total_annual_dividend = 0
        tickers = []
        
        for row in rows:
            ticker, shares, cost_basis, current_price, current_value, gain_loss, annual_div = row
            
            tickers.append(ticker)
            total_value += current_value or 0
            total_cost += (shares * cost_basis) if (shares and cost_basis) else 0
            total_annual_dividend += annual_div or 0
            
            holdings.append({
                "ticker": ticker,
                "shares": float(shares),
                "cost_basis": float(cost_basis) if cost_basis else None,
                "current_price": float(current_price) if current_price else None,
                "current_value": float(current_value) if current_value else None,
                "unrealized_gain_loss": float(gain_loss) if gain_loss else None,
                "annual_dividend": float(annual_div) if annual_div else None
            })
        
        return {
            "tickers": tickers,
            "holdings": holdings,
            "total_value": total_value,
            "total_cost": total_cost,
            "total_annual_dividend": total_annual_dividend,
            "portfolio_yield": (total_annual_dividend / total_value * 100) if total_value > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Error getting portfolio summary: {e}")
        return None


def _get_recent_price_changes(tickers: List[str]) -> List[dict]:
    """Get price changes for tickers in the last 24 hours."""
    try:
        if not tickers:
            return []
        
        tickers_str = "', '".join(tickers)
        query_str = f"""
            SELECT ticker, last_price, price_change_pct, volume
            FROM dbo.vQuotesEnhanced
            WHERE ticker IN ('{tickers_str}')
              AND quote_date >= DATEADD(day, -1, GETDATE())
            ORDER BY ABS(price_change_pct) DESC;
        """
        
        with engine.connect() as conn:
            result = conn.exec_driver_sql(query_str)
            rows = result.fetchall()
        
        changes = []
        for row in rows:
            ticker, last_price, change_pct, volume = row
            changes.append({
                "ticker": ticker,
                "last_price": float(last_price) if last_price else None,
                "change_pct": float(change_pct) if change_pct else None,
                "volume": int(volume) if volume else None
            })
        
        return changes
        
    except Exception as e:
        logger.error(f"Error getting price changes: {e}")
        return []


def _get_recent_dividend_news(tickers: List[str]) -> List[dict]:
    """Get recent dividend announcements for tickers."""
    try:
        if not tickers:
            return []
        
        tickers_str = "', '".join(tickers)
        query_str = f"""
            SELECT TOP 10 ticker, amount, ex_date, payment_date, frequency
            FROM dbo.vDividendsEnhanced
            WHERE ticker IN ('{tickers_str}')
              AND declaration_date >= DATEADD(day, -7, GETDATE())
            ORDER BY declaration_date DESC;
        """
        
        with engine.connect() as conn:
            result = conn.exec_driver_sql(query_str)
            rows = result.fetchall()
        
        news = []
        for row in rows:
            ticker, amount, ex_date, payment_date, frequency = row
            news.append({
                "ticker": ticker,
                "amount": float(amount) if amount else None,
                "ex_date": ex_date.isoformat() if ex_date else None,
                "payment_date": payment_date.isoformat() if payment_date else None,
                "frequency": frequency
            })
        
        return news
        
    except Exception as e:
        logger.error(f"Error getting dividend news: {e}")
        return []


def _get_upcoming_dividends(tickers: List[str]) -> List[dict]:
    """Get upcoming ex-dividend dates (next 7 days)."""
    try:
        if not tickers:
            return []
        
        tickers_str = "', '".join(tickers)
        query_str = f"""
            SELECT ticker, amount, ex_date, payment_date
            FROM dbo.vDividendsEnhanced
            WHERE ticker IN ('{tickers_str}')
              AND ex_date BETWEEN GETDATE() AND DATEADD(day, 7, GETDATE())
            ORDER BY ex_date;
        """
        
        with engine.connect() as conn:
            result = conn.exec_driver_sql(query_str)
            rows = result.fetchall()
        
        upcoming = []
        for row in rows:
            ticker, amount, ex_date, payment_date = row
            upcoming.append({
                "ticker": ticker,
                "amount": float(amount) if amount else None,
                "ex_date": ex_date.isoformat() if ex_date else None,
                "payment_date": payment_date.isoformat() if payment_date else None
            })
        
        return upcoming
        
    except Exception as e:
        logger.error(f"Error getting upcoming dividends: {e}")
        return []


def _generate_digest_with_gpt(
    session_id: str,
    portfolio_data: dict,
    price_changes: List[dict],
    dividend_news: List[dict],
    upcoming_dividends: List[dict]
) -> str:
    """
    Use GPT-4o to generate a personalized portfolio digest.
    
    Args:
        session_id: User session ID
        portfolio_data: Portfolio summary data
        price_changes: Recent price changes
        dividend_news: Recent dividend announcements
        upcoming_dividends: Upcoming ex-dividend dates
        
    Returns:
        Markdown-formatted digest content
    """
    try:
        system_prompt = """You are a financial advisor generating a personalized daily portfolio digest.

Create a clear, concise, and actionable summary using markdown formatting.

Structure:
1. **Price Changes** - Highlight significant moves (>3%)
2. **Dividend News** - Recent announcements
3. **Upcoming Income** - Ex-dividend dates in next 7 days
4. **Recommendations** - Brief actionable insights

Use emojis sparingly (📊 ↑ ↓ ✅) and keep it professional.
Be specific with numbers and dates.
Focus on what matters most to the investor."""

        data_summary = f"""
Portfolio Overview:
- Total Holdings: {len(portfolio_data['holdings'])} stocks
- Total Value: ${portfolio_data['total_value']:,.2f}
- Portfolio Yield: {portfolio_data['portfolio_yield']:.2f}%
- Annual Dividend Income: ${portfolio_data['total_annual_dividend']:,.2f}

Recent Price Changes (24h):
{json.dumps(price_changes[:10], indent=2)}

Recent Dividend Announcements (7 days):
{json.dumps(dividend_news, indent=2)}

Upcoming Ex-Dividend Dates (Next 7 days):
{json.dumps(upcoming_dividends, indent=2)}
"""

        response = oai_client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate a daily portfolio digest based on this data:\n\n{data_summary}"}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        digest_content = response.choices[0].message.content.strip()
        
        logger.info(f"Generated digest with GPT-4o for session {session_id}")
        return digest_content
        
    except Exception as e:
        logger.error(f"Error generating digest with GPT: {e}")
        
        fallback = f"""## 📊 Your Daily Portfolio Update - {datetime.now().strftime("%b %d, %Y")}

### Portfolio Summary
- **Total Value:** ${portfolio_data['total_value']:,.2f}
- **Holdings:** {len(portfolio_data['holdings'])} stocks
- **Portfolio Yield:** {portfolio_data['portfolio_yield']:.2f}%

### Price Changes (Last 24h)
"""
        for pc in price_changes[:5]:
            if pc.get("change_pct"):
                direction = "↑" if pc["change_pct"] > 0 else "↓"
                fallback += f"- **{pc['ticker']}** {direction} {abs(pc['change_pct']):.2f}%\n"
        
        if dividend_news:
            fallback += "\n### Dividend News\n"
            for dn in dividend_news[:3]:
                fallback += f"- **{dn['ticker']}** announced ${dn['amount']:.2f}/share\n"
        
        if upcoming_dividends:
            fallback += "\n### Upcoming Income\n"
            for ud in upcoming_dividends[:3]:
                fallback += f"- **{ud['ticker']}** ex-date: {ud['ex_date']}\n"
        
        return fallback


def generate_portfolio_alert(
    session_id: str,
    alert_type: str,
    ticker: str,
    details: dict
) -> dict:
    """
    Generate specific portfolio alert (e.g., stock moved >5%).
    
    Args:
        session_id: User session ID
        alert_type: 'significant_change', 'dividend_announcement', 'ex_date_reminder'
        ticker: Stock ticker symbol
        details: Alert-specific details
        
    Returns:
        Insight dict
    """
    try:
        insight_id = str(uuid.uuid4())
        
        if alert_type == "significant_change":
            title = f"{ticker} Price Alert: {details.get('change_pct', 0):.1f}% move"
            content = f"""## 🚨 Significant Price Change

**{ticker}** moved **{details.get('change_pct', 0):+.2f}%** today.

- Current Price: ${details.get('current_price', 0):.2f}
- Change: ${details.get('price_change', 0):+.2f}

This represents a significant move that may warrant your attention."""
            priority = 8
            
        elif alert_type == "dividend_announcement":
            title = f"{ticker} Dividend Announcement"
            content = f"""## 💰 Dividend Announcement

**{ticker}** announced a dividend:

- Amount: ${details.get('amount', 0):.2f}/share
- Ex-Date: {details.get('ex_date', 'TBD')}
- Payment Date: {details.get('payment_date', 'TBD')}"""
            priority = 6
            
        elif alert_type == "ex_date_reminder":
            title = f"{ticker} Ex-Dividend Date Tomorrow"
            content = f"""## 📅 Ex-Dividend Reminder

**{ticker}** goes ex-dividend tomorrow.

- Dividend: ${details.get('amount', 0):.2f}/share
- Ex-Date: {details.get('ex_date', 'Tomorrow')}
- To receive this dividend, you must hold shares today."""
            priority = 7
            
        else:
            logger.warning(f"Unknown alert type: {alert_type}")
            return {"success": False, "error": "Unknown alert type"}
        
        query = text("""
            INSERT INTO dbo.proactive_insights
            (insight_id, session_id, insight_type, title, content, priority, created_at,
             read_status, metadata)
            VALUES
            (:insight_id, :session_id, :insight_type, :title, :content, :priority, GETDATE(),
             0, :metadata);
        """)
        
        metadata = {
            "ticker": ticker,
            "alert_type": alert_type,
            "details": details
        }
        
        with engine.begin() as conn:
            conn.execute(query, {
                "insight_id": insight_id,
                "session_id": session_id,
                "insight_type": "portfolio_update",
                "title": title,
                "content": content,
                "priority": priority,
                "metadata": json.dumps(metadata)
            })
        
        logger.info(f"Created portfolio alert {insight_id} ({alert_type}) for {ticker}")
        
        return {
            "success": True,
            "insight_id": insight_id,
            "title": title,
            "content": content,
            "priority": priority
        }
        
    except Exception as e:
        logger.error(f"Failed to generate portfolio alert: {e}")
        return {"success": False, "error": str(e)}


def get_unread_insights(session_id: str, limit: int = 10) -> List[dict]:
    """
    Retrieve unread insights for a session.
    
    Args:
        session_id: User session ID
        limit: Maximum number of insights to return
        
    Returns:
        List of insight dicts
    """
    try:
        query = text("""
            SELECT TOP (:limit)
                insight_id, insight_type, title, content, priority, 
                created_at, metadata
            FROM dbo.proactive_insights
            WHERE session_id = :session_id AND read_status = 0
            ORDER BY priority DESC, created_at DESC;
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {
                "session_id": session_id,
                "limit": limit
            })
            rows = result.fetchall()
        
        insights = []
        for row in rows:
            try:
                metadata = json.loads(row[6]) if row[6] else {}
            except:
                metadata = {}
            
            insights.append({
                "insight_id": row[0],
                "insight_type": row[1],
                "title": row[2],
                "content": row[3],
                "priority": row[4],
                "created_at": row[5].isoformat() if row[5] else None,
                "metadata": metadata
            })
        
        logger.info(f"Retrieved {len(insights)} unread insights for session {session_id}")
        return insights
        
    except Exception as e:
        logger.error(f"Failed to get unread insights: {e}")
        return []


def get_all_insights(session_id: str, limit: int = 50) -> List[dict]:
    """
    Retrieve all insights for a session (read and unread).
    
    Args:
        session_id: User session ID
        limit: Maximum number of insights to return
        
    Returns:
        List of insight dicts
    """
    try:
        query = text("""
            SELECT TOP (:limit)
                insight_id, insight_type, title, content, priority, 
                created_at, read_status, metadata
            FROM dbo.proactive_insights
            WHERE session_id = :session_id
            ORDER BY created_at DESC;
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {
                "session_id": session_id,
                "limit": limit
            })
            rows = result.fetchall()
        
        insights = []
        for row in rows:
            try:
                metadata = json.loads(row[7]) if row[7] else {}
            except:
                metadata = {}
            
            insights.append({
                "insight_id": row[0],
                "insight_type": row[1],
                "title": row[2],
                "content": row[3],
                "priority": row[4],
                "created_at": row[5].isoformat() if row[5] else None,
                "read_status": bool(row[6]),
                "metadata": metadata
            })
        
        logger.info(f"Retrieved {len(insights)} insights for session {session_id}")
        return insights
        
    except Exception as e:
        logger.error(f"Failed to get insights: {e}")
        return []


def mark_insight_read(insight_id: str) -> bool:
    """
    Mark an insight as read.
    
    Args:
        insight_id: Insight ID to mark as read
        
    Returns:
        True if updated successfully, False otherwise
    """
    try:
        query = text("""
            UPDATE dbo.proactive_insights
            SET read_status = 1
            WHERE insight_id = :insight_id;
        """)
        
        with engine.begin() as conn:
            conn.execute(query, {"insight_id": insight_id})
        
        logger.info(f"Marked insight {insight_id} as read")
        return True
        
    except Exception as e:
        logger.error(f"Failed to mark insight as read: {e}")
        return False
