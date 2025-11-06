#!/usr/bin/env python3
"""Create deployment archive for Harvey"""
import os
import zipfile
import shutil

# Define exclude patterns
EXCLUDE_PATTERNS = [
    '.git',
    '__pycache__',
    '.pythonlibs',
    'logs',
    '.pyc',
    '.ollama',
    'node_modules',
    '.uv',
    '.cache',
    'harvey-deploy.zip',
    'create_deployment.py'
]

def should_exclude(file_path):
    """Check if file should be excluded"""
    for pattern in EXCLUDE_PATTERNS:
        if pattern in file_path:
            return True
    return False

def create_archive():
    """Create deployment zip archive"""
    archive_name = 'harvey-deploy.zip'
    
    # Remove old archive if exists
    if os.path.exists(archive_name):
        os.remove(archive_name)
    
    # Create new archive
    with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk('.'):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if not should_exclude(d)]
            
            for file in files:
                file_path = os.path.join(root, file)
                if not should_exclude(file_path):
                    # Add file to archive with relative path
                    arcname = os.path.relpath(file_path, '.')
                    zipf.write(file_path, arcname)
    
    # Get archive size
    size_mb = os.path.getsize(archive_name) / (1024 * 1024)
    print(f"✅ Created {archive_name} ({size_mb:.2f} MB)")
    
    return archive_name

if __name__ == "__main__":
    archive = create_archive()
    print(f"\n📦 Deployment archive ready: {archive}")
    print("\n🚀 To deploy to Azure VM:")
    print(f"   scp {archive} azureuser@20.81.210.213:/home/azureuser/")
    print("\n   Then on Azure VM:")
    print("   cd /home/azureuser/harvey")
    print(f"   unzip -o /home/azureuser/{archive}")
    print("   pip install -r requirements.txt")
    print("   sudo systemctl restart harvey-backend harvey-ml")