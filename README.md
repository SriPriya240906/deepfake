# Deepfake Forensic Analysis Engine

An **AI-assisted deepfake forensic investigation system** that combines deep learning-based detection with frame-level forensic analysis to detect, localize, validate, and explain potential video manipulation.

The system is designed beyond simple **REAL/FAKE classification**. It analyzes facial landmarks, temporal inconsistencies, visual artifacts, and manipulation regions to provide supporting forensic evidence.

---

## 🎯 Project Goal

Deepfake detection should not only answer:

> **"Is this video fake?"**

It should also help answer:

* **When** did suspicious manipulation occur?
* **Where** on the face is the evidence?
* **What** type of visual inconsistency was detected?
* **How strong** is the evidence?
* **Can the evidence be explained or validated?**

The project follows the forensic workflow:

```text
DETECT → LOCALIZE → VALIDATE → EXPLAIN
```

---

# 🏗️ System Architecture

```text
                         INPUT VIDEO
                              │
                              ▼
                 ┌────────────────────────┐
                 │ Frame + Face Extraction│
                 └────────────┬───────────┘
                              │
              ┌───────────────┴────────────────┐
              │                                │
              ▼                                ▼
       LEARNED AI DETECTOR              FORENSIC ENGINE
       ───────────────────              ───────────────
       Deep Learning Model              Face Mesh
       Face Crops                       468 Landmarks
       Real/Fake Probability            Temporal Motion
                                        Pixel Difference
                                        SSIM
                                        Artifact Regions
              │                                │
              ▼                                ▼
        AI Probability                 Forensic Evidence
              │                                │
              └───────────────┬────────────────┘
                              ▼
                      EVIDENCE FUSION
                              │
                              ▼
                  ┌──────────────────────┐
                  │ Forensic Assessment  │
                  └──────────┬───────────┘
                             │
                ┌────────────┼────────────┐
                ▼            ▼            ▼
              WHEN?        WHERE?        WHAT?
              Timeline     Region        Artifact
                             │
                             ▼
                   FINAL INVESTIGATION
                             │
                             ▼
             REAL / MANIPULATED / UNCERTAIN
```

---

# 🔍 Core Forensic Pipeline

The existing forensic engine follows a seven-stage pipeline:

```text
Video
  │
  ▼
1. Frame Extraction
  │
  ▼
2. Facial Landmark Detection
  │
  ▼
3. Landmark Tracking
  │
  ▼
4. Artifact Detection
  │
  ▼
5. Fragment Extraction
  │
  ▼
6. Fragment Aggregation
  │
  ▼
7. Forensic Report
```

### Stage 1 — Frame Extraction

The input video is decoded into individual frames.

```text
Video
 ↓
frame_0000.png
frame_0001.png
frame_0002.png
...
```

### Stage 2 — Facial Landmark Detection

MediaPipe Face Mesh is used to detect up to **468 facial landmarks**.

These landmarks provide a geometric representation of the face across frames.

### Stage 3 — Landmark Tracking

Landmark positions are compared across consecutive frames.

Sudden unexpected movements can indicate potential temporal inconsistencies or facial tracking failures.

### Stage 4 — Artifact Detection

The system analyzes frames using:

* Pixel/frame differences
* SSIM
* Threshold-based artifact detection
* Facial region analysis

Suspicious regions are identified and recorded as forensic evidence.

### Stage 5 — Fragment Extraction

Detected artifact regions are cropped from frames and stored as forensic fragments.

### Stage 6 — Fragment Aggregation

Extracted fragments can be aggregated to visualize the concentration of suspicious regions.

### Stage 7 — Forensic Report

The system generates a structured analysis containing:

* Total frames
* Detected facial frames
* Suspicious/glitch frames
* Artifact regions
* Extracted fragments
* Forensic anomaly score
* Analysis status

> **Important:** The current forensic anomaly score is not a learned deepfake probability. It represents evidence detected by the forensic pipeline.

---

# 🤖 AI Detection Layer

The project is being extended with a learned deepfake detector.

The learned detector is trained using publicly available deepfake datasets rather than the application's demonstration videos.

The planned workflow is:

```text
Training Dataset
      │
      ▼
Face Extraction
      │
      ▼
Data Augmentation
      │
      ▼
Transfer Learning
      │
      ▼
Deep Learning Detector
      │
      ▼
Real / Fake Probability
```

The initial model strategy uses transfer learning with architectures such as:

