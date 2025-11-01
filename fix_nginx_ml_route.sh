#!/bin/bash
# Fix Nginx configuration to route ML API requests

echo "Updating Nginx configuration for ML API routing..."

cat > /etc/nginx/sites-available/harvey << 'EOF'
upstream harvey_backend {
    server localhost:8000;
}

upstream ml_api {
    server localhost:9000;
}

server {
    listen 80;
    server_name _;

    client_max_body_size 50M;

    # Harvey backend (all routes except /ml/)
    location / {
        proxy_pass http://harvey_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for streaming
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # ML API routes (proxy /v1/ml/ to ML API)
    location /v1/ml/ {
        proxy_pass http://ml_api/v1/ml/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for ML API
        proxy_connect_timeout 30s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    # Direct ML API health check
    location /ml/health {
        proxy_pass http://ml_api/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

echo "Nginx configuration updated"

# Test configuration
nginx -t

# Reload Nginx
systemctl reload nginx

echo "✅ Nginx reloaded - ML API routing should now work"
echo ""
echo "Test with:"
echo "  curl http://localhost/healthz"
echo "  curl http://localhost/v1/ml/health"
echo "  curl http://localhost/ml/health"
