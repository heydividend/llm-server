#!/bin/bash
# Harvey Backend - Push Latest Changes to GitHub

echo "=========================================="
echo "Harvey Backend - Pushing to GitHub"
echo "=========================================="
echo ""

echo "📋 Adding new files..."
git add .

echo ""
echo "📝 Creating commit..."
git commit -m "Add portfolio upload, PDF processing, feedback system, and ML optimizations

Features added:
- Multi-format portfolio upload (CSV, Excel, PDF, screenshots)
- PDF.co integration for advanced document processing
- Portfolio parser with flexible column recognition
- Comprehensive feedback-driven learning system
- GPT-4o fine-tuning pipeline with training data export
- ML API timeout optimization (5s, prevents hanging)
- FreeTDS/unixODBC database driver configuration
- Azure SQL Server schema compatibility fixes
- Performance improvements and circuit breaker optimization
- Complete API documentation and deployment guides

Deployment:
- Updated Azure VM deployment scripts
- Database schema migrations for feedback system
- Nginx configuration for ML API routing
- Production-ready with self-healing capabilities
"

echo ""
echo "🚀 Pushing to GitHub..."
git push origin main

echo ""
echo "✅ Push complete!"
echo ""
echo "Next steps:"
echo "1. Verify at: https://github.com/heydividend/llm-server"
echo "2. Deploy to Azure VM using updated deployment script"
echo "3. Create feedback tables on Azure SQL Server"
echo ""