* EfficientNet
* Xception

The model operates on **face crops** rather than relying only on complete video frames.

---

# 🔬 Evidence Fusion

The project combines two complementary sources of information:

### Learned AI Evidence

```text
Deep Learning Model
        ↓
AI Manipulation Probability
```

### Forensic Evidence

```text
Landmark Analysis
Temporal Analysis
Pixel Differences
SSIM
Artifact Regions
        ↓
Forensic Evidence
```

These are combined through an **evidence-fusion layer**.

This allows the system to distinguish between:

```text
Strong AI + Strong Forensics
        ↓
High-confidence manipulation

Weak AI + Weak Forensics
        ↓
Likely real / low evidence

AI and forensic disagreement
        ↓
UNCERTAIN
```

The system is therefore designed to avoid blindly forcing every input into a binary decision.

---

# 🌐 Application Architecture

The current application uses a modern web architecture.

```text
┌──────────────────────────────┐
│        Next.js Frontend      │
│                              │
│ Upload / Analysis / Results  │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│        FastAPI Backend       │
│                              │
│ REST API + Analysis Control  │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│    Forensic Analysis Engine  │
│                              │
│ Frame → Face → Landmarks     │
│ → Artifacts → Evidence       │
└──────────────────────────────┘
```

---

# 💻 Technology Stack

## Frontend

* Next.js
* React
* TypeScript
* Tailwind CSS
* Lucide React
* React Dropzone

## Backend

* Python
* FastAPI
* Uvicorn
* Pydantic
* Aiofiles

## Computer Vision / Forensics

* OpenCV
* MediaPipe
* NumPy
* scikit-image

## Deep Learning

* PyTorch
* Torchvision
* EfficientNet / Xception-based transfer learning

## Development

* Python 3.11+
* Node.js
* Git
* GitHub

---

# 📂 Project Structure

```text
deepfake/
│
├── backend/
│   └── app/
│       ├── forensic_engine.py
│       ├── services.py
│       └── ...
│
├── frontend/
│   ├── app/
│   ├── components/
│   └── ...
│
├── frame_extractor.py
├── face_mesh.py
├── landmark_tracker.py
├── artifact_detector.py
├── fragment_extractor.py
├── fragment_aggregator.py
├── report_generator.py
├── main.py
│
├── tests/
│
├── dataset/
│
├── frames/
├── frames_real/
├── frames_fake/
├── fragments/
├── output/
│
├── face_landmarker.task
├── requirements.txt
├── README.md
└── .gitignore
```

---

# 🚀 API

The FastAPI backend exposes endpoints for video analysis.

### Health Check

```http
GET /health
```

### Video Analysis

```http
POST /api/analyze/video
```

Used for video-to-video forensic comparison.

### Photo + Video Analysis

```http
POST /api/analyze/photo-video
```

Used for reference-photo versus suspected-video verification.

### Analysis Status

```http
GET /api/analysis/{analysis_id}/status
```

Returns the current analysis progress.

### Analysis Result

```http
GET /api/analysis/{analysis_id}
```

Returns the completed analysis result.

---

# 🔄 Analysis Modes

## 1. Video-to-Video Comparison

```text
Original / Reference Video
            +
Suspected Video
            ↓
       Forensic Engine
            ↓
       Comparison
            ↓
       Evidence Report
```

## 2. Photo-to-Video Verification

```text
Reference Photo
      +
Suspected Video
      ↓
Face Analysis
      ↓
Temporal + Artifact Analysis
      ↓
Forensic Assessment
```

---

# 📊 Current Forensic Evidence

The system can currently analyze:

| Evidence              | Purpose                           |
| --------------------- | --------------------------------- |
| Facial landmarks      | Detect geometric inconsistencies  |
| Landmark displacement | Identify sudden temporal changes  |
| Frame difference      | Detect visual changes             |
| SSIM                  | Measure structural similarity     |
| Artifact regions      | Localize suspicious areas         |
| Fragments             | Preserve suspicious image patches |
| Fragment aggregation  | Visualize artifact concentration  |
| Temporal behavior     | Analyze changes across frames     |

---

# 🧪 Dataset

The learned AI detector requires a proper deepfake dataset.

The project uses **FaceForensics++** as the initial training dataset.

The dataset contains:

```text
REAL
 └── Original YouTube Videos

FAKE
 ├── Deepfakes
 ├── Face2Face
 ├── FaceSwap
 └── NeuralTextures
```

