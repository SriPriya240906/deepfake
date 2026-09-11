"""
frame_extractor.py — Stage 1 of the deepfake forensic analysis pipeline.

Decodes a video file frame-by-frame and saves each frame as a PNG image.
Supported formats: MP4, AVI, MOV.
"""

import os
import cv2


# Extensions accepted by the pipeline
SUPPORTED_EXTENSIONS = {".mp4", ".avi", ".mov"}


class FrameExtractor:
    """Extracts individual frames from a video file and saves them as PNG images."""

    def __init__(self, video_path: str, output_dir: str = "frames") -> None:
        """
        Parameters
        ----------
        video_path : str
            Path to the source video file.
        output_dir : str
            Directory where extracted frames will be written (default: "frames").
        """
        self.video_path = video_path
        self.output_dir = output_dir

    def extract(self) -> tuple[int, float]:
        """
        Decode the video and save every frame as a zero-padded PNG.

        Frame files are named ``frame_0000.png``, ``frame_0001.png``, etc.
        and are written to ``self.output_dir``.

        Returns
        -------
        tuple[int, float]
            ``(total_frame_count, fps)`` — the number of frames written and
            the video's frames-per-second value reported by OpenCV.

        Raises
        ------
        FileNotFoundError
            If ``self.video_path`` does not point to an existing file.
        ValueError
            If the file extension is not in {.mp4, .avi, .mov}.
        RuntimeError
            If OpenCV cannot open the file even though the extension is valid.
        """
        # --- 1. Validate that the file exists on disk ---
        if not os.path.isfile(self.video_path):
            raise FileNotFoundError(
                f"Video file not found: '{self.video_path}'"
            )

        # --- 2. Validate the file extension ---
        _, ext = os.path.splitext(self.video_path)
        ext_lower = ext.lower()
        if ext_lower not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported video format '{ext_lower}'. "
                f"Supported formats: {sorted(SUPPORTED_EXTENSIONS)}"
            )

        # --- 3. Open the video with OpenCV ---
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise RuntimeError(
                f"OpenCV failed to open the video file: '{self.video_path}'"
            )

        # --- 4. Read video metadata ---
        fps = cap.get(cv2.CAP_PROP_FPS)

        # --- 5. Ensure the output directory exists ---
        os.makedirs(self.output_dir, exist_ok=True)

        # --- 6. Decode and save every frame ---
        frame_index = 0
        while True:
            ret, frame = cap.read()
            # ret is False when there are no more frames
            if not ret:
                break

            # Build zero-padded filename: frame_0000.png, frame_0001.png, …
            filename = f"frame_{frame_index:04d}.png"
            output_path = os.path.join(self.output_dir, filename)

            # Save the frame as a BGR PNG (lossless)
            cv2.imwrite(output_path, frame)
            frame_index += 1

        # --- 7. Release the video capture resource ---
        cap.release()

        total_frame_count = frame_index
        return total_frame_count, fps
