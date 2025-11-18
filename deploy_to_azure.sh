#!/bin/bash
# Deploy Harvey Video Player + Verify Training Agents
# Run this script on Azure VM (20.81.210.213)

echo "================================================"
echo "🚀 Harvey Deployment - Video Player + Training Verification"
echo "================================================"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

HARVEY_DIR="/home/azureuser/harvey"

echo "1️⃣ PULL LATEST CODE FROM GIT"
echo "------------------------------------------------"
cd $HARVEY_DIR || exit 1

git fetch origin
git pull origin main
echo -e "${GREEN}✅ Code updated${NC}"

echo ""
echo "2️⃣ RESTART HARVEY SERVICE"
echo "------------------------------------------------"
sudo systemctl restart harvey-backend
sleep 5
sudo systemctl status harvey-backend --no-pager | head -15

echo ""
echo "3️⃣ VERIFY TRAINING AGENTS"
echo "------------------------------------------------"

echo -e "\n${BLUE}📚 Training Ingestion Service:${NC}"
python3 -c "
from app.services.training_ingestion_service import TrainingDataIngestion
service = TrainingDataIngestion()
total = sum(len(q) for q in service.TRAINING_QUESTIONS.values())
print(f'✅ Loaded {total} training questions')
for category, questions in service.TRAINING_QUESTIONS.items():
    print(f'   - {category}: {len(questions)} questions')
"

echo -e "\n${BLUE}⏰ ML Schedulers Status:${NC}"
sudo systemctl status heydividend-ml-schedulers --no-pager | head -10

echo -e "\n${BLUE}📅 Next Scheduled ML Runs:${NC}"
sudo systemctl list-timers --all | grep heydividend

echo -e "\n${BLUE}📊 Recent Training Logs:${NC}"
ls -lt /var/log/harvey-intelligence/ 2>/dev/null | head -5 || echo "No training logs found"

echo ""
echo "4️⃣ TEST VIDEO PLAYER API"
echo "------------------------------------------------"

echo -e "\n${BLUE}Testing video metadata endpoint...${NC}"
curl -s -X POST http://localhost:8001/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "What are dividend aristocrats?"}],
    "enable_videos": true,
    "stream": false
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
videos = data.get('video_metadata', [])
print(f'✅ Returned {len(videos)} video recommendations')
if videos:
    for v in videos[:2]:
        print(f\"   - {v.get('title', 'Unknown')} ({v.get('duration', 'N/A')})\")
else:
    print('⚠️  No videos in response')
"

echo ""
echo "5️⃣ DEPLOYMENT SUMMARY"
echo "================================================"

echo -e "\n${GREEN}✅ Deployment Complete!${NC}\n"

echo "📊 Status Check:"
if systemctl is-active --quiet harvey-backend; then
    echo -e "  ${GREEN}✅ Harvey Backend: RUNNING${NC}"
else
    echo -e "  ${RED}❌ Harvey Backend: STOPPED${NC}"
fi

if systemctl is-active --quiet heydividend-ml-schedulers; then
    echo -e "  ${GREEN}✅ ML Schedulers: RUNNING${NC}"
else
    echo -e "  ${YELLOW}⚠️  ML Schedulers: Check status${NC}"
fi

echo ""
echo "🌐 Access URLs:"
echo "  • API Docs: http://20.81.210.213:8001/docs"
echo "  • Health: http://20.81.210.213:8001/health"
echo ""
echo "📝 Logs:"
echo "  • Harvey: sudo journalctl -u harvey-backend -f"
echo "  • ML: sudo journalctl -u heydividend-ml-schedulers -f"
echo ""
