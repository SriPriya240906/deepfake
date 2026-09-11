# Design Document: Deepfake Forensic Analysis

## Overview

The Deepfake Forensic Analysis system is a Python pipeline that ingests a video file and produces forensic evidence of deepfake manipulation. It works by extracting frames, running MediaPipe Face Mesh to track 468 facial landmarks per frame, flagging frames where landmark geometry jumps unexpectedly (Glitch_Frames), computing SSIM-based visual inconsistency maps, cropping artifact patches (Fragments), averaging those patches into a Reconstructed_Face image, and emitting a summary report with a normalized Deepfake_Score.

The system is designed as a set of independent, single-responsibility Python modules orchestrated by a `main.py` entry point. An optional Streamlit web UI wraps the same pipeline for browser-based use.

### Key Design Goals

- **Modularity**: each processing stage is a self-contained class/module so it can be tested or swapped independently.
- **Determinism**: given the same video and configuration, the system always produces identical output.
- **Traceability**: every output file is named after its source frame index so results can be traced back to the original video timeline.
- **Configurability**: thresholds (displacement, SSIM, diff intensity, contour area) are constructor/function parameters with sensible defaults.

---

## Architecture

The pipeline is strictly linear. Data flows forward; no module calls back into a previous stage.

```mermaid
flowchart TD
    A[Video File] --> B[Frame_Extractor]
    B --> C[Face_Mesh]
    C --> D[Landmark_Tracker]
    B --> E[Artifact_Detector]
    D --> E
    E --> F[Fragment_Extractor]
    D --> F
    F --> G[Fragment_Aggregator]
    B --> H[Report_Generator]
    D --> H
    G --> H
    H --> I[summary.txt / stdout]
    E --> J[/output/ annotated frames]
    F --> K[/fragments/ patches]
    G --> L[/output/reconstructed_face.png]
```

`main.py` drives the pipeline sequentially:

1. Extract frames → `/frames/`
2. For each frame: run Face_Mesh, collect landmark lists
3. Run Landmark_Tracker over the full landmark sequence → glitch indices
4. For each consecutive frame pair: run Artifact_Detector → annotated frames in `/output/`
5. For each glitch frame: run Fragment_Extractor → patches in `/fragments/`
6. Run Fragment_Aggregator over all patches → `reconstructed_face.png`
7. Run Report_Generator → `summary.txt` + stdout

---

## Components and Interfaces

### FrameExtractor (`frame_extractor.py`)

```python
class FrameExtractor:
    def __init__(self, video_path: str, output_dir: str = "frames") -> None: ...

    def extract(self) -> tuple[int, float]:
        """
        Decodes the video, saves each frame as frame_NNNN.png under output_dir.
        Returns (total_frame_count, fps).
        Raises FileNotFoundError or ValueError for invalid paths/formats.
        """
```

- Uses `cv2.VideoCapture`.
- Supported formats: MP4, AVI, MOV (validated by extension and by checking `cap.isOpened()`).
- Frames saved as BGR PNG images.

---

### FaceMesh (`face_mesh.py`)

```python
class FaceMesh:
    def __init__(self) -> None: ...

    def detect(self, frame: np.ndarray) -> list[tuple[float, float, float]]:
        """
        Runs MediaPipe Face Mesh on a single BGR frame.
        Returns list of 468 (x_px, y_px, z_px) tuples, or [] if no face detected.
        Coordinates are absolute pixels (not normalized).
        """
```

- Wraps `mediapipe.solutions.face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1)`.
- Converts normalized coords: `x_px = lm.x * width`, `y_px = lm.y * height`.
- Stateless: a new MediaPipe context is used per call (or the instance is reused with `static_image_mode=True` which processes each image independently).

---

### LandmarkTracker (`landmark_tracker.py`)

```python
class LandmarkTracker:
    def __init__(self, displacement_threshold: float = 10.0) -> None: ...

    def find_glitch_frames(
        self,
        landmark_sequence: list[list[tuple[float, float, float]]]
    ) -> list[int]:
        """
        Iterates consecutive pairs. Returns sorted list of frame indices
        where mean Euclidean displacement exceeds displacement_threshold.
        Skips pairs where either landmark list is empty.
        """
```

- Mean displacement = average of per-landmark Euclidean distances across all 468 pairs.
- Only the *current* frame index (N) is added to the glitch list when the pair (N-1, N) exceeds the threshold.

