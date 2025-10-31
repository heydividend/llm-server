#!/bin/bash
# Harvey Backend - Automated Azure VM Setup Script
# This script installs all dependencies and configures the Azure VM

set -e  # Exit on error

echo "========================================="
echo "Harvey Backend - Azure VM Setup"
echo "========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo "⚠️  Please run as regular user (azureuser), not root"
   exit 1
fi

echo "📦 Step 1: Installing system dependencies..."
sudo apt update
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    freetds-dev \
    freetds-bin \
    unixodbc \
    unixodbc-dev \
    nginx \
    certbot \
    python3-certbot-nginx \
    git \
    htop \
    curl \
    wget

echo "✅ System dependencies installed"
echo ""

echo "🔧 Step 2: Configuring FreeTDS..."
sudo tee /etc/freetds/freetds.conf > /dev/null <<EOF
[global]
tds version = 7.4
client charset = UTF-8
EOF

echo "✅ FreeTDS configured"
echo ""

echo "🔧 Step 3: Configuring ODBC driver..."
sudo tee /etc/odbcinst.ini > /dev/null <<EOF
[FreeTDS]
Description = FreeTDS Driver
Driver = /usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so
Setup = /usr/lib/x86_64-linux-gnu/odbc/libtdsS.so
EOF

echo "✅ ODBC driver configured"
echo ""

echo "📁 Step 4: Creating Harvey backend directory..."
sudo mkdir -p /opt/harvey-backend
sudo chown $USER:$USER /opt/harvey-backend

echo "✅ Directory created: /opt/harvey-backend"
echo ""

echo "📁 Step 5: Creating log directories..."
sudo mkdir -p /var/log/harvey
sudo mkdir -p /var/log/ml-api
sudo chown $USER:$USER /var/log/harvey
sudo chown $USER:$USER /var/log/ml-api

echo "✅ Log directories created"
echo ""

echo "🔥 Step 6: Configuring UFW firewall..."
sudo ufw --force enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Remove port 9000 if it exists
sudo ufw delete allow 9000/tcp 2>/dev/null || true

echo "✅ Firewall configured (ports 22, 80, 443)"
echo ""

echo "========================================="
echo "✅ Azure VM Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Copy Harvey code to /opt/harvey-backend/"
echo "2. Run deploy_harvey.sh to complete deployment"
echo ""
