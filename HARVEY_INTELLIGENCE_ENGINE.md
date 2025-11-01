# Harvey Intelligence Engine

## Overview
The **Harvey Intelligence Engine** is Harvey's dedicated machine learning microservice that provides 22+ financial prediction models for dividend analysis, portfolio optimization, and stock clustering. It serves as Harvey's AI brain, delivering real-time predictions and insights.

## Architecture

### Service Details
- **Service Name**: Harvey Intelligence Engine (formerly "ML API")
- **Port**: 9000
- **Base URL**: `http://127.0.0.1:9000/api/internal/ml/`
- **Location**: `/home/azureuser/ml-prediction-api/`
- **Systemd Service**: `harvey-intelligence.service`
- **Models**: Loaded from Azure Blob Storage
- **Monitoring**: Harvey's ML Health Monitor with auto-recovery

### Integration Pattern
The Intelligence Engine is an **internal microservice** consumed exclusively by Harvey backend through authenticated endpoints. Future internal systems can integrate following the same pattern.

## API Endpoints (22+ Available)

### Health & Status
- `GET /api/internal/ml/health` - Health check and model status
  ```json
  {
    "status": "healthy",
    "models_loaded": 5,
    "available_models": ["dividend_predictor", "stock_clusterer", ...]
  }
  ```

### Dividend Predictions
- `POST /api/internal/ml/predict/dividend` - Predict next dividend and ex-date
- `POST /api/internal/ml/predict/dividend/confidence` - Get prediction confidence scores
- `POST /api/internal/ml/score/dividend/quality` - Score dividend quality

### Portfolio Optimization
- `POST /api/internal/ml/optimize/portfolio` - Optimize portfolio allocation
- `POST /api/internal/ml/cluster/stocks` - Cluster stocks by characteristics
- `POST /api/internal/ml/analyze/risk` - Analyze portfolio risk metrics

### Advanced Analytics
- `POST /api/internal/ml/predict/price/trend` - Predict price trends
- `POST /api/internal/ml/anomaly/detection` - Detect anomalies in data
- `POST /api/internal/ml/correlation/analysis` - Correlation analysis

## Authentication

### Current Implementation
**Internal API Key**: All requests require `INTERNAL_ML_API_KEY` header
```python
headers = {
    "Authorization": f"Bearer {INTERNAL_ML_API_KEY}",
    "Content-Type": "application/json"
}
```

### For Future Integrations
Internal systems should:
1. Store `INTERNAL_ML_API_KEY` securely (Azure Key Vault recommended)
2. Include API key in all requests
3. Implement retry logic with exponential backoff
4. Monitor health endpoint before making prediction requests

## Model Loading

Models are loaded from **Azure Blob Storage** on startup:
- Container: `harvey-ml-models`
- Path: `/models/{model_name}.pkl`
- Auto-reload: Every 24 hours or on service restart

## Performance & SLA

- **Latency Target**: < 200ms for prediction endpoints
- **Availability**: 99.9% (monitored by Harvey's health check)
- **Auto-Recovery**: Harvey restarts Intelligence Engine if unhealthy
- **Rate Limits**: None (internal service)

## Error Handling

Harvey implements graceful degradation:
- If Intelligence Engine is down, Harvey uses fallback mechanisms
- Predictions return with confidence scores for reliability filtering
- Health monitor logs all failures for debugging

## Monitoring

### Health Checks
Harvey runs health checks every 30 seconds:
```python
# Harvey's ML Health Monitor
interval = 30  # seconds
timeout = 5    # seconds
```

### Logs
- **Systemd Logs**: `sudo journalctl -u harvey-intelligence.service -f`
- **Application Logs**: Streamed to systemd journal
- **Health Metrics**: Exposed via health endpoint

## Deployment

### Production Setup (Azure VM)
- **Systemd Service**: Auto-starts on boot
- **Python Environment**: `/home/azureuser/miniconda3/envs/llm/bin/python`
- **Dependencies**: Installed via `requirements.txt`
- **Nginx**: Routes `/api/internal/ml/` to port 9000

### Service Management
```bash
# Start service
sudo systemctl start harvey-intelligence.service

# Stop service
sudo systemctl stop harvey-intelligence.service

# Restart service
sudo systemctl restart harvey-intelligence.service

# View status
sudo systemctl status harvey-intelligence.service

# View logs
sudo journalctl -u harvey-intelligence.service -f
```

## Future Enhancements

### Planned Integrations
- **Analytics Dashboard**: Real-time ML insights visualization
- **Automated Reporting**: Scheduled batch predictions
- **A/B Testing Framework**: Model performance comparison

### Roadmap
1. ✅ Core prediction endpoints (22+ models)
2. ✅ Health monitoring and auto-recovery
3. 🔄 Automated nightly training pipeline
4. 📋 Versioned API with contract testing
5. 📋 Multi-tenant support for future systems
6. 📋 Real-time streaming predictions

## Training Jobs

Currently **manual** via SSH. See `TRAINING_AUTOMATION.md` for planned nightly automation setup.

## Support & Troubleshooting

### Common Issues

**Intelligence Engine won't start**
```bash
# Check dependencies
cd /home/azureuser/ml-prediction-api
/home/azureuser/miniconda3/envs/llm/bin/pip install -r requirements.txt

# Check logs
sudo journalctl -u harvey-intelligence.service -n 50
```

**No models loaded**
- Verify Azure Blob Storage connection
- Check `AZURE_STORAGE_CONNECTION_STRING` environment variable
- Ensure models exist in blob container

**Harvey can't connect**
- Verify Intelligence Engine is running: `curl http://127.0.0.1:9000/`
- Check `ML_API_BASE_URL` in Harvey's `.env` file
- Review Harvey's ML Health Monitor logs

## API Contract Versioning

**Current Version**: v1 (implicit)
**Breaking Changes**: Will be communicated via versioned endpoints (`/api/internal/ml/v2/...`)

For API contract details, see endpoint documentation above.
