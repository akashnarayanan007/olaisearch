# M1: Scaffolding & End-to-End Vertical Slice

## Overview
This milestone establishes the project foundation and delivers a working demo from day 1.

## Decision Log

### 2024-09-28: Provider Abstraction with Retry Logic
**Decision**: All AI provider calls go through an abstract `Provider` interface with retry logic.

**Rationale**:
- Single point of failure mitigation via fallback chain
- Consistent error handling across all AI calls
- Easy to swap providers (OmniRoute → OpenAI → Local)
- Built-in cost/latency tracking

**Implementation**:
- `backend/providers/base.py`: Abstract interface
- `backend/providers/omniroute.py`: OmniRoute implementation with tenacity retry
- Exponential backoff: 1s → 2s → 4s → ... up to 60s max
- 3 retry attempts before raising ProviderException

**Trade-offs**:
- Pro: Resilient to transient failures
- Pro: Uniform interface for all models
- Con: Adds latency on failures (acceptable for robustness)

---

### 2024-09-28: SQLite + FTS5 for Local-First Search
**Decision**: Use SQLite with FTS5 virtual table for full-text search, not Elasticsearch.

**Rationale**:
- Zero setup: works out of the box, no server needed
- BM25 ranking built-in via FTS5
- Sufficient for initial scale (thousands of manuscripts)
- Can migrate to Elasticsearch/OpenSearch later if needed

**Implementation**:
- `backend/storage/database.py`: SQLite wrapper
- FTS5 tokenizer: unicode61 (handles Indic scripts)
- Tables: `manuscripts`, `lines`, `lines_fts` (virtual)

**Trade-offs**:
- Pro: Instant setup, zero dependencies
- Pro: Portable (single file database)
- Con: Single-machine only (acceptable for local deployment)
- Con: No distributed features (not needed for M1)

**Future**: If we need distributed search, abstract the interface and swap in Elasticsearch.

---

### 2024-09-28: Vertical Slice First
**Decision**: M1 delivers upload → Tesseract → SQLite FTS → search before any learned models.

**Rationale**:
- Always have a working demo
- Prove the end-to-end flow early
- Tesseract provides a baseline to compare learned models against
- Reduces risk: if learned models take longer, we still have something

**Implementation**:
- FastAPI endpoints: `/api/v1/upload`, `/api/v1/search`
- Tesseract with Tamil/Malayalam/Sanskrit language packs
- Simple indexing: whole page as one line (segmentation in M4)
- BM25 search via FTS5

**Trade-offs**:
- Pro: De-risks the project timeline
- Pro: Demo exists from day 3
- Con: Initial OCR quality will be lower (acceptable, will improve)

---

### 2024-09-28: Structured Logging with structlog
**Decision**: Use structlog for structured, machine-readable logs.

**Rationale**:
- Easier debugging with key-value context
- Can switch to JSON logs in production
- Consistent log format across all modules
- Better for monitoring/alerting

**Example**:
```python
logger.info("manuscript_indexed", manuscript_id=id, num_lines=10)
```

**Trade-offs**:
- Pro: Much better than string interpolation
- Pro: Queryable logs
- Con: Slight learning curve (minimal)

---

### 2024-09-28: Type Hints Everywhere
**Decision**: Strict type hints on all functions, enforced by mypy.

**Rationale**:
- Catches bugs at dev time, not runtime
- Better IDE autocomplete
- Self-documenting code
- Expected in production Python code

**Configuration**: `pyproject.toml` has mypy settings

**Trade-offs**:
- Pro: Prevents entire classes of bugs
- Pro: Makes refactoring safer
- Con: Slightly more verbose (worth it)

---

## Next Decisions (Future Milestones)

- M2: Choice of handwriting-style fonts for synthetic data
- M3: U-Net architecture for restoration
- M4: Projection profile vs Kraken segmenter
- M5: ROVER voting strategy and VLM confidence calibration
- M7: Dense embedding model (BGE-M3 vs multilingual-e5-large)
