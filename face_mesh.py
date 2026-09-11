"""
face_mesh.py — Wraps MediaPipe Face Mesh to detect 468 facial landmarks in a single BGR frame.

Supports both the legacy mediapipe.solutions API and the newer mediapipe Tasks API.
"""

import cv2
import numpy as np


class FaceMesh:
    """
    Stateless facial landmark detector using MediaPipe Face Mesh.

    Each call to detect() processes the frame independently.
    Supports mediapipe >= 0.10 (Tasks API) and older versions (solutions API).
    """

    def __init__(self) -> None:
        self._use_tasks = False
        self._detector = None
        self._legacy = None
        self._init_detector()

    def _init_detector(self) -> None:
        """Initialize the appropriate MediaPipe API based on installed version."""
        import mediapipe as mp

        # Try the newer Tasks-based API first (mediapipe >= 0.10)
        try:
            from mediapipe.tasks import python as mp_python
            from mediapipe.tasks.python import vision as mp_vision
            import urllib.request
            import os

            model_path = "face_landmarker.task"

            # Download the model if not present
            if not os.path.exists(model_path):
                print("  Downloading MediaPipe face landmarker model...")
                url = (
                    "https://storage.googleapis.com/mediapipe-models/"
                    "face_landmarker/face_landmarker/float16/1/face_landmarker.task"
                )
                urllib.request.urlretrieve(url, model_path)
                print("  ✓ Model downloaded.")

            base_options = mp_python.BaseOptions(model_asset_path=model_path)
            options = mp_vision.FaceLandmarkerOptions(
                base_options=base_options,
                num_faces=1,
            )
            self._detector = mp_vision.FaceLandmarker.create_from_options(options)
            self._use_tasks = True

        except Exception:
            # Fall back to legacy solutions API
            try:
                self._legacy = mp.solutions.face_mesh.FaceMesh(
                    static_image_mode=True,
                    max_num_faces=1,
                    refine_landmarks=False,
                )
                self._use_tasks = False
            except Exception as e:
                raise RuntimeError(
                    f"Could not initialize MediaPipe Face Mesh: {e}\n"
                    "Try: pip install mediapipe==0.10.9"
                ) from e

    def detect(self, frame: np.ndarray) -> list[tuple[float, float, float]]:
        """
        Runs MediaPipe Face Mesh on a single BGR frame.
        Returns list of 468 (x_px, y_px, z_px) tuples, or [] if no face detected.
        Coordinates are absolute pixels (not normalized).
        """
        if frame is None or frame.size == 0:
            return []

        height, width = frame.shape[:2]

        if self._use_tasks:
            return self._detect_tasks(frame, width, height)
        else:
            return self._detect_legacy(frame, width, height)

    def _detect_tasks(self, frame: np.ndarray, width: int, height: int) -> list[tuple[float, float, float]]:
        """Detect using the newer MediaPipe Tasks API."""
        import mediapipe as mp
        from mediapipe.tasks.python.vision import FaceLandmarkerResult

        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        result = self._detector.detect(mp_image)

        if not result.face_landmarks:
            return []

        face_landmarks = result.face_landmarks[0]
        return [
            (lm.x * width, lm.y * height, lm.z * width)
            for lm in face_landmarks
        ]

    def _detect_legacy(self, frame: np.ndarray, width: int, height: int) -> list[tuple[float, float, float]]:
        """Detect using the legacy mediapipe.solutions API."""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._legacy.process(rgb_frame)

        if not results.multi_face_landmarks:
            return []

        face_landmarks = results.multi_face_landmarks[0]
        return [
            (lm.x * width, lm.y * height, lm.z * width)
            for lm in face_landmarks.landmark
        ]
