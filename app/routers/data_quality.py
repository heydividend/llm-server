"""
Data Quality API Endpoint for Harvey
Provides database quality analysis and reports.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy import text
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Any
import logging

from app.core.database import engine

router = APIRouter(prefix="/data-quality", tags=["data-quality"])
logger = logging.getLogger(__name__)


@router.get("/report", response_class=PlainTextResponse)
async def get_data_quality_report():
    """
    Generate comprehensive data quality report for dividend database.
    Returns detailed analysis of problematic tickers and data issues.
    """
    try:
        issues = {
            'unrealistic_amounts': [],
            'negative_amounts': [],
            'zero_amounts': [],
            'missing_dates': [],
            'low_confidence': [],
            'duplicates': []
        }
        stats = {}
        
        with engine.connect() as conn:
            # Analyze dividend amounts
            query = text("""
                SELECT 
                    Ticker,
                    Dividend_Amount,
                    Ex_Dividend_Date,
                    Payment_Date,
                    Data_Source,
                    Confidence_Score
                FROM vDividendsEnhanced
                WHERE Dividend_Amount IS NOT NULL
                ORDER BY Dividend_Amount DESC
            """)
            
            result = conn.execute(query)
            rows = result.fetchall()
            
            for row in rows:
                amount = float(row.Dividend_Amount)
                ticker = row.Ticker
                
                # Unrealistic amounts (> $1,000/share)
                if amount > 1000:
                    issues['unrealistic_amounts'].append({
                        'ticker': ticker,
                        'amount': amount,
                        'ex_date': str(row.Ex_Dividend_Date) if row.Ex_Dividend_Date else None,
                        'pay_date': str(row.Payment_Date) if row.Payment_Date else None,
                        'source': row.Data_Source,
                        'confidence': float(row.Confidence_Score) if row.Confidence_Score else 0
                    })
                
                # Negative amounts
                elif amount < 0:
                    issues['negative_amounts'].append({
                        'ticker': ticker,
                        'amount': amount,
                        'ex_date': str(row.Ex_Dividend_Date) if row.Ex_Dividend_Date else None,
                        'source': row.Data_Source
                    })
                
                # Zero amounts
                elif amount == 0:
                    issues['zero_amounts'].append({
                        'ticker': ticker,
                        'ex_date': str(row.Ex_Dividend_Date) if row.Ex_Dividend_Date else None,
                        'source': row.Data_Source
                    })
            
            # Check for missing dates
            query = text("""
                SELECT 
                    Ticker,
                    Dividend_Amount,
                    Ex_Dividend_Date,
                    Payment_Date,
                    Data_Source
                FROM vDividendsEnhanced
                WHERE Dividend_Amount > 0
                    AND (Ex_Dividend_Date IS NULL OR Payment_Date IS NULL)
            """)
            
            result = conn.execute(query)
            for row in result.fetchall():
                issues['missing_dates'].append({
                    'ticker': row.Ticker,
                    'amount': float(row.Dividend_Amount),
                    'missing': 'ex_date' if not row.Ex_Dividend_Date else 'payment_date',
                    'source': row.Data_Source
                })
            
            # Low confidence scores
            query = text("""
                SELECT 
                    Ticker,
                    Dividend_Amount,
                    Ex_Dividend_Date,
                    Confidence_Score,
                    Data_Source
                FROM vDividendsEnhanced
                WHERE Confidence_Score IS NOT NULL 
                    AND Confidence_Score < 0.5
                    AND Dividend_Amount > 0
            """)
            
            result = conn.execute(query)
            for row in result.fetchall():
                issues['low_confidence'].append({
                    'ticker': row.Ticker,
                    'amount': float(row.Dividend_Amount),
                    'ex_date': str(row.Ex_Dividend_Date) if row.Ex_Dividend_Date else None,
                    'confidence': float(row.Confidence_Score),
                    'source': row.Data_Source
                })
            
            # Check for duplicates
            query = text("""
                SELECT 
                    Ticker,
                    Ex_Dividend_Date,
                    COUNT(*) AS duplicate_count,
                    STRING_AGG(CAST(Dividend_Amount AS VARCHAR), ', ') AS amounts
                FROM vDividendsEnhanced
                WHERE Ex_Dividend_Date IS NOT NULL
                GROUP BY Ticker, Ex_Dividend_Date
                HAVING COUNT(*) > 1
                ORDER BY COUNT(*) DESC
            """)
            
            result = conn.execute(query)
            for row in result.fetchall():
                issues['duplicates'].append({
                    'ticker': row.Ticker,
                    'ex_date': str(row.Ex_Dividend_Date),
                    'count': row.duplicate_count,
                    'amounts': row.amounts
                })
            
            # Generate statistics
            query = text("""
                SELECT 
                    COUNT(*) AS total_records,
                    COUNT(DISTINCT Ticker) AS unique_tickers,
                    AVG(Dividend_Amount) AS avg_dividend,
                    MIN(Dividend_Amount) AS min_dividend,
                    MAX(Dividend_Amount) AS max_dividend,
                    AVG(Confidence_Score) AS avg_confidence
                FROM vDividendsEnhanced
                WHERE Dividend_Amount > 0
            """)
            
            result = conn.execute(query)
            row = result.fetchone()
            
            stats = {
                'total_records': row.total_records,
                'unique_tickers': row.unique_tickers,
                'avg_dividend': float(row.avg_dividend) if row.avg_dividend else 0,
                'min_dividend': float(row.min_dividend) if row.min_dividend else 0,
                'max_dividend': float(row.max_dividend) if row.max_dividend else 0,
                'avg_confidence': float(row.avg_confidence) if row.avg_confidence else 0
            }
        
        # Format report
        report = []
        report.append("=" * 80)
        report.append("HARVEY DATA QUALITY REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        report.append("SUMMARY STATISTICS")
        report.append("=" * 80)
        report.append(f"Total Dividend Records: {stats['total_records']:,}")
        report.append(f"Unique Tickers: {stats['unique_tickers']:,}")
        report.append(f"Average Dividend: ${stats['avg_dividend']:.2f}")
        report.append(f"Min Dividend: ${stats['min_dividend']:.2f}")
        report.append(f"Max Dividend: ${stats['max_dividend']:,.2f}")
        report.append(f"Average Confidence Score: {stats['avg_confidence']:.2%}\n")
        
        report.append("DATA QUALITY ISSUES")
        report.append("=" * 80)
        
        # Unrealistic amounts
        if issues['unrealistic_amounts']:
            report.append(f"\n⚠️  UNREALISTIC AMOUNTS (>$1,000) - {len(issues['unrealistic_amounts'])} issues")
            report.append("-" * 80)
            for issue in sorted(issues['unrealistic_amounts'], key=lambda x: x['amount'], reverse=True)[:50]:
                report.append(f"  {issue['ticker']:12} ${issue['amount']:>15,.2f}  Ex: {issue['ex_date'] or 'N/A':12}  Pay: {issue['pay_date'] or 'N/A':12}  Source: {issue['source']}")
        
        # Negative amounts
        if issues['negative_amounts']:
            report.append(f"\n⚠️  NEGATIVE AMOUNTS - {len(issues['negative_amounts'])} issues")
            report.append("-" * 80)
            for issue in issues['negative_amounts'][:50]:
                report.append(f"  {issue['ticker']:12} ${issue['amount']:>15,.2f}  Ex: {issue['ex_date'] or 'N/A'}  Source: {issue['source']}")
        
        # Zero amounts
        if issues['zero_amounts']:
            report.append(f"\n⚠️  ZERO AMOUNTS - {len(issues['zero_amounts'])} issues (showing first 20)")
            report.append("-" * 80)
            for issue in issues['zero_amounts'][:20]:
                report.append(f"  {issue['ticker']:12} Ex: {issue['ex_date'] or 'N/A'}  Source: {issue['source']}")
        
        # Missing dates
        if issues['missing_dates']:
            report.append(f"\n⚠️  MISSING DATES - {len(issues['missing_dates'])} issues (showing first 20)")
            report.append("-" * 80)
            for issue in issues['missing_dates'][:20]:
                report.append(f"  {issue['ticker']:12} ${issue['amount']:>10,.2f}  Missing: {issue['missing']}  Source: {issue['source']}")
        
        # Low confidence
        if issues['low_confidence']:
            report.append(f"\n⚠️  LOW CONFIDENCE (<0.5) - {len(issues['low_confidence'])} issues (showing first 20)")
            report.append("-" * 80)
            for issue in sorted(issues['low_confidence'], key=lambda x: x['confidence'])[:20]:
                report.append(f"  {issue['ticker']:12} ${issue['amount']:>10,.2f}  Confidence: {issue['confidence']:.2%}  Source: {issue['source']}")
        
        # Duplicates
        if issues['duplicates']:
            report.append(f"\n⚠️  DUPLICATE ENTRIES - {len(issues['duplicates'])} issues (showing first 20)")
            report.append("-" * 80)
            for issue in sorted(issues['duplicates'], key=lambda x: x['count'], reverse=True)[:20]:
                report.append(f"  {issue['ticker']:12} Ex: {issue['ex_date']}  Count: {issue['count']}  Amounts: {issue['amounts']}")
        
        report.append("\n" + "=" * 80)
        report.append("RECOMMENDATIONS")
        report.append("=" * 80)
        
        if issues['unrealistic_amounts']:
            report.append("✓ Add filter: WHERE Dividend_Amount <= 1000")
        if issues['negative_amounts'] or issues['zero_amounts']:
            report.append("✓ Add filter: WHERE Dividend_Amount > 0")
        if issues['low_confidence']:
            report.append("✓ Add filter: WHERE Confidence_Score >= 0.7")
        if issues['duplicates']:
            report.append("✓ Deduplicate using ROW_NUMBER() OVER (PARTITION BY Ticker, Ex_Dividend_Date)")
        if issues['missing_dates']:
            report.append("✓ Add validation: WHERE Ex_Dividend_Date IS NOT NULL AND Payment_Date IS NOT NULL")
        
        report.append("\n" + "=" * 80)
        
        return "\n".join(report)
        
    except Exception as e:
        logger.error(f"Data quality report failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/issues/json")
async def get_data_quality_issues_json():
    """
    Get data quality issues in JSON format for programmatic access.
    """
    try:
        issues = {
            'unrealistic_amounts': [],
            'negative_amounts': [],
            'zero_amounts': [],
            'missing_dates': [],
            'low_confidence': [],
            'duplicates': []
        }
        
        with engine.connect() as conn:
            # Unrealistic amounts
            query = text("""
                SELECT TOP 100
                    Ticker,
                    Dividend_Amount,
                    Ex_Dividend_Date,
                    Payment_Date,
                    Data_Source,
                    Confidence_Score
                FROM vDividendsEnhanced
                WHERE Dividend_Amount > 1000
                ORDER BY Dividend_Amount DESC
            """)
            
            result = conn.execute(query)
            for row in result.fetchall():
                issues['unrealistic_amounts'].append({
                    'ticker': row.Ticker,
                    'amount': float(row.Dividend_Amount),
                    'ex_date': str(row.Ex_Dividend_Date) if row.Ex_Dividend_Date else None,
                    'pay_date': str(row.Payment_Date) if row.Payment_Date else None,
                    'source': row.Data_Source,
                    'confidence': float(row.Confidence_Score) if row.Confidence_Score else 0
                })
        
        return JSONResponse(content={
            'timestamp': datetime.now().isoformat(),
            'issues': issues,
            'total_issues': sum(len(v) for v in issues.values())
        })
        
    except Exception as e:
        logger.error(f"Data quality JSON failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
