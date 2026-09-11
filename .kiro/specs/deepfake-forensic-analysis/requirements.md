# Requirements Document

## Introduction

This feature implements a Deepfake Forensic Analysis system that ingests a video file, extracts frames, detects facial landmark failures, identifies visual artifacts, extracts glitch fragments, and performs partial identity reconstruction from those fragments. The system produces annotated output frames, extracted patch images, and a reconstructed face image, along with a summary report of deepfake likelihood.

## Glossary

- **System**: The Deepfake Forensic Analysis application as a whole
- **Frame_Extractor**: The module responsible for reading a video file and converting it into individual image frames
- **Face_Mesh**: The MediaPipe Face Mesh component that detects and returns 468 facial landmark coordinates per frame
- **Landmark_Tracker**: The module that compares landmark positions between consecutive frames to detect sudden displacements
- **Glitch_Frame**: A video frame in which one or more landmark displacements exceed the configured threshold, indicating a potential deepfake artifact
- **Artifact_Detector**: The module that performs frame differencing and SSIM analysis to identify visually inconsistent regions
- **Fragment_Extractor**: The module that crops inconsistent regions (patches) from Glitch_Frames and saves them to disk
- **Fragment_Aggregator**: The module that combines all extracted patches into a single reconstructed face image
- **Deepfake_Score**: A normalized float value in [0.0, 1.0] representing the estimated likelihood that the input video is a deepfake
- **SSIM**: Structural Similarity Index Measure — a perceptual metric comparing two images for luminance, contrast, and structure
- **Landmark_Displacement**: The Euclidean distance between the position of a facial landmark in frame N and the same landmark in frame N-1
- **Displacement_Threshold**: The configurable pixel distance above which a landmark movement is classified as a failure
- **Fragment**: A cropped image patch extracted from a Glitch_Frame representing a visually inconsistent region
- **Reconstructed_Face**: The output image produced by averaging or overlaying all extracted Fragments

---

## Requirements

### Requirement 1: Video Ingestion and Frame Extraction

**User Story:** As a forensic analyst, I want to provide a video file as input, so that the system can process it frame by frame for deepfake analysis.

#### Acceptance Criteria

1. THE Frame_Extractor SHALL accept a file path to a video in MP4, AVI, or MOV format as its sole input parameter.
2. WHEN a valid video file path is provided, THE Frame_Extractor SHALL decode the video and produce an ordered sequence of BGR image frames using OpenCV.
3. WHEN a video file path is provided that does not exist or is not a supported format, THE Frame_Extractor SHALL raise a descriptive error identifying the invalid path or unsupported format.
4. THE Frame_Extractor SHALL save each extracted frame as a PNG image to the `/frames` directory, named sequentially (e.g., `frame_0000.png`, `frame_0001.png`).
5. WHEN frame extraction is complete, THE Frame_Extractor SHALL return the total frame count and the frames-per-second (FPS) value of the source video.

---

### Requirement 2: Facial Landmark Detection

**User Story:** As a forensic analyst, I want facial landmarks detected on every frame, so that I can track face geometry across the video timeline.

#### Acceptance Criteria

1. WHEN a BGR image frame is provided, THE Face_Mesh SHALL detect up to one face and return a list of 468 normalized (x, y, z) landmark coordinates.
2. WHEN no face is detected in a frame, THE Face_Mesh SHALL return an empty landmark list for that frame.
3. THE Face_Mesh SHALL convert normalized landmark coordinates to absolute pixel coordinates using the frame's width and height before returning results.
4. THE Face_Mesh SHALL process each frame independently and SHALL NOT retain state between frames.

---

### Requirement 3: Landmark Failure Detection

**User Story:** As a forensic analyst, I want sudden landmark displacements flagged automatically, so that I can identify frames where the deepfake model failed to maintain facial consistency.

#### Acceptance Criteria

1. WHEN landmark lists for two consecutive frames are both non-empty, THE Landmark_Tracker SHALL compute the mean Euclidean Landmark_Displacement across all 468 landmark pairs.
2. WHEN the mean Landmark_Displacement exceeds the Displacement_Threshold, THE Landmark_Tracker SHALL classify the current frame as a Glitch_Frame.
3. THE Landmark_Tracker SHALL use a default Displacement_Threshold of 10.0 pixels, configurable via a parameter.
4. WHEN either of the two consecutive frames has an empty landmark list, THE Landmark_Tracker SHALL skip displacement computation for that pair and SHALL NOT classify either frame as a Glitch_Frame solely due to missing landmarks.
5. THE Landmark_Tracker SHALL return an ordered list of frame indices classified as Glitch_Frames after processing the full frame sequence.

---

### Requirement 4: Artifact Detection via Frame Differencing and SSIM

**User Story:** As a forensic analyst, I want visual inconsistencies between consecutive frames highlighted, so that I can see exactly where deepfake artifacts appear spatially.

#### Acceptance Criteria

