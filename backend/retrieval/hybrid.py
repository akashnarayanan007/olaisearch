"""Hybrid retrieval engine with BM25, character n-grams, phonetic index,
dense embeddings, Reciprocal Rank Fusion, reranking, cross-lingual search,
query understanding, and n-best OCR uncertainty awareness.

Architecture:
- SQLite FTS5: BM25 (words + char n-grams + phonetic/normalized)
- FAISS: dense multilingual embeddings
- RRF: fuse all result lists
- Reranker: optional cross-encoder or LLM reranker
- N-best: index top-k recognition alternatives weighted by confidence
"""
from __future__ import annotations

import hashlib
import re
import sqlite3
import time
from typing import Any

import numpy as np

from backend.core.logging import get_logger
from backend.core.models import BoundingBox, SearchResult

logger = get_logger(__name__)


# ─── Phonetic / Transliteration Normalization ─────────────────────────────────

class PhoneticNormalizer:
    """Normalize Indic text to Roman transliteration for phonetic search.

    When user types Tamil in Roman (e.g., "kaṇṭa"), it matches the transliteration index.
    """

    TAMIL_TO_ROMAN: dict[str, str] = {
        "க": "ka", "ங": "nga", "ச": "cha", "ஞ": "nya", "ட": "ḍa",
        "ண": "ṇa", "த": "ta", "ந": "na", "ப": "pa", "ம": "ma",
        "ய": "ya", "ர": "ra", "ல": "la", "வ": "va", "ழ": "zha",
        "ள": "lla", "ற": "ra", "ன": "na",
        "அ": "a", "ஆ": "ā", "இ": "i", "ஈ": "ī", "உ": "u", "ஊ": "ū",
        "எ": "e", "ஏ": "ē", "ஐ": "ai", "ஒ": "o", "ஓ": "ō", "ஔ": "au",
    }

    MALAYALAM_TO_ROMAN: dict[str, str] = {
        "ക": "ka", "ഖ": "kha", "ഗ": "ga", "ഘ": "gha", "ങ": "nga",
        "ച": "cha", "ജ": "ja", "ഞ": "nya",
    }

    DEVANAGARI_TO_ROMAN: dict[str, str] = {
        "क": "ka", "ख": "kha", "ग": "ga", "घ": "gha", "ङ": "nga",
        "च": "ca", "छ": "cha", "ज": "ja", "झ": "jha", "ञ": "nya",
        "ट": "ṭa", "ठ": "ṭha", "ड": "ḍa", "ढ": "ḍha", "ण": "ṇa",
        "त": "ta", "थ": "tha", "द": "da", "ध": "dha", "न": "na",
        "प": "pa", "फ": "pha", "ब": "ba", "भ": "bha", "म": "ma",
        "य": "ya", "र": "ra", "ल": "la", "व": "va", "श": "sha",
        "ष": "sya", "स": "sa", "ह": "ha",
    }

    def normalize(self, text: str, script: str = "auto") -> str:
        """Convert Indic text to Roman transliteration for phonetic matching."""
        if script == "auto":
            # Auto-detect script
            if any(c in "அ-ஶ" for c in text):
                mapping = self.TAMIL_TO_ROMAN
            elif any(c in "ക-ൺ" for c in text):
                mapping = self.MALAYALAM_TO_ROMAN
            elif any(c in "क-ह" for c in text):
                mapping = self.DEVANAGARI_TO_ROMAN
            else:
                return text.lower()
        elif script == "tam":
            mapping = self.TAMIL_TO_ROMAN
        elif script == "mal":
            mapping = self.MALAYALAM_TO_ROMAN
        else:
            mapping = self.DEVANAGARI_TO_ROMAN

        result = []
        for ch in text:
            if ch in mapping:
                result.append(mapping[ch])
            else:
                result.append(ch.lower())
        return " ".join(result)


# ─── Character N-grams ────────────────────────────────────────────────────────

