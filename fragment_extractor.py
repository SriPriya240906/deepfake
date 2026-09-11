"""
fragment_extractor.py — Extracts inconsistent image patches from glitch frames.

Crops bounding rectangles identified by the artifact detector and saves them
as individual fragment images for later reconstruction.
"""

import os
import cv2
import numpy as np


class FragmentExtractor:
    """
    Extracts and saves image patches (fragments) from frames where artifacts
    were detected.
    """

    def __init__(self, output_dir: str = "fragments") -> None:
        """
        Parameters
        ----------
        output_dir : str
            Directory where fragment images are saved (default: "fragments").
        """
        self.output_dir = output_dir

    def extract(
        self,
        frame: np.ndarray,
        frame_index: int,
        bounding_rects: list[tuple[int, int, int, int]],
    ) -> list[str]:
        """
        Crops each bounding rect from frame and saves to output_dir.
        Falls back to centered 128x128 crop when bounding_rects is empty.
        Returns list of saved file paths.

        Parameters
        ----------
        frame : np.ndarray
            The source frame (BGR image).
        frame_index : int
            Index of the frame in the video sequence.
        bounding_rects : list of (x, y, w, h) tuples
            Bounding rectangles to crop from the frame.

        Returns
        -------
        list[str]
            List of file paths for all saved fragment images.
        """
        # --- 1. Ensure output directory exists ---
        os.makedirs(self.output_dir, exist_ok=True)

        saved_paths: list[str] = []

        # --- 2. If no bounding rects provided, use fallback centered crop ---
        if len(bounding_rects) == 0:
            h, w = frame.shape[:2]
            # Centered 128x128 crop, clamped to frame bounds
            crop_size = 128
            cx = max(0, w // 2 - crop_size // 2)
            cy = max(0, h // 2 - crop_size // 2)
            cx = min(cx, w - crop_size) if w >= crop_size else 0
            cy = min(cy, h - crop_size) if h >= crop_size else 0

            # Extract the crop (handle edge case where frame is smaller than 128x128)
            x_end = min(cx + crop_size, w)
            y_end = min(cy + crop_size, h)
            fragment = frame[cy:y_end, cx:x_end]

            # Save fallback fragment
            filename = f"fragment_{frame_index:04d}_00.png"
            output_path = os.path.join(self.output_dir, filename)
            cv2.imwrite(output_path, fragment)
            saved_paths.append(output_path)

            return saved_paths

        # --- 3. Crop and save each bounding rectangle ---
        for patch_index, (x, y, w, h) in enumerate(bounding_rects):
            # Clamp coordinates to frame bounds
            h_frame, w_frame = frame.shape[:2]
            x = max(0, x)
            y = max(0, y)
            x_end = min(x + w, w_frame)
            y_end = min(y + h, h_frame)

            # Extract the fragment
            fragment = frame[y:y_end, x:x_end]

            # Save with naming convention: fragment_NNNN_PP.png
            filename = f"fragment_{frame_index:04d}_{patch_index:02d}.png"
            output_path = os.path.join(self.output_dir, filename)
            cv2.imwrite(output_path, fragment)
            saved_paths.append(output_path)

        return saved_paths
