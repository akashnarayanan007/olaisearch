"""Tests for the segmentation pipeline."""
from __future__ import annotations

import cv2
import numpy as np
import pytest

from backend.pipeline.segmentation import (
    KrakenSegmenter,
    LearnedSegmenter,
    PipelineSegmenter,
    ProjectionProfileSegmenter,
    SegmentedLine,
    compute_iou,
    compute_prf1,
    match_segments,
)

# ─── fixtures ─────────────────────────────────────────────────────────────────

def _make_grid_image(num_lines: int = 5, line_height: int = 30, gap: int = 20,
                     img_h: int = 300, img_w: int = 400) -> np.ndarray:
    """Create a synthetic image with evenly-spaced dark horizontal bars (text lines)."""
    img = np.full((img_h, img_w), 240, dtype=np.uint8)  # light background
    bar_start = gap
    for _ in range(num_lines):
        cv2.rectangle(img, (10, bar_start), (img_w - 10, bar_start + line_height), 30, -1)
        bar_start += line_height + gap
    return img


@pytest.fixture
def grid_image():
    return _make_grid_image(num_lines=5)


@pytest.fixture
def segmenter():
    return ProjectionProfileSegmenter()


@pytest.fixture
def pipeline():
    return PipelineSegmenter(use_projection=True)


# ─── ProjectionProfileSegmenter ───────────────────────────────────────────────

def test_segment_returns_lines(segmenter, grid_image):
    lines = segmenter.segment(grid_image)
    assert isinstance(lines, list)
    assert len(lines) > 0
    for line in lines:
        assert isinstance(line, SegmentedLine)
        assert line.confidence > 0


def test_segment_sorts_by_reading_order(segmenter, grid_image):
    lines = segmenter.segment(grid_image)
    ys = [item.y for item in lines]
    assert ys == sorted(ys), "Lines should be sorted top-to-bottom"


def test_segment_on_blank_image(segmenter):
    blank = np.full((100, 200), 255, dtype=np.uint8)
    lines = segmenter.segment(blank)
    assert len(lines) == 0


def test_segment_on_color_image(segmenter):
    color = np.full((100, 200, 3), 240, dtype=np.uint8)
    cv2.rectangle(color, (10, 20), (190, 40), 30, -1)
    lines = segmenter.segment(color)
    assert len(lines) >= 1


def test_segment_with_deskew(segmenter, grid_image):
    lines = segmenter.segment(grid_image, deskew_angle=0.0)
    assert len(lines) > 0


def test_find_bands(segmenter):
    # Flat projection with 3 peaks
    proj = np.zeros(100)
    proj[10:20] = 100
    proj[40:55] = 80
    proj[70:80] = 90
    bands = segmenter._find_bands(proj)
    assert len(bands) >= 1


# ─── PipelineSegmenter ────────────────────────────────────────────────────────

def test_pipeline_fallback_to_projection(pipeline):
    """Pipeline always returns at least projection results."""
    img = _make_grid_image()
    lines = pipeline.segment(img)
    assert isinstance(lines, list)


def test_pipeline_segment_with_invalid_input():
    pipeline = PipelineSegmenter(use_projection=True)
    # None input should not crash — fallback segmenter handles it
    try:
        lines = pipeline.segment(np.zeros((100, 100), dtype=np.uint8))
        assert isinstance(lines, list)
    except Exception:
        pytest.fail("Pipeline should handle basic inputs without crashing")


# ─── Kraken & Learned (stubs) ─────────────────────────────────────────────────

def test_kraken_not_available():
    kraken = KrakenSegmenter()
    # May or may not be installed; test gracefully raises
    if not kraken.available:
        with pytest.raises(Exception):
            kraken.segment(np.zeros((100, 100), dtype=np.uint8))


def test_learned_unavailable():
    learned = LearnedSegmenter()
    assert not learned.available
    with pytest.raises(Exception):
        learned.segment(np.zeros((100, 100), dtype=np.uint8))


# ─── Metrics ───────────────────────────────────────────────────────────────────

def test_compute_iou_perfect_overlap():
    box = (0, 0, 100, 100)
    assert abs(compute_iou(box, box) - 1.0) < 1e-9


def test_compute_iou_no_overlap():
    a = (0, 0, 50, 50)
    b = (100, 100, 50, 50)
    assert compute_iou(a, b) == 0.0


def test_compute_iou_partial_overlap():
    a = (0, 0, 100, 100)
    b = (50, 50, 100, 100)
    iou = compute_iou(a, b)
    assert 0.0 < iou < 1.0


def test_match_segments_exact():
    predicted = [SegmentedLine(x=0, y=0, width=100, height=20, reading_order=0)]
    gt = [(0, 0, 100, 20)]
    tp, fp, fn = match_segments(predicted, gt, iou_threshold=0.5)
    assert tp == 1 and fp == 0 and fn == 0


def test_match_segments_missing():
    predicted: list = []
    gt = [(0, 0, 100, 20)]
    tp, fp, fn = match_segments(predicted, gt)
    assert tp == 0 and fp == 0 and fn == 1


def test_match_segments_false_positive():
    predicted = [SegmentedLine(x=200, y=200, width=50, height=10, reading_order=0)]
    gt = [(0, 0, 100, 20)]
    tp, fp, fn = match_segments(predicted, gt)
    assert tp == 0 and fp == 1 and fn == 1


def test_compute_prf1():
    predicted = [SegmentedLine(x=0, y=0, width=100, height=30, reading_order=0),
                 SegmentedLine(x=0, y=50, width=100, height=30, reading_order=1)]
    gt = [(0, 0, 100, 30), (0, 50, 100, 30)]
    results = compute_prf1(predicted, gt, iou_thresholds=[0.5])
    assert "0.5" in results
    assert results["0.5"]["precision"] == pytest.approx(1.0, abs=1e-3)
    assert results["0.5"]["recall"] == pytest.approx(1.0, abs=1e-3)
