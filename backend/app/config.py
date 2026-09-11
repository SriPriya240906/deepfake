"""
Configuration settings for the FastAPI backend
"""

import os
from pathlib import Path
from typing import List

class Settings:
    # API Configuration
    API_VERSION = "1.0.0"
    API_TITLE = "Deepfake Forensic Analysis API"
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # Next.js development server
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # Alternative port
        "http://127.0.0.1:3001",
    ]
    
    # File Upload Configuration
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    UPLOAD_DIR = Path("uploads")
    RESULTS_DIR = Path("results")
    
    # Analysis Configuration
    DEFAULT_DISPLACEMENT_THRESHOLD = 10.0
    DEFAULT_DIFF_THRESHOLD = 20
    DEFAULT_SSIM_THRESHOLD = 0.85
    
    # Forensic Engine Configuration (paths to existing Python modules)
    FORENSIC_ENGINE_ROOT = Path("..").resolve()  # Points to project root
    
    def __init__(self):
        # Create necessary directories
        self.UPLOAD_DIR.mkdir(exist_ok=True)
        self.RESULTS_DIR.mkdir(exist_ok=True)
        
        # Create subdirectories for organized storage
        (self.UPLOAD_DIR / "temp").mkdir(exist_ok=True)
        (self.RESULTS_DIR / "analyses").mkdir(exist_ok=True)

# Global settings instance
settings = Settings()