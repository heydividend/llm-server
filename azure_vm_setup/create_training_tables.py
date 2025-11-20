#!/usr/bin/env python3
"""
Create Harvey AI Training Tables on Azure SQL Server
Uses pymssql (no ODBC drivers required)
"""

import os
import pymssql
from dotenv import load_dotenv

load_dotenv(override=True)

def create_training_tables():
    """Create all training tables in Azure SQL Server."""
    
    print("🔌 Connecting to Azure SQL Server...")
    print(f"   Host: {os.getenv('SQLSERVER_HOST')}")
    print(f"   Database: {os.getenv('SQLSERVER_DB')}")
    
    conn = pymssql.connect(
        server=os.getenv('SQLSERVER_HOST'),
        user=os.getenv('SQLSERVER_USER'),
        password=os.getenv('SQLSERVER_PASSWORD'),
        database=os.getenv('SQLSERVER_DB')
    )
    
    cursor = conn.cursor()
    
    print("✅ Connected successfully!\n")
    
    # Read SQL schema
    with open('/tmp/create_training_tables.sql', 'r') as f:
        sql_statements = f.read()
    
    # Split into individual statements and execute
    statements = sql_statements.split(';')
    
    for i, stmt in enumerate(statements, 1):
        stmt = stmt.strip()
        if stmt and not stmt.startswith('--') and stmt != 'PRINT':
            try:
                print(f"Executing statement {i}...")
                cursor.execute(stmt)
                conn.commit()
            except Exception as e:
                if "already an object named" in str(e):
                    print(f"   ⏭️  Table already exists (skipping)")
                else:
                    print(f"   ⚠️  Error: {e}")
    
    print("\n📊 Verifying tables...")
    cursor.execute("""
        SELECT TABLE_NAME, 
               (SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = T.TABLE_NAME) as column_count
        FROM INFORMATION_SCHEMA.TABLES T
        WHERE TABLE_NAME IN (
            'training_questions', 
            'training_responses', 
            'harvey_training_data',
            'conversation_history',
            'feedback_log',
            'model_audit'
        )
        ORDER BY TABLE_NAME
    """)
    
    tables = cursor.fetchall()
    
    print("\n✅ Training Tables Created:")
    print("=" * 60)
    for table_name, col_count in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        print(f"   ✓ {table_name:<30} {col_count} columns, {row_count} rows")
    
    print("=" * 60)
    print(f"\n🎉 Successfully created {len(tables)} training tables!")
    
    conn.close()

if __name__ == "__main__":
    create_training_tables()
