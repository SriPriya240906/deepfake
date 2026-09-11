# Deepfake Forensic Analysis

A Python-based system for detecting deepfake artifacts in videos using landmark failure detection and frame-level reconstruction.

## Features

- **Video Frame Extraction**: Converts videos (MP4, AVI, MOV) into individual frames
- **Facial Landmark Detection**: Uses MediaPipe Face Mesh to track 468 facial landmarks per frame
- **Landmark Failure Detection**: Identifies "glitch frames" where landmarks jump unexpectedly
- **Artifact Detection**: Uses frame differencing and SSIM to detect visual inconsistencies
- **Fragment Extraction**: Crops and saves artifact regions from glitch frames
- **Identity Reconstruction**: Aggregates fragments to reveal partial identity leakage
- **Deepfake Scoring**: Computes likelihood score based on glitch frame ratio
- **Web UI**: Optional Streamlit interface for easy video upload and analysis

## Installation

1. **Clone or download this repository**

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

Required packages:
- opencv-python
- mediapipe
- numpy
- scikit-image
- matplotlib
- streamlit
- pytest
- hypothesis

## Usage

### Command Line Interface

Run analysis on a video file:

```bash
python main.py path/to/video.mp4
```

**Optional arguments**:
- `--displacement-threshold`: Landmark displacement threshold in pixels (default: 10.0)
- `--diff-threshold`: Pixel intensity threshold for frame differencing (default: 30)
- `--ssim-threshold`: SSIM threshold for artifact detection (default: 0.85)

**Example**:
```bash
python main.py sample_video.mp4 --displacement-threshold 15.0 --ssim-threshold 0.80
```

### Web UI (Streamlit)

Launch the browser-based interface:

```bash
streamlit run app.py
```

Or use the `--ui` flag:

```bash
python main.py --ui
```

The web UI provides:
- Video file upload (drag & drop)
- Real-time progress tracking
- Interactive parameter adjustment
- Visual galleries of annotated frames and fragments
- Downloadable results (reconstructed face, summary report)

## Output

The system generates the following outputs:

### Directories
- `frames/` — Extracted video frames (frame_0000.png, frame_0001.png, ...)
- `output/` — Annotated frames with artifact bounding boxes
- `fragments/` — Cropped artifact patches from glitch frames

### Files
- `output/reconstructed_face.png` — Aggregated reconstruction from all fragments
- `output/summary.txt` — Analysis summary with deepfake score

### Summary Report Format
```
Total Frames : 1200
Glitch Frames: 47
Deepfake Score: 0.0392
```

## How It Works

1. **Frame Extraction**: Video is decoded into individual PNG frames
2. **Landmark Detection**: MediaPipe detects 468 facial landmarks per frame
3. **Glitch Detection**: Frames with sudden landmark displacement (>threshold) are flagged
4. **Artifact Detection**: Frame differencing + SSIM identify visual inconsistencies
5. **Fragment Extraction**: Inconsistent regions are cropped and saved
6. **Reconstruction**: Fragments are resized to 256×256 and pixel-averaged
7. **Scoring**: Deepfake score = (glitch frames / total frames)

## Architecture

The system follows a modular pipeline design:

```
Video → FrameExtractor → FaceMesh → LandmarkTracker → ArtifactDetector 
     → FragmentExtractor → FragmentAggregator → ReportGenerator
```

Each module is independent and can be tested or replaced separately.

## Module Overview

- `frame_extractor.py` — Video decoding and frame extraction
- `face_mesh.py` — MediaPipe Face Mesh wrapper for landmark detection
- `landmark_tracker.py` — Glitch frame detection via displacement analysis
- `artifact_detector.py` — Frame differencing and SSIM-based artifact detection
- `fragment_extractor.py` — Artifact region cropping and saving
- `fragment_aggregator.py` — Fragment averaging for identity reconstruction
- `report_generator.py` — Summary report and deepfake score computation
- `main.py` — CLI entry point and pipeline orchestration
- `app.py` — Streamlit web UI

## Testing

Run the test suite:

```bash
pytest tests/
```

The project includes:
- Unit tests for each module
- Property-based tests using Hypothesis
- Integration tests for the full pipeline

## Configuration

Default thresholds can be adjusted via CLI arguments or the web UI:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `displacement_threshold` | 10.0 px | Landmark displacement threshold |
| `diff_threshold` | 30 | Pixel intensity threshold |
| `ssim_threshold` | 0.85 | SSIM threshold |
| `min_contour_area` | 500 px² | Minimum artifact region size |
| `target_size` | 256×256 | Reconstructed face resolution |

## Limitations

- Reconstruction quality depends on the number and size of detected artifacts
- Works best on videos with clear facial visibility
- Processing time scales linearly with video length
- Requires face detection in frames for landmark tracking

## License

This project is provided as-is for educational and research purposes.

## Credits

Built using:
- [OpenCV](https://opencv.org/) for video processing
- [MediaPipe](https://mediapipe.dev/) for facial landmark detection
- [scikit-image](https://scikit-image.org/) for SSIM computation
- [Streamlit](https://streamlit.io/) for web UI

# deepfake