class CharNGramIndexer:
    """Character n-gram extraction for fuzzy matching (handles OCR noise)."""

    def __init__(self, min_n: int = 2, max_n: int = 5):
        self.min_n = min_n
        self.max_n = max_n

    def extract(self, text: str) -> list[str]:
        """Extract character n-grams from text."""
        ngrams = set()
        text_clean = text.lower().strip()
        for n in range(self.min_n, self.max_n + 1):
            if len(text_clean) >= n:
                for i in range(len(text_clean) - n + 1):
                    ngrams.add(text_clean[i : i + n])
        return list(ngrams)

    def extract_ngrams(self, text: str, n: tuple[int, int] | None = None) -> list[str]:
        """Extract character n-grams with explicit (min_n, max_n) range."""
        if n is None:
            n = (self.min_n, self.max_n)
        min_n, max_n = n
        ngrams = set()
        text_clean = text.lower().strip()
        for length in range(min_n, max_n + 1):
            if len(text_clean) >= length:
                for i in range(len(text_clean) - length + 1):
                    ngrams.add(text_clean[i : i + length])
        return list(ngrams)

    def search(self, query: str, terms: list[str], top_k: int = 5) -> list[dict[str, Any]]:
        """Find the closest terms to *query* by overlapping character n-grams.

        Returns a list of ``{"term": str, "score": float}`` sorted by score descending.
        """
        if not terms or not query:
            return []
        query_ngrams = set(self.extract(query))
        results: list[dict[str, Any]] = []
        for term in terms:
            term_ngrams = set(self.extract(term))
            if not query_ngrams or not term_ngrams:
                continue
            overlap = len(query_ngrams & term_ngrams)
            union = len(query_ngrams | term_ngrams)
            score = overlap / union if union > 0 else 0.0
            results.append({"term": term, "score": round(score, 4)})
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:top_k]

    def to_fts_query(self, text: str) -> str:
        """Build FTS5 query from char n-grams of a search string."""
        ngrams = self.extract(text)
        if not ngrams:
            return text
        return " OR ".join(f'"{ng}"' for ng in ngrams[:20])  # limit query size


# ─── Dense Embeddings (FAISS) ─────────────────────────────────────────────────

