"""Synthetic dataset for training and evaluation."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from backend.core.logging import get_logger
from backend.ml.degradation.generator import PalmLeafDegradationGenerator

logger = get_logger(__name__)

# Sample Tamil text for synthetic data generation
SAMPLE_TEXTS: list[list[str]] = [
    # Tamil
    ["தமிழ் மொழியில் எழுதப்பட்ட ஓலைச் செய்தாள்", "பழைய கலை நூல்"],
    ["சித்த மருத்துவம் தொடர்பான ஆவணம்", "ஆயுர்வேத மருந்து வகைகள்"],
    ["இலக்கியம் மற்றும் இசை நூல்", "பன்னிரண்டு ஆசிரியர்கள்"],
    ["சோழர் கால ஓலைச் செய்தாள்", "வரி மற்றும் நிலம் தொடர்பான ஆவணம்"],
    ["மங்கல வாழ்த்துச் செய்யுள்", "திருமங்கையாழ்வார் பாடல்"],
    # Sanskrit
    ["अथ तोषितामनुशासनम्", "श्रीमद्भागवतम्"],
    ["कालिदासः रघुवंशम्", "शाकuntalam"],
    # Malayalam
    ["മലയാളത്തിൽ എഴുതിയ ഓലാച്ചിട്ട", "പഴയ സാഹിത്യ നാടകം"],
]

SCRIPT_CODES = ["tam", "san", "mal", "eng"]


class SyntheticDataset:
    """Generate synthetic palm-leaf datasets for training and eval."""

    def __init__(self, output_dir: str = "data/synthetic"):
        self.output_dir = Path(output_dir)
        self.generator = PalmLeafDegradationGenerator()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        count: int = 100,
        level: str = "medium",
        scripts: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Generate synthetic manuscript samples.

        Args:
            count: Number of samples to generate
            level: Degradation level
            scripts: Languages to use

        Returns:
            List of sample metadata dicts
        """
        scripts = scripts or SCRIPT_CODES
        samples = []

        for i in range(count):
            script = scripts[i % len(scripts)]
            text_set = self._get_sample_texts_for_script(script)

            # Pick random text
            text_lines = text_set[i % len(text_set)]

            # Generate
            result = self.generator.generate(
                text_lines=text_lines,
                seed=42 + i,
                level=level,
            )

            # Save images
            out_dir = self.output_dir / f"sample_{i:04d}"
            out_dir.mkdir(exist_ok=True)

            cv2.imwrite(str(out_dir / "degraded.jpg"), result["degraded"])
            cv2.imwrite(str(out_dir / "clean.jpg"), result["clean"])
            cv2.imwrite(str(out_dir / "texture.jpg"), result["texture"])

            # Save masks
            mask = (result["text_mask"] * 255).astype(np.uint8)
            cv2.imwrite(str(out_dir / "text_mask.png"), mask)

            # Save labels
            labels = {
                "id": f"sample_{i:04d}",
                "script": script,
                "level": level,
                "seed": result["metadata"]["seed"],
                "applied_damage": result["metadata"]["applied_damage"],
                "num_lines": result["metadata"]["num_lines"],
                "image_shape": list(result["degraded"].shape),
                "text": [bbox["text"] for bbox in result["bboxes"]],
                "bboxes": result["bboxes"],
            }
            with open(out_dir / "labels.json", "w", encoding="utf-8") as f:
                json.dump(labels, f, ensure_ascii=False, indent=2)

            samples.append(labels)
            logger.info("synthetic_sample_generated", id=labels["id"], script=script, level=level)

        logger.info("synthetic_dataset_generated", count=count, level=level)
        return samples

    def _get_sample_texts_for_script(self, script: str) -> list[list[str]]:
        """Get appropriate sample texts for a script."""
        if script == "tam":
            return SAMPLE_TEXTS[:5]
        elif script == "san":
            return SAMPLE_TEXTS[5:7]
        elif script == "mal":
            return SAMPLE_TEXTS[7:8]
        return SAMPLE_TEXTS[:3]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--level", default="medium")
    parser.add_argument("--output", default="data/synthetic")
    args = parser.parse_args()

    dataset = SyntheticDataset(output_dir=args.output)
    samples = dataset.generate(count=args.count, level=args.level)
    print(f"Generated {len(samples)} samples in {args.output}")
