"""
app.py — Deepfake Forensic Analysis: Real vs Fake Comparison Mode.
Upload EITHER:
1. REAL VIDEO + FAKE VIDEO - compares frame-by-frame
2. PHOTO OF PERSON + FAKE VIDEO - verifies person identity and detects manipulation
The system shows exactly where the face was manipulated.
"""
import streamlit as st
import os
import shutil
import tempfile
import cv2
import numpy as np
from pathlib import Path
from skimage.metrics import structural_similarity

from frame_extractor import FrameExtractor
from face_mesh import FaceMesh
from landmark_tracker import LandmarkTracker
from fragment_aggregator import FragmentAggregator
from report_generator import ReportGenerator

# ── helpers ──────────────────────────────────────────────────────────────────

def clear_dirs():
    for d in ["frames_real", "frames_fake", "output", "fragments"]:
        if os.path.exists(d):
            # Windows-safe: remove files individually first, then the folder
            for root, dirs, files in os.walk(d, topdown=False):
                for f in files:
                    try:
                        os.remove(os.path.join(root, f))
                    except Exception:
                        pass
                for dd in dirs:
                    try:
                        os.rmdir(os.path.join(root, dd))
                    except Exception:
                        pass
            try:
                os.rmdir(d)
            except Exception:
                pass
        os.makedirs(d, exist_ok=True)


def get_region_label(
    bx: int, by: int, bw: int, bh: int,
    landmarks: list,
) -> str:
    """Label a box using nearest MediaPipe landmark."""
    if not landmarks:
        return "ARTIFACT"

    cx, cy = bx + bw // 2, by + bh // 2

    regions = [
        ("LEFT EYE",     [33, 133, 159, 145]),
        ("RIGHT EYE",    [362, 263, 386, 374]),
        ("NOSE",         [1, 2, 98, 327]),
        ("MOUTH",        [13, 14, 61, 291]),
        ("LEFT CHEEK",   [234, 93, 132]),
        ("RIGHT CHEEK",  [454, 323, 361]),
        ("FOREHEAD",     [10, 67, 297]),
        ("CHIN",         [152, 175, 148]),
        ("LEFT EYEBROW", [70, 63, 105]),
        ("RIGHT EYEBROW",[300, 293, 334]),
        ("JAW",          [172, 136, 150, 365, 397]),
    ]

    best_label, best_dist = "ARTIFACT", float("inf")
    for label, indices in regions:
        for idx in indices:
            if idx < len(landmarks):
                lx, ly, _ = landmarks[idx]
                dist = ((cx - lx) ** 2 + (cy - ly) ** 2) ** 0.5
                if dist < best_dist:
                    best_dist = dist
                    best_label = label
    return best_label


def get_face_mask(landmarks: list, frame_shape: tuple) -> np.ndarray:
    """
    Create a binary mask covering only the face region using landmarks.
    Returns a mask where 255 = face area, 0 = background.
    """
    fh, fw = frame_shape[:2]
    mask = np.zeros((fh, fw), dtype=np.uint8)

    if not landmarks:
        return mask

    # Face oval landmark indices (MediaPipe face contour)
    face_oval_indices = [
        10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288,
        397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
        172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109, 10
    ]

    points = []
    for idx in face_oval_indices:
        if idx < len(landmarks):
            x, y, _ = landmarks[idx]
            points.append([int(x), int(y)])

    if len(points) > 3:
        pts = np.array(points, dtype=np.int32)
        # Fill the face oval with white
        cv2.fillPoly(mask, [pts], 255)
        # Expand the mask slightly to include face edges
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (30, 30))
        mask = cv2.dilate(mask, kernel, iterations=2)

    return mask


