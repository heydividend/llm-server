"""
Natural Language Alerts Service

Parses natural language alert requests using GPT-4o function calling
and monitors market conditions to trigger alerts.
"""

import os
import json
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from sqlalchemy import text

from app.core.database import engine
from app.core.llm_providers import oai_client, CHAT_MODEL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("alert_service")

ALERT_PARSING_FUNCTIONS = [
    {
        "name": "create_alert_rule",
        "description": "Create a structured alert rule from natural language",
        "parameters": {
            "type": "object",
            "properties": {
                "condition_type": {
                    "type": "string",
                    "enum": ["price_target", "dividend_cut", "yield_change", "price_drop", "price_increase"],
                    "description": "Type of alert condition"
                },
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol (optional, null for portfolio-wide alerts)"
                },
                "operator": {
                    "type": "string",
                    "enum": ["above", "below", "equals", "increases_by", "decreases_by"],
                    "description": "Comparison operator"
                },
                "value": {
                    "type": "number",
                    "description": "Threshold value (price, yield percentage, etc)"
                },
                "threshold_type": {
                    "type": "string",
                    "enum": ["absolute", "percentage"],
                    "description": "Whether value is absolute ($200) or percentage (5%)"
                },
                "rule_name": {
                    "type": "string",
                    "description": "Human-readable name for the alert"
                }
            },
            "required": ["condition_type", "operator", "rule_name"]
        }
    }
]


