"""
Data Quality Report Generator for Harvey Financial Database
Identifies problematic dividend data and generates comprehensive quality reports.
"""

import sys
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Any
from sqlalchemy import text
import pandas as pd

sys.path.insert(0, '/home/runner/workspace')
from app.core.database import engine


class DataQualityAnalyzer:
    """Analyzes dividend data quality and generates reports."""
    
    def __init__(self):
        self.issues = {
            'unrealistic_amounts': [],
            'negative_amounts': [],
            'zero_amounts': [],
            'missing_dates': [],
            'future_historical': [],
            'low_confidence': [],
            'duplicate_entries': [],
            'outliers': []
        }
        self.stats = {}
    
    def analyze(self):
        """Run all data quality checks."""
        print("=" * 80)
        print("HARVEY DATA QUALITY REPORT")
        print("=" * 80)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        with engine.connect() as conn:
            self._analyze_dividend_amounts(conn)
            self._analyze_dates(conn)
            self._analyze_confidence_scores(conn)
            self._analyze_duplicates(conn)
            self._generate_statistics(conn)
        
        self._print_report()
        self._export_csv()
    
    def _analyze_dividend_amounts(self, conn):
        """Check for unrealistic, negative, or zero dividend amounts."""
        print("📊 Analyzing dividend amounts...")
        
        query = text("""
            SELECT 
                Ticker,
                Dividend_Amount,
                AdjDividend_Amount,
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
                self.issues['unrealistic_amounts'].append({
                    'ticker': ticker,
                    'amount': amount,
                    'ex_date': row.Ex_Dividend_Date,
                    'source': row.Data_Source,
                    'confidence': float(row.Confidence_Score) if row.Confidence_Score else 0
                })
            
            # Negative amounts
            elif amount < 0:
                self.issues['negative_amounts'].append({
                    'ticker': ticker,
                    'amount': amount,
                    'ex_date': row.Ex_Dividend_Date,
                    'source': row.Data_Source
                })
            
            # Zero amounts
            elif amount == 0:
                self.issues['zero_amounts'].append({
                    'ticker': ticker,
                    'ex_date': row.Ex_Dividend_Date,
                    'source': row.Data_Source
                })
        
        print(f"  ✓ Found {len(self.issues['unrealistic_amounts'])} unrealistic amounts (>$1,000)")
        print(f"  ✓ Found {len(self.issues['negative_amounts'])} negative amounts")
        print(f"  ✓ Found {len(self.issues['zero_amounts'])} zero amounts")
    
    def _analyze_dates(self, conn):
        """Check for missing or problematic dates."""
        print("\n📅 Analyzing dates...")
        
        query = text("""
            SELECT 
                Ticker,
                Dividend_Amount,
                Declaration_Date,
                Ex_Dividend_Date,
                Payment_Date,
                Data_Source
            FROM vDividendsEnhanced
            WHERE Dividend_Amount > 0
        """)
        
        result = conn.execute(query)
        rows = result.fetchall()
        today = date.today()
        
        for row in rows:
            ticker = row.Ticker
            
            # Missing critical dates
            if not row.Ex_Dividend_Date or not row.Payment_Date:
                self.issues['missing_dates'].append({
                    'ticker': ticker,
                    'amount': float(row.Dividend_Amount),
                    'missing': 'ex_date' if not row.Ex_Dividend_Date else 'payment_date',
                    'source': row.Data_Source
                })
            
            # Future dates for old dividends (payment date > 2 years from now)
            if row.Payment_Date:
                days_diff = (row.Payment_Date - today).days
                if days_diff > 730:  # More than 2 years in future
                    self.issues['future_historical'].append({
                        'ticker': ticker,
                        'amount': float(row.Dividend_Amount),
                        'payment_date': row.Payment_Date,
                        'days_future': days_diff,
                        'source': row.Data_Source
                    })
        
        print(f"  ✓ Found {len(self.issues['missing_dates'])} records with missing dates")
        print(f"  ✓ Found {len(self.issues['future_historical'])} suspicious future dates")
    
    def _analyze_confidence_scores(self, conn):
        """Check for low-confidence data."""
        print("\n🎯 Analyzing confidence scores...")
        
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
        rows = result.fetchall()
        
        for row in rows:
            self.issues['low_confidence'].append({
                'ticker': row.Ticker,
                'amount': float(row.Dividend_Amount),
                'ex_date': row.Ex_Dividend_Date,
                'confidence': float(row.Confidence_Score),
                'source': row.Data_Source
            })
        
        print(f"  ✓ Found {len(self.issues['low_confidence'])} low-confidence records (<0.5)")
    
    def _analyze_duplicates(self, conn):
        """Check for duplicate dividend entries."""
        print("\n🔍 Analyzing duplicates...")
        
        query = text("""
            SELECT 
                Ticker,
                Ex_Dividend_Date,
                COUNT(*) AS duplicate_count,
                STRING_AGG(CAST(Dividend_Amount AS VARCHAR), ', ') AS amounts,
                STRING_AGG(Data_Source, ', ') AS sources
            FROM vDividendsEnhanced
            WHERE Ex_Dividend_Date IS NOT NULL
            GROUP BY Ticker, Ex_Dividend_Date
            HAVING COUNT(*) > 1
            ORDER BY COUNT(*) DESC
        """)
        
        result = conn.execute(query)
        rows = result.fetchall()
        
        for row in rows:
            self.issues['duplicate_entries'].append({
                'ticker': row.Ticker,
                'ex_date': row.Ex_Dividend_Date,
                'count': row.duplicate_count,
                'amounts': row.amounts,
                'sources': row.sources
            })
        
        print(f"  ✓ Found {len(self.issues['duplicate_entries'])} duplicate ticker/date combinations")
    
    def _generate_statistics(self, conn):
        """Generate overall database statistics."""
        print("\n📈 Generating statistics...")
        
        # Overall stats
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
        
        self.stats['total_records'] = row.total_records
        self.stats['unique_tickers'] = row.unique_tickers
        self.stats['avg_dividend'] = float(row.avg_dividend) if row.avg_dividend else 0
        self.stats['min_dividend'] = float(row.min_dividend) if row.min_dividend else 0
        self.stats['max_dividend'] = float(row.max_dividend) if row.max_dividend else 0
        self.stats['avg_confidence'] = float(row.avg_confidence) if row.avg_confidence else 0
        
        # Data source breakdown
        query = text("""
            SELECT 
                Data_Source,
                COUNT(*) AS count,
                AVG(Confidence_Score) AS avg_confidence
            FROM vDividendsEnhanced
            GROUP BY Data_Source
            ORDER BY COUNT(*) DESC
        """)
        
        result = conn.execute(query)
        self.stats['sources'] = [
            {
                'source': row.Data_Source,
                'count': row.count,
                'avg_confidence': float(row.avg_confidence) if row.avg_confidence else 0
            }
            for row in result.fetchall()
        ]
        
        print("  ✓ Statistics generated")
    
    def _print_report(self):
        """Print comprehensive report to console."""
        print("\n" + "=" * 80)
        print("SUMMARY STATISTICS")
        print("=" * 80)
        print(f"Total Dividend Records: {self.stats['total_records']:,}")
        print(f"Unique Tickers: {self.stats['unique_tickers']:,}")
        print(f"Average Dividend: ${self.stats['avg_dividend']:.2f}")
        print(f"Min Dividend: ${self.stats['min_dividend']:.2f}")
        print(f"Max Dividend: ${self.stats['max_dividend']:,.2f}")
        print(f"Average Confidence Score: {self.stats['avg_confidence']:.2%}")
        
        print("\n" + "-" * 80)
        print("DATA SOURCES")
        print("-" * 80)
        for source in self.stats['sources']:
            print(f"  {source['source']}: {source['count']:,} records (avg confidence: {source['avg_confidence']:.2%})")
        
        print("\n" + "=" * 80)
        print("DATA QUALITY ISSUES")
        print("=" * 80)
        
        # Unrealistic amounts
        if self.issues['unrealistic_amounts']:
            print(f"\n⚠️  UNREALISTIC AMOUNTS (>{1000}) - {len(self.issues['unrealistic_amounts'])} issues")
            print("-" * 80)
            for issue in sorted(self.issues['unrealistic_amounts'], key=lambda x: x['amount'], reverse=True)[:20]:
                print(f"  {issue['ticker']:12} ${issue['amount']:>15,.2f}  Ex: {issue['ex_date']}  Source: {issue['source']}")
        
        # Negative amounts
        if self.issues['negative_amounts']:
            print(f"\n⚠️  NEGATIVE AMOUNTS - {len(self.issues['negative_amounts'])} issues")
            print("-" * 80)
            for issue in self.issues['negative_amounts'][:20]:
                print(f"  {issue['ticker']:12} ${issue['amount']:>15,.2f}  Ex: {issue['ex_date']}  Source: {issue['source']}")
        
        # Zero amounts
        if self.issues['zero_amounts']:
            print(f"\n⚠️  ZERO AMOUNTS - {len(self.issues['zero_amounts'])} issues")
            print("-" * 80)
            print(f"  {len(self.issues['zero_amounts'])} records with $0.00 dividends (showing first 10)")
            for issue in self.issues['zero_amounts'][:10]:
                print(f"  {issue['ticker']:12} Ex: {issue['ex_date']}  Source: {issue['source']}")
        
        # Missing dates
        if self.issues['missing_dates']:
            print(f"\n⚠️  MISSING DATES - {len(self.issues['missing_dates'])} issues")
            print("-" * 80)
            for issue in self.issues['missing_dates'][:20]:
                print(f"  {issue['ticker']:12} ${issue['amount']:>10,.2f}  Missing: {issue['missing']}  Source: {issue['source']}")
        
        # Low confidence
        if self.issues['low_confidence']:
            print(f"\n⚠️  LOW CONFIDENCE (<0.5) - {len(self.issues['low_confidence'])} issues")
            print("-" * 80)
            for issue in sorted(self.issues['low_confidence'], key=lambda x: x['confidence'])[:20]:
                print(f"  {issue['ticker']:12} ${issue['amount']:>10,.2f}  Confidence: {issue['confidence']:.2%}  Source: {issue['source']}")
        
        # Duplicates
        if self.issues['duplicate_entries']:
            print(f"\n⚠️  DUPLICATE ENTRIES - {len(self.issues['duplicate_entries'])} issues")
            print("-" * 80)
            for issue in sorted(self.issues['duplicate_entries'], key=lambda x: x['count'], reverse=True)[:20]:
                print(f"  {issue['ticker']:12} Ex: {issue['ex_date']}  Count: {issue['count']}  Amounts: {issue['amounts']}")
        
        print("\n" + "=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)
        
        if self.issues['unrealistic_amounts']:
            print("✓ Filter dividends >$1,000 as likely data errors")
        if self.issues['negative_amounts'] or self.issues['zero_amounts']:
            print("✓ Exclude negative/zero dividend amounts from queries")
        if self.issues['low_confidence']:
            print("✓ Use Confidence_Score >= 0.7 filter in production queries")
        if self.issues['duplicate_entries']:
            print("✓ Deduplicate using ROW_NUMBER() in vDividendsEnhanced view")
        if self.issues['missing_dates']:
            print("✓ Validate required fields (ex_date, payment_date) on data ingestion")
        
        print("\n" + "=" * 80)
        print("REPORT COMPLETE")
        print("=" * 80)
    
    def _export_csv(self):
        """Export detailed issues to CSV files."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Export unrealistic amounts
        if self.issues['unrealistic_amounts']:
            df = pd.DataFrame(self.issues['unrealistic_amounts'])
            filename = f'data_quality_unrealistic_{timestamp}.csv'
            df.to_csv(filename, index=False)
            print(f"\n📄 Exported unrealistic amounts to: {filename}")
        
        # Export low confidence
        if self.issues['low_confidence']:
            df = pd.DataFrame(self.issues['low_confidence'])
            filename = f'data_quality_low_confidence_{timestamp}.csv'
            df.to_csv(filename, index=False)
            print(f"📄 Exported low confidence records to: {filename}")
        
        # Export duplicates
        if self.issues['duplicate_entries']:
            df = pd.DataFrame(self.issues['duplicate_entries'])
            filename = f'data_quality_duplicates_{timestamp}.csv'
            df.to_csv(filename, index=False)
            print(f"📄 Exported duplicates to: {filename}")


def main():
    """Run data quality analysis."""
    try:
        analyzer = DataQualityAnalyzer()
        analyzer.analyze()
        return 0
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
