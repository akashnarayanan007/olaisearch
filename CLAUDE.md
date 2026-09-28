# OlaiSearch - Development Guide

This document contains commands, conventions, and architecture notes for working on OlaiSearch.

## Quick Commands

```bash
# Development
make dev              # Start all services (API, frontend, Redis)
make test             # Run all tests
make lint             # Run ruff and black
make type-check       # Run mypy

# Data generation
python -m backend.ml.degradation generate --count 1000
python scripts/list_models.py    # Query available OmniRoute models

# Evaluation
make eval             # Run all evaluation scripts
python eval/scripts/eval_recognition.py
python eval/scripts/eval_retrieval.py
python eval/scripts/generate_report.py

# Training
python backend/ml/restoration/train.py --config config/restoration.yaml
python backend/ml/recognition/train.py --config config/recognition.yaml
```

## Project Structure

```
olaisearch/
├── backend/          # Python backend (FastAPI)
│   ├── api/         # API endpoints
│   ├── core/        # Core utilities (config, models, logging)
│   ├── providers/   # AI provider abstraction (OmniRoute, local)
│   ├── pipeline/    # Processing stages (restoration, OCR, etc.)
│   ├── retrieval/   # Search and indexing
│   ├── chat/        # ManuscriptChat Q&A
│   └── ml/          # ML models and training
├── frontend/         # React + Vite frontend
├── eval/            # Evaluation scripts and results
├── scripts/         # Utility scripts
├── tests/           # Test suite
├── config/          # Configuration files
└── docs/            # Documentation
```

## Conventions

### Code Style
- Python 3.11+ with type hints
- Line length: 100 characters
- Formatting: black + ruff
- All code must pass: `make lint && make type-check && make test`

### Git Commits
- Format: `"M{milestone}: {short description}"`
- Example: `"M1: Add provider abstraction layer with retry logic"`
- Commit after each completed milestone component

### Environment Variables
- Never commit `.env` file
- All secrets in `.env`, loaded via `pydantic-settings`
- Use `.env.example` as template

### Testing
- Unit tests for individual functions/classes
- Integration tests for pipelines
- Golden file tests for OCR/restoration outputs
- All metrics must be reproducible from eval scripts

### Evaluation
- ALWAYS separate synthetic and real results
- Never fabricate metrics
- Document limitations in `docs/RETRIEVAL_EVAL_LIMITATIONS.md`
- All CER/WER computed on Unicode grapheme clusters, not code points

### Models
- All model IDs in `config/models.yaml`
- Models must be swappable via config
- Local fallbacks for every OmniRoute model
- VLM confidence calibrated, never trusted raw

## Architecture Principles

1. **Provider Abstraction**: All AI calls go through `backend/providers/` with retry, cache, fallback
2. **Stage Interface**: Each pipeline stage implements `Stage.process(input) -> output`
3. **Grapheme Awareness**: All Indic text metrics use grapheme clusters via `grapheme` library
4. **Evidence Tiers**: Chat responses separate manuscript/archive/background evidence
5. **Local-First**: SQLite + FAISS for zero-setup deployment
6. **Uncertainty Exposure**: Show confidence scores, alternatives, and calibration

## Current Milestone: M1

**Goal**: Scaffolding + vertical slice (upload → Tesseract → SQLite FTS → search)

**Tasks**:
- [x] Project structure and config
- [ ] Provider abstraction layer
- [ ] Basic upload endpoint
- [ ] Tesseract integration
- [ ] SQLite FTS5 indexing
- [ ] Search endpoint
- [ ] Minimal frontend
- [ ] Docker compose setup
- [ ] Tests and CI

## Notes for Claude

- Always stop after each milestone for review
- Run tests before committing
- Never fabricate evaluation metrics
- Document design decisions in `docs/DECISIONS.md`
- Treat VLM confidence as weak signal, calibrate it
- All provenance patterns from real colophon examples
- MCP and multi-agent marked as OPTIONAL STRETCH in M10
