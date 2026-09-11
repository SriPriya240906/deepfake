"""
create_test_video.py — Generates a synthetic test video for pipeline testing.

Creates a 5-second MP4 with a moving colored rectangle simulating face-like
motion, including intentional "glitch" frames with sudden jumps.
"""

import cv2
import numpy as np
import os


def create_test_video(output_path: str = "test_video.mp4", fps: int = 10, duration: int = 5):
    """
    Creates a synthetic test video with simulated face-like motion and glitch frames.

    Parameters
    ----------
    output_path : str
        Path to save the generated video.
    fps : int
        Frames per second (default: 10).
    duration : int
        Duration in seconds (default: 5).
    """
    width, height = 640, 480
    total_frames = fps * duration

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    print(f"Generating test video: {output_path}")
    print(f"  Resolution: {width}x{height}, {fps} FPS, {duration}s ({total_frames} frames)")

    for i in range(total_frames):
        # Create a dark background
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:] = (30, 30, 50)  # dark blue-grey background

        # Simulate smooth face movement
        cx = int(width // 2 + 80 * np.sin(i * 0.2))
        cy = int(height // 2 + 40 * np.cos(i * 0.15))

        # Introduce glitch frames at specific intervals (sudden position jump)
        is_glitch = (i % 8 == 0 and i > 0)
        if is_glitch:
            cx += np.random.randint(-100, 100)
            cy += np.random.randint(-80, 80)
            # Add noise to simulate deepfake artifact
            noise = np.random.randint(0, 60, frame.shape, dtype=np.uint8)
            frame = cv2.add(frame, noise)

        # Draw a face-like oval (skin tone)
        cv2.ellipse(frame, (cx, cy), (90, 110), 0, 0, 360, (180, 140, 100), -1)

        # Eyes
        cv2.circle(frame, (cx - 30, cy - 20), 12, (50, 50, 80), -1)
        cv2.circle(frame, (cx + 30, cy - 20), 12, (50, 50, 80), -1)
        cv2.circle(frame, (cx - 30, cy - 20), 5, (255, 255, 255), -1)
        cv2.circle(frame, (cx + 30, cy - 20), 5, (255, 255, 255), -1)

        # Nose
        cv2.ellipse(frame, (cx, cy + 10), (10, 15), 0, 0, 360, (160, 120, 80), -1)

        # Mouth
        cv2.ellipse(frame, (cx, cy + 45), (30, 12), 0, 0, 180, (120, 80, 80), 2)

        # Add frame number text
        cv2.putText(
            frame,
            f"Frame {i:03d}{'  [GLITCH]' if is_glitch else ''}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (200, 200, 200),
            2,
        )

        writer.write(frame)

    writer.release()
    print(f"  ✓ Saved to: {os.path.abspath(output_path)}")
    print(f"\nRun the analysis with:")
    print(f"  python main.py {output_path}")
    print(f"\nOr launch the web UI with:")
    print(f"  python -m streamlit run app.py")


if __name__ == "__main__":
    create_test_video()
