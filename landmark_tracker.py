"""
landmark_tracker.py

Detects "glitch frames" in a video by measuring how much facial landmarks
jump between consecutive frames. A large mean displacement suggests a
deepfake boundary or rendering artefact.
"""

import numpy as np


class LandmarkTracker:
    """
    Compares consecutive landmark lists and flags frames where the mean
    Euclidean displacement of all 468 MediaPipe face-mesh landmarks
    exceeds a configurable threshold.
    """

    def __init__(self, displacement_threshold: float = 10.0) -> None:
        # Maximum allowed mean landmark displacement (in pixels) before a
        # frame is considered a glitch.
        self.displacement_threshold = displacement_threshold

    def find_glitch_frames(
        self,
        landmark_sequence: list[list[tuple[float, float, float]]],
    ) -> list[int]:
        """
        Iterates consecutive pairs (N-1, N) in landmark_sequence.
        Returns a sorted list of frame indices N where the mean Euclidean
        displacement between frames N-1 and N exceeds displacement_threshold.

        Pairs where either landmark list is empty are skipped entirely.

        Parameters
        ----------
        landmark_sequence : list of landmark lists
            Each element is a list of 468 (x_px, y_px, z_px) tuples for one
            frame, or an empty list when no face was detected.

        Returns
        -------
        list[int]
            Sorted list of glitch frame indices.
        """
        glitch_frames: list[int] = []

        # Need at least two frames to form a consecutive pair.
        for n in range(1, len(landmark_sequence)):
            prev_landmarks = landmark_sequence[n - 1]
            curr_landmarks = landmark_sequence[n]

            # Skip this pair if either frame had no detected face.
            if len(prev_landmarks) == 0 or len(curr_landmarks) == 0:
                continue

            # Convert to (468, 3) numpy arrays for vectorised computation.
            arr_prev = np.array(prev_landmarks, dtype=np.float64)  # shape (468, 3)
            arr_curr = np.array(curr_landmarks, dtype=np.float64)  # shape (468, 3)

            # Compute per-landmark Euclidean distance using only x and y
            # (z is depth in MediaPipe's normalised space and is less reliable).
            # mean displacement = mean of sqrt((x2-x1)^2 + (y2-y1)^2) over 468 pts
            mean_displacement = np.mean(
                np.sqrt(np.sum((arr_curr[:, :2] - arr_prev[:, :2]) ** 2, axis=1))
            )

            # Flag frame N when the displacement exceeds the threshold.
            if mean_displacement > self.displacement_threshold:
                glitch_frames.append(n)

        # Return indices in ascending order (they are already inserted in order,
        # but sort explicitly to satisfy the contract regardless of future changes).
        return sorted(glitch_frames)
