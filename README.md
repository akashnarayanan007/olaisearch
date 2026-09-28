# OlaiSearch — Palm-Leaf Manuscript Digitization & Search Platform

Production-grade, multilingual palm-leaf manuscript digitization and search platform with hybrid retrieval, ensemble OCR, and a three-tier evidence chat system. Built for researchers working with Tamil, Malayalam, and Sanskrit manuscripts.

## What It Does

| Stage | What Happens | Tech |
|-------|-------------|------|
| **Upload** | Ingests a manuscript image (JPG/PNG/TIFF) | FastAPI multipart upload |
| **Restoration** | CLAHE, background flattening, Sauvola binarization | OpenCV + scikit-image |
| **Segmentation** | Detects text lines via projection profiles | NumPy + OpenCV connected components |
| **Script ID** | CNN classifies script (Tam/Mal/San/Eng) | PyTorch lightweight CNN |
| **Recognition** | Tesseract + VLM fallback, ROVER confidence voting | pytesseract + OmniRoute API |
| **Post-correction** | Lexicon-based correction, date normalization, entity extraction | Custom rules + LLM stub |
| **Indexing** | BM25 (FTS5) + char n-grams + phonetic + FAISS dense | SQLite FTS5 + FAISS |
| **Chat** | Three-tier evidence Q&A with citation verifier | OmniRoute LLM + verification |

## Supported Languages

Tamil (`tam`), Malayalam (`mal`), Sanskrit (`san`) — with Unicode-range heuristic fallback and extensible script registry.

## Architecture

```
Upload → Restoration → Segmentation → Script ID → Recognition Ensemble →
Post-Correction → Transliteration → Entity Extraction → Hybrid Indexing
                                                    ↓
                              Hybrid Retrieval (BM25 + n-gram + phonetic + dense) → RRF Fusion
                                                    ↓
                              ManuscriptChat (Three-Tier Evidence: MANUSCRIPT / ARCHIVE / BACKGROUND)
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full system diagram.

## Quick Start

```bash
# Clone and setup
git clone https://github.com/yourusername/olaisearch
cd olaisearch
cp .env.example .env
# Edit .env — set OMNIROUTE_API_KEY (optional; system works without it for local-only features)

# Install dependencies
pip install -e ".[dev]"

# Start the API server
python -m uvicorn backend.main:app --reload --port 8000

# Start the frontend (separate terminal)
cd frontend
npm install
npm run dev

# Access
# - API:       http://localhost:8000/docs
# - Frontend:  http://localhost:5173
```

### Docker

```bash
docker-compose up -d
# API:    http://localhost:8000
# Frontend: http://localhost:5173
```

## Project Structure

```
olaisearch/
├── backend/
│   ├── main.py              # FastAPI app + all endpoints
│   ├── core/                # Config, models, logging
│   ├── providers/           # OmniRoute provider abstraction
│   ├── pipeline/            # Restoration, segmentation, OCR, post-correction
│   ├── retrieval/           # Hybrid retriever (BM25 + n-gram + phonetic + dense)
│   ├── chat/                # ManuscriptChat + CitationVerifier
│   └── ml/                  # Degradation engine, restoration model
├── frontend/                # React + Vite + Tailwind
│   ├── src/pages/           # UploadPage, SearchPage, ChatPage, AnalyticsPage
│   ├── src/components/      # ManuscriptViewer, EvidenceCard
│   └── src/api/             # Axios client
├── tests/unit/              # pytest tests (all mock-based, no API key needed)
├── eval/scripts/            # Segmentation, recognition, retrieval eval
├── eval/results/            # Populated by eval scripts
├── docs/                    # Architecture, results, interview Q&A, demo script
└── config/models.yaml       # Model role mapping
```

## Evaluation Results

*All metrics are computed from scripts in `eval/scripts/`. No numbers are fabricated.*

| Metric | Status | Detail |
|--------|--------|--------|
| Segmentation PRF1 | **not_measured** | Requires `python -m backend.ml.degradation generate --count 1000` then `python eval/scripts/eval_segmentation.py` |
| Recognition CER/WER | **not_measured** | Requires synthetic test data |
| Retrieval Recall@K | **not_measured** | Requires `eval/corpus/queries.jsonl` |
| Cross-lingual coverage | **not_measured** | Depends on Tesseract Indic packs |

See [docs/RESULTS.md](docs/RESULTS.md) for the full results table and how to populate it.

## Milestone Status

| Milestone | Description | Status |
|-----------|-------------|--------|
| M0 | Project scaffolding, FastAPI, config, logging | ✅ |
| M1 | Vertical slice: upload → Tesseract → SQLite FTS → search | ✅ |
| M2 | Synthetic degradation engine | ✅ |
| M3 | Image restoration (classical CV) | ✅ |
| M4 | Text line segmentation (projection profile) | ✅ |
| M5 | Script identification + recognition ensemble | ✅ |
| M6 | Post-correction, transliteration, entity extraction | ✅ |
| M7 | Hybrid retrieval engine (BM25 + n-gram + phonetic + dense + RRF) | ✅ |
| M8 | ManuscriptChat with three-tier evidence + citation verifier | ✅ |
| M9 | Full API + React + Vite + Tailwind frontend | ✅ |
| M10 | HITL correction UI, uncertainty heatmap, exports, batch mode | 🔲 TODO |
| M11 | Docker, demo mode, docs, placement package | ✅ |

## Key Design Decisions

- **VLM confidence is a weak signal** — calibrated against actual errors before weighting in the ensemble
- **Three evidence tiers are code-enforced** — the `CitationVerifier` strips unverifiable claims at runtime
- **Grapheme-aware metrics** — CER/WER computed on Unicode grapheme clusters, not code points
- **Local-first fallbacks** — every API-dependent feature degrades gracefully without an API key
- **Never fabricate metrics** — `not_measured` is used where real data hasn't been collected

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — system diagram, pipeline stages, retrieval engine
- [Evaluation Results](docs/RESULTS.md) — metrics table (populated by eval scripts)
- [Known Issues](docs/KNOWN_ISSUES.md) — limitations and outstanding bugs
- [User TODOs](docs/TODO_USER.md) — tasks requiring real data or external setup
- [Interview Q&A](docs/INTERVIEW_QA.md) — prepared answers for placement interviews
- [Demo Script](docs/DEMO_SCRIPT.md) — 3-minute presentation script
- [Blog Post Draft](docs/BLOG_POST.md) — publishable article about the project
- [Resume Bullets](docs/RESUME_BULLETS.md) — role-specific resume entries
- [Design Decisions](docs/DECISIONS.md) — recorded rationale for key choices

## License

MIT — see [LICENSE](LICENSE)