---

### ArtifactDetector (`artifact_detector.py`)

```python
class ArtifactDetector:
    def __init__(
        self,
        diff_threshold: int = 30,
        ssim_threshold: float = 0.85,
        min_contour_area: int = 500,
        annotation_color: tuple[int, int, int] = (0, 0, 255),
        output_dir: str = "output",
    ) -> None: ...

    def process_pair(
        self,
        frame_prev: np.ndarray,
        frame_curr: np.ndarray,
        frame_index: int,
    ) -> tuple[bool, list[tuple[int, int, int, int]]]:
        """
        Computes diff + SSIM between grayscale versions of the two frames.
        Draws bounding rects on frame_curr for regions exceeding thresholds.
        Saves annotated frame to output_dir/frame_NNNN.png.
        Returns (has_artifact: bool, bounding_rects: list of (x, y, w, h)).
        """
```

- Uses `cv2.absdiff` for per-pixel difference, `skimage.metrics.structural_similarity` for SSIM.
- Contours found via `cv2.findContours` on the thresholded diff mask.
- Bounding rects drawn only when `mean_ssim < ssim_threshold`.

---

### FragmentExtractor (`fragment_extractor.py`)

```python
class FragmentExtractor:
    def __init__(self, output_dir: str = "fragments") -> None: ...

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
        """
```

- File naming: `fragment_{frame_index:04d}_{patch_index:02d}.png`.
- Fallback crop: `cx = w//2 - 64`, `cy = h//2 - 64` clamped to frame bounds.

---

### FragmentAggregator (`fragment_aggregator.py`)

```python
class FragmentAggregator:
    def __init__(
        self,
        target_size: tuple[int, int] = (256, 256),
        output_dir: str = "output",
    ) -> None: ...

    def aggregate(self, fragment_paths: list[str]) -> str | None:
        """
        Resizes all fragments to target_size, computes per-pixel mean.
        Saves result as reconstructed_face.png.
        Returns output path, or None if fragment_paths is empty (logs warning).
        """
```

- Uses `np.mean(stack, axis=0).astype(np.uint8)` for pixel averaging.
- Single-fragment case: resize and save directly without averaging.

---

### ReportGenerator (`report_generator.py`)

```python
class ReportGenerator:
    def __init__(self, output_dir: str = "output") -> None: ...

    def generate(
        self,
        total_frames: int,
        glitch_indices: list[int],
    ) -> float:
        """
        Computes deepfake_score = len(glitch_indices) / total_frames.
        Prints summary to stdout and saves summary.txt.
        Returns deepfake_score.
        """
```

- Deepfake_Score clamped to [0.0, 1.0] (edge case: 0 total frames → score = 0.0).
- Summary format:
  ```
  Total Frames : 1200
  Glitch Frames: 47
  Deepfake Score: 0.0392
  ```

---

### main.py

Orchestrates all modules. Accepts CLI arguments via `argparse`:

| Argument | Default | Description |
|---|---|---|
| `video` | (required) | Path to input video |
| `--displacement-threshold` | 10.0 | Landmark displacement threshold |
| `--diff-threshold` | 30 | Pixel diff threshold |
| `--ssim-threshold` | 0.85 | SSIM threshold |
| `--ui` | False | Launch Streamlit UI |

---

### app.py (Optional Streamlit UI)

Wraps the pipeline behind a Streamlit interface:
- File uploader (MP4/AVI/MOV)
- Progress bar during frame processing
- Displays Deepfake_Score, Glitch_Frame count
- Gallery of annotated frames and fragment patches
- Gallery of Reconstructed_Face
- Download buttons for `reconstructed_face.png` and `summary.txt`

---

## Data Models

### Directory Layout

```
<working_dir>/
├── frames/
│   ├── frame_0000.png
│   └── frame_NNNN.png
├── fragments/
│   ├── fragment_0042_00.png
│   └── fragment_NNNN_PP.png
└── output/
    ├── frame_0000.png          # annotated
    ├── frame_NNNN.png
    ├── reconstructed_face.png
    └── summary.txt
```

### In-Memory Types

