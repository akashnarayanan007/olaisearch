# Known Issues

> This file tracks known limitations and outstanding bugs. Never hide issues.

---

## 🔴 Critical

- **No real manuscript data:** All eval metrics currently `not_measured`. Must be populated before any deployment.
- **Tesseract language packs:** Windows installation of Tamil/Malayalam/Sanskrit OCR packs is manual. See `docs/README.md` install notes.
- **OmniRoute API key required for VLM fallback:** Without `OMNIROUTE_API_KEY`, VLM recognition and chat fall back to templates — acceptable for demo but not for production.

---

## 🟡 High

- **FAISS index rebuild time:** Rebuilding dense index on >10k documents takes >5 seconds on CPU. Consider incremental FAISS updates.
- **UCanLoad library unavailable on Windows:** Synthetic degradation generator uses `ucanload` which has limited Windows support. Falls back to PIL, but some damage effects (Perlin noise) may be lower quality.
- **Provenance detection is heuristic-only:** The `ProvenanceDetector` uses regex patterns, not a trained model. Results are labeled as "heuristics" in output but may produce false positives.
- **Citation verifier strips unverifiable citations** but may also strip valid ones if the database schema changes.

---

## 🟢 Medium

- **Image upload size limit:** No enforced max file size in the current endpoint — large TIFFs may OOM. Add a size check.
- **No batch upload endpoint:** Only single-file upload. Batch processing is not implemented.
- **Segmenter struggles with curved leaves:** Projection-profile method assumes planar geometry. Curved palm-leaf lines may be split incorrectly.
- **Cross-lingual search only works for Devanagari→Roman phonetics:** Tamil/Malayalam transliteration rules are incomplete.
- **No persistence for conversation history:** Chat state is in-memory; page reload clears it.

---

## ℹ️ Notes

- All metrics in `docs/RESULTS.md` are `not_measured` until real eval data is generated.
- Docker setup is tested on Linux; Windows Docker Desktop may need extra PATH configuration for Tesseract.
- The `backend/main.py` has some unused imports from older refactors — these will be cleaned up in the next lint pass.
