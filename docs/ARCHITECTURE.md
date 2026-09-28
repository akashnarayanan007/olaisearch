# Architecture

OlaiSearch is a multi-stage processing pipeline backed by a hybrid retrieval engine and a three-tier evidence chat system.

---

## System Diagram

```
┌─────────────┐     ┌─────────────────────────────────────────────────────┐
│  Frontend    │────▶│                   FastAPI (backend/main.py)         │
│  React+Vite  │◀────│                   :8000                             │
└─────────────┘     └──────────┬──────────────────────────────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
   ┌──────────────┐   ┌────────────────┐   ┌──────────────────┐
   │   Pipeline    │   │  HybridRetriev-│   │   ManuscriptChat  │
   │  (stages A-H) │   │  er            │   │   (three tiers)   │
   └──────┬───────┘   └───────┬────────┘   └────────┬─────────┘
          │                   │                      │
          ▼                   ▼                      ▼
   ┌──────────────┐   ┌────────────────┐   ┌──────────────────┐
   │  SQLite FTS5 │   │  SQLite +      │   │  OmniRoute API    │
   │  BM25 index  │   │  FAISS dense   │   │  (VLM / LLM)      │
   │  (words)     │   │  (embeddings)  │   │  + fallback stub  │
   └──────────────┘   └────────────────┘   └──────────────────┘
          │
   ┌──────────────┐
   │  Char n-gram │
   │  FTS5 index  │
   └──────────────┘
   ┌──────────────┐
   │  Phonetic    │
   │  FTS5 index  │
   └──────────────┘
```

---

## Pipeline Stages (A–H)

| Stage | Class | Module | Status |
|-------|-------|--------|--------|
| A. Quality check | `_quality_check()` | `main.py` | ✅ Baseline |
| B. Restoration | `ClassicalRestoration` | `pipeline/restoration.py` | ✅ Partial (U-Net stub) |
| C. Segmentation | `ProjectionProfileSegmenter` | `pipeline/segmentation.py` | ✅ Working |
| D. Script ID | `ScriptIdentifier` | `pipeline/script_id.py` | ✅ CNN + heuristic |
| E. Recognition | `RecognitionEnsemble` | `pipeline/recognition.py` | ✅ Tesseract + VLM stub |
| F. Post-correction | `LexiconCorrector` | `pipeline/postcorrection.py` | ✅ Partial |
| G. Transliterate/Translate | `Transliterator`, `Translator` | `pipeline/postcorrection.py` | ✅ Tamil rule-based |
| H. Entity extraction | `EntityExtractor` | `pipeline/postcorrection.py` | ✅ LLM-stub |

---

## Retrieval Engine

Four parallel indexes, fused by **Reciprocal Rank Fusion** (k=60):

1. **BM25 (FTS5)** — word-level tokenization via SQLite FTS5
2. **Char n-gram (FTS5)** — 2- to 5-char overlapping n-grams for typo tolerance
3. **Phonetic (FTS5)** — Roman transliteration of Tamil/Malayalam/Devanagari queries
4. **Dense (FAISS)** — multilingual sentence-transformers embeddings

A 5th **reranker** index is planned (cross-encoder) but not yet implemented.

### Index Schema

```sql
CREATE VIRTUAL TABLE documents_fts USING fts5(
    text, content='documents', content_rowid='rowid'
);

CREATE TABLE documents (
    doc_id TEXT PRIMARY KEY,
    script TEXT,
    language TEXT,
    full_text TEXT
);

CREATE TABLE ocr_alternatives (
    id INTEGER PRIMARY KEY,
    doc_id TEXT,
    text TEXT,
    confidence REAL
);

CREATE TABLE embeddings (
    doc_id TEXT,
    vector BLOB,
    PRIMARY KEY (doc_id)
);
```

---

## Evidence Tiers (Chat)

Every answer must separate evidence into three non-mixed tiers:

| Tier | Source | Trust |
|------|--------|-------|
| **MANUSCRIPT** | Exact text span from the manuscript image (OCR + correction) | Highest — ground truth |
| **ARCHIVE** | Cross-references to other indexed manuscripts or external knowledge base | Medium — corroborated but indirect |
| **BACKGROUND** | General knowledge (history, linguistics, Siddha medicine) | Lowest — unverified, labeled explicitly |

The `CitationVerifier` class extracts `{manuscript_id, line_id, ...}` citation strings from LLM output and validates them against the database. Unverified citations are stripped from the response.

---

## Provider Abstraction

All AI model calls go through `backend/providers/` with:

- **Retry**: exponential backoff (up to 3 attempts) via `tenacity`
- **Fallback chain**: VLM → Tesseract → SentenceTransformers stub
- **SQLite caching**: SHA-256 keyed cache of `(model, prompt, args) → response`
- **Token/cost tracking**: per-request cost logged to `structlog`

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, async/await, Pydantic v2 |
| Search | SQLite FTS5 (BM25) + FAISS (dense) + CharNGram |
| ML | PyTorch (U-Net stub), sentence-transformers, Tesseract OCR |
| AI API | OmniRoute (OpenAI-compatible, multi-provider) |
| Frontend | React 18, Vite, Tailwind CSS, Axios |
| Docker | multi-stage build, nginx reverse proxy |
| Testing | pytest, unittest.mock, no external service deps |
| Linting | ruff, black, mypy, pre-commit |
