# How the Deepfake Forensic Analysis System Works

## Core Concept: Temporal Inconsistency Detection

This system detects deepfakes **WITHOUT needing the original video**. It works by analyzing inconsistencies between consecutive frames within the same video.

---

## Why It Doesn't Need the Original Video

**Traditional approach (needs original):**
- Compare fake video to original video
- Find differences
- Problem: You rarely have the original

**Our approach (no original needed):**
- Compare each frame to the PREVIOUS frame in the SAME video
- Real videos have smooth transitions
- Deepfake videos have "glitches" where the AI fails
- Find these glitches automatically

---

## What the System Detects

### 1. Landmark Failures (Glitch Frames)
- Uses MediaPipe to detect 468 facial landmarks per frame
- Compares landmark positions between consecutive frames
- If landmarks suddenly "jump" more than threshold (default: 10 pixels), it's a glitch
- **Why this works:** Deepfake models sometimes fail to maintain consistent face geometry

### 2. Visual Artifacts (Frame Differencing + SSIM)
- Computes pixel-by-pixel difference between consecutive frames
- Computes SSIM (Structural Similarity Index) — measures how similar two frames are
- If difference is high OR SSIM is low, marks regions as artifacts
- **Why this works:** Deepfake models create:
  - Blending boundaries (face edge doesn't match background)
  - Texture inconsistencies (skin looks different frame-to-frame)
  - Lighting mismatches (face lighting shifts unnaturally)
  - Color shifts (hue/saturation changes abruptly)

### 3. Fragment Extraction
- Crops the detected artifact regions from glitch frames
- Saves them as individual images
- **Purpose:** Evidence of manipulation — these are the "smoking gun" patches

### 4. Reconstruction
- Takes a glitch frame (real face from the video)
- Overlays a heatmap showing WHERE artifacts were concentrated
- Red = heavily manipulated, Blue = less affected
- **Purpose:** Visual summary showing which face regions were most manipulated

---

## Output Explained

### Deepfake Score
```
Score = (Number of Glitch Frames) / (Total Frames)
```
- 0.00 - 0.02: Likely real or very high-quality deepfake
- 0.02 - 0.10: Moderate deepfake likelihood
- 0.10+: High deepfake likelihood

### Annotated Frames
- Original frame with RED BOXES drawn around artifact regions
- Each box labeled: LEFT EYE, MOUTH, FACE EDGE, etc.
- Bottom banner shows: DEEPFAKE ARTIFACT DETECTED or CLEAN FRAME

### Fragments
- Small cropped images of the artifact regions
- Named: `fragment_0042_00.png` (frame 42, patch 0)

### Reconstructed Face
- Real face from a glitch frame
- Color heatmap overlay showing manipulation intensity
- Shows which facial regions were most affected

---

## Why It Works on Any Fake Video

The system looks for **temporal inconsistencies** — things that change unnaturally between frames.

**Examples of what it catches:**
- Face-swap models: boundary flickering, lighting mismatches
- Face reenactment: landmark geometry jumps
- Lip-sync deepfakes: mouth region texture changes
- GAN-generated faces: temporal instability in fine details

**It doesn't need:**
- The original person's video
- Training data
- A machine learning model
- Comparison to a database

**It only needs:**
- The suspicious video itself
- Consecutive frames to compare

---

## Limitations

1. **Very high-quality deepfakes** with perfect temporal consistency may score low
2. **Real videos with fast motion** may trigger false positives
3. **Low-resolution videos** may not have enough detail for landmark detection
4. **Videos without faces** won't work (system requires face detection)

---

## Adjusting Sensitivity

In the Streamlit UI sidebar, you can tune:

- **Landmark Displacement Threshold** (default: 10px)
  - Lower = more sensitive (catches smaller jumps)
  - Higher = less sensitive (only catches large jumps)

- **Frame Diff Threshold** (default: 8)
  - Lower = more sensitive (flags smaller pixel changes)
  - Higher = less sensitive (only flags large changes)

- **SSIM Threshold** (default: 0.98)
  - Higher = more sensitive (flags even slight similarity drops)
  - Lower = less sensitive (only flags major similarity drops)

---

## For Your Professor Demo

**Key points to explain:**
1. "This system detects deepfakes by finding temporal inconsistencies — places where the AI model failed to maintain smooth transitions between frames."

2. "It doesn't need the original video because it compares each frame to the previous frame in the same video."

3. "The red boxes show exactly WHERE the manipulation happened — eye regions, face boundaries, mouth areas, etc."

4. "The deepfake score tells us what percentage of frames had detectable artifacts."

5. "This approach works on any type of face manipulation: face swaps, reenactment, lip-sync, or GAN-generated faces."
