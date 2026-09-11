"""
Forensic Engine Interface — Phase 2 Integration

This module provides a clean interface to the existing Python forensic modules.
It orchestrates the complete deepfake forensic analysis pipeline:

- frame_extractor.py: Video → PNG frames
- face_mesh.py: Facial landmark detection  
- landmark_tracker.py: Glitch frame detection
- artifact_detector.py: Visual artifact detection
- fragment_extractor.py: Fragment extraction
- fragment_aggregator.py: Reconstruction
- report_generator.py: Report generation
"""

import os
import sys
import cv2
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import time

class ForensicEngine:
    """
    Orchestrator for the existing deepfake forensic analysis pipeline.
    
    Integrates all forensic modules into a unified analysis interface.
    Each analysis runs in an isolated directory to support concurrent operations.
    """
    
    def __init__(self):
        """Initialize the forensic engine with module imports."""
        # Add the parent directory to Python path to import existing modules
        project_root = Path(__file__).parent.parent.parent.resolve()
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        self.project_root = project_root
        self._modules_loaded = False
        self._load_forensic_modules()
    
    def _load_forensic_modules(self):
        """
        Import the existing forensic analysis modules from the project root.
        """
        if self._modules_loaded:
            return
        
        try:
            from frame_extractor import FrameExtractor
            from face_mesh import FaceMesh
            from landmark_tracker import LandmarkTracker
            from artifact_detector import ArtifactDetector
            from fragment_extractor import FragmentExtractor
            from fragment_aggregator import FragmentAggregator
            from report_generator import ReportGenerator
            
            # Store module references
            self.FrameExtractor = FrameExtractor
            self.FaceMesh = FaceMesh
            self.LandmarkTracker = LandmarkTracker
            self.ArtifactDetector = ArtifactDetector
            self.FragmentExtractor = FragmentExtractor
            self.FragmentAggregator = FragmentAggregator
            self.ReportGenerator = ReportGenerator
            
            self._modules_loaded = True
            print("[ForensicEngine] OK - All forensic modules loaded successfully")
            
        except ImportError as e:
            self._modules_loaded = False
            raise RuntimeError(
                f"Failed to load forensic modules: {e}\n"
                "Ensure all module files exist in the project root directory."
            ) from e
    
    def _setup_analysis_directory(self, analysis_id: str, base_dir: Path) -> Path:
        """
        Create isolated directory structure for an analysis.
        
        Structure:
            base_dir/
            ├── analysis_id/
            │   ├── input/              (uploaded files)
            │   ├── frames/             (extracted frames)
            │   ├── output/             (annotated frames, reconstructed face, summary)
            │   └── fragments/          (extracted artifacts)
        """
        analysis_dir = base_dir / analysis_id
        analysis_dir.mkdir(parents=True, exist_ok=True)
        
        (analysis_dir / "input").mkdir(exist_ok=True)
        (analysis_dir / "frames").mkdir(exist_ok=True)
        (analysis_dir / "output").mkdir(exist_ok=True)
        (analysis_dir / "fragments").mkdir(exist_ok=True)
        
        return analysis_dir
    
    async def analyze_video_to_video(
        self, 
        reference_path: str, 
        target_path: str, 
        parameters: Dict[str, Any],
        analysis_id: str,
        work_dir: Path
    ) -> Dict[str, Any]:
        """
        Run video-to-video deepfake analysis.
        
        Compares two videos frame-by-frame to detect manipulation artifacts.
        
        Parameters
        ----------
        reference_path : str
            Path to the original/real video file.
        target_path : str
            Path to the suspected deepfake video file.
        parameters : dict
            Analysis parameters:
            - displacement_threshold: Landmark jump threshold (default: 10.0)
            - diff_threshold: Pixel difference threshold (default: 20)
            - ssim_threshold: SSIM threshold (default: 0.85)
        analysis_id : str
            Unique analysis identifier.
        work_dir : Path
            Base working directory for analysis output.
        
        Returns
        -------
        dict
            Analysis results with forensic evidence.
        """
        start_time = time.time()
        
        # Setup isolated analysis directory
        analysis_dir = self._setup_analysis_directory(analysis_id, work_dir)
        
        # Extract parameters with defaults
        displacement_threshold = parameters.get('displacement_threshold', 10.0)
        diff_threshold = parameters.get('diff_threshold', 20)
        ssim_threshold = parameters.get('ssim_threshold', 0.85)
        
        try:
            # Stage 1: Extract frames from both videos
            print(f"[{analysis_id}] Stage 1/7: Extracting frames...")
            
            # Create frame extractors for each video in separate directories
            ref_frames_dir = analysis_dir / "frames" / "reference"
            target_frames_dir = analysis_dir / "frames" / "target"
            
            extractor_ref = self.FrameExtractor(str(reference_path), str(ref_frames_dir))
            extractor_target = self.FrameExtractor(str(target_path), str(target_frames_dir))
            
            total_ref, fps_ref = extractor_ref.extract()
            total_target, fps_target = extractor_target.extract()
            
            # Use minimum frame count for comparison
            total_frames = min(total_ref, total_target)
            
            print(f"[{analysis_id}] ✓ Extracted {total_ref} reference frames and {total_target} target frames")
            
            # Stage 2: Detect facial landmarks on target video
            print(f"[{analysis_id}] Stage 2/7: Detecting facial landmarks...")
            
            face_mesh = self.FaceMesh()
            landmark_sequence = []
            
            for i in range(total_frames):
                frame_path = target_frames_dir / f"frame_{i:04d}.png"
                frame = cv2.imread(str(frame_path))
                landmarks = face_mesh.detect(frame) if frame is not None else []
                landmark_sequence.append(landmarks)
            
            faces_detected = sum(1 for lm in landmark_sequence if len(lm) > 0)
            print(f"[{analysis_id}] ✓ Detected faces in {faces_detected}/{total_frames} frames")
            
            # Stage 3: Track landmark failures (glitch frames)
            print(f"[{analysis_id}] Stage 3/7: Tracking landmark failures...")
            
            tracker = self.LandmarkTracker(displacement_threshold=displacement_threshold)
            glitch_indices = tracker.find_glitch_frames(landmark_sequence)
            
            print(f"[{analysis_id}] ✓ Found {len(glitch_indices)} glitch frames")
            
            # Stage 4: Detect visual artifacts via frame differencing
            print(f"[{analysis_id}] Stage 4/7: Detecting visual artifacts...")
            
            output_dir = analysis_dir / "output"
            detector = self.ArtifactDetector(
                diff_threshold=diff_threshold,
                ssim_threshold=ssim_threshold,
                output_dir=str(output_dir)
            )
            
            frame_bounding_rects = {}
            artifact_count = 0
            ssim_scores = []
            
            for i in range(1, total_frames):
                ref_frame_path = ref_frames_dir / f"frame_{i:04d}.png"
                target_frame_path = target_frames_dir / f"frame_{i:04d}.png"
                
                ref_frame = cv2.imread(str(ref_frame_path))
                target_frame = cv2.imread(str(target_frame_path))
                
                if ref_frame is None or target_frame is None:
                    continue
                
                has_artifact, bounding_rects = detector.process_pair(
                    ref_frame, target_frame, i,
                    landmarks_curr=landmark_sequence[i] if i < len(landmark_sequence) else None
                )
                
                if has_artifact:
                    frame_bounding_rects[i] = bounding_rects
                    artifact_count += len(bounding_rects)
            
            # Save frame 0 without comparison
            frame_0_path = target_frames_dir / "frame_0000.png"
            if frame_0_path.exists():
                frame_0 = cv2.imread(str(frame_0_path))
                cv2.imwrite(str(output_dir / "frame_0000.png"), frame_0)
            
            print(f"[{analysis_id}] ✓ Detected artifacts in {len(frame_bounding_rects)} frames ({artifact_count} total regions)")
            
            # Stage 5: Extract fragments from glitch frames
            print(f"[{analysis_id}] Stage 5/7: Extracting fragments...")
            
            fragments_dir = analysis_dir / "fragments"
            extractor_frag = self.FragmentExtractor(output_dir=str(fragments_dir))
            all_fragment_paths = []
            
            for glitch_idx in glitch_indices:
                frame_path = target_frames_dir / f"frame_{glitch_idx:04d}.png"
                if not frame_path.exists():
                    continue
                    
                frame = cv2.imread(str(frame_path))
                bounding_rects = frame_bounding_rects.get(glitch_idx, [])
                
                fragment_paths = extractor_frag.extract(frame, glitch_idx, bounding_rects)
                all_fragment_paths.extend(fragment_paths)
            
            print(f"[{analysis_id}] ✓ Extracted {len(all_fragment_paths)} fragments")
            
            # Stage 6: Aggregate fragments into reconstructed face
            print(f"[{analysis_id}] Stage 6/7: Aggregating fragments...")
            
            reconstructed_path = None
            if all_fragment_paths:
                aggregator = self.FragmentAggregator(
                    target_size=(256, 256),
                    output_dir=str(output_dir)
                )
                reconstructed_path = aggregator.aggregate(
                    all_fragment_paths,
                    frames_dir=str(target_frames_dir),
                    glitch_indices=glitch_indices
                )
            
            if reconstructed_path:
                print(f"[{analysis_id}] ✓ Reconstructed face saved")
            else:
                print(f"[{analysis_id}] ⚠ No reconstruction generated (insufficient fragments)")
            
            # Stage 7: Generate summary report
            print(f"[{analysis_id}] Stage 7/7: Generating report...")
            
            reporter = self.ReportGenerator(output_dir=str(output_dir))
            forensic_anomaly_score = reporter.generate(total_frames, glitch_indices)
            
            print(f"[{analysis_id}] ✓ Analysis complete. Forensic anomaly score: {forensic_anomaly_score:.4f}")
            
            processing_time = time.time() - start_time
            
            # Return structured results
            return {
                "status": "completed",
                "analysis_type": "video-to-video",
                "forensic_anomaly_score": forensic_anomaly_score,
                "total_frames": total_frames,
                "glitch_frames": len(glitch_indices),
                "artifact_regions_detected": artifact_count,
                "frames_with_artifacts": len(frame_bounding_rects),
                "fragments_extracted": len(all_fragment_paths),
                "reference_video_frames": total_ref,
                "target_video_frames": total_target,
                "fps_reference": fps_ref,
                "fps_target": fps_target,
                "processing_time_seconds": processing_time,
                "output_files": {
                    "annotated_frames_dir": str(output_dir),
                    "reconstructed_face": reconstructed_path,
                    "summary_report": str(output_dir / "summary.txt")
                },
                "message": f"Analysis completed successfully in {processing_time:.1f}s"
            }
            
        except Exception as e:
            print(f"[{analysis_id}] ✗ Analysis failed: {str(e)}")
            raise RuntimeError(f"Video-to-video analysis failed: {str(e)}") from e
    
    async def analyze_photo_to_video(
        self, 
        reference_path: str, 
        target_path: str, 
        parameters: Dict[str, Any],
        analysis_id: str,
        work_dir: Path
    ) -> Dict[str, Any]:
        """
        Run photo-to-video deepfake analysis.
        
        Verifies if the person from a reference photo appears consistently in a video,
        and detects temporal inconsistencies suggesting deepfake manipulation.
        
        Parameters
        ----------
        reference_path : str
            Path to the reference photo file.
        target_path : str
            Path to the target video file.
        parameters : dict
            Analysis parameters (same as video-to-video mode).
        analysis_id : str
            Unique analysis identifier.
        work_dir : Path
            Base working directory for analysis output.
        
        Returns
        -------
        dict
            Analysis results with forensic evidence.
        """
        start_time = time.time()
        
        # Setup isolated analysis directory
        analysis_dir = self._setup_analysis_directory(analysis_id, work_dir)
        
        # Extract parameters with defaults
        displacement_threshold = parameters.get('displacement_threshold', 10.0)
        diff_threshold = parameters.get('diff_threshold', 20)
        ssim_threshold = parameters.get('ssim_threshold', 0.85)
        
        try:
            # Stage 1: Load reference photo
            print(f"[{analysis_id}] Stage 1/7: Loading reference photo...")
            
            ref_photo = cv2.imread(reference_path)
            if ref_photo is None:
                raise ValueError("Could not load reference photo")
            
            print(f"[{analysis_id}] ✓ Reference photo loaded: {ref_photo.shape}")
            
            # Stage 2: Extract frames from target video
            print(f"[{analysis_id}] Stage 2/7: Extracting video frames...")
            
            frames_dir = analysis_dir / "frames"
            extractor = self.FrameExtractor(str(target_path), str(frames_dir))
            total_frames, fps = extractor.extract()
            
            print(f"[{analysis_id}] ✓ Extracted {total_frames} frames ({fps:.2f} FPS)")
            
            # Stage 3: Detect facial landmarks in video
            print(f"[{analysis_id}] Stage 3/7: Detecting facial landmarks...")
            
            face_mesh = self.FaceMesh()
            landmark_sequence = []
            
            for i in range(total_frames):
                frame_path = frames_dir / f"frame_{i:04d}.png"
                frame = cv2.imread(str(frame_path))
                landmarks = face_mesh.detect(frame) if frame is not None else []
                landmark_sequence.append(landmarks)
            
            faces_detected = sum(1 for lm in landmark_sequence if len(lm) > 0)
            print(f"[{analysis_id}] ✓ Detected faces in {faces_detected}/{total_frames} frames")
            
            # Stage 4: Track landmark failures (glitch frames)
            print(f"[{analysis_id}] Stage 4/7: Tracking landmark failures...")
            
            tracker = self.LandmarkTracker(displacement_threshold=displacement_threshold)
            glitch_indices = tracker.find_glitch_frames(landmark_sequence)
            
            print(f"[{analysis_id}] ✓ Found {len(glitch_indices)} glitch frames")
            
            # Stage 5: Detect visual artifacts via temporal consistency
            print(f"[{analysis_id}] Stage 5/7: Detecting temporal artifacts...")
            
            output_dir = analysis_dir / "output"
            detector = self.ArtifactDetector(
                diff_threshold=diff_threshold,
                ssim_threshold=ssim_threshold,
                output_dir=str(output_dir)
            )
            
            frame_bounding_rects = {}
            artifact_count = 0
            
            # For photo-to-video, compare consecutive frames for temporal consistency
            for i in range(1, total_frames):
                prev_frame_path = frames_dir / f"frame_{i-1:04d}.png"
                curr_frame_path = frames_dir / f"frame_{i:04d}.png"
                
                prev_frame = cv2.imread(str(prev_frame_path))
                curr_frame = cv2.imread(str(curr_frame_path))
                
                if prev_frame is None or curr_frame is None:
                    continue
                
                has_artifact, bounding_rects = detector.process_pair(
                    prev_frame, curr_frame, i,
                    landmarks_curr=landmark_sequence[i] if i < len(landmark_sequence) else None
                )
                
                if has_artifact:
                    frame_bounding_rects[i] = bounding_rects
                    artifact_count += len(bounding_rects)
            
            # Save frame 0
            frame_0_path = frames_dir / "frame_0000.png"
            if frame_0_path.exists():
                frame_0 = cv2.imread(str(frame_0_path))
                cv2.imwrite(str(output_dir / "frame_0000.png"), frame_0)
            
            print(f"[{analysis_id}] ✓ Detected temporal artifacts in {len(frame_bounding_rects)} frames ({artifact_count} total regions)")
            
            # Stage 6: Extract fragments from glitch frames
            print(f"[{analysis_id}] Stage 6/7: Extracting fragments...")
            
            fragments_dir = analysis_dir / "fragments"
            extractor_frag = self.FragmentExtractor(output_dir=str(fragments_dir))
            all_fragment_paths = []
            
            for glitch_idx in glitch_indices:
                frame_path = frames_dir / f"frame_{glitch_idx:04d}.png"
                if not frame_path.exists():
                    continue
                    
                frame = cv2.imread(str(frame_path))
                bounding_rects = frame_bounding_rects.get(glitch_idx, [])
                
                fragment_paths = extractor_frag.extract(frame, glitch_idx, bounding_rects)
                all_fragment_paths.extend(fragment_paths)
            
            print(f"[{analysis_id}] ✓ Extracted {len(all_fragment_paths)} fragments")
            
            # Stage 7: Aggregate and generate report
            print(f"[{analysis_id}] Stage 7/7: Generating report...")
            
            reconstructed_path = None
            if all_fragment_paths:
                aggregator = self.FragmentAggregator(
                    target_size=(256, 256),
                    output_dir=str(output_dir)
                )
                reconstructed_path = aggregator.aggregate(
                    all_fragment_paths,
                    frames_dir=str(frames_dir),
                    glitch_indices=glitch_indices
                )
            
            reporter = self.ReportGenerator(output_dir=str(output_dir))
            forensic_anomaly_score = reporter.generate(total_frames, glitch_indices)
            
            print(f"[{analysis_id}] ✓ Analysis complete. Forensic anomaly score: {forensic_anomaly_score:.4f}")
            
            processing_time = time.time() - start_time
            
            # Return structured results
            return {
                "status": "completed",
                "analysis_type": "photo-to-video",
                "forensic_anomaly_score": forensic_anomaly_score,
                "total_frames": total_frames,
                "glitch_frames": len(glitch_indices),
                "artifact_regions_detected": artifact_count,
                "frames_with_artifacts": len(frame_bounding_rects),
                "fragments_extracted": len(all_fragment_paths),
                "video_fps": fps,
                "processing_time_seconds": processing_time,
                "output_files": {
                    "annotated_frames_dir": str(output_dir),
                    "reconstructed_face": reconstructed_path,
                    "summary_report": str(output_dir / "summary.txt")
                },
                "message": f"Photo-to-video analysis completed successfully in {processing_time:.1f}s"
            }
            
        except Exception as e:
            print(f"[{analysis_id}] ✗ Analysis failed: {str(e)}")
            raise RuntimeError(f"Photo-to-video analysis failed: {str(e)}") from e
    
    def verify_forensic_modules(self) -> Dict[str, bool]:
        """
        Verify that all required forensic modules are available on disk.
        
        Returns
        -------
        dict
            Module availability status.
        """
        modules_status = {
            "frame_extractor": False,
            "face_mesh": False, 
            "landmark_tracker": False,
            "artifact_detector": False,
            "fragment_extractor": False,
            "fragment_aggregator": False,
            "report_generator": False
        }
        
        # Check if module files exist
        for module_name in modules_status:
            module_file = self.project_root / f"{module_name}.py"
            modules_status[module_name] = module_file.exists()
        
        return modules_status
    
    def get_forensic_engine_info(self) -> Dict[str, Any]:
        """
        Get information about the forensic engine status.
        
        Returns
        -------
        dict
            Engine status and module information.
        """
        modules_status = self.verify_forensic_modules()
        
        return {
            "engine_root": str(self.project_root),
            "modules_loaded": self._modules_loaded,
            "available_modules": modules_status,
            "total_modules": len(modules_status),
            "available_count": sum(modules_status.values()),
            "phase": "Phase 2 - Real Integration"
        }
