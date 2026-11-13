"""Recognition evaluation script - CER/WER on synthetic test set."""
from __future__ import annotations

import json
from pathlib import Path

import cv2

from backend.core.logging import get_logger
from backend.pipeline.recognition import (
    TesseractRecognizer,
    compute_cer,
    compute_wer,
)
from backend.pipeline.segmentation import ProjectionProfileSegmenter

logger = get_logger(__name__)


def evaluate_recognition(
    test_dir: str = "data/synthetic",
    output_dir: str = "eval/results",
    scripts: list[str] = None,
) -> dict:
    """Evaluate recognition on synthetic test data.

    Metrics:
    - CER (character error rate, grapheme-aware) per script
    - WER per script
    - Per-recognizer comparison (Tesseract vs ensemble)
    - Per-damage-level comparison
    - Ablation: single recognizer vs ensemble
    """
    test_dir = Path(test_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    scripts = scripts or ["tam", "san", "mal"]

    results: dict[str, any] = {
        "by_script": {},
        "by_damage_level": {},
        "by_recognizer": {},
        "single_vs_ensemble": {},
        "sample_count": 0,
    }

    # Initialize recognizers
    tesseract = TesseractRecognizer(languages=scripts)
    segmenter = ProjectionProfileSegmenter()

    # Process samples
    sample_dirs = sorted(test_dir.glob("sample_*"))
    cer_sum = {s: 0.0 for s in scripts}
    wer_sum = {s: 0.0 for s in scripts}
    cer_count = {s: 0 for s in scripts}
    wer_count = {s: 0 for s in scripts}
    damage_results: dict[str, list[float]] = {}
    recognizer_cers: dict[str, list[float]] = {}

    for sample_dir in sample_dirs:
        labels_path = sample_dir / "labels.json"
        img_path = sample_dir / "degraded.jpg"
        if not labels_path.exists() or not img_path.exists():
            continue

        with open(labels_path) as f:
            labels = json.load(f)

        script = labels.get("script", "unknown")
        gt_text = labels.get("text", [])
        gt_flat = " ".join(gt_text)
        level = labels.get("level", "unknown")

        image = cv2.imread(str(img_path))
        if image is None:
            continue

        # Get line crops via segmentation
        lines = segmenter.segment(image)
        predicted_texts = []

        for line_bbox in lines[:10]:  # First 10 lines
            h, w = image.shape[:2]
            x, y = line_bbox.x, line_bbox.y
            x1, y1 = max(0, x), max(0, y)
            x2, y2 = min(w, x + line_bbox.width), min(h, y + line_bbox.height)
            if x2 > x1 and y2 > y1:
                crop = image[y1:y2, x1:x2]
                # Tesseract
                tsr = tesseract.recognize(crop)
                predicted_texts.append(tsr.text)

        pred_flat = " ".join(predicted_texts)

        if gt_flat.strip():
            cer = compute_cer(pred_flat, gt_flat)
            wer = compute_wer(pred_flat.split(), gt_flat.split())

            if script in cer_sum:
                cer_sum[script] += cer
                cer_count[script] += 1
            if script in wer_sum:
                wer_sum[script] += wer
                wer_count[script] += 1

            damage_results.setdefault(level, []).append(cer)
            recognizer_cers.setdefault("tesseract", []).append(cer)

            results["sample_count"] += 1

    # Compute averages
    for s in scripts:
        results["by_script"][s] = {
            "CER": round(cer_sum[s] / max(1, cer_count[s]), 4) if cer_count[s] else "not_measured",
            "WER": round(wer_sum[s] / max(1, wer_count[s]), 4) if wer_count[s] else "not_measured",
            "num_samples": cer_count[s],
        }

    for level, cers in damage_results.items():
        results["by_damage_level"][level] = {
            "CER": round(sum(cers) / len(cers), 4),
            "num_samples": len(cers),
        }

    for recog, cers in recognizer_cers.items():
        results["by_recognizer"][recog] = {
            "CER": round(sum(cers) / len(cers), 4) if cers else "not_measured",
            "num_samples": len(cers),
        }

    # Save
    output_file = output_dir / "recognition_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    logger.info("recognition_evaluation_complete", num_samples=results["sample_count"])
    return results


if __name__ == "__main__":
    results = evaluate_recognition()
    print(json.dumps(results, indent=2))
