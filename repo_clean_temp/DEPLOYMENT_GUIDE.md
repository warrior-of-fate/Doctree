# Deployment Guide

This guide walks through deploying the pdf-topic-scanner project to production environments.

## Architecture Overview

- **Frontend:** Next.js app → Vercel (recommended)
- **Backend:** FastAPI server → Render, Railway, or AWS (recommended)
- **Database & Cache:** Optional; currently uses in-memory processing

---

## Frontend Deployment (Vercel)

### Prerequisites
- GitHub account
- Vercel account (free tier available)

### Steps

1. **Push to GitHub**
   ```bash
   git push origin main
   ```

2. **Connect GitHub to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import your GitHub repository (`death-by-love/pdf-`)
   - Select your repository and click "Import"

3. **Configure Build Settings**
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build` (Vercel auto-detects Next.js)
   - **Output Directory:** `.next`
   - **Install Command:** `npm ci`

4. **Add Environment Variables** (if needed)
   In Vercel dashboard → Settings → Environment Variables:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-url.com
   ```

5. **Deploy**
   - Click "Deploy"
   - Vercel will build and deploy your frontend automatically
   - Your frontend URL will be provided (e.g., `https://pdf-topic-scanner.vercel.app`)

### Continuous Deployment
- Every push to `main` automatically triggers a new deployment
- Preview deployments created for pull requests

---

## Backend Deployment (Render or Railway)

### Option A: Render

#### Prerequisites
- Render account (free tier available at [render.com](https://render.com))
- GitHub connected to Render

#### Steps

1. **Create a New Service**
   - Log in to Render dashboard
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure the Service**
   - **Name:** `pdf-topic-scanner-backend`
   - **Environment:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn src.api.server:app --host 0.0.0.0 --port 8000`

3. **Set Environment Variables** (optional)
   - **PYTHONUNBUFFERED:** `1`
   - Any custom environment variables your app needs

4. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy your backend
   - Your backend URL will be provided (e.g., `https://pdf-topic-scanner-backend.onrender.com`)

5. **Update Frontend**
   - Go back to Vercel dashboard
   - Settings → Environment Variables
   - Update `NEXT_PUBLIC_API_URL` to your Render backend URL
   - Trigger a redeploy on Vercel

### Option B: Railway

#### Prerequisites
- Railway account (free tier available at [railway.app](https://railway.app))
- GitHub connected to Railway

#### Steps

1. **Create a New Project**
   - Log in to Railway dashboard
   - Click "Create New Project"
   - Select "Deploy from GitHub Repo"

2. **Select Repository**
   - Choose your `pdf-` repository
   - Railway will auto-detect Python and create a service

3. **Configure the Service**
   - Go to "Variables" tab
   - Set `PYTHONUNBUFFERED=1`

4. **Configure Deployment**
   - Go to "Settings" tab
   - **Start Command:** `uvicorn src.api.server:app --host 0.0.0.0 --port $PORT`
   - Railway automatically assigns `$PORT` environment variable

5. **Deploy**
   - Railway will automatically build and deploy
   - Your backend URL will be provided in the "Deployments" tab
   - Click on your deployment to get the live URL

6. **Update Frontend**
   - Go back to Vercel dashboard
   - Settings → Environment Variables
   - Update `NEXT_PUBLIC_API_URL` to your Railway backend URL
   - Trigger a redeploy on Vercel

---

## Environment Variables

### Frontend (Vercel)
```env
# .env.local (local development)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Vercel production
NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

### Backend (Render/Railway)
```env
# Environment variables (if needed)
PYTHONUNBUFFERED=1
MAX_FILE_SIZE=524288000  # 500MB in bytes
```

---

## Testing the Deployment

After deploying both frontend and backend:

1. **Test Frontend**
   ```bash
   curl https://your-vercel-url.vercel.app/
   # Should return Next.js HTML
   ```

2. **Test Backend**
   ```bash
   curl https://your-backend-url.com/docs
   # Should return Swagger UI or OpenAPI spec
   ```

3. **Test Integration**
   - Open your Vercel frontend URL in a browser
   - Upload a test PDF file
   - Verify the response returns a valid hierarchy

---

## Performance Considerations

### Frontend
- Vercel provides edge caching and automatic GZIP compression
- CDN delivers content from nearest edge location
- Next.js Image Optimization (if used) is handled automatically

### Backend
- Consider adding a Redis cache layer for frequently processed PDFs
- Enable request rate limiting (see `src/api/server.py`)
- Monitor CPU and memory usage; scale if needed:
  - **Render:** Edit service → Scaling → increase instances
  - **Railway:** Edit service → increase RAM/CPU

### Database (Future)
- For production, consider adding PostgreSQL or MongoDB
- Render and Railway both offer managed database services
- Use environment variables to pass connection strings

---

## Troubleshooting

### Frontend Not Loading
- Check Vercel logs: Dashboard → Deployments → Logs
- Ensure `NEXT_PUBLIC_API_URL` is set correctly
- Verify backend is running and accessible

### Backend Returning 502/503
- Check Render/Railway logs
- Ensure all Python dependencies installed (`pip install -r requirements.txt`)
- Check startup command syntax

### CORS Issues
- If frontend can't reach backend, update CORS settings in `src/api/server.py`
- Current setup allows all origins; secure for production:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["https://your-vercel-url.vercel.app"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```

### Large PDF Uploads Timeout
- Increase timeout settings in Vercel/Railway dashboard
- Check `MAX_FILE_SIZE` in backend (default: 500MB)
- Consider using S3 for file uploads instead of direct upload

---

## Monitoring & Logs

### Vercel
- Dashboard → Deployments → select deployment → Logs
- Real-time request logs and error tracking

### Render
- Dashboard → select service → Logs tab
- Real-time application output and error messages

### Railway
- Dashboard → select project → Logs tab
- Real-time deployment logs and metrics

---

## Scaling

### Horizontal Scaling
- **Vercel:** Automatic; no additional setup needed
- **Render (Pro):** Edit service → Scale to multiple instances
- **Railway:** Increase RAM/CPU in service settings; can add replicas

### Database Scaling (Future)
- Render: Managed PostgreSQL with automatic backups
- Railway: MySQL/PostgreSQL services; easy horizontal scaling

---

## Security Checklist

- [ ] CORS origins restricted to your frontend domain
- [ ] Environment variables stored securely (not in code)
- [ ] API endpoint validation and input sanitization in place
- [ ] Rate limiting enabled on backend
- [ ] HTTPS enforced (automatic on Vercel/Render/Railway)
- [ ] API keys/secrets never committed to git (use `.env` and `.gitignore`)

---

## Cost Estimation

### Vercel (Frontend)
- **Free tier:** Up to 100GB bandwidth/month
- **Pro:** $20/month + overage costs

### Render (Backend)
- **Free tier:** Limited CPU/RAM, auto-sleeps after inactivity
- **Standard:** $7/month per service + bandwidth

### Railway (Backend)
- **Pay-as-you-go:** $5 free credit/month, then usage-based pricing
- Competitive for high-traffic workloads

---

## Next Steps

1. **Push to GitHub** and authenticate with your credentials
2. **Deploy Frontend** to Vercel
3. **Deploy Backend** to Render or Railway
4. **Update Environment Variables** for API connectivity
5. **Test** end-to-end integration
6. **Set up CI/CD** (GitHub Actions already configured)
7. **Monitor** logs and performance metrics
