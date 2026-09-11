"""
create_demo_video.py — Generates a realistic deepfake simulation video for demo purposes.

Creates a video that simulates deepfake artifacts:
- Smooth face movement (normal frames)
- Sudden landmark jumps (glitch frames)
- Face texture inconsistencies (blending artifacts)
- Color/lighting shifts between frames
- Edge flickering around face boundary

This is suitable for demonstrating the forensic analysis pipeline to professors.
"""

import cv2
import numpy as np
import os


def draw_realistic_face(frame, cx, cy, skin_tone, lighting_factor=1.0, noise_level=0):
    """Draw a detailed synthetic face at position (cx, cy)."""
    h, w = frame.shape[:2]

    # Clamp position to frame bounds
    cx = max(100, min(w - 100, cx))
    cy = max(120, min(h - 120, cy))

    # --- Face oval ---
    face_color = tuple(int(c * lighting_factor) for c in skin_tone)
    cv2.ellipse(frame, (cx, cy), (85, 105), 0, 0, 360, face_color, -1)

    # --- Forehead shading ---
    forehead_color = tuple(min(255, int(c * lighting_factor * 1.05)) for c in skin_tone)
    cv2.ellipse(frame, (cx, cy - 40), (70, 50), 0, 180, 360, forehead_color, -1)

    # --- Eyebrows ---
    brow_color = (40, 30, 20)
    cv2.ellipse(frame, (cx - 30, cy - 38), (22, 6), -10, 0, 180, brow_color, -1)
    cv2.ellipse(frame, (cx + 30, cy - 38), (22, 6), 10, 0, 180, brow_color, -1)

    # --- Eyes (whites) ---
    cv2.ellipse(frame, (cx - 30, cy - 22), (18, 11), 0, 0, 360, (240, 240, 240), -1)
    cv2.ellipse(frame, (cx + 30, cy - 22), (18, 11), 0, 0, 360, (240, 240, 240), -1)

    # --- Irises ---
    iris_color = (60, 80, 120)
    cv2.circle(frame, (cx - 30, cy - 22), 8, iris_color, -1)
    cv2.circle(frame, (cx + 30, cy - 22), 8, iris_color, -1)

    # --- Pupils ---
    cv2.circle(frame, (cx - 30, cy - 22), 4, (10, 10, 10), -1)
    cv2.circle(frame, (cx + 30, cy - 22), 4, (10, 10, 10), -1)

    # --- Eye highlights ---
    cv2.circle(frame, (cx - 27, cy - 25), 2, (255, 255, 255), -1)
    cv2.circle(frame, (cx + 33, cy - 25), 2, (255, 255, 255), -1)

    # --- Nose ---
    nose_color = tuple(max(0, int(c * lighting_factor * 0.88)) for c in skin_tone)
    cv2.ellipse(frame, (cx, cy + 8), (12, 18), 0, 0, 360, nose_color, -1)
    cv2.circle(frame, (cx - 10, cy + 22), 6, nose_color, -1)
    cv2.circle(frame, (cx + 10, cy + 22), 6, nose_color, -1)

    # --- Lips ---
    lip_color = (80, 60, 120)
    cv2.ellipse(frame, (cx, cy + 45), (28, 10), 0, 0, 180, lip_color, -1)
    cv2.ellipse(frame, (cx, cy + 38), (28, 8), 0, 180, 360, lip_color, -1)

    # --- Chin ---
    chin_color = tuple(max(0, int(c * lighting_factor * 0.92)) for c in skin_tone)
    cv2.ellipse(frame, (cx, cy + 80), (55, 35), 0, 0, 180, chin_color, -1)

    # --- Ears ---
    ear_color = tuple(max(0, int(c * lighting_factor * 0.85)) for c in skin_tone)
    cv2.ellipse(frame, (cx - 88, cy), (12, 22), 0, 0, 360, ear_color, -1)
    cv2.ellipse(frame, (cx + 88, cy), (12, 22), 0, 0, 360, ear_color, -1)

    # --- Hair ---
    hair_color = (30, 20, 15)
    cv2.ellipse(frame, (cx, cy - 80), (90, 55), 0, 180, 360, hair_color, -1)
    cv2.rectangle(frame, (cx - 90, cy - 110), (cx + 90, cy - 80), hair_color, -1)

    # --- Add noise if glitch frame ---
    if noise_level > 0:
        noise_region = frame[max(0, cy-110):min(h, cy+110), max(0, cx-100):min(w, cx+100)]
        if noise_region.size > 0:
            noise = np.random.randint(0, noise_level, noise_region.shape, dtype=np.uint8)
            frame[max(0, cy-110):min(h, cy+110), max(0, cx-100):min(w, cx+100)] = cv2.add(
                noise_region, noise
            )

    return frame


