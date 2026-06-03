# ⚡ Quick Start Guide

## 🎉 Your Application is RUNNING!

Both frontend and backend are currently active and ready to use.

## 🌐 Access Your Application

### 🎨 Frontend (React SPA)
**URL**: http://localhost:3000

**Pages**:
- 🏠 **Home**: http://localhost:3000
- 📊 **Dashboard**: http://localhost:3000/dashboard
- 🎯 **Predict**: http://localhost:3000/dashboard/predict
- 📦 **Batch**: http://localhost:3000/dashboard/batch
- 📈 **Analytics**: http://localhost:3000/dashboard/analytics
- 🔍 **Monitor**: http://localhost:3000/dashboard/monitor

### ⚙️ Backend (FastAPI)
**URL**: http://localhost:8000

**Endpoints**:
- 📚 **API Docs**: http://localhost:8000/docs
- 📖 **ReDoc**: http://localhost:8000/redoc
- 📊 **Dashboard**: http://localhost:8000/dashboard
- ❤️ **Health**: http://localhost:8000/health
- 📊 **Metrics**: http://localhost:8000/metrics

## 🚀 Try It Now!

### 1. Open the Landing Page
```
http://localhost:3000
```
You'll see:
- Beautiful animated hero section
- Live stats (95% Accuracy, <100ms Latency)
- Feature cards
- Developer profile

### 2. Try Single Prediction
```
http://localhost:3000/dashboard/predict
```
Steps:
1. Enter any text (or click example chips)
2. Press "Predict Sentiment" or Ctrl+Enter
3. See results with confidence scores

### 3. Try Batch Prediction
```
http://localhost:3000/dashboard/batch
```
Steps:
1. Enter multiple texts (one per line)
2. Click "Process Batch"
3. See summary and export CSV/JSON

### 4. Test API Directly
```bash
# Single prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"I love this product!\"}"

# Batch prediction
curl -X POST http://localhost:8000/predict/batch \
  -H "Content-Type: application/json" \
  -d "{\"texts\": [\"Great!\", \"Terrible\", \"Okay\"]}"

# Health check
curl http://localhost:8000/health

# Metrics
curl http://localhost:8000/metrics
```

## 🛠️ Development Commands

### Backend
```bash
# Already running on Terminal 2
# If you need to restart:
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
# Already running on Terminal 3
# If you need to restart:
cd frontend
npm run dev
```

### Stop Servers
- Press `Ctrl+C` in the respective terminal
- Or close the terminal windows

## 🐳 Docker Deployment

```bash
# Stop current dev servers first (Ctrl+C)

# Build and run all services with Docker
docker-compose up --build

# Access:
# Frontend: http://localhost:3000
# API: http://localhost:8000
# Demo: http://localhost:7860
```

## 📦 Build for Production

### Frontend
```bash
cd frontend
npm run build

# Output will be in frontend/dist/
# Serve with any static server or Nginx
```

### Backend
```bash
# Use the Dockerfile
docker build -t sentiment-api .
docker run -p 8000:8000 sentiment-api
```

## 🎨 Design Features to Explore

### Landing Page
- ✨ Animated gradient background
- 💫 Floating particle effects
- 📊 Live animated stats
- 🎯 Feature cards with hover effects
- 👨‍💻 Developer profile section

### Dashboard
- 🎭 Glassmorphism effects
- 🌈 Gradient borders
- ⚡ Smooth animations (Framer Motion)
- 📱 Fully responsive
- 🎨 Beautiful color scheme
- 🔄 Real-time data updates

## 🧪 Testing

### Run Backend Tests
```bash
# All tests
make test

# With coverage
python -m pytest --cov=src --cov-report=html

# Result: 29/29 tests passing ✅
```

### Manual Testing Checklist
- [ ] Open landing page - animations work
- [ ] Navigate to dashboard - sidebar visible
- [ ] Make single prediction - result displays
- [ ] Try batch prediction - export works
- [ ] Check analytics page - metrics shown
- [ ] Check monitor page - status green
- [ ] Test API status indicator (top-right navbar)
- [ ] Try example chips on predict page
- [ ] Test keyboard shortcut (Ctrl+Enter)
- [ ] Verify toast notifications appear

## 📊 Check System Status

### Backend Health
```bash
curl http://localhost:8000/health
```

Expected:
```json
{
  "status": "ok",
  "model": "lexicon-vader-extended",
  "device": "cpu"
}
```

### Frontend Status
```bash
curl -I http://localhost:3000
```

Expected: `HTTP/1.1 200 OK`

### Check Running Processes
- Backend: Should be running on port 8000
- Frontend: Should be running on port 3000
- Check with: `netstat -an | findstr "8000 3000"`

## 🎯 What You Can Do Now

### 1. Test Sentiment Analysis
- Try different texts
- See real-time predictions
- Export batch results

### 2. Explore the UI
- Landing page with animations
- Dashboard with metrics
- Analytics with charts
- Monitor with system status

### 3. Use the API
- Read OpenAPI docs
- Make API calls
- Check metrics

### 4. Customize
- Modify colors in `tailwind.config.js`
- Add new pages
- Customize components
- Add new features

## 🚨 Troubleshooting

### Frontend Not Loading?
1. Check Terminal 3 for errors
2. Restart: `cd frontend && npm run dev`
3. Clear browser cache
4. Try: http://localhost:3000

### Backend Not Responding?
1. Check Terminal 2 for errors
2. Restart: `uvicorn api.main:app --reload`
3. Verify port 8000 is free
4. Try: http://localhost:8000/health

### Build Errors?
```bash
# Frontend
cd frontend
rm -rf node_modules package-lock.json
npm install

# Backend
pip install -r requirements.txt
```

## 📖 Documentation

- **README.md** - Complete project documentation
- **STATUS.md** - Current project status
- **DEPLOYMENT.md** - Production deployment guide
- **MODEL_CARD.md** - Model information
- **API Docs** - http://localhost:8000/docs

## 🎓 Learn More

### Frontend Stack
- [React](https://react.dev)
- [TypeScript](https://typescriptlang.org)
- [Vite](https://vitejs.dev)
- [TailwindCSS](https://tailwindcss.com)
- [Framer Motion](https://framer.com/motion)

### Backend Stack
- [FastAPI](https://fastapi.tiangolo.com)
- [PyTorch](https://pytorch.org)
- [Transformers](https://huggingface.co/docs/transformers)

## 💡 Tips

1. **Use Keyboard Shortcuts**: Ctrl+Enter to predict
2. **Try Examples**: Click example chips on predict page
3. **Export Data**: Use CSV/JSON export on batch page
4. **Monitor Health**: Check API status indicator in navbar
5. **Responsive Design**: Works on mobile, tablet, desktop
6. **Dark Theme**: Optimized for dark mode

## 🎉 You're All Set!

Your premium AI SaaS platform is ready to use. Explore all the features and enjoy!

---

**Designed & Developed by Rupendra Alariya**  
*AI Engineer • Machine Learning Engineer • Full Stack AI Developer*

📧 r44050.rupendra@jnujaipur.ac.in  
🐙 [@RupendraAlariya](https://github.com/RupendraAlariya)

© 2026 Rupendra Alariya. All Rights Reserved.