def create_alert_from_natural_language(
    session_id: str,
    natural_language: str
) -> dict:
    """
    Use OpenAI to parse natural language into structured alert rule.
    
    Examples:
    - "Tell me when AAPL goes above $200"
    - "Alert me if any of my stocks cut their dividend"
    - "Notify me when VYM yield exceeds 4%"
    
    Uses GPT-4o function calling to extract:
    - condition_type: 'price_target', 'dividend_cut', 'yield_change', 'price_drop'
    - ticker: Optional ticker symbol
    - trigger_condition: JSON with operator and value
    
    Args:
        session_id: User session ID
        natural_language: Natural language alert request
        
    Returns:
        {
            'alert_id': str,
            'rule_name': str,
            'condition_type': str,
            'ticker': str,
            'trigger_condition': dict,
            'is_active': bool
        }
    """
    try:
        logger.info(f"Parsing alert request: '{natural_language}' for session {session_id}")
        
        system_prompt = """You are an alert parsing expert. Parse natural language alert requests into structured rules.

Examples:
- "Tell me when AAPL goes above $200" → price_target, AAPL, above, 200, absolute
- "Alert if VYM yield exceeds 4%" → yield_change, VYM, above, 4, percentage
- "Notify when any stock drops 10%" → price_drop, null, decreases_by, 10, percentage
- "Tell me if dividend is cut" → dividend_cut, null, decreases_by, 0, percentage

Extract ticker symbols when mentioned. For portfolio-wide alerts, set ticker to null."""

        response = oai_client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": natural_language}
            ],
            functions=ALERT_PARSING_FUNCTIONS,
            function_call={"name": "create_alert_rule"},
            temperature=0.1
        )
        
        message = response.choices[0].message
        
        if not message.function_call:
            logger.warning("GPT-4o did not return function call, using fallback")
            return {
                "success": False,
                "error": "Could not parse alert request. Please be more specific."
            }
        
        parsed = json.loads(message.function_call.arguments)
        logger.info(f"Parsed alert: {parsed}")
        
        alert_id = str(uuid.uuid4())
        
        trigger_condition = {
            "operator": parsed.get("operator"),
            "value": parsed.get("value"),
            "threshold_type": parsed.get("threshold_type", "absolute")
        }
        
        ticker = (parsed.get("ticker") or "").strip().upper() or None
        rule_name = parsed.get("rule_name") or natural_language[:100]
        
        query = text("""
            INSERT INTO dbo.alert_rules 
            (alert_id, session_id, rule_name, natural_language, condition_type, 
             ticker, trigger_condition, is_active, notification_method, created_at)
            VALUES 
            (:alert_id, :session_id, :rule_name, :natural_language, :condition_type,
             :ticker, :trigger_condition, 1, 'in_app', GETDATE());
        """)
        
        with engine.begin() as conn:
            conn.execute(query, {
                "alert_id": alert_id,
                "session_id": session_id,
                "rule_name": rule_name,
                "natural_language": natural_language,
                "condition_type": parsed.get("condition_type"),
                "ticker": ticker,
                "trigger_condition": json.dumps(trigger_condition)
            })
        
        logger.info(f"Created alert {alert_id}: {rule_name}")
        
        return {
            "success": True,
            "alert_id": alert_id,
            "rule_name": rule_name,
            "condition_type": parsed.get("condition_type"),
            "ticker": ticker,
            "trigger_condition": trigger_condition,
            "is_active": True
        }
        
    except Exception as e:
        logger.error(f"Failed to create alert: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


def check_alert_conditions(alert_id: Optional[str] = None) -> List[dict]:
    """
    Check if alert conditions are met. If alert_id is None, check all active alerts.
    
    For each active alert:
    1. Query current market data (vQuotesEnhanced, vDividendsEnhanced)
    2. Evaluate trigger condition
    3. If triggered, create alert_event and mark for notification
    
    Args:
        alert_id: Specific alert to check, or None for all active alerts
        
    Returns:
        List of triggered alerts
    """
    try:
        if alert_id:
            query = text("""
                SELECT alert_id, session_id, rule_name, condition_type, ticker, trigger_condition
                FROM dbo.alert_rules
                WHERE alert_id = :alert_id AND is_active = 1;
            """)
            with engine.connect() as conn:
                result = conn.execute(query, {"alert_id": alert_id})
                alerts = result.fetchall()
        else:
            query = text("""
                SELECT alert_id, session_id, rule_name, condition_type, ticker, trigger_condition
                FROM dbo.alert_rules
                WHERE is_active = 1;
            """)
            with engine.connect() as conn:
                result = conn.execute(query)
                alerts = result.fetchall()
        
        triggered_alerts = []
        
        for row in alerts:
            alert_id_val, session_id, rule_name, condition_type, ticker, trigger_condition_json = row
            
            try:
                trigger_condition = json.loads(trigger_condition_json)
            except:
                logger.warning(f"Invalid trigger_condition JSON for alert {alert_id_val}")
                continue
            
            triggered = _evaluate_alert_condition(
                alert_id_val,
                condition_type,
                ticker,
                trigger_condition
            )
            
            if triggered:
                event_id = _create_alert_event(
                    alert_id_val,
                    session_id,
                    rule_name,
                    ticker,
                    triggered
                )
                
                triggered_alerts.append({
                    "alert_id": alert_id_val,
                    "event_id": event_id,
                    "rule_name": rule_name,
                    "ticker": ticker,
                    "details": triggered
                })
                
                logger.info(f"Alert triggered: {rule_name} (event {event_id})")
        
        query_update = text("""
            UPDATE dbo.alert_rules
            SET last_checked = GETDATE()
            WHERE alert_id IN :alert_ids;
        """)
        
        if alerts:
            alert_ids_to_update = tuple(row[0] for row in alerts)
            if len(alert_ids_to_update) == 1:
                alert_ids_to_update = f"('{alert_ids_to_update[0]}')"
            
            with engine.begin() as conn:
                conn.exec_driver_sql(
                    f"UPDATE dbo.alert_rules SET last_checked = GETDATE() WHERE alert_id IN {alert_ids_to_update}"
                )
        
        return triggered_alerts
        
    except Exception as e:
        logger.error(f"Failed to check alert conditions: {e}", exc_info=True)
        return []


def _evaluate_alert_condition(
    alert_id: str,
    condition_type: str,
    ticker: Optional[str],
    trigger_condition: dict
) -> Optional[dict]:
    """
    Evaluate if an alert condition is met.
    
    Args:
        alert_id: Alert ID
        condition_type: Type of condition (price_target, dividend_cut, etc)
        ticker: Ticker symbol or None for portfolio-wide
        trigger_condition: Trigger parameters (operator, value, threshold_type)
        
    Returns:
        Dict with trigger details if condition met, None otherwise
    """
    try:
        operator = trigger_condition.get("operator")
        value = trigger_condition.get("value")
        threshold_type = trigger_condition.get("threshold_type", "absolute")
        
        if condition_type in ["price_target", "price_drop", "price_increase"]:
            return _check_price_condition(ticker, operator, value, threshold_type)
        
        elif condition_type == "yield_change":
            return _check_yield_condition(ticker, operator, value)
        
        elif condition_type == "dividend_cut":
            return _check_dividend_cut(ticker)
        
        else:
            logger.warning(f"Unknown condition_type: {condition_type}")
            return None
            
    except Exception as e:
        logger.error(f"Error evaluating alert condition: {e}")
        return None


def _check_price_condition(
    ticker: Optional[str],
    operator: str,
    value: float,
    threshold_type: str
) -> Optional[dict]:
    """Check price-based alert conditions."""
    try:
        if not ticker:
            logger.warning("Price alerts require a ticker symbol")
            return None
        
        query = text("""
            SELECT TOP 1 ticker, last_price, price_change_pct
            FROM dbo.vQuotesEnhanced
            WHERE ticker = :ticker
            ORDER BY quote_date DESC;
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {"ticker": ticker})
            row = result.fetchone()
        
        if not row:
            logger.warning(f"No price data found for {ticker}")
            return None
        
        ticker_val, last_price, price_change_pct = row
        
        if threshold_type == "absolute":
            if operator == "above" and last_price > value:
                return {
                    "condition_met": f"{ticker} price ${last_price:.2f} is above ${value:.2f}",
                    "current_value": last_price
                }
            elif operator == "below" and last_price < value:
                return {
                    "condition_met": f"{ticker} price ${last_price:.2f} is below ${value:.2f}",
                    "current_value": last_price
                }
        
        elif threshold_type == "percentage":
            if operator == "decreases_by" and price_change_pct and price_change_pct <= -value:
                return {
                    "condition_met": f"{ticker} dropped {abs(price_change_pct):.2f}% (threshold: {value}%)",
                    "current_value": price_change_pct
                }
            elif operator == "increases_by" and price_change_pct and price_change_pct >= value:
                return {
                    "condition_met": f"{ticker} increased {price_change_pct:.2f}% (threshold: {value}%)",
                    "current_value": price_change_pct
                }
        
        return None
        
    except Exception as e:
        logger.error(f"Error checking price condition: {e}")
        return None


def _check_yield_condition(
    ticker: Optional[str],
    operator: str,
    value: float
) -> Optional[dict]:
    """Check dividend yield alert conditions."""
    try:
        if not ticker:
            logger.warning("Yield alerts require a ticker symbol")
            return None
        
        query = text("""
            SELECT TOP 1 ticker, dividend_yield
            FROM dbo.vQuotesEnhanced
            WHERE ticker = :ticker AND dividend_yield IS NOT NULL
            ORDER BY quote_date DESC;
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {"ticker": ticker})
            row = result.fetchone()
        
        if not row:
            logger.warning(f"No yield data found for {ticker}")
            return None
        
        ticker_val, dividend_yield = row
        
        if operator == "above" and dividend_yield > value:
            return {
                "condition_met": f"{ticker} yield {dividend_yield:.2f}% exceeds {value}%",
                "current_value": dividend_yield
            }
        elif operator == "below" and dividend_yield < value:
            return {
                "condition_met": f"{ticker} yield {dividend_yield:.2f}% is below {value}%",
                "current_value": dividend_yield
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error checking yield condition: {e}")
        return None


def _check_dividend_cut(ticker: Optional[str]) -> Optional[dict]:
    """Check for dividend cuts in the last 7 days."""
    try:
        if ticker:
            query = text("""
                SELECT TOP 1 ticker, amount, previous_amount, change_pct
                FROM dbo.vDividendSignals
                WHERE ticker = :ticker 
                  AND signal_type = 'dividend_cut'
                  AND signal_date >= DATEADD(day, -7, GETDATE())
                ORDER BY signal_date DESC;
            """)
            
            with engine.connect() as conn:
                result = conn.execute(query, {"ticker": ticker})
                row = result.fetchone()
        else:
            query = text("""
                SELECT TOP 1 ticker, amount, previous_amount, change_pct
                FROM dbo.vDividendSignals
                WHERE signal_type = 'dividend_cut'
                  AND signal_date >= DATEADD(day, -7, GETDATE())
                ORDER BY signal_date DESC;
            """)
            
            with engine.connect() as conn:
                result = conn.execute(query)
                row = result.fetchone()
        
        if row:
            ticker_val, amount, previous_amount, change_pct = row
            return {
                "condition_met": f"{ticker_val} cut dividend from ${previous_amount:.2f} to ${amount:.2f} ({change_pct:.1f}%)",
                "current_value": amount
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error checking dividend cut: {e}")
        return None


def _create_alert_event(
    alert_id: str,
    session_id: str,
    rule_name: str,
    ticker: Optional[str],
    trigger_details: dict
) -> str:
    """
    Create an alert event when a condition is triggered.
    
    Args:
        alert_id: Alert rule ID
        session_id: User session ID
        rule_name: Alert rule name
        ticker: Ticker symbol (if any)
        trigger_details: Details about what triggered the alert
        
    Returns:
        event_id (UUID string)
    """
    try:
        event_id = str(uuid.uuid4())
        
        query = text("""
            INSERT INTO dbo.alert_events
            (event_id, alert_id, triggered_at, condition_met, ticker, current_value, 
             notification_sent, read_status)
            VALUES
            (:event_id, :alert_id, GETDATE(), :condition_met, :ticker, :current_value,
             0, 0);
        """)
        
        with engine.begin() as conn:
            conn.execute(query, {
                "event_id": event_id,
                "alert_id": alert_id,
                "condition_met": trigger_details.get("condition_met"),
                "ticker": ticker,
                "current_value": trigger_details.get("current_value")
            })
        
        logger.info(f"Created alert event {event_id} for alert {alert_id}")
        return event_id
        
    except Exception as e:
        logger.error(f"Failed to create alert event: {e}")
        raise


def get_user_alerts(session_id: str, active_only: bool = True) -> List[dict]:
    """
    Retrieve user's alert rules.
    
    Args:
        session_id: User session ID
        active_only: If True, only return active alerts
        
    Returns:
        List of alert rule dicts
    """
    try:
        if active_only:
            query = text("""
                SELECT alert_id, rule_name, natural_language, condition_type, ticker,
                       trigger_condition, is_active, created_at, last_checked
                FROM dbo.alert_rules
                WHERE session_id = :session_id AND is_active = 1
                ORDER BY created_at DESC;
            """)
        else:
            query = text("""
                SELECT alert_id, rule_name, natural_language, condition_type, ticker,
                       trigger_condition, is_active, created_at, last_checked
                FROM dbo.alert_rules
                WHERE session_id = :session_id
                ORDER BY created_at DESC;
            """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {"session_id": session_id})
            rows = result.fetchall()
        
        alerts = []
        for row in rows:
            try:
                trigger_condition = json.loads(row[5]) if row[5] else {}
            except:
                trigger_condition = {}
            
            alerts.append({
                "alert_id": row[0],
                "rule_name": row[1],
                "natural_language": row[2],
                "condition_type": row[3],
                "ticker": row[4],
                "trigger_condition": trigger_condition,
                "is_active": bool(row[6]),
                "created_at": row[7].isoformat() if row[7] else None,
                "last_checked": row[8].isoformat() if row[8] else None
            })
        
        logger.info(f"Retrieved {len(alerts)} alerts for session {session_id}")
        return alerts
        
    except Exception as e:
        logger.error(f"Failed to get user alerts: {e}")
        return []


def get_alert_events(session_id: str, unread_only: bool = True, limit: int = 50) -> List[dict]:
    """
    Get alert events (triggered alerts) for a session.
    
    Args:
        session_id: User session ID
        unread_only: If True, only return unread events
        limit: Maximum number of events to return
        
    Returns:
        List of alert event dicts
    """
    try:
        if unread_only:
            query = text("""
                SELECT TOP (:limit)
                    e.event_id, e.alert_id, e.triggered_at, e.condition_met, 
                    e.ticker, e.current_value, e.read_status,
                    r.rule_name
                FROM dbo.alert_events e
                JOIN dbo.alert_rules r ON e.alert_id = r.alert_id
                WHERE r.session_id = :session_id AND e.read_status = 0
                ORDER BY e.triggered_at DESC;
            """)
        else:
            query = text("""
                SELECT TOP (:limit)
                    e.event_id, e.alert_id, e.triggered_at, e.condition_met, 
                    e.ticker, e.current_value, e.read_status,
                    r.rule_name
                FROM dbo.alert_events e
                JOIN dbo.alert_rules r ON e.alert_id = r.alert_id
                WHERE r.session_id = :session_id
                ORDER BY e.triggered_at DESC;
            """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {
                "session_id": session_id,
                "limit": limit
            })
            rows = result.fetchall()
        
        events = []
        for row in rows:
            events.append({
                "event_id": row[0],
                "alert_id": row[1],
                "triggered_at": row[2].isoformat() if row[2] else None,
                "condition_met": row[3],
                "ticker": row[4],
                "current_value": float(row[5]) if row[5] else None,
                "read_status": bool(row[6]),
                "rule_name": row[7]
            })
        
        logger.info(f"Retrieved {len(events)} alert events for session {session_id}")
        return events
        
    except Exception as e:
        logger.error(f"Failed to get alert events: {e}")
        return []


def delete_alert(alert_id: str) -> bool:
    """
    Delete an alert rule.
    
    Args:
        alert_id: Alert ID to delete
        
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        query = text("""
            DELETE FROM dbo.alert_rules
            WHERE alert_id = :alert_id;
        """)
        
        with engine.begin() as conn:
            conn.execute(query, {"alert_id": alert_id})
        
        logger.info(f"Deleted alert {alert_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete alert: {e}")
        return False


def mark_alert_event_read(event_id: str) -> bool:
    """
    Mark an alert event as read.
    
    Args:
        event_id: Event ID to mark as read
        
    Returns:
        True if updated successfully, False otherwise
    """
    try:
        query = text("""
            UPDATE dbo.alert_events
            SET read_status = 1
            WHERE event_id = :event_id;
        """)
        
        with engine.begin() as conn:
            conn.execute(query, {"event_id": event_id})
        
        logger.info(f"Marked alert event {event_id} as read")
        return True
        
    except Exception as e:
        logger.error(f"Failed to mark alert event as read: {e}")
        return False
