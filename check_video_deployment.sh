#!/bin/bash
# Check video knowledge base on Azure VM

echo "=== Checking Video Knowledge Base on Azure VM ==="

# 1. Check if file exists
echo -e "\n1. File existence check:"
ls -lh /home/azureuser/harvey/app/data/video_knowledge_base.json

# 2. Count videos in file
echo -e "\n2. Video count:"
python3 -c "
import json
with open('/home/azureuser/harvey/app/data/video_knowledge_base.json') as f:
    videos = json.load(f)
print(f'Total videos: {len(videos)}')
if videos:
    print(f'First video: {videos[0].get(\"title\", \"Unknown\")}')
"

# 3. Test VideoAnswerService directly
echo -e "\n3. Testing VideoAnswerService:"
cd /home/azureuser/harvey
python3 -c "
from app.services.video_answer_service import VideoAnswerService
service = VideoAnswerService()
print(f'Videos loaded: {len(service.video_knowledge_base)}')
print(f'Search index size: {len(service.search_index)} keywords')

# Test search
results = service.search_videos('dividend aristocrats', max_results=3)
print(f'\nSearch results: {len(results)} videos')
for i, video in enumerate(results, 1):
    print(f'  {i}. {video.get(\"title\", \"Unknown\")} (score: {video.get(\"relevance_score\", 0)})')
"

# 4. Test with enable_videos=true
echo -e "\n4. Testing API with enable_videos=true:"
curl -s -X POST http://localhost:8001/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "dividend aristocrats"}],
    "enable_videos": true,
    "stream": false
  }' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    videos = data.get('video_metadata', [])
    print(f'API returned: {len(videos)} videos')
    if videos:
        for v in videos:
            print(f'  - {v.get(\"title\", \"Unknown\")}')
    else:
        print('Response keys:', list(data.keys()))
except Exception as e:
    print(f'Error: {e}')
"

