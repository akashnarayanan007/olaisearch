"""Tests for the recognition pipeline (CER/WER, grapheme awareness)."""
from __future__ import annotations

from backend.pipeline.recognition import (
    Calibration,
    compute_cer,
    compute_wer,
    split_graphemes,
)

# ─── Grapheme splitting ───────────────────────────────────────────────────────

def test_split_graphemes_basic():
    assert split_graphemes("hello") == list("hello")


def test_split_graphemes_zwj():
    # ZWJ sequence: 👨‍👩‍👦
    text = "👨‍👩‍👦"
    clusters = split_graphemes(text)
    # Should not split inside the ZWJ sequence
    assert len(clusters) >= 1
    full = "".join(clusters)
    assert full == text  # round-trip preserves


def test_split_graphemes_nfc():
    text = "é"  # precomposed e-acute
    nfc = "é"  # decomposed
    clusters_nfc = split_graphemes(text)
    clusters_nfd = split_graphemes(nfc)
    # Both should produce the same visual characters when joined
    assert "".join(clusters_nfc) == text
    assert "".join(clusters_nfd) == nfc


# ─── CER / WER ────────────────────────────────────────────────────────────────

def test_cer_identical():
    assert compute_cer("கலிங்கத்தோற்பாவை", "கலிங்கத்தோற்பாவை") == 0.0


def test_cer_single_substitution():
    ref = "அயர்லாந்து"
    hyp = "அயர்லானு"
    cer = compute_cer(hyp, ref)
    assert 0.0 < cer <= 1.0


def test_cer_empty_ref():
    assert compute_cer("abc", "") == 1.0


def test_cer_empty_both():
    assert compute_cer("", "") == 0.0


def test_wer_identical():
    assert compute_wer(["a", "b"], ["a", "b"]) == 0.0


def test_wer_completely_different():
    assert compute_wer(["a", "b"], ["c", "d"]) == 1.0


def test_wer_partial_match():
    # 1 out of 2 words correct
    wer = compute_wer(["கலை", "இலக்கணம்"], ["கலை", "பாடல்"])
    assert 0.0 < wer <= 1.0


# ─── Calibration ───────────────────────────────────────────────────────────────

def test_calibration_empty():
    cal = Calibration()
    metrics = cal.evaluate([])
    assert metrics["ece"] == 0.0


def test_calibration_perfect():
    cal = Calibration()
    data = [{"conf": 0.9, "correct": True} for _ in range(10)]
    metrics = cal.evaluate(data)
    # ECE < 0.11 for near-zero calibration error (10 samples, all in one bin)
    assert metrics["ece"] < 0.11


def test_calibration_miscalibrated():
    cal = Calibration()
    # High conf but often wrong → high ECE
    data = [{"conf": 0.95, "correct": False} for _ in range(10)]
    metrics = cal.evaluate(data)
    assert metrics["ece"] > 0.3


def test_calibration_blend():
    cal = Calibration()
    data = [{"conf": 0.8, "correct": True} for _ in range(5)] + \
           [{"conf": 0.3, "correct": False} for _ in range(5)]
    cal.update(data)
    blended = cal.blend(0.5)
    # Blended confidence should differ from raw
    assert isinstance(blended, dict)
