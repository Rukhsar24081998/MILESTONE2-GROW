# 🚀 Complete Deployment Guide

This guide shows you how to deploy the Mutual Fund FAQ Assistant with:
- **Backend (FastAPI)** → Render.com
- **Frontend (HTML/CSS/JS)** → Vercel

---

## 📋 Prerequisites

1. GitHub account (already have: https://github.com/Rukhsar24081998/MILESTONE2-GROW)
2. Render.com account (free tier available)
3. Vercel account (already set up)
4. Groq API key (already have)

---

## 🔄 Step 1: Push Latest Changes to GitHub

```bash
cd "/Users/rukhsarkhan/Mileston2 "
git add -A
git commit -m "feat: Prepare for Render + Vercel deployment

- Add requirements-deploy.txt for backend dependencies
- Add Procfile for Render deployment
- Update UI to use Render backend URL in production"
git push origin main
```

---

## 🖥️ Step 2: Deploy Backend to Render.com

### 2.1 Create Render Account
1. Go to: https://render.com
2. Sign up with GitHub
3. Click **"+ New"** → **"Web Service"**

### 2.2 Configure Web Service

**Connect Repository:**
- Select: `Rukhsar24081998/MILESTONE2-GROW`
- Click **Connect**

**Settings:**
- **Name**: `milestone2-groww-backend`
- **Region**: Choose closest to you (e.g., Oregon, Frankfurt)
- **Branch**: `main`
- **Root Directory**: Leave blank (root of repo)
- **Runtime**: `Python 3`

**Build Command:**
```bash
pip install -r requirements-deploy.txt
```

**Start Command:**
```bash
uvicorn app.api.main:app --host 0.0.0.0 --port $PORT
```

### 2.3 Add Environment Variables

Click **"Advanced"** → **"Add Environment Variable"**:

| Variable | Value |
|----------|-------|
| `GROQ_API_KEY` | `your_groq_api_key_here` |
| `LLM_PROVIDER` | `groq` |
| `LLM_MODEL` | `llama-3.3-70b-versatile` |
| `LLM_TEMPERATURE` | `0.1` |
| `LLM_MAX_TOKENS` | `300` |
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` |

### 2.4 Deploy

Click **"Create Web Service"**

**Wait for deployment** (5-10 minutes for first build)

**Your backend URL will be:**
```
https://milestone2-groww-backend.onrender.com
```

### 2.5 Test Backend

```bash
# Health check
curl https://milestone2-groww-backend.onrender.com/health

# Test API
curl -X POST https://milestone2-groww-backend.onrender.com/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the expense ratio of HDFC Mid Cap Fund?"}'
```

---

## 🌐 Step 3: Update Frontend with Backend URL

Once backend is deployed on Render:

1. Copy your Render backend URL (e.g., `https://milestone2-groww-backend.onrender.com`)

2. Update `ui/index.html`:
```javascript
const API_BASE = window.location.hostname === 'localhost' 
  ? 'http://localhost:8000' 
  : 'https://milestone2-groww-backend.onrender.com';  // ← Update this
```

3. Commit and push:
```bash
git add ui/index.html
git commit -m "update: Set Render backend URL for production"
git push origin main
```

---

## 🎨 Step 4: Deploy Frontend to Vercel

### 4.1 Update Vercel Configuration

Since backend is now on Render, update `vercel.json` to serve only static files:

```json
{
  "name": "milestone2-groww",
  "version": 2,
  "builds": [
    {
      "src": "ui/index.html",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "ui/index.html"
    }
  ]
}
```

### 4.2 Deploy to Vercel

**Option A: Using Vercel Dashboard**
1. Go to: https://vercel.com/dashboard
2. Find your project: `milestone2-groww`
3. Go to **Settings** → **General**
4. Update configuration or redeploy

**Option B: Using CLI**
```bash
cd "/Users/rukhsarkhan/Mileston2 "
npx vercel --prod
```

**Your frontend URL:**
```
https://milestone2-groww.vercel.app
```

---

## ✅ Step 5: Verify Full Stack

### Test the complete flow:

1. **Open Frontend**: https://milestone2-groww.vercel.app
2. **Ask a question**: "What is the expense ratio of HDFC Mid Cap Fund?"
3. **Verify**: Answer should come from Render backend with Groq LLM

### Test API directly:

```bash
# Frontend
curl https://milestone2-groww.vercel.app

# Backend
curl https://milestone2-groww-backend.onrender.com/health

# Full Q&A
curl -X POST https://milestone2-groww-backend.onrender.com/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the NAV of HDFC Small Cap Fund?"}'
```

---

## 🔧 Troubleshooting

### Backend Issues

**Problem**: Backend not starting
```bash
# Check logs on Render dashboard
# Go to: Render Dashboard → Your Service → Logs
```

**Problem**: Missing dependencies
```bash
# Ensure all dependencies are in requirements-deploy.txt
pip freeze > requirements-deploy.txt
```

**Problem**: Groq API errors
```bash
# Verify environment variable is set on Render
# Check: Render Dashboard → Environment tab
```

### Frontend Issues

**Problem**: CORS errors
- Backend already has CORS middleware enabled
- Should allow all origins in production

**Problem**: API not responding
- Check browser console for errors
- Verify backend URL in `ui/index.html` is correct

---

## 📊 Architecture Overview

```
User Browser
    ↓
https://milestone2-groww.vercel.app (Frontend - Vercel)
    ↓
https://milestone2-groww-backend.onrender.com (Backend - Render)
    ↓
├── FastAPI Server
├── Groq LLM (llama-3.3-70b-versatile)
├── ChromaDB (Vector Store)
└── BGE Embeddings
```

**Request Flow:**
1. User opens Vercel URL
2. Frontend loads (HTML/CSS/JS)
3. User asks question
4. Frontend sends POST to Render backend `/api/ask`
5. Backend:
   - Retrieves context from ChromaDB
   - Sends to Groq LLM
   - Returns answer with citation
6. Frontend displays answer

---

## 💰 Cost Breakdown

| Service | Plan | Cost |
|---------|------|------|
| **Render** | Free Tier | $0/month (750 hrs) |
| **Vercel** | Hobby Plan | $0/month |
| **Groq API** | Free Tier | $0/month (rate limited) |
| **Total** | | **$0/month** 🎉 |

---

## 🚀 Alternative: Deploy Backend on Railway

If you prefer Railway over Render:

### Railway Setup:
1. Go to: https://railway.app
2. Sign in with GitHub
3. **New Project** → **Deploy from GitHub repo**
4. Select: `Rukhsar24081998/MILESTONE2-GROW`
5. Add environment variables (same as Render)
6. Deploy!

**Railway advantages:**
- $5 free credit/month
- Faster cold starts than Render
- Better for always-on services

---

## 🔄 Auto-Deploy on Push

Both Render and Vercel are connected to GitHub:

```bash
# Any push to main branch auto-deploys
git push origin main

# Render: Auto-deploys backend
# Vercel: Auto-deploys frontend
```

---

## 📝 Summary Checklist

- [ ] Push code to GitHub
- [ ] Create Render web service
- [ ] Add environment variables on Render
- [ ] Deploy backend on Render
- [ ] Test backend API
- [ ] Update `ui/index.html` with Render URL
- [ ] Update `vercel.json` for static-only
- [ ] Deploy frontend on Vercel
- [ ] Test complete flow
- [ ] Share your live URLs! 🎉

---

## 🎯 Final URLs

**Frontend**: https://milestone2-groww.vercel.app  
**Backend**: https://milestone2-groww-backend.onrender.com  
**API Docs**: https://milestone2-groww-backend.onrender.com/docs  
**Health Check**: https://milestone2-groww-backend.onrender.com/health

---

**Need help?** Check the logs on Render dashboard or Vercel deployment logs!
