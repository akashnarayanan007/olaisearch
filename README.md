# OlaiSearch - Palm-Leaf Manuscript Digitization Platform

Production-grade, multilingual palm-leaf manuscript digitization and search platform with hybrid retrieval, ensemble OCR, and conversational Q&A.

## Features

- 🔍 **Hybrid Search**: BM25 + character n-grams + dense embeddings + cross-lingual retrieval
- 🤖 **Ensemble OCR**: Tesseract + CRNN + VLM with confidence-weighted ROVER voting
- 🎨 **Image Restoration**: Classical CV + learned U-Net denoising
- 💬 **ManuscriptChat**: RAG-based Q&A with visual citations and three evidence tiers
- 🔬 **Synthetic Data**: Unlimited training data via physically-motivated degradation engine
- 📊 **Comprehensive Evaluation**: All metrics reproducible from scripts, separate synthetic/real results

## Supported Languages

Tamil, Malayalam, Sanskrit (Devanagari), with extensible architecture for additional Indic scripts.

## Architecture

```
Upload → Restoration → Segmentation → Script ID → Recognition Ensemble → 
Post-Correction → Translation → Indexing → Hybrid Retrieval → ManuscriptChat
```

## Quick Start

```bash
# Clone and setup
git clone <repo-url>
cd olaisearch
cp .env.example .env
# Edit .env with your OMNIROUTE_API_KEY

# Install dependencies
pip install -e ".[dev]"

# Start services
make dev

# Access
# - API: http://localhost:8000
# - Frontend: http://localhost:3000
# - API Docs: http://localhost:8000/docs
```

## Development Status

**Current Milestone**: M1 - Scaffolding & Vertical Slice ✅ IN PROGRESS

See [CLAUDE.md](CLAUDE.md) for development commands and conventions.

## Evaluation Results

*Results will be generated from `eval/scripts/` and populated here.*

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Evaluation Results](docs/RESULTS.md)
- [Design Decisions](docs/DECISIONS.md)
- [API Documentation](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

## License

MIT License - see [LICENSE](LICENSE)

## Citation

```bibtex
@software{olaisearch2024,
  title={OlaiSearch: Palm-Leaf Manuscript Digitization Platform},
  author={Akash},
  year={2024},
  url={https://github.com/yourusername/olaisearch}
}
```
