"""Tests for the post-correction pipeline."""
from __future__ import annotations

import json
import pytest

from backend.pipeline.postcorrection import (
    LexiconCorrector,
    Transliterator,
    DateNormalizer,
    DomainGlossary,
)


# ─── LexiconCorrector ──────────────────────────────────────────────────────────

def test_correct_exact_match():
    corr = LexiconCorrector()
    text = "கலிங் கதாபாவை"
    result = corr.correct(text, lexicon={"கலிங்", "கதாபாவை"})
    assert result["text"] == text


def test_correct_near_match():
    corr = LexiconCorrector()
    text = "கலின்க கதாபாவை"  # one char off
    result = corr.correct(text, lexicon={"கலிங்", "கதாபாவை"})
    assert result["text"] != text  # correction applied
    assert len(result["diffs"]) > 0


def test_correct_no_lexicon():
    corr = LexiconCorrector()
    result = corr.correct("any text")
    assert result["text"] == "any text"
    assert result["diffs"] == []


# ─── Transliterator ────────────────────────────────────────────────────────────

def test_transliterate_tamil_to_roman():
    trans = Transliterator()
    # Tamil character 'அ' → 'a'
    result = trans.transliterate("அ", script="tam")
    assert isinstance(result, str)
    assert len(result) > 0


def test_transliterate_roman_passthrough():
    trans = Transliterator()
    result = trans.transliterate("hello", script="eng")
    assert result == "hello"


def test_transliterate_unknown_script():
    trans = Transliterator()
    result = trans.transliterate("some text", script="xyz")
    assert isinstance(result, str)


# ─── DateNormalizer ────────────────────────────────────────────────────────────

def test_normalize_saka_date():
    norm = DateNormalizer()
    # Saka year 1450 ≈ 1528 CE
    result = norm.normalize("Saka 1450", era="saka")
    assert result.get("ce_year") is not None
    assert result["ce_year"] > 0


def test_normalize_kali_date():
    norm = DateNormalizer()
    result = norm.normalize("Kali 5000", era="kali")
    assert result.get("ce_year") is not None


def test_normalize_tamil_renal():
    norm = DateNormalizer()
    result = norm.normalize("Tamil Renal 1050", era="tamil")
    assert result.get("ce_year") is not None or result.get("normalised") is not None


def test_normalize_no_match():
    norm = DateNormalizer()
    result = norm.normalize("no date here", era="saka")
    assert result.get("ce_year") is None or result.get("found") is False


# ─── DomainGlossary ────────────────────────────────────────────────────────────

def test_glossary_add_lookup():
    gl = DomainGlossary()
    gl.add("மருந்து", "ayurveda", "medicinal herb")
    entries = gl.lookup("மருந்து")
    assert len(entries) >= 1
    assert any("ayurveda" in e.get("domain", "") or "herb" in str(e) for e in entries)


def test_glossary_empty_lookup():
    gl = DomainGlossary()
    assert gl.lookup("unknown_term_xyz") == [] or gl.lookup("unknown_term_xyz") == {}
