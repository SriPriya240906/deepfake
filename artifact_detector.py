"""
artifact_detector.py — Detects and visualizes deepfake artifact regions.

Labels are now computed relative to actual detected face landmark positions,
not the full frame — so RIGHT EYE always appears on the actual eye region.
"""

import os
import cv2
import numpy as np
from skimage.metrics import structural_similarity


class ArtifactDetector:
    """
    Compares consecutive frames to detect deepfake artifact regions.
    Uses actual face landmark positions for accurate region labeling.
    """

    def __init__(
        self,
        diff_threshold: int = 25,       # higher = less sensitive, fewer false positives
        ssim_threshold: float = 0.80,   # only flag truly abnormal drops
        min_contour_area: int = 300,    # ignore tiny noise regions
        annotation_color: tuple[int, int, int] = (0, 0, 255),
        output_dir: str = "output",
        show_heatmap: bool = True,
        show_labels: bool = True,
    ) -> None:
        self.diff_threshold = diff_threshold
        self.ssim_threshold = ssim_threshold
        self.min_contour_area = min_contour_area
        self.annotation_color = annotation_color
        self.output_dir = output_dir
        self.show_heatmap = show_heatmap
        self.show_labels = show_labels

    def _label_from_landmarks(
        self,
        bx: int, by: int, bw: int, bh: int,
        landmarks: list[tuple[float, float, float]],
    ) -> str:
        """
        Label a bounding box by finding which face region's landmarks
        are closest to the box center.

        MediaPipe Face Mesh landmark indices (key ones):
          Left eye center  : 468 area → use 33, 133
          Right eye center : 362, 263
          Nose tip         : 1
          Mouth center     : 13, 14
          Left cheek       : 234
          Right cheek      : 454
          Forehead         : 10
          Chin             : 152
          Left eyebrow     : 70
          Right eyebrow    : 300
        """
        if not landmarks:
            return "ARTIFACT"

        cx = bx + bw // 2
        cy = by + bh // 2

        # Key landmark groups with their labels
        # Each entry: (label, [landmark_indices])
        regions = [
            ("LEFT EYE",    [33, 133, 159, 145]),
            ("RIGHT EYE",   [362, 263, 386, 374]),
            ("NOSE",        [1, 2, 98, 327]),
            ("MOUTH",       [13, 14, 61, 291, 17]),
            ("LEFT CHEEK",  [234, 93, 132]),
            ("RIGHT CHEEK", [454, 323, 361]),
            ("FOREHEAD",    [10, 67, 297]),
            ("CHIN",        [152, 175, 148, 377]),
            ("LEFT EYEBROW",[70, 63, 105]),
            ("RIGHT EYEBROW",[300, 293, 334]),
            ("FACE EDGE",   [234, 454, 152, 10]),
        ]

        best_label = "ARTIFACT"
        best_dist = float("inf")

        for label, indices in regions:
            for idx in indices:
                if idx < len(landmarks):
                    lx, ly, _ = landmarks[idx]
                    dist = ((cx - lx) ** 2 + (cy - ly) ** 2) ** 0.5
                    if dist < best_dist:
                        best_dist = dist
                        best_label = label

        return best_label

    def process_pair(
        self,
        frame_prev: np.ndarray,
        frame_curr: np.ndarray,
        frame_index: int,
        landmarks_curr: list[tuple[float, float, float]] = None,
    ) -> tuple[bool, list[tuple[int, int, int, int]]]:
        """
        Detects artifact regions between two consecutive frames.
        Uses landmarks_curr for accurate region labeling if provided.

        Returns (has_artifact, bounding_rects).
        """
        fh, fw = frame_curr.shape[:2]

        # --- 1. Grayscale ---
        gray_prev = cv2.cvtColor(frame_prev, cv2.COLOR_BGR2GRAY)
        gray_curr = cv2.cvtColor(frame_curr, cv2.COLOR_BGR2GRAY)

        # --- 2. Pixel difference ---
        diff = cv2.absdiff(gray_prev, gray_curr)

        # --- 3. SSIM ---
        mean_ssim, ssim_map = structural_similarity(gray_prev, gray_curr, full=True)
        ssim_diff = ((1.0 - ssim_map) * 127).astype(np.uint8)

        # --- 4. Combined inconsistency map ---
        combined = cv2.addWeighted(diff, 0.6, ssim_diff, 0.4, 0)

        # --- 5. Binary mask ---
        _, mask = cv2.threshold(combined, self.diff_threshold, 255, cv2.THRESH_BINARY)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # --- 6. Find contours ---
        contours, _ = cv2.findContours(
            mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # --- 7. Filter by area ---
        bounding_rects: list[tuple[int, int, int, int]] = []
        for contour in contours:
            if cv2.contourArea(contour) >= self.min_contour_area:
                x, y, w, h = cv2.boundingRect(contour)
                bounding_rects.append((x, y, w, h))

        has_artifact = mean_ssim < self.ssim_threshold and len(bounding_rects) > 0

        # --- 8. Annotate frame ---
        annotated = frame_curr.copy()

        if has_artifact and bounding_rects:
            # Heatmap overlay
            if self.show_heatmap:
                heatmap = cv2.applyColorMap(
                    cv2.GaussianBlur(combined, (21, 21), 0), cv2.COLORMAP_JET
                )
                heat_mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR).astype(bool)
                blended = cv2.addWeighted(annotated, 0.65, heatmap, 0.35, 0)
                annotated[heat_mask] = blended[heat_mask]

            # Draw boxes with landmark-based labels
            for x, y, w, h in bounding_rects:
                # Glow border
                cv2.rectangle(annotated, (x-2, y-2), (x+w+2, y+h+2), (0, 0, 120), 1)
                # Red box
                cv2.rectangle(annotated, (x, y), (x+w, y+h), self.annotation_color, 2)

                if self.show_labels:
                    # Use landmark positions if available, else skip label
                    if landmarks_curr:
                        label = self._label_from_landmarks(x, y, w, h, landmarks_curr)
                    else:
                        label = "ARTIFACT"

                    (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
                    label_y = max(y - 4, lh + 6)
                    cv2.rectangle(annotated,
                                  (x, label_y - lh - 4), (x + lw + 6, label_y),
                                  (0, 0, 180), -1)
                    cv2.putText(annotated, label, (x + 3, label_y - 2),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1)

            # Red banner
            cv2.rectangle(annotated, (0, fh - 38), (fw, fh), (0, 0, 180), -1)
            cv2.putText(annotated,
                        f"DEEPFAKE ARTIFACT DETECTED  |  Regions: {len(bounding_rects)}  |  SSIM: {mean_ssim:.3f}",
                        (8, fh - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (255, 255, 255), 1)
        else:
            # Green banner
            cv2.rectangle(annotated, (0, fh - 38), (fw, fh), (0, 130, 0), -1)
            cv2.putText(annotated, f"CLEAN FRAME  |  SSIM: {mean_ssim:.3f}",
                        (8, fh - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (255, 255, 255), 1)

        # Frame number
        cv2.putText(annotated, f"#{frame_index:04d}",
                    (fw - 70, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        os.makedirs(self.output_dir, exist_ok=True)
        cv2.imwrite(os.path.join(self.output_dir, f"frame_{frame_index:04d}.png"), annotated)

        return has_artifact, bounding_rects