```python
# Landmark list for one frame
LandmarkList = list[tuple[float, float, float]]  # (x_px, y_px, z_px), len=468 or 0

# Full landmark sequence across all frames
LandmarkSequence = list[LandmarkList]

# Bounding rectangle from ArtifactDetector
BoundingRect = tuple[int, int, int, int]  # (x, y, w, h)

# Deepfake score
DeepfakeScore = float  # in [0.0, 1.0]
```

### Configuration Defaults

| Parameter | Default | Module |
|---|---|---|
| `displacement_threshold` | 10.0 px | LandmarkTracker |
| `diff_threshold` | 30 | ArtifactDetector |
| `ssim_threshold` | 0.85 | ArtifactDetector |
| `min_contour_area` | 500 px² | ArtifactDetector |
| `annotation_color` | (0,0,255) BGR | ArtifactDetector |
| `target_size` | (256, 256) | FragmentAggregator |
| `fallback_crop_size` | 128×128 | FragmentExtractor |


---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Frame extraction round-trip

*For any* valid video file containing N frames, after `FrameExtractor.extract()` completes, exactly N PNG files named `frame_0000.png` through `frame_{N-1:04d}.png` shall exist in the output directory, and the returned frame count shall equal N.

**Validates: Requirements 1.2, 1.4, 1.5**

---

### Property 2: Invalid input always raises

*For any* file path that does not exist or has an extension outside {.mp4, .avi, .mov}, `FrameExtractor.extract()` shall raise an exception.

**Validates: Requirements 1.3**

---

### Property 3: Face Mesh output shape invariant

*For any* BGR image frame in which MediaPipe detects a face, `FaceMesh.detect()` shall return a list of exactly 468 elements, and every (x, y) coordinate shall satisfy `0 <= x <= frame_width` and `0 <= y <= frame_height`.

**Validates: Requirements 2.1, 2.3**

---

### Property 4: Face Mesh statelessness (idempotence)

*For any* BGR image frame, calling `FaceMesh.detect()` twice on the same frame shall return identical results.

**Validates: Requirements 2.4**

---

### Property 5: Glitch classification correctness

*For any* landmark sequence, a frame index N shall appear in `LandmarkTracker.find_glitch_frames()` if and only if both landmark lists at positions N-1 and N are non-empty and the mean Euclidean displacement between them exceeds `displacement_threshold`. The returned list shall be sorted in ascending order.

**Validates: Requirements 3.1, 3.2, 3.4, 3.5**

---

### Property 6: Identical frames produce no artifacts

*For any* frame F, calling `ArtifactDetector.process_pair(F, F, index)` shall return `has_artifact=False` and an empty bounding-rect list, because the pixel diff is zero and SSIM is 1.0.

**Validates: Requirements 4.1, 4.2, 4.3**

---

### Property 7: Bounding rect count matches contour count

*For any* pair of frames, the number of bounding rectangles returned by `ArtifactDetector.process_pair()` shall equal the number of contours in the thresholded diff mask whose area is ≥ `min_contour_area`.

**Validates: Requirements 4.4**

---

### Property 8: Annotated frame always saved

*For any* frame index processed by `ArtifactDetector.process_pair()`, the file `output/frame_{index:04d}.png` shall exist after the call, regardless of whether artifacts were detected.

**Validates: Requirements 4.5, 4.6**

---

### Property 9: Fragment extraction round-trip

*For any* frame and list of N bounding rectangles (N ≥ 1), `FragmentExtractor.extract()` shall return exactly N file paths, each following the naming convention `fragment_{frame_index:04d}_{patch_index:02d}.png`, and each path shall point to an existing file on disk.

**Validates: Requirements 5.1, 5.2, 5.4**

---

### Property 10: Reconstructed face size invariant

*For any* non-empty list of fragment image paths, `FragmentAggregator.aggregate()` shall produce an image with shape `(256, 256, 3)` saved as `output/reconstructed_face.png`.

**Validates: Requirements 6.1, 6.3, 6.4**

---

### Property 11: Identical fragments aggregate to identity

*For any* set of N identical fragment images (N ≥ 1), `FragmentAggregator.aggregate()` shall produce an output image equal (pixel-for-pixel) to that fragment resized to 256×256.

**Validates: Requirements 6.2**

---

### Property 12: Deepfake score formula and report round-trip

*For any* non-negative integer `glitch_count` ≤ `total_frames` (with `total_frames` > 0), `ReportGenerator.generate()` shall return `glitch_count / total_frames` rounded to four decimal places, and the file `output/summary.txt` shall contain that score along with the correct frame counts.

