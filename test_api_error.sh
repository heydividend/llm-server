#!/bin/bash
# Check what error the API is returning

echo "=== Full API Error Response ==="
curl -s -X POST http://localhost:8001/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "dividend aristocrats"}],
    "enable_videos": true,
    "stream": false
  }' | python3 -m json.tool

echo -e "\n=== Harvey Backend Logs (last 50 lines) ==="
sudo journalctl -u harvey-backend -n 50 --no-pager

echo -e "\n=== Check if Harvey is actually running ==="
systemctl status harvey-backend --no-pager | head -n 15

echo -e "\n=== Test basic health endpoint ==="
curl -s http://localhost:8001/health | python3 -m json.tool || echo "Health endpoint failed"
