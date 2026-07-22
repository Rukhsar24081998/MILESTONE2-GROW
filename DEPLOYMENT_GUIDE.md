# 🚀 Complete Deployment Guide

This guide shows you how to deploy the Mutual Fund FAQ Assistant with:
- **Backend (FastAPI)** → Render.com (**free** web service)
- **Frontend (HTML/CSS/JS)** → Vercel

Railway is **not** used. The UI points at Render: `https://milestone2-groww-backend.onrender.com`.

**Free-tier notes:** 750 instance hours/month; spins down after ~15 minutes idle (~1 minute cold start on the next request).

---

## 📋 Prerequisites

1. GitHub account (already have: https://github.com/Rukhsar24081998/MILESTONE2-GROW)
2. Render.com account (free tier — no credit card required for free web services)
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

## 🖥️ Step 2: Deploy Backend to Render.com (free)

### Option A — Blueprint (recommended)

Repo includes `render.yaml` (free plan, Singapore region).

1. Push this repo to GitHub (`main`).
2. Open: https://dashboard.render.com/blueprints
3. **New Blueprint Instance** → select `Rukhsar24081998/MILESTONE2-GROW`
4. When prompted, set **`GROQ_API_KEY`** (required).
5. Apply. Service URL will be:
   ```
   https://milestone2-groww-backend.onrender.com
   ```

### Option B — Manual Web Service

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
- **Region**: Singapore (or closest)
- **Branch**: `main`
- **Root Directory**: Leave blank (root of repo)
- **Runtime**: `Python 3`
- **Instance type**: **Free**

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
| `LLM_MODEL` | `llama-3.1-8b-instant` |
| `LLM_TEMPERATURE` | `0.1` |
| `LLM_MAX_TOKENS` | `300` |
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` |

### 2.4 Deploy

Click **"Create Web Service"**

**Wait for deployment** (5-10 minutes for first build; torch/embeddings make the first build slow)

**Your backend URL will be:**
```
https://milestone2-groww-backend.onrender.com
```

### 2.5 Test Backend

```bash
# Health check (first request after idle may take ~1 min on free tier)
curl https://milestone2-groww-backend.onrender.com/health

# Test API
curl -X POST https://milestone2-groww-backend.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the expense ratio of Groww Nifty 50?"}'
```

### Remove old Railway backend

If a Railway service still exists in your Railway dashboard, delete it there (the app no longer calls Railway). No Railway config remains in this repo.

---

## 🌐 Step 3: Frontend API URL

`ui/index.html` already uses Render in production and `http://localhost:8000` on localhost. No change needed unless your Render service name differs — then update the production URL in `API_BASE`.

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
curl -X POST https://milestone2-groww-backend.onrender.com/ask \
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
├── Groq LLM (llama-3.1-8b-instant)
├── ChromaDB (Vector Store)
└── BGE Embeddings
```

**Request Flow:**
1. User opens Vercel URL
2. Frontend loads (HTML/CSS/JS)
3. User asks question
4. Frontend sends POST to Render backend `/ask`
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

- [ ] Push code to GitHub (includes `render.yaml` + Render `API_BASE`)
- [ ] Create Render free web service (Blueprint or manual)
- [ ] Set `GROQ_API_KEY` on Render
- [ ] Confirm `https://milestone2-groww-backend.onrender.com/health`
- [ ] Delete any leftover Railway service in the Railway dashboard
- [ ] Deploy frontend on Vercel
- [ ] Test complete chat flow (allow ~1 min cold start on free tier)

---

## 🎯 Final URLs

**Frontend**: https://milestone2-groww.vercel.app  
**Backend**: https://milestone2-groww-backend.onrender.com  
**API Docs**: https://milestone2-groww-backend.onrender.com/docs  
**Health Check**: https://milestone2-groww-backend.onrender.com/health

---

**Need help?** Check the logs on Render dashboard or Vercel deployment logs!
