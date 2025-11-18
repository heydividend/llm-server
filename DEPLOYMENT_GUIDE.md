# Harvey Video Player Deployment Guide
## November 18, 2025

## 🎯 What's Being Deployed

### NEW: HeyDividend Video Player System
**Backend:**
- `video_answer_service.py` - Semantic video search with structured metadata
- `ai_controller.py` - Streaming SSE with `video_metadata` events
- API parameter: `enable_videos` (defaults to true)

**Frontend:**
- React/TypeScript components
- Vanilla JavaScript version  
- Multi-framework integration guides

### VERIFY: Training & ML Services Already on Azure VM
- Training Ingestion Service (1,000+ questions)
- ML Schedulers (systemd timers for automated training)
- Evaluation Service (quality scoring)

---

## 📦 Deployment Package Contents

```
deployment_package/
├── app/
│   ├── controllers/
│   │   └── ai_controller.py          (36 KB - UPDATED)
│   └── services/
│       └── video_answer_service.py   (11 KB - NEW)
└── frontend/
    ├── components/video/              (React components)
    ├── vanilla-js/                    (Vanilla JS player)
    ├── MULTI_FRONTEND_INTEGRATION_GUIDE.md
    ├── HEYDIVIDEND_VIDEO_PLAYER_GUIDE.md
    └── VIDEO_SYSTEM_SUMMARY.md
```

---

## 🚀 Deployment Method: Manual Transfer

### Step 1: Create Deployment Archive

```bash
# On Replit - create tar archive
cd deployment_package
tar -czf ../harvey-video-player.tar.gz app/ frontend/
cd ..
ls -lh harvey-video-player.tar.gz
```

### Step 2: Transfer to Azure VM

Using sshpass (password in environment):

```bash
# Transfer archive
sshpass -p "$AZURE_VM_PASSWORD" scp harvey-video-player.tar.gz azureuser@20.81.210.213:/home/azureuser/

# Extract and deploy
sshpass -p "$AZURE_VM_PASSWORD" ssh azureuser@20.81.210.213 << 'EOF'
cd /home/azureuser
tar -xzf harvey-video-player.tar.gz

# Backup current files
mkdir -p harvey_backups/$(date +%Y%m%d_%H%M%S)
cp harvey/app/services/video_answer_service.py harvey_backups/$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || true
cp harvey/app/controllers/ai_controller.py harvey_backups/$(date +%Y%m%d_%H%M%S)/

# Deploy new files
cp -r app/services/* harvey/app/services/
cp -r app/controllers/* harvey/app/controllers/
cp -r frontend/* harvey/frontend/

# Restart Harvey service
sudo systemctl restart harvey-backend
sleep 5

# Check status
sudo systemctl status harvey-backend --no-pager
EOF
```

---

## ✅ Post-Deployment Verification

### 1. Test Video API Response

```bash
curl -X POST http://20.81.210.213:8001/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Tell me about dividend stocks"}],
    "enable_videos": true,
    "stream": false
  }' | jq '.video_metadata'
```

**Expected:** Array of video metadata objects

### 2. Test Streaming SSE

```bash
curl -N -X POST http://20.81.210.213:8001/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "What are dividend aristocrats?"}],
    "enable_videos": true,
    "stream": true
  }'
```

**Look for:** `data: {"video_metadata":[...]}` event

### 3. Verify ML Services Status

```bash
ssh azureuser@20.81.210.213 << 'EOF'
# Check ML scheduler status
sudo systemctl status heydividend-ml-schedulers --no-pager

# View next scheduled runs
sudo systemctl list-timers --all | grep heydividend

# Check training logs
ls -lt /var/log/harvey-intelligence/ | head -10
EOF
```

### 4. Test Harvey Backend

```bash
# Health check
curl http://20.81.210.213:8001/health

# API docs
curl http://20.81.210.213:8001/docs
```

---

## 🔧 Service Management

### Harvey Backend Service

```bash
# Restart
sudo systemctl restart harvey-backend

# Status
sudo systemctl status harvey-backend

# Logs
sudo journalctl -u harvey-backend -f

# Recent errors
sudo journalctl -u harvey-backend --since "10 minutes ago" | grep ERROR
```

### ML Training Services

```bash
# Check scheduler
sudo systemctl status heydividend-ml-schedulers

# View upcoming runs
sudo systemctl list-timers --all | grep heydividend

# Manual training run
cd /home/azureuser/harvey/ml_training
python train_all_models.py
```

### Training Ingestion Service

```bash
# Test training ingestion
cd /home/azureuser/harvey
python -c "
from app.services.training_ingestion_service import TrainingDataIngestion
service = TrainingDataIngestion()
print(f'Training questions loaded: {len(service.TRAINING_QUESTIONS)}')
"
```

---

## 📊 What's Already Running on Azure VM

### Active Services

1. **harvey-backend** (Port 8001)
   - Main Harvey API
   - Chat completions endpoint
   - NEW: Video answer service

2. **harvey-ml** (Port 9000)
   - ML API endpoints
   - 22+ intelligence endpoints

3. **heydividend-ml-schedulers** (systemd timer)
   - Payout Rating ML: Daily 1:00 AM
   - Dividend Calendar ML: Sunday 2:00 AM
   - ML Training: Sunday 3:00 AM

### Training Services (On-Demand)

- Training Ingestion Service (1,000+ questions)
- Training Evaluation Service (quality scoring)
- Passive Income Training Service (7,200+ questions)

---

## 🔍 Troubleshooting

### Video Metadata Not Returning

```bash
# Check service logs
sudo journalctl -u harvey-backend -n 100 | grep -i video

# Test VideoAnswerService directly
python -c "
from app.services.video_answer_service import VideoAnswerService
service = VideoAnswerService()
result = service.search_videos('dividend stocks', max_results=2)
print(f'Found {len(result)} videos')
print(result[0] if result else 'No videos found')
"
```

### ML Schedulers Not Running

```bash
# Check timer status
sudo systemctl status heydividend-ml-schedulers.timer

# Enable timer if stopped
sudo systemctl enable heydividend-ml-schedulers.timer
sudo systemctl start heydividend-ml-schedulers.timer

# View logs
sudo journalctl -u heydividend-ml-schedulers -n 100
```

### Harvey Backend Not Starting

```bash
# Check logs for errors
sudo journalctl -u harvey-backend -n 50

# Test manually
cd /home/azureuser/harvey
/home/azureuser/miniconda3/bin/python main.py
```

---

## 🎯 Success Criteria

✅ Harvey backend running (systemctl status)
✅ Video metadata returns in API responses
✅ Streaming SSE emits video_metadata events
✅ ML schedulers active (systemctl list-timers)
✅ No errors in recent logs
✅ Health endpoints responding

---

## 📝 Notes

- **Development**: Video service works in Replit but DB connections fail (expected - no ODBC)
- **Production**: All services function on Azure VM with proper DB connectivity
- **Backup**: Old files backed up to `harvey_backups/` directory
- **Rollback**: Copy from backup directory if needed

---

**Deployment Date:** November 18, 2025  
**Package Size:** ~50 KB (code) + documentation  
**Estimated Downtime:** <30 seconds (service restart)
