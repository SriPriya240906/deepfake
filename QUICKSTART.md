# 🚀 Phase 1 - Quick Start Guide

## What You Have

A professional deepfake forensic analysis platform with:
- ✅ **Next.js Frontend** - Beautiful, responsive UI
- ✅ **FastAPI Backend** - RESTful API with analysis endpoints
- ✅ **Mock Analysis Engine** - Simulates deepfake detection in Phase 1
- ✅ **Existing Python Modules** - All preserved and ready for Phase 2

## Current Status

### 🟢 Running Now
```
Frontend: http://localhost:3000
Backend:  http://127.0.0.1:8000
```

### 📊 What's Ready to Use
1. **Landing Page** - Professional forensic branding
2. **Video-to-Video Analysis** - Upload 2 videos, get comparison results
3. **Photo-to-Video Analysis** - Upload photo + video, get verification
4. **Results Dashboard** - Timeline, face analysis, evidence panels
5. **API Documentation** - http://127.0.0.1:8000/docs

## How to Use

### 1. Upload Files
- Go to http://localhost:3000
- Click "Start Analysis"
- Choose analysis mode
- Upload files (drag & drop or click)

### 2. Watch Processing
- See 6-stage pipeline animation
- Real-time progress tracking
- Processing steps: Extract → Landmarks → Tracking → Artifacts → Fragments → Report

### 3. View Results
- Deepfake score (0-100%)
- Risk assessment
- Timeline with frame-by-frame breakdown
- Face analysis with manipulation regions
- Detailed forensic evidence

### 4. Start Another Analysis
- Click "New Analysis" to reset
- System clears and waits for next upload

## File Structure

```
frontend/          - Next.js application
  ├── src/
  │   ├── app/        - Pages and routing
  │   ├── components/ - Reusable UI components
  │   └── lib/        - Utilities and API client
  └── package.json

backend/           - FastAPI application
  ├── app/
  │   ├── models.py     - API schemas
  │   ├── services.py   - Business logic
  │   └── config.py     - Settings
  ├── main.py         - FastAPI app
  └── requirements.txt

Original modules (untouched):
  ├── app.py           - Streamlit UI (preserved)
  ├── main.py          - CLI interface (preserved)
  └── [forensic modules]
```

## Key Files Modified

Only these files were changed for Phase 1:
- `backend/requirements.txt` - Added FastAPI dependencies
- `frontend/package.json` - Added React/TypeScript packages
- All other files either newly created or completely preserved

## Troubleshooting

### Frontend not loading?
```powershell
cd frontend
npm install
npm run dev
```

### Backend not starting?
```powershell
cd backend
python -m pip install -r requirements.txt
python run_server.py
```

### Port already in use?
- Frontend default: 3000 → change with `PORT=3001 npm run dev`
- Backend default: 8000 → change host in run_server.py

## API Examples

### Start Video Analysis
```bash
curl -X POST http://127.0.0.1:8000/api/analyze/video \
  -F "reference_video=@video1.mp4" \
  -F "target_video=@video2.mp4"
```

### Get Analysis Status
```bash
curl http://127.0.0.1:8000/api/analysis/{analysis_id}/status
```

### View Results
```bash
curl http://127.0.0.1:8000/api/analysis/{analysis_id}
```

### API Documentation
Open http://127.0.0.1:8000/docs in browser

## Phase 2 Roadmap

Next phase will:
1. Connect to real forensic engine modules
2. Replace mock analysis with actual detection
3. Add database for persistent storage
4. Implement authentication
5. Deploy to production

## Success Indicators ✅

You should see:
- ✅ Professional landing page with forensic branding
- ✅ Smooth file upload experience
- ✅ Real-time processing animation
- ✅ Comprehensive results visualization
- ✅ Backend API responding to requests
- ✅ Graceful fallback when backend offline

## That's It! 🎉

Everything is set up and ready to use. The system provides a complete UI for forensic analysis while preserving all existing Python modules for integration in Phase 2.

Enjoy the professional deepfake forensic analysis platform!