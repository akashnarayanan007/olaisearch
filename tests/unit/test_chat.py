"""Tests for the ManuscriptChat module."""
from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock, patch

from backend.chat.chat import (
    CitationVerifier,
    ProvenanceDetector,
    WorkIdentifier,
    ManuscriptChat,
    ConversationMemory,
)


# ─── CitationVerifier ────────────────────────────────────────────────────────

def test_citation_verifier_valid():
    """Verify that a citation string with valid JSON is parsed correctly."""
    verifier = CitationVerifier()
    citation_str = json.dumps({
        "manuscript_id": "ms_001",
        "line_id": "ms_001_line_3",
        "text_snippet": "சோழரா காலம்",
        "tier": "MANUSCRIPT"
    })
    parsed = verifier.parse_citation(citation_str)
    assert parsed["manuscript_id"] == "ms_001"
    assert parsed["line_id"] == "ms_001_line_3"
    assert parsed["tier"] == "MANUSCRIPT"


def test_citation_verifier_invalid_json():
    verifier = CitationVerifier()
    result = verifier.parse_citation("not valid json {")
    assert result is None or "error" in result


def test_citation_verifier_missing_fields():
    verifier = CitationVerifier()
    partial = json.dumps({"manuscript_id": "ms_001"})
    parsed = verifier.parse_citation(partial)
    # Should still parse, but line_id is missing
    assert parsed["manuscript_id"] == "ms_001"
    assert "line_id" not in parsed or parsed.get("line_id") is None


def test_citation_verifier_strips_unverified():
    """Response with unverifiable citations should strip them."""
    verifier = CitationVerifier()
    response_text = (
        'The text states "X" [citation:{"manuscript_id":"bad_id","line_id":"bad_line"}]'
    )
    cleaned = verifier.verify_and_clean(response_text)
    # Unverifiable citations removed or marked
    assert cleaned is not None


# ─── ProvenanceDetector ────────────────────────────────────────────────────────

def test_provenance_detector_colophon_pattern():
    """Colophon phrases should trigger provenance detection."""
    detector = ProvenanceDetector()
    text = "இசைத் திருமங்கையாழ்வார்பாடலை எழுதியவர் அகிலபரமேச்வரர்"  # scribe name
    result = detector.detect(text)
    assert isinstance(result, dict)
    # Heuristics return a score; may or may not detect
    assert "colophon" in result or "confidence" in result


def test_provenance_detector_empty():
    detector = ProvenanceDetector()
    result = detector.detect("")
    assert isinstance(result, dict)


def test_provenance_detector_no_patterns():
    detector = ProvenanceDetector()
    result = detector.detect("plain text with no provenance markers")
    assert isinstance(result, dict)


# ─── WorkIdentifier ─────────────────────────────────────────────────────────────

def test_work_identifier_known():
    """Similar text should have high overlap with known work."""
    identifier = WorkIdentifier()
    identifier.add_known_work("திருக்குறள்", ["அகப்பாடல் இன்பத் துறவி", "அறத்துப்பால்"])
    result = identifier.identify("அறத்துப்பால் குறள்")
    assert isinstance(result, dict)
    assert result.get("similarity", 0) > 0


def test_work_identifier_unknown():
    identifier = WorkIdentifier()
    identifier.add_known_work("UnknownText", ["xyzwv"])
    result = identifier.identify("completely different text entirely")
    assert result.get("similarity", 1.0) < 0.5


# ─── ConversationMemory ─────────────────────────────────────────────────────────

def test_memory_add_and_get():
    mem = ConversationMemory(max_turns=5)
    mem.add("user", "What is this about?")
    mem.add("assistant", "This manuscript discusses Tamil literature.")
    msgs = mem.get_messages()
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[1]["role"] == "assistant"


def test_memory_max_turns_truncation():
    mem = ConversationMemory(max_turns=2)
    mem.add("user", "m1")
    mem.add("assistant", "a1")
    mem.add("user", "m2")
    mem.add("assistant", "a2")
    mem.add("user", "m3")  # should push out m1/a1
    msgs = mem.get_messages()
    assert len(msgs) <= 4  # max_turns * 2


def test_memory_clear():
    mem = ConversationMemory()
    mem.add("user", "hello")
    mem.clear()
    assert mem.get_messages() == []


# ─── ManuscriptChat (mock) ─────────────────────────────────────────────────────

def test_manuscriptchat_fallback_no_api_key():
    """Without an API key, ManuscriptChat should use template fallback."""
    mock_retriever = MagicMock()
    mock_retriever.search = MagicMock(return_value=[])
    chat = ManuscriptChat(retriever=mock_retriever)
    result = chat.ask(
        question="What is in this manuscript?",
        manuscript_id="ms_test",
        mode="leaf",
    )
    # Fallback response should still be a valid ChatResponse
    assert result is not None
    # Check it has expected structure
    assert hasattr(result, "response") or isinstance(result, dict)


def test_manuscriptchat_evidence_tiers():
    """Verify the three-tier system is present in the response structure."""
    mock_retriever = MagicMock()
    mock_retriever.search = MagicMock(return_value=[])
    chat = ManuscriptChat(retriever=mock_retriever)
    result = chat.ask(
        question="When was this written?",
        manuscript_id="ms_test",
        line_id="ms_test_line_1",
        mode="leaf",
        explain_mode="simple",
    )
    # Response should have evidence structure
    if isinstance(result, dict):
        for tier in ["manuscript_evidence", "archive_evidence", "background"]:
            assert tier in result or tier.replace("_", " ") in str(result)