class DenseEmbedder:
    """Multilingual dense embedding generator (local fallback: sentence-transformers)."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            logger.info("embedder_loaded", model=model_name)
        except Exception as e:
            logger.warning("embedder_fallback_to_hashing", model=model_name, error=str(e))

    def embed(self, texts: list[str]) -> np.ndarray:
        """Embed a list of texts into dense vectors."""
        if self.model is not None:
            return self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False).astype(np.float32)
        # Fallback: simple hash-based vector (not semantic but enables structure)
        return self._hash_fallback(texts)

    def _hash_fallback(self, texts: list[str]) -> np.ndarray:
        """Fallback: hash each word to a pseudo-vector dimension."""
        dim = 128
        vectors = np.zeros((len(texts), dim), dtype=np.float32)
        for i, text in enumerate(texts):
            words = text.lower().split()
            for w in words:
                h = int(hashlib.md5(w.encode()).hexdigest(), 16)
                vec_idx = h % dim
                magnitude = 1.0 / (1.0 + len(words))
                vectors[i, vec_idx] += magnitude
            # Normalize
            norm = np.linalg.norm(vectors[i])
            if norm > 0:
                vectors[i] /= norm
        return vectors


# ─── Reciprocal Rank Fusion ──────────────────────────────────────────────────

def reciprocal_rank_fusion(
    ranked_lists: list[Any], k: int = 60
) -> list[Any]:
    """Fuse multiple ranked result lists using RRF.

    Accepts two formats:
    - Dict format:  [{"doc_id": "a", "rank": 1}, {"doc_id": "b", "rank": 2}]
    - Tuple format: [("a", 1.0), ("b", 0.8)]

    Returns results in the same format as the input.
    """
    if not ranked_lists or not any(ranked_lists):
        return []

    # Detect input format from first non-empty list
    first = next((r for r in ranked_lists if r), None)
    if not first:
        return []

    is_dict_format = isinstance(first[0], dict)

    scores: dict[str, float] = {}
    for ranked in ranked_lists:
        for rank_idx, item in enumerate(ranked):
            if is_dict_format:
                doc_id = item["doc_id"]
            else:
                doc_id = item[0]
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank_idx + 1)

    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    if is_dict_format:
        return [{"doc_id": doc_id, "score": round(score, 6)} for doc_id, score in sorted_items]
    else:
        return [(doc_id, round(score, 6)) for doc_id, score in sorted_items]


# ─── Query Understanding ─────────────────────────────────────────────────────

class QueryUnderstander:
    """Language detection, OCR-noise-tolerant expansion, and LLM rewriting."""

    def __init__(self):
        self.phonetic = PhoneticNormalizer()
        self.ngram = CharNGramIndexer()

    def detect_script(self, query: str) -> str:
        """Detect script of query."""
        if re.search(r"[அ-ஶ]", query):
            return "tam"
        if re.search(r"[ക-ൺ]", query):
            return "mal"
        if re.search(r"[क-ह]", query):
            return "san"
        return "eng"

    def expand_for_ocr_noise(self, query: str, noise_level: float = 0.1) -> list[str]:
        """Generate variants of query to handle OCR noise."""
        variants = [query]
        # Add char n-gram version for fuzzy match
        if len(query) > 2:
            variants.append(self.ngram.to_fts_query(query))
        # Add phonetic Roman version
        roman = self.phonetic.normalize(query)
        if roman != query:
            variants.append(roman)
        return variants

    def rewrite_with_llm(self, query: str, provider=None) -> str | None:
        """Optional LLM query rewriting."""
        if provider is None:
            return None
        prompt = f"Rewrite this search query for a palm-leaf manuscript archive to get better results: {query}"
        try:
            res = provider.generate(prompt=prompt)
            return res.get("text") if isinstance(res, dict) else str(res)
        except Exception:
            return None


# ─── N-Best OCR Awareness ────────────────────────────────────────────────────

class NBesterIndexer:
    """Index top-k recognition alternatives (n-best) weighted by confidence."""

    def __init__(self, n_best: int = 3):
        self.n_best = n_best

    def build_index_entries(
        self,
        line_id: str,
        manuscript_id: str,
        text: str,
        alternatives: list[dict[str, float]],
        bbox: BoundingBox | None = None,
    ) -> list[dict[str, Any]]:
        """Create FTS index entries for each n-best alternative.

        Args:
            alternatives: [{'text': str, 'confidence': float}, ...]
        """
        entries = []
        # Best hypothesis
        entries.append({
            "line_id": line_id,
            "manuscript_id": manuscript_id,
            "text": text,
            "confidence": 1.0,
            "hypothesis_rank": 0,
        })
        for i, alt in enumerate(alternatives[: self.n_best]):
            entries.append({
                "line_id": line_id,
                "manuscript_id": manuscript_id,
                "text": alt.get("text", ""),
                "confidence": alt.get("confidence", 0.5),
                "hypothesis_rank": i + 1,
            })
        return entries


# ─── Main Hybrid Retriever ───────────────────────────────────────────────────

class HybridRetriever:
    """Full hybrid retrieval engine.

    Components:
    - BM25 FTS5 (words)
    - Character n-gram FTS5 (fuzzy)
    - Phonetic/normalized FTS5 (cross-lingual)
    - Dense embeddings (FAISS)
    - N-best alternative index
    - RRF fusion
    - Optional reranker
    """

    def __init__(
        self,
        db_path: str = "olaisearch.db",
        faiss_index_path: str | None = None,
    ):
        self.db_path = db_path
        self.db: sqlite3.Connection | None = None
        self.embedder = DenseEmbedder()
        self.ngram_indexer = CharNGramIndexer()
        self.phonetic_norm = PhoneticNormalizer()
        self.nbester = NBesterIndexer()
        self.query_understander = QueryUnderstander()
        self.faiss_index = None
        self._setup_db()

    def _setup_db(self):
        """Set up extended database schema."""
        self.db = sqlite3.connect(self.db_path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        cursor = self.db.cursor()

        # Base lines table (mirrored for joins)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lines (
                id TEXT PRIMARY KEY,
                manuscript_id TEXT NOT NULL,
                text TEXT NOT NULL,
                bbox_x INTEGER DEFAULT 0,
                bbox_y INTEGER DEFAULT 0,
                bbox_width INTEGER DEFAULT 0,
                bbox_height INTEGER DEFAULT 0,
                confidence REAL DEFAULT 0.0,
                script TEXT DEFAULT 'eng'
            )
        """)
        # BM25 FTS5 table for words
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS lines_fts USING fts5(
                line_id, manuscript_id, text,
                tokenize='unicode61'
            )
        """)
        # Extended FTS tables
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS lines_ngram_fts USING fts5(
                line_id UNINDEXED, manuscript_id UNINDEXED, ngrams,
                tokenize='unicode61'
            )
        """)
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS lines_phonetic_fts USING fts5(
                line_id UNINDEXED, manuscript_id UNINDEXED, phonetic_text,
                tokenize='unicode61'
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ocr_alternatives (
                line_id TEXT NOT NULL,
                manuscript_id TEXT NOT NULL,
                text TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                hypothesis_rank INTEGER DEFAULT 0,
                PRIMARY KEY (line_id, hypothesis_rank)
            )
        """)
        self.db.commit()

    def connect(self):
        """Connect to database."""
        self._setup_db()

    def index_manuscript(self, manuscript: Any):
        """Index a manuscript into all retrieval structures."""
        if self.db is None:
            self._setup_db()

        cursor = self.db.cursor()

        for i, line in enumerate(manuscript.lines):
            # Standard BM25 FTS
            cursor.execute("""
                INSERT OR REPLACE INTO lines_fts(line_id, manuscript_id, text)
                VALUES (?, ?, ?)
            """, (line.id, manuscript.id, line.text))

            # Char n-gram FTS
            ngrams = " ".join(self.ngram_indexer.extract(line.text))
            cursor.execute("""
                INSERT OR REPLACE INTO lines_ngram_fts(line_id, manuscript_id, ngrams)
                VALUES (?, ?, ?)
            """, (line.id, manuscript.id, ngrams))

            # Phonetic
            phonetic = self.phonetic_norm.normalize(line.text, manuscript.script)
            cursor.execute("""
                INSERT OR REPLACE INTO lines_phonetic_fts(line_id, manuscript_id, phonetic_text)
                VALUES (?, ?, ?)
            """, (line.id, manuscript.id, phonetic))

            # N-best alternatives
            if line.alternatives:
                for j, alt in enumerate(line.alternatives[: self.nbester.n_best]):
                    cursor.execute("""
                        INSERT OR REPLACE INTO ocr_alternatives
                        (line_id, manuscript_id, text, confidence, hypothesis_rank)
                        VALUES (?, ?, ?, ?, ?)
                    """, (line.id, manuscript.id, alt.text, alt.confidence, j + 1))

        self.db.commit()

        # Also embed into FAISS
        self._embed_lines(manuscript)
        logger.info(
            "hybrid_indexed",
            manuscript_id=manuscript.id,
            num_lines=len(manuscript.lines),
        )

    def _embed_lines(self, manuscript: Any):
        """Embed manuscript lines into FAISS index."""
        texts = [line.text for line in manuscript.lines if line.text]
        if not texts:
            return
        vectors = self.embedder.embed(texts)
        if self.faiss_index is None:
            import faiss
            vector_dim = self.embedder.embed(["test"]).shape[-1]
            self.faiss_index = faiss.IndexFlatIP(vector_dim)
            self._line_metadata: list[dict[str, Any]] = []
        self.faiss_index.add(np.ascontiguousarray(vectors))
        for i, line in enumerate(manuscript.lines):
            self._line_metadata.append({
                "line_id": line.id,
                "manuscript_id": manuscript.id,
                "text": line.text,
                "bbox": line.bbox,
            })

    def search(self, query: str, limit: int = 10, use_rerank: bool = False) -> list[SearchResult]:
        """Perform hybrid search across all indexes."""
        start = time.time()
        self.query_understander.detect_script(query)
        variants = self.query_understander.expand_for_ocr_noise(query)

        ranked_lists: list[list[tuple[str, float]]] = []

        # 1. BM25 words
        try:
            results = self._fts_search(query)
            ranked_lists.append([(r["line_id"], r["score"]) for r in results])
        except Exception as e:
            logger.warning("bm25_search_failed", error=str(e))

        # 2. Char n-grams
        for variant in variants:
            try:
                ngram_results = self._ngram_search(variant)
                ranked_lists.append([(r["line_id"], r["score"]) for r in ngram_results])
            except Exception as e:
                logger.warning("ngram_search_failed", error=str(e))

        # 3. Phonetic
        try:
            phonetic_results = self._phonetic_search(query)
            ranked_lists.append([(r["line_id"], r["score"]) for r in phonetic_results])
        except Exception as e:
            logger.warning("phonetic_search_failed", error=str(e))

        # 4. Dense embeddings
        try:
            dense_results = self._dense_search(query)
            if dense_results:
                ranked_lists.append(dense_results)
        except Exception as e:
            logger.warning("dense_search_failed", error=str(e))

        # RRF fuse
        if ranked_lists:
            fused = reciprocal_rank_fusion(ranked_lists, k=60)
            top_doc_ids = [doc_id for doc_id, _ in fused[:limit]]

            results = self._fetch_results(top_doc_ids)
        else:
            results = []

        elapsed_ms = (time.time() - start) * 1000
        logger.info(
            "hybrid_search_complete",
            query=query,
            num_results=len(results),
            elapsed_ms=round(elapsed_ms, 1),
        )
        return results

    def _fts_search(self, query: str, limit: int = 50) -> list[dict[str, Any]]:
        """BM25 FTS5 search."""
        if self.db is None:
            return []
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT l.id AS line_id, l.manuscript_id, l.text, fts.rank AS score
            FROM lines_fts fts
            JOIN lines l ON fts.line_id = l.id
            WHERE lines_fts MATCH ?
            ORDER BY rank LIMIT ?
        """, (query, limit))
        return [dict(row) for row in cursor.fetchall()]

    def _ngram_search(self, query: str, limit: int = 50) -> list[dict[str, Any]]:
        """Char n-gram FTS search."""
        if self.db is None:
            return []
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT l.id AS line_id, l.manuscript_id, l.text, fts.rank AS score
            FROM lines_ngram_fts fts
            JOIN lines l ON fts.line_id = l.id
            WHERE lines_ngram_fts MATCH ?
            ORDER BY rank LIMIT ?
        """, (query, limit))
        return [dict(row) for row in cursor.fetchall()]

    def _phonetic_search(self, query: str, limit: int = 50) -> list[dict[str, Any]]:
        """Phonetic FTS search."""
        if self.db is None:
            return []
        phonetic_q = self.phonetic_norm.normalize(query)
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT l.id AS line_id, l.manuscript_id, l.text, fts.rank AS score
            FROM lines_phonetic_fts fts
            JOIN lines l ON fts.line_id = l.id
            WHERE lines_phonetic_fts MATCH ?
            ORDER BY rank LIMIT ?
        """, (phonetic_q, limit))
        return [dict(row) for row in cursor.fetchall()]

    def _dense_search(self, query: str, limit: int = 50) -> list[tuple[str, float]]:
        """Dense FAISS search."""
        if self.faiss_index is None or self.faiss_index.ntotal == 0:
            return []
        qvec = self.embedder.embed([query]).astype(np.float32)
        _, idx = self.faiss_index.search(qvec, min(limit, self.faiss_index.ntotal))
        results = []
        for i in idx[0]:
            if i >= 0 and i < len(getattr(self, "_line_metadata", [])):
                meta = self._line_metadata[i]
                results.append((meta["line_id"], 1.0 - float(i) / self.faiss_index.ntotal))
        return results

    def _fetch_results(self, line_ids: list[str]) -> list[SearchResult]:
        """Fetch full results for line IDs."""
        if self.db is None or not line_ids:
            return []
        cursor = self.db.cursor()
        placeholders = ",".join("?" * len(line_ids))
        cursor.execute(f"""
            SELECT l.id AS line_id, l.manuscript_id, l.text,
                   l.bbox_x, l.bbox_y, l.bbox_width, l.bbox_height, l.confidence, l.script
            FROM lines l
            WHERE l.id IN ({placeholders})
        """, line_ids)
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append(SearchResult(
                manuscript_id=row["manuscript_id"],
                line_id=row["line_id"],
                text=row["text"],
                score=0.0,
                bbox=BoundingBox(
                    x=row["bbox_x"], y=row["bbox_y"],
                    width=row["bbox_width"], height=row["bbox_height"],
                ),
                metadata={"confidence": row["confidence"], "script": row["script"]},
            ))
        return results

    def close(self):
        """Close database connection."""
        if self.db:
            self.db.close()
            self.db = None
