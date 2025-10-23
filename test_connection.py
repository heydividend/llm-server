import os
import pyodbc
from urllib.parse import quote_plus

HOST = os.getenv("SQLSERVER_HOST")
PORT = os.getenv("SQLSERVER_PORT", "1433")
DB = os.getenv("SQLSERVER_DB")
USER = os.getenv("SQLSERVER_USER")
PWD = os.getenv("SQLSERVER_PASSWORD")

print(f"Testing connection to: {HOST}:{PORT}")
print(f"Database: {DB}")
print(f"User: {USER}")

try:
    conn_str = (
        f"DRIVER={{FreeTDS}};"
        f"SERVER={HOST};"
        f"PORT={PORT};"
        f"DATABASE={DB};"
        f"UID={USER};"
        f"PWD={PWD};"
        f"TDS_Version=7.3;"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
    )
    
    print("\nAttempting connection...")
    conn = pyodbc.connect(conn_str, timeout=10)
    print("✅ Connection successful!")
    
    cursor = conn.cursor()
    cursor.execute("SELECT @@VERSION")
    row = cursor.fetchone()
    print(f"\nServer version: {row[0][:100]}...")
    
    conn.close()
    print("\n✅ Test completed successfully")
    
except pyodbc.Error as e:
    print(f"\n❌ Connection failed: {e}")
    import traceback
    traceback.print_exc()
