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
    conn.autocommit(True)  # Enable autocommit mode
    
    print("✅ Connected successfully!\n")
    
    # Define tables without foreign keys (add them later if needed)
    tables = [
        ("training_questions", """
            CREATE TABLE training_questions (
                question_id NVARCHAR(50) PRIMARY KEY,
                category NVARCHAR(50) NOT NULL,
                question_text NVARCHAR(MAX) NOT NULL,
                complexity_level NVARCHAR(20) DEFAULT 'medium',
                source NVARCHAR(50) DEFAULT 'gemini',
                processed BIT DEFAULT 0,
                created_at DATETIME2 DEFAULT GETDATE()
            )
        """),
        ("training_responses", """
            CREATE TABLE training_responses (
                response_id NVARCHAR(50) PRIMARY KEY,
                question_id NVARCHAR(50) NOT NULL,
                model_name NVARCHAR(50) NOT NULL,
                response_text NVARCHAR(MAX) NOT NULL,
                response_time_ms INT,
                confidence_score DECIMAL(3,2),
                quality_score DECIMAL(3,2),
                created_at DATETIME2 DEFAULT GETDATE()
            )
        """),
        ("harvey_training_data", """
            CREATE TABLE harvey_training_data (
                training_id NVARCHAR(50) PRIMARY KEY,
                question_id NVARCHAR(50) NOT NULL,
                best_model NVARCHAR(50),
                combined_response NVARCHAR(MAX),
                training_format NVARCHAR(MAX),
                quality_score DECIMAL(3,2),
                exported BIT DEFAULT 0,
                export_date DATETIME2,
                created_at DATETIME2 DEFAULT GETDATE()
            )
        """),
        ("conversation_history", """
            CREATE TABLE conversation_history (
                conversation_id NVARCHAR(50) PRIMARY KEY,
                user_id NVARCHAR(50),
                session_id NVARCHAR(50),
                messages NVARCHAR(MAX),
                total_tokens INT DEFAULT 0,
                created_at DATETIME2 DEFAULT GETDATE(),
                updated_at DATETIME2 DEFAULT GETDATE()
            )
        """),
        ("feedback_log", """
            CREATE TABLE feedback_log (
                feedback_id NVARCHAR(50) PRIMARY KEY,
                user_id NVARCHAR(50),
                question NVARCHAR(MAX),
                response NVARCHAR(MAX),
                rating INT,
                sentiment NVARCHAR(20),
                feedback_text NVARCHAR(MAX),
                created_at DATETIME2 DEFAULT GETDATE()
            )
        """),
        ("model_audit", """
            CREATE TABLE model_audit (
                audit_id NVARCHAR(50) PRIMARY KEY,
                model_name NVARCHAR(50) NOT NULL,
                query_type NVARCHAR(50),
                tokens_used INT,
                response_time_ms INT,
                success BIT DEFAULT 1,
                error_message NVARCHAR(MAX),
                created_at DATETIME2 DEFAULT GETDATE()
            )
        """),
    ]
    
    # Create each table
    print("📊 Creating training tables...\n")
    for table_name, create_sql in tables:
        try:
            # Check if table exists
            cursor.execute(f"""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = '{table_name}'
            """)
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                print(f"   ⏭️  {table_name:<30} (already exists)")
            else:
                cursor.execute(create_sql)
                print(f"   ✅ {table_name:<30} (created)")
                
        except Exception as e:
            print(f"   ❌ {table_name:<30} Error: {e}")
    
    # Create indexes
    print("\n📊 Creating indexes...\n")
    indexes = [
        ("idx_training_questions_category", 
         "CREATE INDEX idx_training_questions_category ON training_questions(category)"),
        ("idx_training_questions_processed", 
         "CREATE INDEX idx_training_questions_processed ON training_questions(processed)"),
        ("idx_training_responses_question", 
         "CREATE INDEX idx_training_responses_question ON training_responses(question_id)"),
        ("idx_training_responses_model", 
         "CREATE INDEX idx_training_responses_model ON training_responses(model_name)"),
        ("idx_harvey_training_exported", 
         "CREATE INDEX idx_harvey_training_exported ON harvey_training_data(exported)"),
    ]
    
    for index_name, create_sql in indexes:
        try:
            cursor.execute(f"""
                SELECT COUNT(*) FROM sys.indexes 
                WHERE name = '{index_name}'
            """)
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                print(f"   ⏭️  {index_name:<40} (exists)")
            else:
                cursor.execute(create_sql)
                print(f"   ✅ {index_name:<40} (created)")
        except Exception as e:
            print(f"   ⚠️  {index_name:<40} Error: {e}")
    
    # Verify final state
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
    
    tables_created = cursor.fetchall()
    
    print("\n✅ Training Tables Status:")
    print("=" * 60)
    for table_name, col_count in tables_created:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        print(f"   ✓ {table_name:<30} {col_count} columns, {row_count} rows")
    
    print("=" * 60)
    print(f"\n🎉 Successfully verified {len(tables_created)}/6 training tables!")
    
    conn.close()

if __name__ == "__main__":
    create_training_tables()
