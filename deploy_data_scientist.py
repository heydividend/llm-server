#!/usr/bin/env python3
"""
Harvey AI - Data Scientist Agent Deployment Script
Deploys training tables and Data Scientist Agent to Azure VM
"""

import os
import paramiko
from pathlib import Path

# Azure VM credentials
AZURE_VM_USER = os.getenv("AZURE_VM_USER")
AZURE_VM_IP = os.getenv("AZURE_VM_IP")
SSH_VM_PASSWORD = os.getenv("SSH_VM_PASSWORD")
HARVEY_DIR = "/home/azureuser/harvey"

def print_step(step_num, message):
    """Print formatted step message."""
    print(f"\n{'='*60}")
    print(f"📋 Step {step_num}: {message}")
    print('='*60)

def execute_remote_command(ssh, command, description=""):
    """Execute a command on the remote server and print output."""
    if description:
        print(f"   🔧 {description}")
    
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    
    if output:
        print(output)
    if error and exit_status != 0:
        print(f"   ⚠️  Error: {error}")
        return False
    
    return exit_status == 0

def upload_file(sftp, local_path, remote_path, description=""):
    """Upload a file via SFTP."""
    if description:
        print(f"   📤 {description}")
    try:
        sftp.put(local_path, remote_path)
        print(f"   ✅ Uploaded: {Path(local_path).name}")
        return True
    except Exception as e:
        print(f"   ❌ Upload failed: {e}")
        return False

def main():
    print("="*60)
    print("Harvey AI - Data Scientist Agent Deployment")
    print("="*60)
    print(f"\n🎯 Target: {AZURE_VM_USER}@{AZURE_VM_IP}")
    print(f"📁 Directory: {HARVEY_DIR}")
    
    # Verify credentials
    if not all([AZURE_VM_USER, AZURE_VM_IP, SSH_VM_PASSWORD]):
        print("\n❌ Error: Missing Azure VM credentials")
        print("   Required: AZURE_VM_USER, AZURE_VM_IP, SSH_VM_PASSWORD")
        return 1
    
    # Type guard: credentials exist at this point
    assert AZURE_VM_IP is not None
    assert AZURE_VM_USER is not None
    assert SSH_VM_PASSWORD is not None
    
    # Create SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect to Azure VM
        print("\n🔌 Connecting to Azure VM...")
        ssh.connect(
            hostname=AZURE_VM_IP,
            username=AZURE_VM_USER,
            password=SSH_VM_PASSWORD,
            timeout=30
        )
        print("   ✅ Connected successfully!")
        
        # Create SFTP client
        sftp = ssh.open_sftp()
        
        # Step 1: Upload SQL schema
        print_step(1, "Uploading SQL schema")
        upload_file(
            sftp,
            "/tmp/create_training_tables.sql",
            "/tmp/create_training_tables.sql",
            "Uploading training tables schema"
        )
        
        # Step 2: Upload table creation script
        print_step(2, "Uploading table creation script")
        upload_file(
            sftp,
            "azure_vm_setup/create_training_tables.py",
            f"{HARVEY_DIR}/azure_vm_setup/create_training_tables.py",
            "Uploading Python script"
        )
        
        # Step 3: Upload Data Scientist Agent
        print_step(3, "Uploading Data Scientist Agent")
        upload_file(
            sftp,
            "app/services/data_scientist_agent.py",
            f"{HARVEY_DIR}/app/services/data_scientist_agent.py",
            "Uploading agent service"
        )
        
        # Step 4: Create training tables
        print_step(4, "Creating training tables in Azure SQL")
        execute_remote_command(
            ssh,
            f"cd {HARVEY_DIR} && python3 azure_vm_setup/create_training_tables.py",
            "Running table creation script"
        )
        
        # Step 5: Test database connection
        print_step(5, "Testing database connection")
        test_cmd = f"""cd {HARVEY_DIR} && python3 -c "
import pymssql, os
from dotenv import load_dotenv

load_dotenv(override=True)

conn = pymssql.connect(
    server=os.getenv('SQLSERVER_HOST'),
    user=os.getenv('SQLSERVER_USER'),
    password=os.getenv('SQLSERVER_PASSWORD'),
    database=os.getenv('SQLSERVER_DB')
)

cursor = conn.cursor()
tables = ['training_questions', 'training_responses', 'harvey_training_data', 
          'conversation_history', 'feedback_log', 'model_audit']

print('📊 Training Tables Status:')
print('=' * 60)
for table in tables:
    cursor.execute(f'SELECT COUNT(*) FROM {{table}}')
    count = cursor.fetchone()[0]
    print(f'   ✓ {{table:<30}} {{count:>8}} rows')
print('=' * 60)

conn.close()
"
"""
        execute_remote_command(ssh, test_cmd, "Verifying tables")
        
        # Step 6: Run schema analysis
        print_step(6, "Running database schema analysis")
        execute_remote_command(
            ssh,
            f"cd {HARVEY_DIR} && python3 scripts/data_scientist_agent.py --schema-only",
            "Analyzing database schema"
        )
        
        # Step 7: Run full analysis with AI
        print_step(7, "Running full AI analysis with Gemini")
        execute_remote_command(
            ssh,
            f"cd {HARVEY_DIR} && python3 scripts/data_scientist_agent.py --analyze --output /tmp/harvey_analysis.json",
            "Generating ML recommendations"
        )
        
        # Step 8: Download analysis report
        print_step(8, "Downloading analysis report")
        try:
            sftp.get(
                "/tmp/harvey_analysis.json",
                "attached_assets/harvey_analysis.json"
            )
            print("   ✅ Analysis report downloaded to: attached_assets/harvey_analysis.json")
        except Exception as e:
            print(f"   ⚠️  Could not download report: {e}")
        
        # Close connections
        sftp.close()
        ssh.close()
        
        # Success summary
        print("\n" + "="*60)
        print("✅ Deployment Complete!")
        print("="*60)
        print("\n📋 What was deployed:")
        print("   • Training tables (6 tables created)")
        print("   • Data Scientist Agent with pymssql")
        print("   • Database schema analysis")
        print("   • AI-powered ML recommendations")
        print("\n📊 View the analysis report:")
        print("   cat attached_assets/harvey_analysis.json | python3 -m json.tool")
        print()
        
        return 0
        
    except paramiko.AuthenticationException:
        print("\n❌ Authentication failed - check SSH credentials")
        return 1
    except paramiko.SSHException as e:
        print(f"\n❌ SSH error: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        return 1
    finally:
        ssh.close()

if __name__ == "__main__":
    exit(main())
