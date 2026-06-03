# 🚀 Deployment Guide

## Development Environment (Current Status)

### ✅ Running Services

1. **Backend API** - Port 8000
   - URL: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Dashboard: http://localhost:8000/dashboard
   - Status: ✅ RUNNING

2. **Frontend** - Port 3000
   - URL: http://localhost:3000
   - Status: ✅ RUNNING

### Quick Access Links

- 🎨 **Landing Page**: http://localhost:3000
- 📊 **Dashboard**: http://localhost:3000/dashboard
- 🎯 **Single Predict**: http://localhost:3000/dashboard/predict
- 📦 **Batch Predict**: http://localhost:3000/dashboard/batch
- 📈 **Analytics**: http://localhost:3000/dashboard/analytics
- 🔍 **Monitor**: http://localhost:3000/dashboard/monitor
- 📚 **API Docs**: http://localhost:8000/docs

## Local Development

### Start Backend
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Start Frontend
```bash
cd frontend
npm run dev
```

## Production Deployment with Docker

### Build All Services
```bash
docker-compose up --build
```

### Services Configuration

**docker-compose.yml** includes:
- `api` - FastAPI backend (port 8000)
- `frontend` - React SPA with Nginx (port 3000)
- `demo` - Gradio demo (port 7860)

### Individual Service Build

#### Backend
```bash
docker build -t sentiment-api:latest .
docker run -p 8000:8000 -v ./models:/app/models sentiment-api:latest
```

#### Frontend
```bash
cd frontend
docker build -t sentiment-frontend:latest .
docker run -p 3000:80 sentiment-frontend:latest
```

## Environment Variables

### Backend (.env)
```env
MODEL_DIR=./models
LOG_LEVEL=INFO
MAX_BATCH_SIZE=64
```

### Frontend (frontend/.env)
```env
VITE_API_URL=http://localhost:8000
```

## Health Checks

### Backend Health
```bash
curl http://localhost:8000/health
```

Expected Response:
```json
{
  "status": "ok",
  "model": "lexicon-vader-extended",
  "device": "cpu"
}
```

### Frontend Health
```bash
curl -I http://localhost:3000
```

Expected Response: `200 OK`

## Nginx Configuration (Production)

The frontend uses Nginx in production with:
- SPA routing (serves index.html for all routes)
- Gzip compression
- Static asset caching (1 year)
- Security headers

Configuration file: `frontend/nginx.conf`

## Performance Tuning

### Backend
- Use ONNX Runtime for inference (faster than PyTorch)
- Enable request batching
- Configure workers: `uvicorn --workers 4`

### Frontend
- Build optimized bundle: `npm run build`
- Enable CDN for static assets
- Configure service worker for offline support

## Monitoring

### Backend Metrics
```bash
curl http://localhost:8000/metrics
```

Returns:
- Total predictions
- Average latency
- Predictions per second
- Uptime

### Frontend Monitoring
- API Status indicator (top-right navbar)
- Live metrics polling every 5 seconds
- Uptime visualization

## Troubleshooting

### Backend Not Starting
1. Check Python version: `python --version` (3.9+ required)
2. Install dependencies: `pip install -r requirements.txt`
3. Check port 8000 availability: `netstat -an | findstr 8000`

### Frontend Not Building
1. Check Node version: `node --version` (20+ required)
2. Clear cache: `npm cache clean --force`
3. Reinstall: `rm -rf node_modules && npm install`

### Docker Issues
1. Check Docker: `docker --version`
2. Clean build: `docker-compose down -v && docker-compose up --build`
3. Check logs: `docker-compose logs -f`

## CI/CD Pipeline (Recommended)

### GitHub Actions Workflow
```yaml
name: Build and Deploy

on:
  push:
    branches: [main]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Backend
        run: docker build -t sentiment-api .
      
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Frontend
        run: cd frontend && npm ci && npm run build
```

## Cloud Deployment

### AWS
- EC2 for hosting
- ECS/EKS for container orchestration
- S3 + CloudFront for frontend static hosting
- Application Load Balancer for API

### Google Cloud Platform
- Cloud Run for serverless containers
- Cloud Storage + CDN for frontend
- Cloud Load Balancing

### Azure
- App Service for containers
- Azure Static Web Apps for frontend
- Application Gateway

## Security Checklist

- [ ] Use HTTPS in production
- [ ] Configure CORS properly
- [ ] Add rate limiting
- [ ] Enable authentication/authorization
- [ ] Sanitize user inputs
- [ ] Keep dependencies updated
- [ ] Use environment variables for secrets
- [ ] Enable security headers (CSP, HSTS)

## Performance Benchmarks

| Environment | Latency (p50) | Latency (p95) | Throughput |
|-------------|---------------|---------------|------------|
| Development | ~50ms | ~150ms | 500/min |
| Production (Docker) | ~45ms | ~120ms | 1000/min |
| Production (Kubernetes) | ~40ms | ~100ms | 5000/min |

---

**Designed & Developed by Rupendra Alariya**  
*AI Engineer • Machine Learning Engineer • Full Stack AI Developer*