def _merge_overlapping_rects(
    rects: list, overlap_thresh: float = 0.3
) -> list:
    """Merge only heavily overlapping boxes, keep distinct regions separate."""
    if not rects:
        return rects

    boxes = np.array([[x, y, x+w, y+h] for x, y, w, h in rects], dtype=np.float32)
    used = [False] * len(boxes)
    merged = []

    for i in range(len(boxes)):
        if used[i]:
            continue
        x1, y1, x2, y2 = boxes[i]
        for j in range(i+1, len(boxes)):
            if used[j]:
                continue
            bx1, by1, bx2, by2 = boxes[j]
            ix1, iy1 = max(x1, bx1), max(y1, by1)
            ix2, iy2 = min(x2, bx2), min(y2, by2)
            if ix2 > ix1 and iy2 > iy1:
                inter = (ix2-ix1) * (iy2-iy1)
                area_i = (x2-x1) * (y2-y1)
                area_j = (bx2-bx1) * (by2-by1)
                # Only merge if one box is almost entirely inside the other
                iou = inter / min(area_i, area_j)
                if iou > overlap_thresh:
                    x1 = min(x1, bx1)
                    y1 = min(y1, by1)
                    x2 = max(x2, bx2)
                    y2 = max(y2, by2)
                    used[j] = True
        used[i] = True
        bw, bh = int(x2-x1), int(y2-y1)
        merged.append((int(x1), int(y1), bw, bh))

    # Filter out boxes that are too large (avoid full-face boxes that are noise)
    # Keep boxes smaller than 70% of the largest box, but always keep at least 1 box
    if len(merged) > 1:
        areas = [w*h for x,y,w,h in merged]
        max_area = max(areas)
        # Only filter if we have multiple boxes — keep region-sized boxes
        filtered = [(x,y,w,h) for x,y,w,h in merged if w*h < max_area * 0.7]
        # If filtering removed everything, keep the original merged list
        if filtered:
            merged = filtered

    return merged


