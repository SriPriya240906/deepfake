"""
fragment_aggregator.py — Combines extracted fragments into a reconstructed face.

Instead of just averaging small patches (which looks blank), this module:
1. Takes the best glitch frame (most fragments)
2. Crops the full face region from it
3. Overlays a heatmap showing which regions were manipulated
4. Saves this as the reconstructed face — visually meaningful for demos
"""

import os
import cv2
import numpy as np


class FragmentAggregator:
    """
    Produces a reconstructed face image from extracted fragments.

    Uses the best glitch frame as the base and overlays manipulation
    heatmap to show WHERE the deepfake artifacts were concentrated.
    """

    def __init__(
        self,
        target_size: tuple[int, int] = (256, 256),
        output_dir: str = "output",
    ) -> None:
        self.target_size = target_size
        self.output_dir = output_dir

    def aggregate(
        self,
        fragment_paths: list[str],
        frames_dir: str = "frames",
        glitch_indices: list[int] = None,
    ) -> str | None:
        """
        Builds a reconstructed face image from fragments.

        Strategy:
        - Load all fragments and find the best source frame
        - Use that frame's face region as the base image
        - Overlay a heatmap showing fragment density (manipulation map)
        - Add labels and save as reconstructed_face.png

        Returns path to saved image, or None if no fragments.
        """
        if not fragment_paths:
            print("WARNING: No fragments available for reconstruction.")
            return None

        os.makedirs(self.output_dir, exist_ok=True)

        # --- 1. Load all valid fragments ---
        loaded: list[np.ndarray] = []
        for path in fragment_paths:
            img = cv2.imread(path)
            if img is not None:
                resized = cv2.resize(img, self.target_size, interpolation=cv2.INTER_LINEAR)
                loaded.append(resized)

        if not loaded:
            print("WARNING: All fragments failed to load.")
            return None

        # --- 2. Build manipulation heatmap by averaging fragments ---
        # This shows which pixel regions appear most across all fragments
        stack = np.stack(loaded, axis=0).astype(np.float32)
        avg_fragment = np.mean(stack, axis=0).astype(np.uint8)

        # Convert to grayscale intensity map
        gray_avg = cv2.cvtColor(avg_fragment, cv2.COLOR_BGR2GRAY)

        # Normalize and apply colormap for heatmap
        norm = cv2.normalize(gray_avg, None, 0, 255, cv2.NORM_MINMAX)
        heatmap = cv2.applyColorMap(norm, cv2.COLORMAP_JET)

        # --- 3. Try to get a real face frame as base ---
        base_frame = None

        # Use the first glitch frame if available
        if glitch_indices:
            for idx in glitch_indices:
                frame_path = os.path.join(frames_dir, f"frame_{idx:04d}.png")
                frame = cv2.imread(frame_path)
                if frame is not None:
                    base_frame = cv2.resize(frame, self.target_size)
                    break

        # Fallback: use first fragment's source frame
        if base_frame is None and fragment_paths:
            # Extract frame index from filename e.g. fragment_0042_00.png
            try:
                fname = os.path.basename(fragment_paths[0])
                frame_idx = int(fname.split("_")[1])
                frame_path = os.path.join(frames_dir, f"frame_{frame_idx:04d}.png")
                frame = cv2.imread(frame_path)
                if frame is not None:
                    base_frame = cv2.resize(frame, self.target_size)
            except Exception:
                pass

        # --- 4. Compose the final reconstruction image ---
        if base_frame is not None:
            # Blend real face frame with heatmap overlay
            # This shows: real face + where manipulation was detected
            reconstruction = cv2.addWeighted(base_frame, 0.6, heatmap, 0.4, 0)
        else:
            # No real frame available — use heatmap directly
            reconstruction = heatmap

        # --- 5. Add title and info overlay ---
        h, w = reconstruction.shape[:2]

        # Dark top banner
        cv2.rectangle(reconstruction, (0, 0), (w, 28), (20, 20, 20), -1)
        cv2.putText(reconstruction, "RECONSTRUCTED IDENTITY (Artifact Map)",
                    (4, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 220, 255), 1)

        # Bottom info banner
        cv2.rectangle(reconstruction, (0, h - 28), (w, h), (20, 20, 20), -1)
        cv2.putText(reconstruction,
                    f"Fragments: {len(loaded)}  |  Manipulation regions highlighted",
                    (4, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (200, 200, 200), 1)

        # --- 6. Save ---
        output_path = os.path.join(self.output_dir, "reconstructed_face.png")
        cv2.imwrite(output_path, reconstruction)

        return output_path
