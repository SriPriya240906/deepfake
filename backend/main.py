"""
FastAPI Backend for Deepfake Forensic Analysis

This backend serves as an API layer for the existing Python forensic engine.
It provides endpoints for file upload, analysis processing, and result retrieval.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import uuid
import json
import asyncio
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from app.models import AnalysisRequest, AnalysisResponse, AnalysisStatus
from app.services import AnalysisService
from app.config import settings

# Create FastAPI app
app = FastAPI(
    title="Deepfake Forensic Analysis API",
    description="Professional deepfake detection and forensic analysis backend",
    version="1.0.0"
)

# Add CORS middleware to allow frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
analysis_service = AnalysisService()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Deepfake Forensic Analysis API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "analysis_engine": "operational",
            "file_storage": "operational"
        }
    }

@app.post("/api/analyze/video", response_model=AnalysisResponse)
async def analyze_video_to_video(
    background_tasks: BackgroundTasks,
    reference_video: UploadFile = File(..., description="Original/reference video file"),
    target_video: UploadFile = File(..., description="Suspected deepfake video file"),
    displacement_threshold: float = Form(10.0, description="Landmark displacement threshold"),
    diff_threshold: int = Form(20, description="Pixel difference threshold"),
    ssim_threshold: float = Form(0.85, description="SSIM threshold")
):
    """
    Start video-to-video deepfake analysis
    
    Compares two videos frame-by-frame to detect manipulation artifacts
    """
    try:
        # Validate file types
        allowed_video_types = ["video/mp4", "video/avi", "video/mov"]
        
        if reference_video.content_type not in allowed_video_types:
            raise HTTPException(status_code=400, detail="Reference video must be MP4, AVI, or MOV format")
        
        if target_video.content_type not in allowed_video_types:
            raise HTTPException(status_code=400, detail="Target video must be MP4, AVI, or MOV format")
        
        # Create analysis request
        analysis_id = str(uuid.uuid4())
        
        # Save uploaded files
        reference_path = await analysis_service.save_upload_file(reference_video, analysis_id, "reference")
        target_path = await analysis_service.save_upload_file(target_video, analysis_id, "target")
        
        # Create analysis record
        analysis_request = AnalysisRequest(
            id=analysis_id,
            type="video-to-video",
            reference_file={
                "name": reference_video.filename,
                "size": reference_video.size,
                "type": reference_video.content_type,
                "path": reference_path
            },
            target_file={
                "name": target_video.filename,
                "size": target_video.size,
                "type": target_video.content_type,
                "path": target_path
            },
            parameters={
                "displacement_threshold": displacement_threshold,
                "diff_threshold": diff_threshold,
                "ssim_threshold": ssim_threshold
            }
        )
        
        # Store analysis request
        await analysis_service.store_analysis_request(analysis_request)
        
        # Start background analysis
        background_tasks.add_task(
            analysis_service.process_video_analysis,
            analysis_id,
            reference_path,
            target_path,
            {
                "displacement_threshold": displacement_threshold,
                "diff_threshold": diff_threshold,
                "ssim_threshold": ssim_threshold
            }
        )
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            status="pending",
            message="Video analysis started successfully",
            estimated_duration=180  # 3 minutes
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start analysis: {str(e)}")

@app.post("/api/analyze/photo-video", response_model=AnalysisResponse)
async def analyze_photo_to_video(
    background_tasks: BackgroundTasks,
    reference_photo: UploadFile = File(..., description="Reference photo of person"),
    target_video: UploadFile = File(..., description="Suspected deepfake video file"),
    displacement_threshold: float = Form(10.0, description="Landmark displacement threshold"),
    diff_threshold: int = Form(20, description="Pixel difference threshold"),
    ssim_threshold: float = Form(0.85, description="SSIM threshold")
):
    """
    Start photo-to-video deepfake analysis
    
    Verifies person identity and detects manipulation in video
    """
    try:
        # Validate file types
        allowed_image_types = ["image/jpeg", "image/jpg", "image/png"]
        allowed_video_types = ["video/mp4", "video/avi", "video/mov"]
        
        if reference_photo.content_type not in allowed_image_types:
            raise HTTPException(status_code=400, detail="Reference photo must be JPG or PNG format")
        
        if target_video.content_type not in allowed_video_types:
            raise HTTPException(status_code=400, detail="Target video must be MP4, AVI, or MOV format")
        
        # Create analysis request
        analysis_id = str(uuid.uuid4())
        
        # Save uploaded files
        reference_path = await analysis_service.save_upload_file(reference_photo, analysis_id, "reference")
        target_path = await analysis_service.save_upload_file(target_video, analysis_id, "target")
        
        # Create analysis record
        analysis_request = AnalysisRequest(
            id=analysis_id,
            type="photo-to-video",
            reference_file={
                "name": reference_photo.filename,
                "size": reference_photo.size,
                "type": reference_photo.content_type,
                "path": reference_path
            },
            target_file={
                "name": target_video.filename,
                "size": target_video.size,
                "type": target_video.content_type,
                "path": target_path
            },
            parameters={
                "displacement_threshold": displacement_threshold,
                "diff_threshold": diff_threshold,
                "ssim_threshold": ssim_threshold
            }
        )
        
        # Store analysis request
        await analysis_service.store_analysis_request(analysis_request)
        
        # Start background analysis
        background_tasks.add_task(
            analysis_service.process_photo_analysis,
            analysis_id,
            reference_path,
            target_path,
            {
                "displacement_threshold": displacement_threshold,
                "diff_threshold": diff_threshold,
                "ssim_threshold": ssim_threshold
            }
        )
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            status="pending",
            message="Photo-to-video analysis started successfully",
            estimated_duration=150  # 2.5 minutes
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start analysis: {str(e)}")

@app.get("/api/analysis/{analysis_id}/status", response_model=AnalysisStatus)
async def get_analysis_status(analysis_id: str):
    """
    Get the current status of an analysis
    """
    try:
        status = await analysis_service.get_analysis_status(analysis_id)
        if not status:
            raise HTTPException(status_code=404, detail="Analysis not found")
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analysis status: {str(e)}")

@app.get("/api/analysis/{analysis_id}")
async def get_analysis_results(analysis_id: str):
    """
    Get the complete results of an analysis
    """
    try:
        results = await analysis_service.get_analysis_results(analysis_id)
        if not results:
            raise HTTPException(status_code=404, detail="Analysis results not found")
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analysis results: {str(e)}")

@app.get("/api/analyses")
async def list_analyses(limit: int = 50, offset: int = 0):
    """
    List recent analyses
    """
    try:
        analyses = await analysis_service.list_analyses(limit=limit, offset=offset)
        return {
            "analyses": analyses,
            "total": len(analyses),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list analyses: {str(e)}")

@app.delete("/api/analysis/{analysis_id}")
async def delete_analysis(analysis_id: str):
    """
    Delete an analysis and its associated files
    """
    try:
        success = await analysis_service.delete_analysis(analysis_id)
        if not success:
            raise HTTPException(status_code=404, detail="Analysis not found")
        return {"message": "Analysis deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete analysis: {str(e)}")

if __name__ == "__main__":
    # Run the development server
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )