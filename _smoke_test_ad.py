import tempfile, os, numpy as np
from artifact_detector import ArtifactDetector

with tempfile.TemporaryDirectory() as tmp:
    det = ArtifactDetector(output_dir=tmp)
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    has_artifact, rects = det.process_pair(frame, frame, 0)
    saved = os.path.join(tmp, "frame_0000.png")
    print("has_artifact:", has_artifact)
    print("rects:", rects)
    print("file saved:", os.path.exists(saved))
    assert not has_artifact, "identical frames must not flag an artifact"
    assert rects == [], "identical frames must return empty rects"
    assert os.path.exists(saved), "output file must be saved"
    print("All assertions passed.")
