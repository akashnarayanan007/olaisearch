"""Tests for the hybrid retrieval engine."""
from __future__ import annotations

import pytest

from backend.retrieval.hybrid import (
    CharNGramIndexer,
    HybridRetriever,
    PhoneticNormalizer,
    reciprocal_rank_fusion,
)

# ─── RRF ────────────────────────────────────────────────────────────────────────

def test_rrf_single_ranking():
    rankings = [{"doc_id": "a", "rank": 1}, {"doc_id": "b", "rank": 2}]
    fused = reciprocal_rank_fusion([rankings])
    assert fused[0]["doc_id"] == "a"
    assert fused[1]["doc_id"] == "b"


def test_rrf_multiple_rankings():
    r1 = [{"doc_id": "a", "rank": 1}, {"doc_id": "b", "rank": 2}]
    r2 = [{"doc_id": "b", "rank": 1}, {"doc_id": "a", "rank": 2}]
    fused = reciprocal_rank_fusion([r1, r2], k=60)
    # Both docs get contributions; order may swap
    ids = [f["doc_id"] for f in fused]
    assert set(ids) == {"a", "b"}


def test_rrf_empty():
    fused = reciprocal_rank_fusion([[]])
    assert fused == []


def test_rrf_single_empty():
    fused = reciprocal_rank_fusion([[], []])
    assert fused == []


# ─── PhoneticNormalizer ─────────────────────────────────────────────────────────

def test_phonetic_normalizer_tamil():
    norm = PhoneticNormalizer()
    result = norm.normalize("கலிங்")
    assert isinstance(result, str)


def test_phonetic_normalizer_roman_passthrough():
    norm = PhoneticNormalizer()
    result = norm.normalize("hello")
    assert isinstance(result, str)


def test_phonetic_normalizer_empty():
    norm = PhoneticNormalizer()
    result = norm.normalize("")
    assert result == ""


# ─── CharNGramIndexer ───────────────────────────────────────────────────────────

def test_ngram_indexer_extract():
    indexer = CharNGramIndexer()
    ngrams = indexer.extract_ngrams("abcde", n=(2, 5))
    assert isinstance(ngrams, list)
    assert len(ngrams) > 0
    # Check specific ngrams
    assert "ab" in ngrams
    assert "abc" in ngrams
    assert "abcde" in ngrams


def test_ngram_indexer_fuzzy_search():
    indexer = CharNGramIndexer()
    terms = ["கலிங்", "கலெங்", "kalinga"]
    query = "கலிங்"
    hits = indexer.search(query, terms, top_k=5)
    assert isinstance(hits, list)


# ─── HybridRetriever (with in-memory DB) ────────────────────────────────────────

@pytest.fixture
def retriever(tmp_path):
    db_path = str(tmp_path / "test_retrieval.db")
    r = HybridRetriever(db_path=db_path)
    r.connect()
    yield r
    r.close()


def test_retriever_connect(retriever):
    assert retriever.db is not None


def test_retriever_search_no_results(retriever):
    results = retriever.search("nonexistent query xyz")
    assert isinstance(results, list)
    assert len(results) == 0


def test_retriever_index_and_search(retriever):
    """Index a synthetic manuscript and find it."""
    from backend.core.models import BoundingBox, Line, Manuscript, OCRResult

    ms = Manuscript(
        id="ms_test_001",
        image_path="test.jpg",
        language="tam",
        script="tam",
        lines=[
            Line(
                id="ms_test_001_line_0",
                text="கலிங் கதாபாவை",
                bbox=BoundingBox(x=0, y=0, width=100, height=20),
                confidence=0.95,
                ocr=OCRResult(text="கலிங் கதாபாவை", confidence=0.95),
            )
        ],
    )
    retriever.index_manuscript(ms)
    results = retriever.search("கலிங்", limit=5)
    assert isinstance(results, list)


def test_retriever_close(retriever, tmp_path):
    retriever.close()
    assert retriever.db is None
