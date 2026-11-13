"""Tests for the script identification module."""
from __future__ import annotations

import pytest

try:
    import torch
except ImportError:
    torch = None

from backend.pipeline.script_id import (
    SCRIPT_REGISTRY,
    ScriptCNN,
    ScriptIdentifier,
)

# ─── registry ─────────────────────────────────────────────────────────────────

def test_script_registry_has_entries():
    assert "tam" in SCRIPT_REGISTRY
    assert "san" in SCRIPT_REGISTRY
    assert "mal" in SCRIPT_REGISTRY


def test_script_registry_maps_to_tesseract_langs():
    """Each registered code maps to a non-empty string."""
    for code, langs in SCRIPT_REGISTRY.items():
        assert isinstance(langs, str)
        assert len(langs) > 0


# ─── ScriptIdentifier (heuristic branch) ─────────────────────────────────────

def test_identifier_unicode_heuristic_tamil():
    ident = ScriptIdentifier()
    result = ident.identify_text("இது உம்")  # Tamil characters
    assert result["script"] == "tam"
    assert result["confidence"] > 0.5


def test_identifier_unicode_heuristic_sanskrit():
    ident = ScriptIdentifier()
    result = ident.identify_text("कालिदासः")  # Devanagari
    assert result["script"] == "san"


def test_identifier_unicode_heuristic_unknown():
    ident = ScriptIdentifier()
    result = ident.identify_text("hello world")
    # Falls back to 'eng' or similar
    assert result["script"] in SCRIPT_REGISTRY


def test_identifier_empty_text():
    ident = ScriptIdentifier()
    result = ident.identify_text("")
    assert result["script"] == "eng"
    assert result["method"] == "unicode_heuristic"


# ─── ScriptCNN (requires torch) ─────────────────────────────────────────────

@pytest.mark.skipif(torch is None, reason="PyTorch not installed")
def test_script_cnn_initialization():
    cnn = ScriptCNN()
    assert cnn.model is not None  # PyTorch linear model created in __init__


@pytest.mark.skipif(torch is None, reason="PyTorch not installed")
def test_script_cnn_forward():
    cnn = ScriptCNN()
    x = torch.randn(1, 1, 40, 200)
    with torch.no_grad():
        out = cnn.model(x)
    assert out.shape[-1] == 10


@pytest.mark.skipif(torch is None, reason="PyTorch not installed")
def test_script_cnn_forward_shapes():
    cnn = ScriptCNN()
    batch_sizes = [1, 4, 16]
    for bs in batch_sizes:
        x = torch.randn(bs, 1, 40, 200)
        with torch.no_grad():
            out = cnn.model(x)
        assert out.shape[0] == bs