def add_deepfake_artifact(frame, cx, cy, artifact_type):
    """Add visible deepfake-style artifacts to a frame."""
    h, w = frame.shape[:2]

    if artifact_type == "edge_flicker":
        # Flickering edge around face — common deepfake artifact
        for r in range(80, 115, 5):
            color = (
                np.random.randint(100, 200),
                np.random.randint(50, 150),
                np.random.randint(50, 150),
            )
            cv2.ellipse(frame, (cx, cy), (r, r + 20), 0, 0, 360, color, 1)

    elif artifact_type == "color_shift":
        # Sudden color/lighting shift — face looks different from background
        face_region = frame[max(0, cy-110):min(h, cy+110), max(0, cx-100):min(w, cx+100)]
        if face_region.size > 0:
            # Shift hue of face region
            hsv = cv2.cvtColor(face_region, cv2.COLOR_BGR2HSV).astype(np.float32)
            hsv[:, :, 0] = (hsv[:, :, 0] + 15) % 180
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.3, 0, 255)
            frame[max(0, cy-110):min(h, cy+110), max(0, cx-100):min(w, cx+100)] = \
                cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    elif artifact_type == "blur_boundary":
        # Blurry boundary between face and background — GAN blending artifact
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.ellipse(mask, (cx, cy), (90, 110), 0, 0, 360, 255, 15)
        blurred = cv2.GaussianBlur(frame, (21, 21), 0)
        frame[mask > 0] = blurred[mask > 0]

    elif artifact_type == "texture_inconsistency":
        # Patch of different texture — common in face-swap models
        patch_x = cx - 20 + np.random.randint(-30, 30)
        patch_y = cy - 10 + np.random.randint(-20, 20)
        patch_size = np.random.randint(20, 45)
        x1, y1 = max(0, patch_x), max(0, patch_y)
        x2, y2 = min(w, patch_x + patch_size), min(h, patch_y + patch_size)
        if x2 > x1 and y2 > y1:
            patch = frame[y1:y2, x1:x2].copy()
            patch = cv2.GaussianBlur(patch, (7, 7), 0)
            patch = cv2.addWeighted(patch, 0.6, np.full_like(patch, 180), 0.4, 0)
            frame[y1:y2, x1:x2] = patch

    return frame


def create_demo_video(output_path: str = "deepfake_demo.mp4", fps: int = 15, duration: int = 8):
    """
    Creates a realistic deepfake simulation video.

    Parameters
    ----------
    output_path : str
        Output video file path.
    fps : int
        Frames per second.
    duration : int
        Duration in seconds.
    """
    width, height = 640, 480
    total_frames = fps * duration

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # Two different "identities" — simulates face swap
    identity_A = (180, 145, 110)  # lighter skin tone
    identity_B = (120, 95, 75)    # darker skin tone

    artifact_types = ["edge_flicker", "color_shift", "blur_boundary", "texture_inconsistency"]

    print(f"\nGenerating deepfake demo video: {output_path}")
    print(f"  {width}x{height} @ {fps}fps, {duration}s = {total_frames} frames")
    print(f"  Simulating: face swaps, glitch frames, artifact regions\n")

    glitch_count = 0

    for i in range(total_frames):
        # Background — gradient to look like a room
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        for row in range(height):
            intensity = int(60 + 40 * (row / height))
            frame[row, :] = (intensity, intensity - 10, intensity - 20)

        # Smooth face movement (natural head motion)
        cx = int(width // 2 + 30 * np.sin(i * 0.18))
        cy = int(height // 2 - 20 + 15 * np.cos(i * 0.12))

        # Determine frame type
        # Glitch frames: every ~12 frames after frame 5
        is_glitch = (i > 5) and (i % 12 == 0)

        # Face swap frames: alternate identity every 20 frames (simulates deepfake swap)
        swap_phase = (i // 20) % 2
        current_identity = identity_A if swap_phase == 0 else identity_B

        # Lighting variation
        lighting = 0.9 + 0.15 * np.sin(i * 0.1)

        if is_glitch:
            glitch_count += 1
            # Sudden position jump — landmark failure
            cx += np.random.randint(-60, 60)
            cy += np.random.randint(-40, 40)

            # Draw face with wrong identity (swap artifact)
            wrong_identity = identity_B if swap_phase == 0 else identity_A
            frame = draw_realistic_face(frame, cx, cy, wrong_identity, lighting, noise_level=40)

            # Add visible artifact
            artifact = artifact_types[glitch_count % len(artifact_types)]
            frame = add_deepfake_artifact(frame, cx, cy, artifact)

            # Label
            cv2.putText(frame, f"FRAME {i:03d} [GLITCH - {artifact.upper()}]",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 80, 255), 2)
            cv2.putText(frame, "DEEPFAKE ARTIFACT DETECTED",
                        (10, height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        else:
            # Normal frame
            frame = draw_realistic_face(frame, cx, cy, current_identity, lighting)
            cv2.putText(frame, f"FRAME {i:03d}  [Identity {'A' if swap_phase == 0 else 'B'}]",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180, 220, 180), 1)

        # Add subtle scan line effect for realism
        if i % 3 == 0:
            scan_y = (i * 7) % height
            frame[scan_y:scan_y+1, :] = frame[scan_y:scan_y+1, :] // 2

        writer.write(frame)

    writer.release()

    print(f"✓ Video saved: {os.path.abspath(output_path)}")
    print(f"  Total frames : {total_frames}")
    print(f"  Glitch frames: {glitch_count}")
    print(f"  Expected deepfake score: ~{glitch_count/total_frames:.4f}")
    print(f"\n{'='*55}")
    print("HOW TO RUN THE ANALYSIS:")
    print(f"{'='*55}")
    print(f"\n  CLI mode:")
    print(f"    python main.py {output_path}")
    print(f"\n  Web UI mode:")
    print(f"    python -m streamlit run app.py")
    print(f"\n  Then upload '{output_path}' in the browser UI")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    create_demo_video()