**Validates: Requirements 7.1, 7.2, 7.3**

---

## Error Handling

| Scenario | Module | Behavior |
|---|---|---|
| Video file not found | FrameExtractor | Raise `FileNotFoundError` with the invalid path |
| Unsupported video format | FrameExtractor | Raise `ValueError` with the extension and list of supported formats |
| OpenCV fails to open file | FrameExtractor | Raise `RuntimeError` wrapping the OpenCV error |
| No face detected in frame | FaceMesh | Return `[]` (not an error) |
| MediaPipe internal error | FaceMesh | Propagate exception with frame index context |
| Empty landmark sequence | LandmarkTracker | Return `[]` (no glitch frames) |
| Zero total frames | ReportGenerator | Return `0.0` score, log warning |
| No fragments available | FragmentAggregator | Log warning, return `None`, do not write file |
| Fragment file unreadable | FragmentAggregator | Log warning, skip that fragment, continue |
| Output directory missing | All file-writing modules | Create directory with `os.makedirs(exist_ok=True)` |

---

## Testing Strategy

### Unit Tests

Each module has its own test file under `tests/`. Tests use `pytest` with `tmp_path` fixtures for file I/O.

- `tests/test_frame_extractor.py` — valid video extraction, invalid path, unsupported format
- `tests/test_face_mesh.py` — face detected (468 landmarks, coords in bounds), no face (empty list), idempotence
- `tests/test_landmark_tracker.py` — displacement computation, glitch classification, empty list skipping, sorted output
- `tests/test_artifact_detector.py` — identical frames (no artifact), high-diff frames (artifact), file saved
- `tests/test_fragment_extractor.py` — N rects → N files, naming convention, fallback crop, empty rects
- `tests/test_fragment_aggregator.py` — output shape, identical-fragment identity, single fragment, empty input
- `tests/test_report_generator.py` — score formula, summary.txt content, zero frames edge case

### Property-Based Tests

Property-based tests use **Hypothesis** (Python). Each test runs a minimum of 100 iterations.

```python
# Tag format: Feature: deepfake-forensic-analysis, Property N: <property_text>
```

| Property | Test file | Hypothesis strategy |
|---|---|---|
| P1: Frame extraction round-trip | `tests/test_frame_extractor.py` | `st.integers(min_value=1, max_value=50)` for frame count; synthetic video via OpenCV VideoWriter |
| P2: Invalid input always raises | `tests/test_frame_extractor.py` | `st.text()` for random paths; `st.sampled_from(['.xyz', '.bmp', ''])` for bad extensions |
| P3: Face Mesh output shape | `tests/test_face_mesh.py` | `st.integers(100, 1920)` for width/height; real face images from a small fixture set |
| P4: Face Mesh idempotence | `tests/test_face_mesh.py` | Same frame fixture, called twice |
| P5: Glitch classification correctness | `tests/test_landmark_tracker.py` | `st.lists(st.floats(0,500), min_size=468, max_size=468)` for landmark coords; `st.floats(0,50)` for threshold |
| P6: Identical frames → no artifacts | `tests/test_artifact_detector.py` | `st.integers(50,500)` for frame dimensions; random solid-color frames |
| P7: Bounding rect count | `tests/test_artifact_detector.py` | Synthetic frame pairs with known diff patterns |
| P8: Annotated frame always saved | `tests/test_artifact_detector.py` | Random frame pairs, verify file existence |
| P9: Fragment extraction round-trip | `tests/test_fragment_extractor.py` | `st.lists(st.tuples(...))` for bounding rects |
| P10: Reconstructed face size | `tests/test_fragment_aggregator.py` | `st.lists(st.integers(10,200))` for fragment sizes |
| P11: Identical fragments → identity | `tests/test_fragment_aggregator.py` | Random solid-color image repeated N times |
| P12: Score formula round-trip | `tests/test_report_generator.py` | `st.integers(0, 10000)` for glitch/total counts |

### Integration Tests

- `tests/test_pipeline.py` — runs `main.py` end-to-end on a short synthetic video (10 frames), verifies all output files exist and `summary.txt` is well-formed.

### Test Dependencies

```
pytest
hypothesis
opencv-python
mediapipe
numpy
scikit-image
```
