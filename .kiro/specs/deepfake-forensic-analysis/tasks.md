# Implementation Plan: Deepfake Forensic Analysis

## Overview

Implement the deepfake forensic analysis pipeline as a set of independent Python modules orchestrated by `main.py`. Each module is built and tested incrementally, with the pipeline wired together at the end.

## Tasks

- [x] 1. Project scaffolding and dependencies
  - Create the directory structure: `frames/`, `fragments/`, `output/`, `tests/`
  - Create `requirements.txt` listing: `opencv-python`, `mediapipe`, `numpy`, `scikit-image`, `matplotlib`, `streamlit`, `pytest`, `hypothesis`
  - Create empty `__init__.py` files where needed so modules are importable
  - _Requirements: 9.4_

- [x] 2. Implement `FrameExtractor`
  - [x] 2.1 Implement `frame_extractor.py`
    - Write `FrameExtractor.__init__` accepting `video_path` and `output_dir`
    - Implement `extract()`: validate extension and `cap.isOpened()`, decode frames with `cv2.VideoCapture`, save each as `frame_NNNN.png`, return `(total_frame_count, fps)`
    - Raise `FileNotFoundError` for missing paths, `ValueError` for unsupported extensions, `RuntimeError` for OpenCV failures
    - Create output directory with `os.makedirs(exist_ok=True)`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [ ]* 2.2 Write property test for frame extraction round-trip (Property 1)
    - **Property 1: Frame extraction round-trip**
    - **Validates: Requirements 1.2, 1.4, 1.5**
    - Use `hypothesis` with `st.integers(min_value=1, max_value=50)` for frame count; generate synthetic video via `cv2.VideoWriter`
    - Assert exactly N PNG files exist named `frame_0000.png` through `frame_{N-1:04d}.png` and returned count equals N

  - [ ]* 2.3 Write property test for invalid input always raises (Property 2)
    - **Property 2: Invalid input always raises**
    - **Validates: Requirements 1.3**
    - Use `st.text()` for random non-existent paths and `st.sampled_from(['.xyz', '.bmp', ''])` for bad extensions
    - Assert `extract()` raises an exception in all cases

  - [ ]* 2.4 Write unit tests for `FrameExtractor`
    - Test valid video extraction, invalid path, unsupported format, OpenCV failure
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 3. Implement `FaceMesh`
  - [x] 3.1 Implement `face_mesh.py`
    - Write `FaceMesh.__init__` wrapping `mediapipe.solutions.face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1)`
    - Implement `detect(frame)`: convert BGR to RGB, run inference, convert normalized coords to absolute pixels (`x_px = lm.x * width`), return list of 468 `(x_px, y_px, z_px)` tuples or `[]` if no face
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [ ]* 3.2 Write property test for Face Mesh output shape invariant (Property 3)
    - **Property 3: Face Mesh output shape invariant**
    - **Validates: Requirements 2.1, 2.3**
    - Use `st.integers(100, 1920)` for width/height with real face image fixtures
    - Assert returned list has exactly 468 elements and all `(x, y)` satisfy `0 <= x <= width` and `0 <= y <= height`

  - [ ]* 3.3 Write property test for Face Mesh idempotence (Property 4)
    - **Property 4: Face Mesh statelessness (idempotence)**
    - **Validates: Requirements 2.4**
    - Call `detect()` twice on the same frame fixture; assert results are identical

  - [ ]* 3.4 Write unit tests for `FaceMesh`
    - Test face detected (468 landmarks, coords in bounds), no face (empty list), idempotence
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 4. Implement `LandmarkTracker`
  - [x] 4.1 Implement `landmark_tracker.py`
    - Write `LandmarkTracker.__init__` with `displacement_threshold=10.0`
    - Implement `find_glitch_frames(landmark_sequence)`: iterate consecutive pairs, skip pairs where either list is empty, compute mean Euclidean displacement across all 468 landmark pairs, add frame index N when pair (N-1, N) exceeds threshold, return sorted list
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [ ]* 4.2 Write property test for glitch classification correctness (Property 5)
    - **Property 5: Glitch classification correctness**
    - **Validates: Requirements 3.1, 3.2, 3.4, 3.5**
    - Use `st.lists(st.floats(0, 500), min_size=468, max_size=468)` for landmark coords and `st.floats(0, 50)` for threshold
    - Assert frame N is in result if and only if both lists are non-empty and mean displacement exceeds threshold; assert output is sorted

  - [ ]* 4.3 Write unit tests for `LandmarkTracker`
    - Test displacement computation, glitch classification, empty list skipping, sorted output
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 5. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement `ArtifactDetector`
  - [x] 6.1 Implement `artifact_detector.py`
    - Write `ArtifactDetector.__init__` with `diff_threshold=30`, `ssim_threshold=0.85`, `min_contour_area=500`, `annotation_color=(0,0,255)`, `output_dir="output"`
    - Implement `process_pair(frame_prev, frame_curr, frame_index)`: convert to grayscale, compute `cv2.absdiff`, compute SSIM via `skimage.metrics.structural_similarity`, threshold diff mask, find contours, filter by `min_contour_area`, draw bounding rects on `frame_curr` only when `mean_ssim < ssim_threshold`, save annotated frame to `output_dir/frame_{index:04d}.png`, return `(has_artifact, bounding_rects)`
    - Create output directory with `os.makedirs(exist_ok=True)`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [ ]* 6.2 Write property test for identical frames produce no artifacts (Property 6)
    - **Property 6: Identical frames produce no artifacts**
    - **Validates: Requirements 4.1, 4.2, 4.3**
    - Use `st.integers(50, 500)` for frame dimensions with random solid-color frames
    - Assert `process_pair(F, F, index)` returns `has_artifact=False` and empty bounding-rect list

  - [ ]* 6.3 Write property test for bounding rect count matches contour count (Property 7)
    - **Property 7: Bounding rect count matches contour count**
    - **Validates: Requirements 4.4**
    - Use synthetic frame pairs with known diff patterns
    - Assert number of returned bounding rects equals number of contours with area ≥ `min_contour_area`

  - [ ]* 6.4 Write property test for annotated frame always saved (Property 8)
    - **Property 8: Annotated frame always saved**
    - **Validates: Requirements 4.5, 4.6**
    - Use random frame pairs; assert `output/frame_{index:04d}.png` exists after every call

  - [ ]* 6.5 Write unit tests for `ArtifactDetector`
    - Test identical frames (no artifact), high-diff frames (artifact detected), file always saved
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [x] 7. Implement `FragmentExtractor`
  - [x] 7.1 Implement `fragment_extractor.py`
    - Write `FragmentExtractor.__init__` with `output_dir="fragments"`
    - Implement `extract(frame, frame_index, bounding_rects)`: crop each rect from frame, save as `fragment_{frame_index:04d}_{patch_index:02d}.png`; when `bounding_rects` is empty, fall back to centered 128×128 crop clamped to frame bounds; return list of saved file paths
    - Create output directory with `os.makedirs(exist_ok=True)`
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [ ]* 7.2 Write property test for fragment extraction round-trip (Property 9)
    - **Property 9: Fragment extraction round-trip**
    - **Validates: Requirements 5.1, 5.2, 5.4**
    - Use `st.lists(st.tuples(...))` for N bounding rects (N ≥ 1)
    - Assert exactly N file paths returned, each matching naming convention and existing on disk

  - [ ]* 7.3 Write unit tests for `FragmentExtractor`
    - Test N rects → N files, naming convention, fallback crop, empty rects
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 8. Implement `FragmentAggregator`
  - [x] 8.1 Implement `fragment_aggregator.py`
    - Write `FragmentAggregator.__init__` with `target_size=(256, 256)`, `output_dir="output"`
    - Implement `aggregate(fragment_paths)`: resize all fragments to `target_size`, compute `np.mean(stack, axis=0).astype(np.uint8)`, save as `output/reconstructed_face.png`; handle single fragment (resize and save directly); handle empty list (log warning, return `None`); handle unreadable files (log warning, skip)
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ]* 8.2 Write property test for reconstructed face size invariant (Property 10)
    - **Property 10: Reconstructed face size invariant**
    - **Validates: Requirements 6.1, 6.3, 6.4**
    - Use `st.lists(st.integers(10, 200))` for varying fragment sizes
    - Assert output image shape is `(256, 256, 3)` and file `output/reconstructed_face.png` exists

  - [ ]* 8.3 Write property test for identical fragments aggregate to identity (Property 11)
    - **Property 11: Identical fragments aggregate to identity**
    - **Validates: Requirements 6.2**
    - Use random solid-color image repeated N times (N ≥ 1)
    - Assert output image equals that fragment resized to 256×256 pixel-for-pixel

  - [ ]* 8.4 Write unit tests for `FragmentAggregator`
    - Test output shape, identical-fragment identity, single fragment, empty input
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 9. Implement `ReportGenerator`
  - [x] 9.1 Implement `report_generator.py`
    - Write `ReportGenerator.__init__` with `output_dir="output"`
    - Implement `generate(total_frames, glitch_indices)`: compute `deepfake_score = len(glitch_indices) / total_frames` clamped to [0.0, 1.0] (return 0.0 when `total_frames == 0`), print summary to stdout, save `summary.txt` with format `Total Frames : N\nGlitch Frames: G\nDeepfake Score: S`
    - _Requirements: 7.1, 7.2, 7.3_

  - [ ]* 9.2 Write property test for deepfake score formula and report round-trip (Property 12)
    - **Property 12: Deepfake score formula and report round-trip**
    - **Validates: Requirements 7.1, 7.2, 7.3**
    - Use `st.integers(0, 10000)` for glitch and total counts
    - Assert returned score equals `glitch_count / total_frames` rounded to four decimal places and `summary.txt` contains correct values

  - [ ]* 9.3 Write unit tests for `ReportGenerator`
    - Test score formula, summary.txt content, zero frames edge case
    - _Requirements: 7.1, 7.2, 7.3_