The initial experiments use the **C23 compression level**.

Dataset files are kept separate from user-uploaded demonstration/test videos.

> FaceForensics++ is used according to its license and terms of use. The dataset is intended for non-commercial research and educational purposes.

---

# ⚠️ Important Data Separation

The videos included with the project for testing and demonstration are **not training data**.

Training data:

```text
FaceForensics++
      ↓
Model Training
```

Unseen user/test videos:

```text
User Video
     ↓
Trained Model
     +
Forensic Engine
```

This separation helps prevent data leakage during evaluation.

---

# 📈 Model Evaluation

The learned detector will be evaluated using:

* Accuracy
* Precision
* Recall
* F1 Score
* ROC-AUC
* Confusion Matrix

Dataset splitting is performed at the **video level** to reduce the possibility of frames from the same source appearing in both training and testing sets.

---

# 🔮 Planned Forensic Enhancements

The project is designed to evolve beyond basic deepfake classification.

### 1. Manipulation Timeline

Identify the exact time intervals containing suspicious activity.

```text
00:00 ─────────────── 00:15
       ████
       suspicious
```

### 2. Region-Level Localization

Identify suspicious facial regions:

```text
Eyes
Nose
Mouth
Jaw
Chin
Cheeks
Forehead
Ears
Neck
```

### 3. Frequency Analysis

Use frequency-domain evidence such as:

* FFT
* DCT

to identify manipulation-related patterns.

### 4. Compression Analysis

Analyze whether suspicious evidence survives:

* JPEG compression
* Resizing
* Blur
* Noise
* Re-encoding

### 5. Manipulation Type Classification

Potential categories:

```text
REAL
FACE_SWAP
FACE_REENACTMENT
LIP_SYNC
EXPRESSION_MANIPULATION
SYNTHETIC_FACE
UNKNOWN
```

### 6. Evidence Conflict Detection

Detect situations where different forensic signals disagree.

```text
AI Detector      → FAKE
Landmarks        → NORMAL
Artifact Analysis→ NORMAL

             ↓

          UNCERTAIN
```

### 7. Forensic Replay

Provide a frame-by-frame reconstruction of suspicious events.

### 8. Multi-Face Analysis

Support videos containing multiple faces and analyze each face independently.

### 9. Audio-Lip Synchronization

Future versions may compare speech audio with mouth movement to identify potential lip-sync manipulation.

---

# ⚠️ Limitations

Current limitations include:

* Performance depends on facial visibility.
* Landmark-based evidence can be affected by extreme poses.
* Low-quality videos can reduce detection reliability.
* Compression can hide or introduce visual artifacts.
* The forensic anomaly score alone should not be interpreted as a definitive deepfake probability.
* Public deepfake datasets may not represent every real-world manipulation technique.
* The current system does not guarantee forensic-level legal evidence.

The system is intended as an **AI-assisted forensic investigation tool**, not a replacement for expert forensic examination.

---

# 🛠️ Installation

## 1. Clone the repository

```bash
git clone https://github.com/<your-username>/<your-repository>.git
cd deepfake
```

## 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

## 3. Start the FastAPI backend

From the project root:

```bash
uvicorn backend.main:app --reload
```

The API will normally be available at:

```text
http://127.0.0.1:8000
```

## 4. Start the Next.js frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend will normally be available at:

```text
http://localhost:3000
```

---

# 🧪 Testing

Run the Python test suite:

```bash
pytest tests/
```

Backend integration tests can be run using the project's integration test files.

---

# 🔐 Security & Privacy Considerations

Uploaded videos are processed by the application's analysis backend.

The system is designed to:

* isolate individual analysis jobs
* avoid using uploaded user videos as training data
* separate training datasets from user inputs
* generate analysis-specific result directories

For production deployment, additional controls such as authentication, secure storage, access control, encryption, and automatic file cleanup should be added.

---

# 🎓 Academic Project

This project is developed as an academic/research-oriented project exploring:

* Deep Learning
* Computer Vision
* Digital Forensics
* Deepfake Detection
* Facial Landmark Analysis
* Temporal Analysis
* Explainable AI
* Evidence-based AI systems

---

# 👩‍💻 Author

**M Sri Priya Dharshini**

B.E. Computer Science and Engineering

---

# 📜 License

This project is provided for educational and research purposes.

Third-party datasets such as FaceForensics++ remain subject to their respective licenses and terms of use.