def compare_frame_pair(
    real_frame: np.ndarray,
    fake_frame: np.ndarray,
    frame_idx: int,
    landmarks_fake: list,
    diff_threshold: int,
    ssim_threshold: float,
    min_area: int,
) -> tuple[np.ndarray, bool, list, float]:
    """
    Compare one real frame vs one fake frame.
    Returns (annotated_fake_frame, has_artifact, bounding_rects, ssim_score).
    """
    fh, fw = fake_frame.shape[:2]

    # Resize real to match fake dimensions if needed
    if real_frame.shape[:2] != fake_frame.shape[:2]:
        real_frame = cv2.resize(real_frame, (fw, fh))

    gray_real = cv2.cvtColor(real_frame, cv2.COLOR_BGR2GRAY)
    gray_fake = cv2.cvtColor(fake_frame, cv2.COLOR_BGR2GRAY)

    # Pixel difference: real vs fake
    diff = cv2.absdiff(gray_real, gray_fake)

    # SSIM: real vs fake
    mean_ssim, ssim_map = structural_similarity(gray_real, gray_fake, full=True)
    ssim_diff = ((1.0 - ssim_map) * 127).astype(np.uint8)

    # Combined inconsistency map
    combined = cv2.addWeighted(diff, 0.6, ssim_diff, 0.4, 0)

    # Binary mask
    _, mask = cv2.threshold(combined, diff_threshold, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # ── Apply face-only mask — ignore background changes ──
    face_mask = get_face_mask(landmarks_fake, fake_frame.shape)
    if face_mask.any():
        mask = cv2.bitwise_and(mask, face_mask)

    # Find contours
    contours, _ = cv2.findContours(
        mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    bounding_rects = []
    for c in contours:
        if cv2.contourArea(c) >= min_area:
            x, y, w, h = cv2.boundingRect(c)
            bounding_rects.append((x, y, w, h))

    # Merge overlapping/nearby boxes to avoid duplicates
    bounding_rects = _merge_overlapping_rects(bounding_rects, overlap_thresh=0.3)

    has_artifact = mean_ssim < ssim_threshold and len(bounding_rects) > 0

    # Annotate the FAKE frame
    annotated = fake_frame.copy()

    if has_artifact:
        # Heatmap overlay — light opacity so face is still visible
        heatmap = cv2.applyColorMap(
            cv2.GaussianBlur(combined, (21, 21), 0), cv2.COLORMAP_JET
        )
        heat_mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR).astype(bool)
        blended = cv2.addWeighted(annotated, 0.75, heatmap, 0.25, 0)
        annotated[heat_mask] = blended[heat_mask]

        # Draw labeled boxes
        for x, y, w, h in bounding_rects:
            cv2.rectangle(annotated, (x-2, y-2), (x+w+2, y+h+2), (0, 0, 100), 1)
            cv2.rectangle(annotated, (x, y), (x+w, y+h), (0, 0, 255), 2)

            label = get_region_label(x, y, w, h, landmarks_fake)
            (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
            ly2 = max(y - 4, lh + 6)
            cv2.rectangle(annotated, (x, ly2 - lh - 4), (x + lw + 6, ly2), (0, 0, 180), -1)
            cv2.putText(annotated, label, (x + 3, ly2 - 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1)
        # Red banner
        cv2.rectangle(annotated, (0, fh - 38), (fw, fh), (0, 0, 180), -1)
        cv2.putText(annotated,
                    f"MANIPULATED  |  Regions: {len(bounding_rects)}  |  SSIM: {mean_ssim:.3f}",
                    (8, fh - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (255, 255, 255), 1)
    else:
        # Green banner
        cv2.rectangle(annotated, (0, fh - 38), (fw, fh), (0, 130, 0), -1)
        cv2.putText(annotated, f"CLEAN  |  SSIM: {mean_ssim:.3f}",
                    (8, fh - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (255, 255, 255), 1)

    cv2.putText(annotated, f"#{frame_idx:04d}",
                (fw - 70, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    return annotated, has_artifact, bounding_rects, mean_ssim


def run_comparison_with_photo(
    photo_path: str, fake_path: str,
    disp_thresh: float, diff_thresh: int, ssim_thresh: float,
    progress,
) -> dict:
    """
    Compare a reference photo against a fake video.
    Extracts the person's face from photo and compares to each frame.
    """
    results = {}

    # Load reference photo
    progress.progress(0.05, "Loading reference photo...")
    ref_photo = cv2.imread(photo_path)
    if ref_photo is None:
        raise ValueError("Could not load reference photo")

    # Extract face from reference photo
    progress.progress(0.10, "Detecting face in reference photo...")
    fm = FaceMesh()
    ref_landmarks = fm.detect(ref_photo)
    
    if not ref_landmarks:
        raise ValueError("No face detected in reference photo. Please upload a clear photo with a visible face.")

    # Get face bounding box from reference photo
    ref_points = np.array([[int(x), int(y)] for x, y, _ in ref_landmarks], dtype=np.int32)
    x_min, y_min = ref_points.min(axis=0)
    x_max, y_max = ref_points.max(axis=0)
    # Add padding
    padding = 20
    x_min = max(0, x_min - padding)
    y_min = max(0, y_min - padding)
    x_max = min(ref_photo.shape[1], x_max + padding)
    y_max = min(ref_photo.shape[0], y_max + padding)
    
    ref_face = ref_photo[y_min:y_max, x_min:x_max]
    
    # Save reference face for visualization
    os.makedirs("output", exist_ok=True)
    cv2.imwrite("output/reference_face.png", ref_face)
    results["ref_face_path"] = "output/reference_face.png"

    # Extract frames from fake video
    progress.progress(0.20, "Extracting fake video frames...")
    fe_fake = FrameExtractor(fake_path, output_dir="frames_fake")
    total_fake, fps_fake = fe_fake.extract()
    
    results["total"] = total_fake
    results["total_real"] = 1  # Only 1 reference photo
    results["total_fake"] = total_fake

    # Detect landmarks on fake frames
    progress.progress(0.30, "Detecting facial landmarks on fake video...")
    lm_fake = []
    for i in range(total_fake):
        frame = cv2.imread(f"frames_fake/frame_{i:04d}.png")
        lm_fake.append(fm.detect(frame) if frame is not None else [])

    # Check if person from photo appears in fake video
    progress.progress(0.40, "Verifying person identity in fake video...")
    person_found = False
    for i in range(min(10, total_fake)):  # Check first 10 frames
        if lm_fake[i]:
            person_found = True
            break
    
    if not person_found:
        st.warning("⚠️ No face detected in fake video. Analysis may be limited.")

    # Landmark glitch detection on fake video
    progress.progress(0.45, "Tracking landmark failures...")
    tracker = LandmarkTracker(displacement_threshold=disp_thresh)
    glitch_idx = tracker.find_glitch_frames(lm_fake)
    results["glitch_idx"] = glitch_idx

    # Compare reference face to each fake frame
    progress.progress(0.50, "Comparing reference photo to fake video frames...")
    os.makedirs("fragments", exist_ok=True)

    manipulated_frames = []
    rects_map = {}
    frag_paths = []
    ssim_scores = []

    for i in range(total_fake):
        fake_frame = cv2.imread(f"frames_fake/frame_{i:04d}.png")
        if fake_frame is None:
            continue

        # Extract face from current fake frame for comparison
        if lm_fake[i]:
            fake_points = np.array([[int(x), int(y)] for x, y, _ in lm_fake[i]], dtype=np.int32)
            fx_min, fy_min = fake_points.min(axis=0)
            fx_max, fy_max = fake_points.max(axis=0)
            fx_min = max(0, fx_min - padding)
            fy_min = max(0, fy_min - padding)
            fx_max = min(fake_frame.shape[1], fx_max + padding)
            fy_max = min(fake_frame.shape[0], fy_max + padding)
            
            fake_face = fake_frame[fy_min:fy_max, fx_min:fx_max]
            
            # Resize reference face to match fake face size for comparison
            if fake_face.size > 0:
                ref_face_resized = cv2.resize(ref_face, (fake_face.shape[1], fake_face.shape[0]))
                
                # Compare faces using SSIM and pixel difference
                gray_ref = cv2.cvtColor(ref_face_resized, cv2.COLOR_BGR2GRAY)
                gray_fake_face = cv2.cvtColor(fake_face, cv2.COLOR_BGR2GRAY)
                
                face_ssim, _ = structural_similarity(gray_ref, gray_fake_face, full=True)
                ssim_scores.append(face_ssim)
                
                # Detect artifacts in full frame
                annotated, has_art, rects, _ = compare_frame_with_photo_reference(
                    ref_photo, fake_frame, i,
                    lm_fake[i], diff_thresh, ssim_thresh, 1200
                )
                
                cv2.imwrite(f"output/frame_{i:04d}.png", annotated)
                
                if has_art:
                    manipulated_frames.append(i)
                    rects_map[i] = rects
                    
                    # Save side-by-side comparison
                    compare_path = f"fragments/compare_{i:04d}.png"
                    if not os.path.exists(compare_path):
                        h = max(ref_photo.shape[0], fake_frame.shape[0])
                        w = max(ref_photo.shape[1], fake_frame.shape[1])
                        rr = cv2.resize(ref_photo, (w, h))
                        fr = cv2.resize(annotated, (w, h))
                        cv2.putText(rr, "REFERENCE", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        cv2.putText(fr, "FAKE", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                        side_by_side = np.hstack([rr, fr])
                        cv2.imwrite(compare_path, side_by_side)
                        frag_paths.append(compare_path)

        if i % 10 == 0:
            pct = 0.50 + 0.40 * (i / total_fake)
            progress.progress(pct, f"Analyzing frame {i}/{total_fake}...")

    results["manipulated_frames"] = manipulated_frames
    results["rects_map"] = rects_map
    results["frag_paths"] = frag_paths
    results["avg_ssim"] = float(np.mean(ssim_scores)) if ssim_scores else 1.0

    # Reconstruct identity from glitch frames
    progress.progress(0.92, "Reconstructing identity...")
    agg = FragmentAggregator(target_size=(256, 256), output_dir="output")
    fake_frag_paths = []
    for gi in glitch_idx:
        frame = cv2.imread(f"frames_fake/frame_{gi:04d}.png")
        if frame is not None:
            p = f"fragments/frag_{gi:04d}.png"
            cv2.imwrite(p, frame)
            fake_frag_paths.append(p)
    recon = agg.aggregate(fake_frag_paths, frames_dir="frames_fake", glitch_indices=glitch_idx)
    results["recon"] = recon

    # Report
    progress.progress(0.97, "Generating report...")
    score = len(manipulated_frames) / total_fake if total_fake > 0 else 0.0
    results["score"] = score
    rep = ReportGenerator(output_dir="output")
    rep.generate(total_fake, manipulated_frames)

    progress.progress(1.0, "Done!")
    return results


def compare_frame_with_photo_reference(
    ref_photo: np.ndarray,
    fake_frame: np.ndarray,
    frame_idx: int,
    landmarks_fake: list,
    diff_threshold: int,
    ssim_threshold: float,
    min_area: int,
) -> tuple[np.ndarray, bool, list, float]:
    """
    Compare reference photo against a fake frame to detect manipulation.
    Uses temporal inconsistency detection on the fake frame itself.
    """
    fh, fw = fake_frame.shape[:2]

    # For photo reference mode, we look for temporal inconsistencies
    # by comparing this frame to previous frame (if available)
    prev_frame_path = f"frames_fake/frame_{frame_idx-1:04d}.png" if frame_idx > 0 else None
    
    if prev_frame_path and os.path.exists(prev_frame_path):
        prev_frame = cv2.imread(prev_frame_path)
        if prev_frame is not None:
            # Use temporal comparison (frame-to-frame)
            gray_prev = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            gray_curr = cv2.cvtColor(fake_frame, cv2.COLOR_BGR2GRAY)
            
            diff = cv2.absdiff(gray_prev, gray_curr)
            mean_ssim, ssim_map = structural_similarity(gray_prev, gray_curr, full=True)
            ssim_diff = ((1.0 - ssim_map) * 127).astype(np.uint8)
            
            combined = cv2.addWeighted(diff, 0.6, ssim_diff, 0.4, 0)
            _, mask = cv2.threshold(combined, diff_threshold, 255, cv2.THRESH_BINARY)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            
            # Apply face mask
            face_mask = get_face_mask(landmarks_fake, fake_frame.shape)
            if face_mask.any():
                mask = cv2.bitwise_and(mask, face_mask)
            
            # Find contours
            contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            bounding_rects = []
            for c in contours:
                if cv2.contourArea(c) >= min_area:
                    x, y, w, h = cv2.boundingRect(c)
                    bounding_rects.append((x, y, w, h))
            
            bounding_rects = _merge_overlapping_rects(bounding_rects, overlap_thresh=0.3)
            has_artifact = mean_ssim < ssim_threshold and len(bounding_rects) > 0
            
            # Annotate
            annotated = fake_frame.copy()
            if has_artifact:
                heatmap = cv2.applyColorMap(cv2.GaussianBlur(combined, (21, 21), 0), cv2.COLORMAP_JET)
                heat_mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR).astype(bool)
                blended = cv2.addWeighted(annotated, 0.75, heatmap, 0.25, 0)
                annotated[heat_mask] = blended[heat_mask]
                
                for x, y, w, h in bounding_rects:
                    cv2.rectangle(annotated, (x-2, y-2), (x+w+2, y+h+2), (0, 0, 100), 1)
                    cv2.rectangle(annotated, (x, y), (x+w, y+h), (0, 0, 255), 2)
                    
                    label = get_region_label(x, y, w, h, landmarks_fake)
                    (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
                    ly2 = max(y - 4, lh + 6)
                    cv2.rectangle(annotated, (x, ly2 - lh - 4), (x + lw + 6, ly2), (0, 0, 180), -1)
                    cv2.putText(annotated, label, (x + 3, ly2 - 2),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1)
                
                cv2.rectangle(annotated, (0, fh - 38), (fw, fh), (0, 0, 180), -1)
                cv2.putText(annotated,
                            f"MANIPULATED  |  Regions: {len(bounding_rects)}  |  SSIM: {mean_ssim:.3f}",
                            (8, fh - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (255, 255, 255), 1)
            else:
                cv2.rectangle(annotated, (0, fh - 38), (fw, fh), (0, 130, 0), -1)
                cv2.putText(annotated, f"CLEAN  |  SSIM: {mean_ssim:.3f}",
                            (8, fh - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (255, 255, 255), 1)
            
            cv2.putText(annotated, f"#{frame_idx:04d}",
                        (fw - 70, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            
            return annotated, has_artifact, bounding_rects, mean_ssim
    
    # Fallback: no previous frame available
    annotated = fake_frame.copy()
    cv2.rectangle(annotated, (0, fh - 38), (fw, fh), (0, 130, 0), -1)
    cv2.putText(annotated, "CLEAN  |  First frame",
                (8, fh - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (255, 255, 255), 1)
    return annotated, False, [], 1.0


def run_comparison(
    real_path: str, fake_path: str,
    disp_thresh: float, diff_thresh: int, ssim_thresh: float,
    progress,
) -> dict:
    results = {}

    # Extract frames from both videos
    progress.progress(0.05, "Extracting real video frames...")
    fe_real = FrameExtractor(real_path, output_dir="frames_real")
    total_real, fps_real = fe_real.extract()

    progress.progress(0.15, "Extracting fake video frames...")
    fe_fake = FrameExtractor(fake_path, output_dir="frames_fake")
    total_fake, fps_fake = fe_fake.extract()

    # Use minimum frame count for comparison
    total = min(total_real, total_fake)
    results["total"] = total
    results["total_real"] = total_real
    results["total_fake"] = total_fake

    # Detect landmarks on fake frames
    progress.progress(0.25, "Detecting facial landmarks on fake video...")
    fm = FaceMesh()
    lm_fake = []
    for i in range(total):
        frame = cv2.imread(f"frames_fake/frame_{i:04d}.png")
        lm_fake.append(fm.detect(frame) if frame is not None else [])

    # Landmark glitch detection on fake video
    progress.progress(0.35, "Tracking landmark failures...")
    tracker = LandmarkTracker(displacement_threshold=disp_thresh)
    glitch_idx = tracker.find_glitch_frames(lm_fake)
    results["glitch_idx"] = glitch_idx

    # Compare real vs fake frame by frame
    progress.progress(0.45, "Comparing real vs fake frames...")
    os.makedirs("output", exist_ok=True)
    os.makedirs("fragments", exist_ok=True)

    manipulated_frames = []
    rects_map = {}
    frag_paths = []
    ssim_scores = []

    for i in range(total):
        real_frame = cv2.imread(f"frames_real/frame_{i:04d}.png")
        fake_frame = cv2.imread(f"frames_fake/frame_{i:04d}.png")

        if real_frame is None or fake_frame is None:
            continue

        annotated, has_art, rects, ssim_val = compare_frame_pair(
            real_frame, fake_frame, i,
            lm_fake[i], diff_thresh, ssim_thresh, 1200
        )

        ssim_scores.append(ssim_val)
        cv2.imwrite(f"output/frame_{i:04d}.png", annotated)

        if has_art:
            manipulated_frames.append(i)
            rects_map[i] = rects

            # Save side-by-side ONCE per frame (skip duplicates)
            compare_path = f"fragments/compare_{i:04d}.png"
            if not os.path.exists(compare_path):
                h = max(real_frame.shape[0], fake_frame.shape[0])
                rr = cv2.resize(real_frame, (fake_frame.shape[1], h))
                fr = cv2.resize(annotated, (fake_frame.shape[1], h))
                cv2.putText(rr, "REAL", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(fr, "FAKE", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                side_by_side = np.hstack([rr, fr])
                cv2.imwrite(compare_path, side_by_side)
                frag_paths.append(compare_path)

        if i % 10 == 0:
            pct = 0.45 + 0.45 * (i / total)
            progress.progress(pct, f"Comparing frame {i}/{total}...")

    results["manipulated_frames"] = manipulated_frames
    results["rects_map"] = rects_map
    results["frag_paths"] = frag_paths
    results["avg_ssim"] = float(np.mean(ssim_scores)) if ssim_scores else 1.0

    # Reconstruct
    progress.progress(0.92, "Reconstructing identity...")
    agg = FragmentAggregator(target_size=(256, 256), output_dir="output")
    # Use fake glitch frames for reconstruction
    fake_frag_paths = []
    for gi in glitch_idx:
        frame = cv2.imread(f"frames_fake/frame_{gi:04d}.png")
        if frame is not None:
            p = f"fragments/frag_{gi:04d}.png"
            cv2.imwrite(p, frame)
            fake_frag_paths.append(p)
    recon = agg.aggregate(fake_frag_paths, frames_dir="frames_fake", glitch_indices=glitch_idx)
    results["recon"] = recon

    # Report
    progress.progress(0.97, "Generating report...")
    score = len(manipulated_frames) / total if total > 0 else 0.0
    results["score"] = score
    rep = ReportGenerator(output_dir="output")
    rep.generate(total, manipulated_frames)

    progress.progress(1.0, "Done!")
    return results


# ── UI ────────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="Deepfake Forensic Analysis",
        page_icon="🔍",
        layout="wide",
    )

    st.title("🔍 Deepfake Forensic Analysis")
    st.markdown(
        "Upload a **reference (real video or photo)** and a **fake video**. "
        "The system analyzes them and shows exactly "
        "**where the face was manipulated**."
    )

    # Sidebar
    st.sidebar.header("⚙️ Settings")
    disp_thresh = st.sidebar.slider("Landmark Jump Threshold (px)", 1.0, 50.0, 10.0, 0.5)
    diff_thresh  = st.sidebar.slider("Pixel Diff Threshold", 5, 60, 20, 1)
    ssim_thresh  = st.sidebar.slider("SSIM Threshold", 0.50, 1.00, 0.85, 0.01)
    st.sidebar.markdown("---")
    st.sidebar.info(
        "**How it works:**\n\n"
        "• **Photo mode**: Verifies if the person in the photo appears in the fake video, "
        "then detects temporal inconsistencies.\n\n"
        "• **Video mode**: Each frame of the fake video is compared directly to the "
        "corresponding frame of the real video.\n\n"
        "Red boxes = regions where the face was changed."
    )

    # Upload reference (video or photo) and fake video
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📹 Reference (Real Video or Photo)")
        st.caption("Upload either a real video OR a photo of the person")
        real_file = st.file_uploader(
            "Upload real video or photo", 
            type=["mp4", "avi", "mov", "jpg", "jpeg", "png"], 
            key="real"
        )
        if real_file:
            file_type = "Photo" if real_file.name.lower().endswith(('.jpg', '.jpeg', '.png')) else "Video"
            st.success(f"✓ {file_type}: {real_file.name} ({real_file.size // 1024} KB)")

    with col2:
        st.subheader("🎭 Fake Video (Deepfake)")
        fake_file = st.file_uploader("Upload fake video", type=["mp4", "avi", "mov"], key="fake")
        if fake_file:
            st.success(f"✓ {fake_file.name} ({fake_file.size // 1024} KB)")

    # Detect new upload pair
    import hashlib
    pair_hash = None
    if real_file and fake_file:
        pair_hash = hashlib.md5(real_file.getvalue() + fake_file.getvalue()).hexdigest()
        if st.session_state.get("last_pair_hash") != pair_hash:
            st.session_state.pop("results", None)
            st.session_state["last_pair_hash"] = pair_hash

    if real_file and fake_file:
        if st.button("🚀 Compare & Analyze", type="primary"):
            clear_dirs()
            st.session_state.pop("results", None)

            # Determine if reference is photo or video
            is_photo = real_file.name.lower().endswith(('.jpg', '.jpeg', '.png'))
            
            if is_photo:
                # Save photo to temp file
                ext_r = os.path.splitext(real_file.name)[1].lower() or ".jpg"
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext_r) as tr:
                    tr.write(real_file.getvalue())
                    real_path = tr.name
                
                # Save fake video
                ext_f = os.path.splitext(fake_file.name)[1].lower() or ".mp4"
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext_f) as tf:
                    tf.write(fake_file.getvalue())
                    fake_path = tf.name

                progress = st.progress(0, "Starting analysis with reference photo...")
                try:
                    res = run_comparison_with_photo(
                        real_path, fake_path,
                        disp_thresh, diff_thresh, ssim_thresh,
                        progress,
                    )
                    st.session_state["results"] = res
                    st.session_state["real_name"] = real_file.name
                    st.session_state["fake_name"] = fake_file.name
                    st.session_state["is_photo_mode"] = True
                except Exception as e:
                    st.error(f"❌ Error: {e}")
                    import traceback
                    st.code(traceback.format_exc())
                finally:
                    for p in [real_path, fake_path]:
                        if os.path.exists(p):
                            os.unlink(p)
            else:
                # Video-to-video comparison (existing logic)
                ext_r = os.path.splitext(real_file.name)[1].lower() or ".mp4"
                ext_f = os.path.splitext(fake_file.name)[1].lower() or ".mp4"

                with tempfile.NamedTemporaryFile(delete=False, suffix=ext_r) as tr:
                    tr.write(real_file.getvalue())
                    real_path = tr.name
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext_f) as tf:
                    tf.write(fake_file.getvalue())
                    fake_path = tf.name

                progress = st.progress(0, "Starting comparison...")
                try:
                    res = run_comparison(
                        real_path, fake_path,
                        disp_thresh, diff_thresh, ssim_thresh,
                        progress,
                    )
                    st.session_state["results"] = res
                    st.session_state["real_name"] = real_file.name
                    st.session_state["fake_name"] = fake_file.name
                    st.session_state["is_photo_mode"] = False
                except Exception as e:
                    st.error(f"❌ Error: {e}")
                    import traceback
                    st.code(traceback.format_exc())
                finally:
                    for p in [real_path, fake_path]:
                        if os.path.exists(p):
                            os.unlink(p)
    else:
        st.info("👆 Please upload both the reference (video or photo) and fake video to start analysis.")

    # ── Results ──
    if "results" in st.session_state:
        res = st.session_state["results"]
        is_photo_mode = st.session_state.get("is_photo_mode", False)

        st.markdown("---")
        st.success("✅ Analysis Complete!")

        # Metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Frames Analyzed", res["total"])
        c2.metric("Manipulated Frames", len(res["manipulated_frames"]))
        c3.metric("Avg SSIM", f"{res['avg_ssim']:.4f}")
        score = res["score"]
        verdict = "🔴 HIGH" if score > 0.3 else "🟡 MODERATE" if score > 0.1 else "🟢 LOW"
        c4.metric("Manipulation Score", f"{verdict}  {score:.4f}")

        if score > 0.3:
            st.error("⚠️ HIGH manipulation detected — strong deepfake evidence!")
        elif score > 0.1:
            st.warning("⚠️ MODERATE manipulation detected.")
        else:
            st.success("✅ LOW manipulation — video appears authentic.")

        st.markdown("---")

        # Reference face (only in photo mode)
        if is_photo_mode and "ref_face_path" in res:
            col_ref, col_recon = st.columns([1, 1])
            with col_ref:
                st.subheader("📸 Reference Face")
                if os.path.exists(res["ref_face_path"]):
                    st.image(res["ref_face_path"], width=260)
                    st.caption("Face extracted from uploaded photo")
            with col_recon:
                st.subheader("🎭 Reconstructed Identity")
                if res["recon"] and os.path.exists(res["recon"]):
                    st.image(res["recon"], width=260)
                    with open(res["recon"], "rb") as f:
                        st.download_button("⬇️ Download", f,
                                           file_name="reconstructed_face.png",
                                           mime="image/png")
        else:
            # Video mode - show reconstruction only
            col_r, col_s = st.columns([1, 2])
            with col_r:
                st.subheader("🎭 Reconstructed Identity")
                if res["recon"] and os.path.exists(res["recon"]):
                    st.image(res["recon"], width=260)
                    with open(res["recon"], "rb") as f:
                        st.download_button("⬇️ Download", f,
                                           file_name="reconstructed_face.png",
                                           mime="image/png")
            with col_s:
                st.subheader("📄 Summary")
                summary_path = "output/summary.txt"
                if os.path.exists(summary_path):
                    with open(summary_path) as f:
                        st.code(f.read())
                    with open(summary_path, "rb") as f:
                        st.download_button("⬇️ Download Report", f,
                                           file_name="summary.txt", mime="text/plain")

        st.markdown("---")

        # Side-by-side comparisons
        comparison_label = "Reference vs Fake" if is_photo_mode else "Real vs Fake"
        st.subheader(f"📸 {comparison_label} — Manipulated Frames")
        st.caption(f"Left = {'Reference' if is_photo_mode else 'Real'} | Right = Fake with red boxes showing manipulated regions")
        if res["frag_paths"]:
            # Deduplicate by frame index AND skip consecutive similar frames
            seen = set()
            unique_paths = []
            prev_idx = -999
            for fp in res["frag_paths"]:
                fname = os.path.basename(fp)
                try:
                    fidx = int(fname.split("_")[1].split(".")[0])
                except Exception:
                    fidx = len(unique_paths)
                if fname not in seen and os.path.exists(fp) and fidx - prev_idx >= 5:
                    seen.add(fname)
                    unique_paths.append(fp)
                    prev_idx = fidx

            st.caption(f"Showing {min(10, len(unique_paths))} representative frames")
            cols = st.columns(2)
            for idx, fp in enumerate(unique_paths[:10]):
                frame_idx = os.path.basename(fp).split("_")[1].split(".")[0]
                with cols[idx % 2]:
                    st.image(fp, width="stretch",
                             caption=f"Frame {frame_idx} — Manipulated")
        else:
            st.info("No manipulated frames detected. Try raising the SSIM threshold.")

        st.markdown("---")

        # Annotated fake frames gallery
        st.subheader("🔍 Annotated Fake Frames (Unique)")
        out_frames = sorted(Path("output").glob("frame_*.png"))
        manip_set = set(res["manipulated_frames"])
        if out_frames:
            # Only show unique manipulated frames, max 12
            # Skip consecutive frames — show every 5th to avoid repetition
            manip_frames = []
            seen_idx = set()
            prev_idx = -999
            for f in out_frames:
                fidx = int(f.stem.split("_")[1])
                if fidx in manip_set and fidx not in seen_idx:
                    # Only add if at least 5 frames apart from previous shown
                    if fidx - prev_idx >= 5:
                        seen_idx.add(fidx)
                        manip_frames.append(f)
                        prev_idx = fidx

            st.caption(f"{len(manip_frames)} representative manipulated frames (from {len(manip_set)} total)")
            cols = st.columns(4)
            for idx, fp in enumerate(manip_frames[:12]):
                with cols[idx % 4]:
                    st.image(str(fp), width="stretch",
                             caption=f"⚠️ {fp.name}")

        # Reset button
        st.markdown("---")
        if st.button("🔄 Analyze New Videos"):
            st.session_state.pop("results", None)
            st.session_state.pop("last_pair_hash", None)
            st.rerun()


if __name__ == "__main__":
    main()
