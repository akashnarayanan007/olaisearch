"""Text line segmentation for palm-leaf manuscripts.

Three strategies (swappable via config):
1. Projection profile + connected components (baseline, no deps)
2. Kraken segmenter (optional, skip gracefully)
3. Small U-Net detector (learned, optional)

All output PAGE-XML-compatible structure with reading order.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from backend.core.exceptions import OCRException
from backend.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SegmentedLine:
    """A detected text line with bounding box and reading order."""

    x: int
    y: int
    width: int
    height: int
    reading_order: int
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProjectionProfileSegmenter:
    """Detect text lines using horizontal and vertical projection profiles.

    Algorithm:
    1. Binarize the image (Otsu or Sauvola)
    2. Compute horizontal projection (sum of ink pixels per row)
    3. Find gaps (rows with low projection) → line boundaries
    4. For each band, find connected components to refine
    5. Sort by reading order (top-to-bottom, left-to-right)
    """

    def __init__(
        self,
        min_line_height: int = 12,
        gap_ratio: float = 0.15,
        min_gap_pixels: int = 4,
    ):
        self.min_line_height = min_line_height
        self.gap_ratio = gap_ratio
        self.min_gap_pixels = min_gap_pixels

    def segment(
        self, image: np.ndarray, deskew_angle: float = 0.0
    ) -> List[SegmentedLine]:
        """Detect text lines in an image.

        Args:
            image: Grayscale (H, W) or color (H, W, 3) uint8
            deskew_angle: If nonzero, rotate image before segmenting

        Returns:
            List of SegmentedLine sorted by reading order
        """
        start = time.time()

        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Deskew if needed
        if abs(deskew_angle) > 0.5:
            h, w = gray.shape
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, deskew_angle, 1.0)
            gray = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC)

        # Binarize
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Horizontal projection
        h_proj = np.sum(binary, axis=1).astype(np.float64)
        h_proj /= 255.0  # normalize to pixel counts

        # Find line bands
        bands = self._find_bands(h_proj)

        # Refine with connected components
        lines = []
        for i, (y_start, y_end) in enumerate(bands):
            band = binary[y_start:y_end, :]

            # Connected components within band
            num_labels, labels = cv2.connectedComponents(
                band, connectivity=8
            )

            if num_labels <= 1:
                continue

            # Group components into lines by vertical overlap
            components = []
            for label in range(1, num_labels):
                mask = labels == label
                ys, xs = np.where(mask)
                if len(xs) < 3:  # too small
                    continue
                components.append((xs.min(), ys.min(), xs.max(), ys.max()))

            if not components:
                continue

            # Project components vertically
            v_proj = np.zeros(band.shape[1])
            for cx1, cy1, cx2, cy2 in components:
                v_proj[cx1 : cx2 + 1] += 1

            # Find horizontal groups (words/lines)
            x_start = cx1 = 0
            x_end = cx2 = band.shape[1]

            if len(components) > 1:
                cx_starts = [c[0] for c in components]
                cx_ends = [c[2] for c in components]
                x_start = min(cx_starts)
                x_end = max(cx_ends)

            line = SegmentedLine(
                x=x_start,
                y=y_start,
                width=x_end - x_start,
                height=y_end - y_start,
                reading_order=len(lines),
                confidence=min(1.0, (y_end - y_start) / 30.0),
                metadata={"band_idx": i, "num_components": len(components)},
            )
            lines.append(line)

        # Sort by reading order (top-to-bottom, left-to-right within same row)
        lines.sort(key=lambda l: (l.y, l.x))
        for idx, line in enumerate(lines):
            line.reading_order = idx

        elapsed_ms = (time.time() - start) * 1000
        logger.info(
            "projection_segmentation_complete",
            num_lines=len(lines),
            elapsed_ms=round(elapsed_ms, 1),
        )
        return lines

    def _find_bands(self, h_proj: np.ndarray) -> List[Tuple[int, int]]:
        """Find text bands from horizontal projection.

        A band starts where projection exceeds threshold and ends at next gap.
        """
        h = len(h_proj)
        if h == 0:
            return []

        # Adaptive threshold: rows with significant ink
        threshold = max(np.mean(h_proj), 0.1) * self.gap_ratio

        in_band = False
        bands: List[Tuple[int, int]] = []
        band_start = 0

        for i, val in enumerate(h_proj):
            if val > threshold:
                if not in_band:
                    band_start = i
                    in_band = True
            else:
                if in_band:
                    band_end = i
                    if band_end - band_start >= self.min_line_height:
                        bands.append((band_start, band_end))
                    in_band = False

        # Last band
        if in_band:
            band_end = h
            if band_end - band_start >= self.min_line_height:
                bands.append((band_start, band_end))

        return bands


class KrakenSegmenter:
    """Kraken text segmenter (optional, skip gracefully if not installed)."""

    def __init__(self):
        self.available = False
        try:
            import kraken  # noqa: F401

            self.available = True
        except ImportError:
            logger.warning("kraken_not_available", hint="pip install kraken-ocr")

    def segment(self, image: np.ndarray) -> List[SegmentedLine]:
        """Segment using Kraken if available."""
        if not self.available:
            raise OCRException("Kraken is not installed. Use projection profile instead.")
        # TODO: implement Kraken segmentation
        raise NotImplementedError("Kraken segmentation not yet implemented")


class LearnedSegmenter:
    """U-Net-based text line detector (optional, trained model)."""

    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        if model_path:
            try:
                import torch

                if torch.path.exists(model_path):
                    state = torch.load(model_path, map_location="cpu")
                    logger.info("learned_segmenter_loaded", path=model_path)
            except Exception as e:
                logger.warning("learned_segmenter_failed", error=str(e))

    @property
    def available(self) -> bool:
        return self.model is not None

    def segment(self, image: np.ndarray) -> List[SegmentedLine]:
        if not self.available:
            raise OCRException("Learned segmenter model not loaded.")
        # TODO: forward pass + threshold
        raise NotImplementedError("Learned segmentation forward pass not yet implemented")


class PipelineSegmenter:
    """High-level segmenter that selects the best strategy.

    Tries learned first, falls back to projection profile, then Kraken.
    """

    def __init__(
        self,
        use_projection: bool = True,
        use_kraken: bool = False,
        use_learned: bool = False,
        projection_params: Optional[Dict[str, Any]] = None,
    ):
        params = projection_params or {}
        self.segmenter: Any = None

        if use_learned:
            self.segmenter = LearnedSegmenter()
            if not self.segmenter.available:
                logger.info("learned_segmenter_unavailable, falling_back_to_projection")
                self.segmenter = None

        if self.segmenter is None and use_projection:
            self.segmenter = ProjectionProfileSegmenter(**params)

        if self.segmenter is None and use_kraken:
            kraken = KrakenSegmenter()
            if kraken.available:
                self.segmenter = kraken

        if self.segmenter is None:
            self.segmenter = ProjectionProfileSegmenter(**params)

        logger.info("pipeline_segmenter_initialized", type=type(self.segmenter).__name__)

    def segment(self, image: np.ndarray) -> List[SegmentedLine]:
        """Run segmentation on an image."""
        try:
            return self.segmenter.segment(image)
        except Exception as e:
            logger.error("segmentation_failed", error=str(e), fallback="projection_profile")
            fallback = ProjectionProfileSegmenter()
            return fallback.segment(image)


def compute_iou(box_a: Tuple[int, int, int, int], box_b: Tuple[int, int, int, int]) -> float:
    """Compute IoU between two boxes (x, y, w, h)."""
    ax1, ay1 = box_a[0], box_a[1]
    ax2, ay2 = box_a[0] + box_a[2], box_a[1] + box_a[3]
    bx1, by1 = box_b[0], box_b[1]
    bx2, by2 = box_b[0] + box_b[2], box_b[1] + box_b[3]

    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)

    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    union = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - inter
    return inter / union if union > 0 else 0.0


def match_segments(
    predicted: List[SegmentedLine], ground_truth: List[Tuple[int, int, int, int]], iou_threshold: float = 0.5
) -> Tuple[int, int, int]:
    """Match predicted segments against ground truth boxes.

    Returns (TP, FP, FN) at the given IoU threshold.
    """
    used = [False] * len(ground_truth)
    tp = fp = fn = 0

    for pred in predicted:
        pbox = (pred.x, pred.y, pred.width, pred.height)
        best_iou = 0.0
        best_idx = -1

        for i, gbox in enumerate(ground_truth):
            if used[i]:
                continue
            iou = compute_iou(pbox, gbox)
            if iou > best_iou:
                best_iou = iou
                best_idx = i

        if best_iou >= iou_threshold and best_idx >= 0:
            used[best_idx] = True
            tp += 1
        else:
            fp += 1

    fn = sum(1 for u in used if not u)
    return tp, fp, fn


def compute_prf1(
    predicted: List[SegmentedLine],
    ground_truth: List[Tuple[int, int, int, int]],
    iou_thresholds: Optional[List[float]] = None,
) -> Dict[str, Dict[str, float]]:
    """Compute precision/recall/F1 at multiple IoU thresholds.

    Returns {threshold: {'precision': p, 'recall': r, 'f1': f1}}
    """
    if iou_thresholds is None:
        iou_thresholds = [0.5, 0.7, 0.9]

    results = {}
    for thr in iou_thresholds:
        tp, fp, fn = match_segments(predicted, ground_truth, thr)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        results[f"{thr:.1f}"] = {"precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4)}

    return results
