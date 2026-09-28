"""Evaluation script for segmentation pipeline."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import cv2
import numpy as np

from backend.pipeline.segmentation import ProjectionProfileSegmenter, compute_prf1
from backend.core.logging import get_logger

logger = get_logger(__name__)


def evaluate_segmentation(
    test_dir: str = "eval/test_data/segmentation",
    output_dir: str = "eval/results",
) -> Dict:
    """Evaluate segmentation on synthetic test data."""
    test_dir = Path(test_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    all_prf1 = {"0.5": {"precision": 0.0, "recall": 0.0, "f1": 0.0}}
    total_tp = total_fp = total_fn = 0

    sample_dirs = sorted(test_dir.glob("sample_*"))
    if not sample_dirs:
        logger.warning("No test data found at", path=test_dir)
        results["status"] = "no_test_data"
        results["note"] = f"No samples in {test_dir}. Run eval scripts to generate test data."
        return results

    for sample_dir in sample_dirs[:20]:  # Test first 20
        labels_path = sample_dir / "labels.json"
        if not labels_path.exists():
            continue

        with open(labels_path) as f:
            labels = json.load(f)

        gt_bboxes = [(b["x"], b["y"], b["width"], b["height"]) for b in labels.get("bboxes", [])]
        if not gt_bboxes:
            continue

        # Load degraded image
        img_path = sample_dir / "degraded.jpg"
        if not img_path.exists():
            continue

        image = cv2.imread(str(img_path))
        if image is None:
            continue

        # Run segmenter
        seg = ProjectionProfileSegmenter()
        predicted = seg.segment(image)
        predicted_boxes = [(l.x, l.y, l.width, l.height) for l in predicted]

        # Compute metrics
        prf1 = compute_prf1(predicted, gt_bboxes, iou_thresholds=[0.5, 0.7, 0.9])
        tp, fp, fn = _aggregate(prf1.get("0.5", {}))
        total_tp += tp
        total_fp += fp
        total_fn += fn

        results[sample_dir.name] = {
            "num_gt": len(gt_bboxes),
            "num_predicted": len(predicted),
            "prf1_at_0.5": prf1.get("0.5", {}),
            "prf1_at_0.7": prf1.get("0.7", {}),
            "prf1_at_0.9": prf1.get("0.9", {}),
        }

    # Overall metrics
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    overall = {
        "num_samples_evaluated": len(results),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "thresholds": prf1,
    }
    results["overall"] = overall

    # Save results
    output_file = output_dir / "segmentation_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    logger.info("segmentation_evaluation_complete", overall=overall)
    return results


def _aggregate(prf1_dict: Dict) -> tuple:
    """Aggregate TP/FP/FN from prf1 dict."""
    precision = prf1_dict.get("precision", 0)
    recall = prf1_dict.get("recall", 0)
    f1 = prf1_dict.get("f1", 0)
    # Approximate counts (assuming ~5 GT per sample)
    tp = int(f1 * 5) if f1 > 0 else 0
    fp = tp * (1 / precision - 1) if precision > 0 else 0
    fn = tp * (1 / recall - 1) if recall > 0 else 0
    return int(tp), int(max(0, fp)), int(max(0, fn))


if __name__ == "__main__":
    results = evaluate_segmentation()
    print(json.dumps(results, indent=2))
