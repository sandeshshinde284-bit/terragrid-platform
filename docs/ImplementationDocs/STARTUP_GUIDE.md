# TerraGrid Startup Guide

## Default Ports Configuration

### Frontend (Vue + Vite)
- **Port:** `5174` (changed from 5173)
- **URL:** `http://localhost:5174`
- **Reason:** Allows running TerraGrid without stopping other applications on port 5173

### Backend (FastAPI)
- **Port:** `8000`
- **URL:** `http://localhost:8000`

### Database
- **Type:** PostgreSQL
- **Host:** localhost
- **Port:** 5432
- **Database:** terragrid_db

---

## How to Start TerraGrid

### Step 1: Start Backend
```bash
cd terragrid-platform
python -m backend.main
# or
python backend/main.py
```

**Expected Output:**
```
INFO:     Application startup complete.
🚀 TERRAGRID FASTAPI SERVER INITIALIZING
```

### Step 2: Start Frontend (in another terminal)
```bash
cd terragrid-platform/frontend
npm run dev
```

**Expected Output:**
```
VITE v8.3.0  ready in 245 ms

➜  Local:   http://localhost:5174/
➜  press h to show help
```

### Step 3: Access Application
- Open browser: `http://localhost:5174`
- You should see the **TerraGrid logo** in the browser tab (favicon)

---

## Port Configuration

### Change Frontend Port (if needed)
Edit `frontend/vite.config.ts`:
```typescript
server: {
  port: 5175,  // Change this number
  strictPort: false,
},
```

### Backend CORS Whitelist
The backend allows these frontend origins:
- `http://localhost:5173` (old, for other apps)
- `http://localhost:5174` (default TerraGrid)
- `http://localhost:5175` through `5179` (alternatives)
- `http://127.0.0.1:5173-5179`

---

## Favicon
- ✅ Logo now displays in browser tab
- **File:** `frontend/public/favicon.svg`
- **Updated:** `frontend/index.html` now correctly references the SVG favicon

---

## Security Notes

### What's Protected
- ✅ CORS restricted to localhost ports
- ✅ API endpoints require proper routing
- ✅ WebSocket connections authenticated

### What's NOT Protected (Phase 2)
- ⚠️ No rate limiting on API endpoints
- ⚠️ No input validation middleware
- ⚠️ No security headers (X-Frame-Options, etc.)
- ⚠️ Direct path access not restricted

**Next Steps:** Implement security middleware before production deployment

---

## Troubleshooting

### Port Already in Use
```bash
# Windows: Find process using port 5174
netstat -ano | findstr :5174

# Kill the process
taskkill /PID <PID> /F

# Or change port in vite.config.ts
```

### Favicon Not Showing
1. Clear browser cache (Ctrl+Shift+Delete)
2. Hard refresh (Ctrl+F5)
3. Verify `favicon.svg` exists in `frontend/public/`

### Backend Connection Refused
- Ensure backend is running on `http://localhost:8000`
- Check `.env` file has correct `DATABASE_URL`
- Verify PostgreSQL is running

---

## Recent Changes
- **Frontend Port:** Changed from 5173 → 5174
- **Favicon:** Updated to use SVG format
- **CORS:** Already supports 5174 (no changes needed)

