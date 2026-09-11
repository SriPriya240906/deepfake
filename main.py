"""
main.py — Entry point for the Deepfake Forensic Analysis pipeline.

Orchestrates all modules in sequence: frame extraction → landmark detection →
glitch tracking → artifact detection → fragment extraction → aggregation → report.
"""

import argparse
import os
import cv2
from frame_extractor import FrameExtractor
from face_mesh import FaceMesh
from landmark_tracker import LandmarkTracker
from artifact_detector import ArtifactDetector
from fragment_extractor import FragmentExtractor
from fragment_aggregator import FragmentAggregator
from report_generator import ReportGenerator


def run_pipeline(
    video_path: str,
    displacement_threshold: float = 10.0,
    diff_threshold: int = 25,
    ssim_threshold: float = 0.80,
) -> None:
    """
    Runs the complete deepfake forensic analysis pipeline.

    Parameters
    ----------
    video_path : str
        Path to the input video file.
    displacement_threshold : float
        Landmark displacement threshold in pixels (default: 10.0).
    diff_threshold : int
        Pixel intensity threshold for frame differencing (default: 30).
    ssim_threshold : float
        SSIM threshold for artifact detection (default: 0.85).
    """
    print(f"\n{'='*60}")
    print("DEEPFAKE FORENSIC ANALYSIS PIPELINE")
    print(f"{'='*60}\n")
    print(f"Input video: {video_path}\n")

    # --- Stage 1: Extract frames ---
    print("[1/7] Extracting frames...")
    extractor = FrameExtractor(video_path, output_dir="frames")
    total_frames, fps = extractor.extract()
    print(f"  [OK] Extracted {total_frames} frames ({fps:.2f} FPS)\n")

    # --- Stage 2: Detect facial landmarks ---
    print("[2/7] Detecting facial landmarks...")
    face_mesh = FaceMesh()
    landmark_sequence = []
    
    for i in range(total_frames):
        frame_path = os.path.join("frames", f"frame_{i:04d}.png")
        frame = cv2.imread(frame_path)
        landmarks = face_mesh.detect(frame)
        landmark_sequence.append(landmarks)
    
    faces_detected = sum(1 for lm in landmark_sequence if len(lm) > 0)
    print(f"  [OK] Detected faces in {faces_detected}/{total_frames} frames\n")

    # --- Stage 3: Track landmark failures (glitch frames) ---
    print("[3/7] Tracking landmark failures...")
    tracker = LandmarkTracker(displacement_threshold=displacement_threshold)
    glitch_indices = tracker.find_glitch_frames(landmark_sequence)
    print(f"  [OK] Found {len(glitch_indices)} glitch frames\n")

    # --- Stage 4: Detect artifacts via frame differencing + SSIM ---
    print("[4/7] Detecting visual artifacts...")
    detector = ArtifactDetector(
        diff_threshold=diff_threshold,
        ssim_threshold=ssim_threshold,
        output_dir="output",
    )
    
    # Store bounding rects for each frame
    frame_bounding_rects = {}
    
    for i in range(1, total_frames):
        prev_frame_path = os.path.join("frames", f"frame_{i-1:04d}.png")
        curr_frame_path = os.path.join("frames", f"frame_{i:04d}.png")
        
        frame_prev = cv2.imread(prev_frame_path)
        frame_curr = cv2.imread(curr_frame_path)
        
        has_artifact, bounding_rects = detector.process_pair(
            frame_prev, frame_curr, i,
            landmarks_curr=landmark_sequence[i],
        )
        
        if has_artifact:
            frame_bounding_rects[i] = bounding_rects
    
    # Also process frame 0 (save without comparison)
    frame_0 = cv2.imread(os.path.join("frames", "frame_0000.png"))
    cv2.imwrite(os.path.join("output", "frame_0000.png"), frame_0)
    
    print(f"  [OK] Detected artifacts in {len(frame_bounding_rects)} frames\n")

    # --- Stage 5: Extract fragments from glitch frames ---
    print("[5/7] Extracting glitch fragments...")
    extractor_frag = FragmentExtractor(output_dir="fragments")
    all_fragment_paths = []
    
    for glitch_idx in glitch_indices:
        frame_path = os.path.join("frames", f"frame_{glitch_idx:04d}.png")
        frame = cv2.imread(frame_path)
        
        # Get bounding rects for this frame (empty list if none)
        bounding_rects = frame_bounding_rects.get(glitch_idx, [])
        
        fragment_paths = extractor_frag.extract(frame, glitch_idx, bounding_rects)
        all_fragment_paths.extend(fragment_paths)
    
    print(f"  [OK] Extracted {len(all_fragment_paths)} fragments\n")

    # --- Stage 6: Aggregate fragments into reconstructed face ---
    print("[6/7] Aggregating fragments...")
    aggregator = FragmentAggregator(target_size=(256, 256), output_dir="output")
    reconstructed_path = aggregator.aggregate(
        all_fragment_paths,
        frames_dir="frames",
        glitch_indices=glitch_indices,
    )
    
    if reconstructed_path:
        print(f"  [OK] Reconstructed face saved to: {reconstructed_path}\n")
    else:
        print(f"  [WARN] No reconstruction generated (insufficient fragments)\n")

    # --- Stage 7: Generate summary report ---
    print("[7/7] Generating report...")
    reporter = ReportGenerator(output_dir="output")
    deepfake_score = reporter.generate(total_frames, glitch_indices)
    
    print(f"\n{'='*60}")
    print("PIPELINE COMPLETE")
    print(f"{'='*60}\n")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Deepfake Forensic Analysis using Landmark Failure and Frame-Level Reconstruction"
    )
    
    parser.add_argument(
        "video",
        type=str,
        help="Path to input video file (MP4, AVI, or MOV)",
    )
    
    parser.add_argument(
        "--displacement-threshold",
        type=float,
        default=10.0,
        help="Landmark displacement threshold in pixels (default: 10.0)",
    )
    
    parser.add_argument(
        "--diff-threshold",
        type=int,
        default=15,
        help="Pixel intensity threshold for frame differencing (default: 15)",
    )
    
    parser.add_argument(
        "--ssim-threshold",
        type=float,
        default=0.92,
        help="SSIM threshold for artifact detection (default: 0.92)",
    )
    
    parser.add_argument(
        "--ui",
        action="store_true",
        help="Launch Streamlit UI instead of CLI pipeline",
    )
    
    args = parser.parse_args()
    
    # If --ui flag is set, launch Streamlit app
    if args.ui:
        print("Launching Streamlit UI...")
        import subprocess
        subprocess.run(["streamlit", "run", "app.py"])
        return
    
    # Otherwise, run the CLI pipeline
    run_pipeline(
        video_path=args.video,
        displacement_threshold=args.displacement_threshold,
        diff_threshold=args.diff_threshold,
        ssim_threshold=args.ssim_threshold,
    )


if __name__ == "__main__":
    main()