1. WHEN two consecutive frames are provided, THE Artifact_Detector SHALL compute a per-pixel absolute difference image and an SSIM map between the two grayscale frames.
2. THE Artifact_Detector SHALL threshold the difference image at a configurable pixel intensity value (default: 30) to produce a binary inconsistency mask.
3. WHEN the mean SSIM score between two consecutive frames falls below a configurable value (default: 0.85), THE Artifact_Detector SHALL classify the frame pair as containing a visual artifact.
4. THE Artifact_Detector SHALL draw bounding rectangles around contiguous inconsistent regions on the current frame using a visually distinct color (default: red, BGR [0, 0, 255]).
5. THE Artifact_Detector SHALL save each annotated frame as a PNG image to the `/output` directory using the same sequential naming convention as the source frames.
6. WHEN no inconsistent regions exceed the minimum contour area of 500 square pixels, THE Artifact_Detector SHALL save the frame without annotations.

---

### Requirement 5: Glitch Fragment Extraction

**User Story:** As a forensic analyst, I want inconsistent image patches saved separately, so that I can examine the raw artifact evidence and use it for reconstruction.

#### Acceptance Criteria

1. WHEN a frame is classified as a Glitch_Frame, THE Fragment_Extractor SHALL crop each bounding rectangle region identified by the Artifact_Detector from that frame.
2. THE Fragment_Extractor SHALL save each cropped patch as a PNG image to the `/fragments` directory, named with the source frame index and patch index (e.g., `fragment_0042_00.png`).
3. WHEN a Glitch_Frame contains no artifact bounding rectangles, THE Fragment_Extractor SHALL extract a centered 128×128 pixel crop from the frame as a fallback fragment.
4. THE Fragment_Extractor SHALL return the list of file paths for all saved fragment images.

---

### Requirement 6: Fragment Aggregation and Partial Identity Reconstruction

**User Story:** As a forensic analyst, I want all extracted fragments combined into a single image, so that I can observe partial identity leakage from the deepfake source.

#### Acceptance Criteria

1. WHEN one or more fragment images are available, THE Fragment_Aggregator SHALL resize all fragments to a common resolution of 256×256 pixels before aggregation.
2. THE Fragment_Aggregator SHALL compute a per-pixel mean across all resized fragments to produce the Reconstructed_Face image.
3. THE Fragment_Aggregator SHALL save the Reconstructed_Face as `reconstructed_face.png` in the `/output` directory.
4. WHEN fewer than two fragment images are available, THE Fragment_Aggregator SHALL save the single available fragment (resized to 256×256) as the Reconstructed_Face without averaging.
5. WHEN no fragment images are available, THE Fragment_Aggregator SHALL log a warning and SHALL NOT produce a Reconstructed_Face file.

---

### Requirement 7: Summary Report Generation

**User Story:** As a forensic analyst, I want a summary of analysis results, so that I can quickly assess the deepfake likelihood of the video.

#### Acceptance Criteria

1. WHEN analysis of all frames is complete, THE System SHALL compute the Deepfake_Score as the ratio of Glitch_Frame count to total frame count, expressed as a float in [0.0, 1.0].
2. THE System SHALL print a summary to standard output containing: total frame count, Glitch_Frame count, and Deepfake_Score rounded to four decimal places.
3. THE System SHALL save the summary as a plain-text file `summary.txt` in the `/output` directory.
4. WHERE a Streamlit or Flask UI is enabled, THE System SHALL display the summary, annotated frames, extracted fragments, and Reconstructed_Face image within the UI.

---

### Requirement 8: Optional Web UI

**User Story:** As a forensic analyst, I want a browser-based interface, so that I can upload videos and view results without using the command line.

#### Acceptance Criteria

1. WHERE the Streamlit UI is enabled, THE System SHALL provide a file upload widget that accepts MP4, AVI, and MOV video files.
2. WHERE the Streamlit UI is enabled, WHEN a video is uploaded and analysis is triggered, THE System SHALL display a progress indicator while processing frames.
3. WHERE the Streamlit UI is enabled, WHEN analysis is complete, THE System SHALL display the Deepfake_Score, Glitch_Frame count, a gallery of annotated output frames, a gallery of extracted fragments, and the Reconstructed_Face image.
4. WHERE the Streamlit UI is enabled, THE System SHALL allow the user to download the Reconstructed_Face image and the `summary.txt` file directly from the UI.

---

### Requirement 9: Modular Code Structure

**User Story:** As a developer, I want each processing step encapsulated in its own module, so that components can be tested, replaced, or extended independently.

#### Acceptance Criteria

1. THE System SHALL implement Frame_Extractor, Face_Mesh, Landmark_Tracker, Artifact_Detector, Fragment_Extractor, and Fragment_Aggregator as separate Python modules or classes, each in its own file.
2. THE System SHALL expose a single entry-point script (`main.py`) that orchestrates all modules in the correct processing order.
3. THE System SHALL include inline comments on all non-trivial logic blocks explaining the purpose and approach of each operation.
4. THE System SHALL list all required third-party dependencies (OpenCV, MediaPipe, NumPy, scikit-image, Matplotlib, Streamlit) in a `requirements.txt` file.
