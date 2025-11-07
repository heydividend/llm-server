#!/usr/bin/env python3
"""
Test Database Connection and Write Operations for Harvey on Azure VM
Using same connection method as Harvey (pyodbc)
"""

import os
import sys
import logging
from datetime import datetime
from urllib.parse import quote_plus

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test connection to Azure SQL Server using pyodbc (same as Harvey)"""
    
    # Get database credentials from environment (same as app/core/database.py)
    host = os.getenv("SQLSERVER_HOST", "")
    port = os.getenv("SQLSERVER_PORT", "1433")
    database = os.getenv("SQLSERVER_DB", "")
    user = os.getenv("SQLSERVER_USER", "")
    password = os.getenv("SQLSERVER_PASSWORD", "")
    driver = os.getenv("ODBC_DRIVER", "FreeTDS")
    
    if not all([host, database, user, password]):
        logger.error("❌ Database credentials not found in environment variables")
        logger.info("Required: SQLSERVER_HOST, SQLSERVER_DB, SQLSERVER_USER, SQLSERVER_PASSWORD")
        logger.info(f"Current values: host={bool(host)}, db={bool(database)}, user={bool(user)}, pwd={bool(password)}")
        return False
    
    logger.info(f"🔌 Testing database connection: {user}@{host}:{port}/{database}")
    logger.info(f"   Using driver: {driver}")
    
    # Try both pyodbc and direct SQLAlchemy connection (as Harvey uses)
    try:
        # First, let's try the SQLAlchemy approach that Harvey uses
        from sqlalchemy import create_engine, text
        from sqlalchemy.exc import SQLAlchemyError
        
        # Build connection string exactly as Harvey does (from app/core/database.py)
        params = {
            "driver": driver,
            "TDS_Version": "7.3",
            "Encrypt": "yes",
            "TrustServerCertificate": "no",
            "LoginTimeout": "10",
            "Connection Timeout": "20",
            "AUTOCOMMIT": "True",
        }
        param_str = "&".join([f"{k}={quote_plus(v)}" for k, v in params.items()])
        engine_url = f"mssql+pyodbc://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{quote_plus(database)}?{param_str}"
        
        logger.info("📝 Creating SQLAlchemy engine (same as Harvey)...")
        
        # Create engine with Harvey's settings
        engine = create_engine(
            engine_url,
            isolation_level="AUTOCOMMIT",
            fast_executemany=True,
            pool_pre_ping=True,
            pool_size=20,
            max_overflow=20,
            pool_recycle=3600,
            pool_timeout=30,
        )
        
        # Test connection
        with engine.connect() as conn:
            logger.info("✅ Database connection successful!")
            
            # Test read operation - get table list
            result = conn.execute(text("""
                SELECT TOP 10 TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
            """))
            
            tables = result.fetchall()
            logger.info(f"📊 Found {len(tables)} tables in database:")
            for table in tables:
                logger.info(f"   - {table[0]}")
            
            # Check for Harvey-specific tables/views
            result = conn.execute(text("""
                SELECT TABLE_NAME, TABLE_TYPE
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE (TABLE_NAME LIKE '%dividend%' 
                   OR TABLE_NAME LIKE '%portfolio%'
                   OR TABLE_NAME LIKE '%ml_%'
                   OR TABLE_NAME LIKE '%feedback%'
                   OR TABLE_NAME LIKE '%audit%'
                   OR TABLE_NAME LIKE 'v%')
                ORDER BY TABLE_TYPE, TABLE_NAME
            """))
            
            harvey_objects = result.fetchall()
            if harvey_objects:
                logger.info(f"\n📈 Harvey-specific tables/views found ({len(harvey_objects)}):")
                for obj in harvey_objects:
                    logger.info(f"   - {obj[0]} ({obj[1]})")
            else:
                logger.info("\n⚠️  No Harvey-specific tables/views found")
            
            # Test write capability - check for writable tables
            write_test_successful = False
            
            # Check for feedback tables (mentioned in Harvey codebase)
            result = conn.execute(text("""
                SELECT COUNT(*) as count 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME IN ('user_feedback', 'feedback_analytics', 'model_audit_log', 'audit_log')
            """))
            
            count = result.fetchone()[0]
            if count > 0:
                logger.info("✅ Found writable tables for Harvey")
                
                # Try a simple INSERT to test write capability
                try:
                    # Try to create a test table to verify write permissions
                    conn.execute(text("""
                        IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'harvey_test_write')
                        CREATE TABLE harvey_test_write (
                            id INT IDENTITY(1,1) PRIMARY KEY,
                            test_message VARCHAR(255),
                            created_at DATETIME DEFAULT GETDATE()
                        )
                    """))
                    
                    # Insert a test record
                    conn.execute(text("""
                        INSERT INTO harvey_test_write (test_message) 
                        VALUES (:msg)
                    """), {"msg": f"Harvey connection test from Replit at {datetime.now()}"})
                    
                    # Read it back
                    result = conn.execute(text("SELECT COUNT(*) FROM harvey_test_write"))
                    test_count = result.fetchone()[0]
                    
                    logger.info(f"✅ Database WRITE test successful - {test_count} test record(s) in harvey_test_write")
                    write_test_successful = True
                    
                    # Clean up
                    conn.execute(text("DROP TABLE harvey_test_write"))
                    
                except Exception as e:
                    logger.warning(f"⚠️  Write test failed: {str(e)}")
                    logger.info("   This might be normal if database is read-only or permissions are restricted")
            
            # Check database views used by Harvey
            result = conn.execute(text("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.VIEWS 
                WHERE TABLE_NAME IN ('vTickers', 'vDividends', 'vPrices', 
                                    'vSecurities', 'vDividendsEnhanced', 'vQuotesEnhanced')
                ORDER BY TABLE_NAME
            """))
            
            views = result.fetchall()
            if views:
                logger.info(f"\n📊 Harvey views available ({len(views)}):")
                for view in views:
                    logger.info(f"   - {view[0]}")
            
            # Summary
            logger.info("\n" + "="*60)
            logger.info("📊 DATABASE CONNECTION SUMMARY")
            logger.info("="*60)
            logger.info(f"✅ Connection: SUCCESSFUL")
            logger.info(f"✅ Read Operations: WORKING")
            if write_test_successful:
                logger.info(f"✅ Write Operations: WORKING")
            else:
                logger.info(f"⚠️  Write Operations: LIMITED (may be read-only)")
            logger.info(f"📍 Server: {host}:{port}")
            logger.info(f"📦 Database: {database}")
            logger.info(f"👤 User: {user}")
            logger.info(f"🔧 Driver: {driver}")
            logger.info("="*60)
            
            return True
            
    except ImportError as e:
        logger.error(f"❌ Missing required package: {str(e)}")
        logger.info("\nTo fix, install required packages:")
        logger.info("  pip install sqlalchemy pyodbc")
        return False
        
    except SQLAlchemyError as e:
        logger.error(f"❌ Database connection failed: {str(e)}")
        logger.info("\nPossible issues:")
        logger.info("1. Database credentials incorrect")
        logger.info("2. Azure SQL Server firewall blocking connection")
        logger.info("3. ODBC driver not installed (FreeTDS or ODBC Driver)")
        logger.info("4. Network connectivity issues")
        return False
        
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Testing Harvey Database Connection (Azure SQL Server)")
    logger.info("="*60)
    
    success = test_database_connection()
    
    if success:
        logger.info("\n✅ Database connectivity verified!")
        sys.exit(0)
    else:
        logger.info("\n❌ Database tests failed. See errors above.")
        sys.exit(1)