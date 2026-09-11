"""
report_generator.py — Generates summary report with deepfake likelihood score.

Computes the deepfake score as the ratio of glitch frames to total frames
and outputs a summary to stdout and a text file.
"""

import os


class ReportGenerator:
    """
    Generates a summary report of the deepfake analysis results.
    """

    def __init__(self, output_dir: str = "output") -> None:
        """
        Parameters
        ----------
        output_dir : str
            Directory where summary.txt is saved (default: "output").
        """
        self.output_dir = output_dir

    def generate(
        self,
        total_frames: int,
        glitch_indices: list[int],
    ) -> float:
        """
        Computes deepfake_score = len(glitch_indices) / total_frames.
        Prints summary to stdout and saves summary.txt.
        Returns deepfake_score.

        Parameters
        ----------
        total_frames : int
            Total number of frames in the video.
        glitch_indices : list[int]
            List of frame indices classified as glitch frames.

        Returns
        -------
        float
            Deepfake score in range [0.0, 1.0].
        """
        # --- 1. Handle edge case: zero frames ---
        if total_frames == 0:
            print("WARNING: Total frames is 0. Setting deepfake score to 0.0.")
            deepfake_score = 0.0
        else:
            # --- 2. Compute deepfake score ---
            glitch_count = len(glitch_indices)
            deepfake_score = glitch_count / total_frames

        # --- 3. Clamp to [0.0, 1.0] (should already be in range, but explicit) ---
        deepfake_score = max(0.0, min(1.0, deepfake_score))

        # --- 4. Format summary text ---
        glitch_count = len(glitch_indices)
        summary_text = (
            f"Total Frames : {total_frames}\n"
            f"Glitch Frames: {glitch_count}\n"
            f"Deepfake Score: {deepfake_score:.4f}\n"
        )

        # --- 5. Print to stdout ---
        print("\n" + "=" * 50)
        print("DEEPFAKE FORENSIC ANALYSIS SUMMARY")
        print("=" * 50)
        print(summary_text)
        print("=" * 50 + "\n")

        # --- 6. Ensure output directory exists ---
        os.makedirs(self.output_dir, exist_ok=True)

        # --- 7. Save summary to file ---
        summary_path = os.path.join(self.output_dir, "summary.txt")
        with open(summary_path, "w") as f:
            f.write(summary_text)

        return deepfake_score
