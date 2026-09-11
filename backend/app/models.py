"""
Pydantic models for API request/response schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum

class AnalysisType(str, Enum):
    VIDEO_TO_VIDEO = "video-to-video"
    PHOTO_TO_VIDEO = "photo-to-video"

class AnalysisStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class FileInfo(BaseModel):
    name: str = Field(..., description="Original filename")
    size: int = Field(..., description="File size in bytes")
    type: str = Field(..., description="MIME type")
    path: Optional[str] = Field(None, description="Internal file path")

class AnalysisRequest(BaseModel):
    id: str = Field(..., description="Unique analysis ID")
    type: AnalysisType = Field(..., description="Type of analysis")
    reference_file: FileInfo = Field(..., description="Reference file information")
    target_file: FileInfo = Field(..., description="Target file information")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Analysis parameters")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AnalysisResponse(BaseModel):
    analysis_id: str = Field(..., description="Unique analysis ID")
    status: AnalysisStatusEnum = Field(..., description="Current status")
    message: str = Field(..., description="Status message")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in seconds")

class ManipulatedRegion(BaseModel):
    region: str = Field(..., description="Facial region name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    frame_index: int = Field(..., description="Frame index where detected")

class TimelineFrame(BaseModel):
    frame_index: int = Field(..., description="Frame index")
    timestamp: float = Field(..., description="Timestamp in seconds")
    is_manipulated: bool = Field(..., description="Whether frame is manipulated")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")

class EvidenceItem(BaseModel):
    type: str = Field(..., description="Evidence type")
    frame_index: int = Field(..., description="Frame index")
    region: str = Field(..., description="Affected region")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    description: str = Field(..., description="Evidence description")

class AnalysisResults(BaseModel):
    deepfake_score: float = Field(..., ge=0.0, le=1.0, description="Overall deepfake score")
    total_frames: int = Field(..., description="Total number of frames analyzed")
    glitch_frames: int = Field(..., description="Number of glitch frames detected")
    manipulated_regions: List[ManipulatedRegion] = Field(default_factory=list)
    timeline: List[TimelineFrame] = Field(default_factory=list)
    evidence: List[EvidenceItem] = Field(default_factory=list)

class AnalysisStatus(BaseModel):
    id: str = Field(..., description="Analysis ID")
    status: AnalysisStatusEnum = Field(..., description="Current status")
    progress: float = Field(0.0, ge=0.0, le=100.0, description="Progress percentage")
    current_step: Optional[str] = Field(None, description="Current processing step")
    created_at: datetime = Field(..., description="Creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    results: Optional[AnalysisResults] = Field(None, description="Analysis results when completed")

class CompleteAnalysis(BaseModel):
    id: str = Field(..., description="Analysis ID")
    type: AnalysisType = Field(..., description="Analysis type")
    status: AnalysisStatusEnum = Field(..., description="Current status")
    progress: float = Field(..., description="Progress percentage")
    created_at: datetime = Field(..., description="Creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    
    # Input files
    reference_file: FileInfo = Field(..., description="Reference file info")
    target_file: FileInfo = Field(..., description="Target file info")
    
    # Results (only when completed)
    results: Optional[AnalysisResults] = Field(None, description="Analysis results")

class AnalysisList(BaseModel):
    analyses: List[CompleteAnalysis] = Field(default_factory=list)
    total: int = Field(..., description="Total number of analyses")
    limit: int = Field(..., description="Results limit")
    offset: int = Field(..., description="Results offset")