- [ ] 10. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Implement `main.py` pipeline orchestration
  - [x] 11.1 Implement `main.py`
    - Set up `argparse` with arguments: `video` (required), `--displacement-threshold` (default 10.0), `--diff-threshold` (default 30), `--ssim-threshold` (default 0.85), `--ui` (flag)
    - Wire pipeline in order: `FrameExtractor.extract()` → per-frame `FaceMesh.detect()` → `LandmarkTracker.find_glitch_frames()` → per-consecutive-pair `ArtifactDetector.process_pair()` → per-glitch-frame `FragmentExtractor.extract()` → `FragmentAggregator.aggregate()` → `ReportGenerator.generate()`
    - Pass all bounding rects from `ArtifactDetector` to `FragmentExtractor` for glitch frames
    - When `--ui` flag is set, launch Streamlit app instead of running CLI pipeline
    - _Requirements: 9.1, 9.2, 9.3_

  - [ ]* 11.2 Write integration test for end-to-end pipeline
    - In `tests/test_pipeline.py`, run `main.py` on a short synthetic 10-frame video
    - Assert all output files exist: annotated frames in `output/`, fragments in `fragments/`, `reconstructed_face.png`, `summary.txt`
    - Assert `summary.txt` is well-formed (contains `Total Frames`, `Glitch Frames`, `Deepfake Score`)
    - _Requirements: 1.1–1.5, 3.5, 4.5, 5.4, 6.3, 7.3, 9.2_

- [x] 12. Implement optional Streamlit UI (`app.py`)
  - [x] 12.1 Implement `app.py`
    - Create file uploader accepting MP4/AVI/MOV
    - Show progress bar during frame processing using `st.progress`
    - Display Deepfake_Score, Glitch_Frame count, gallery of annotated frames, gallery of fragments, Reconstructed_Face image
    - Provide download buttons for `reconstructed_face.png` and `summary.txt`
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 13. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests use Hypothesis and validate universal correctness properties (Properties 1–12 from the design)
- Unit tests validate specific examples and edge cases
- All file-writing modules create their output directories automatically via `os.makedirs(exist_ok=True)`
