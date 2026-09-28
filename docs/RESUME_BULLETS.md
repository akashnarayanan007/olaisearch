# Resume Bullets — OlaiSearch

> Use these for your resume. Pick 4–6 that match the roles you're applying for.

## For AI/ML Engineer Roles

- **Built a production-grade palm-leaf manuscript digitization pipeline** in Python/FastAPI processing images through 8 stages: restoration, projection-profile segmentation, script identification (CNN), multi-recognizer OCR ensemble with confidence calibration, lexicon post-correction, and entity extraction.
- **Designed a hybrid retrieval engine** combining SQLite FTS5 (BM25), character n-gram indexing, phonetic cross-script search, and FAISS dense embeddings, fused via Reciprocal Rank Fusion — improving recall on noisy OCR text by X% over BM25 alone.
- **Implemented grapheme-aware CER/WER metrics** using the `grapheme` Unicode library for Indic scripts (Tamil, Malayalam, Sanskrit), replacing naive code-point metrics that misrepresent Indic OCR quality by 2–3×.
- **Built a three-tier evidence chat system** with a citation verifier that strips ungrounded LLM claims, ensuring every factual statement maps to a verifiable manuscript line.

## For Data Scientist Roles

- **Created a synthetic degradation engine** that simulates 6 damage types (water stains, ink fade/bleed, holes, uneven lighting, camera blur, Perlin texture) on palm-leaf manuscripts for data augmentation and robustness testing.
- **Evaluated segmentation and OCR performance** across scripts and damage levels using PRF1 at IoU 0.5/0.7/0.9 and grapheme-aware CER/WER, documenting all results with honest "not yet measured" markers where data was absent.
- **Conducted ablation analysis** on retrieval modes (BM25 vs n-gram vs phonetic vs dense vs hybrid) using Recall@K, MRR, and nDCG@10.

## For Backend / Full-Stack Roles

- **Architected a multi-stage FastAPI pipeline** with async stages, tenacity-based retry with exponential backoff, SQLite response caching, and graceful fallback chains (VLM → Tesseract → template).
- **Built a React + Vite frontend** with a zoomable manuscript viewer (SVG bounding-box overlay), cross-lingual search, three-tier evidence chat, and an analytics dashboard tracking provider costs and archive statistics.
- **Designed a provider abstraction layer** (OmniRoute) supporting OpenAI-compatible APIs with cost tracking, token logging, and local fallback — enabling model swaps without backend changes.
- **Containerized the application** with multi-stage Docker builds (backend + nginx frontend) and a `docker-compose.yml` supporting API, Redis cache, and frontend services.

## For Research / Academic Engineering Roles

- **Implemented ISO 15919 transliteration** with rule-based Tamil/Malayalam/Devanagari→Roman mapping for cross-lingual search without requiring a translation model.
- **Designed a provenance detection heuristic** that identifies colophon and mangalacharana patterns in manuscript text to suggest authorship and dating.
- **Integrated date normalization** for Tamil, Saka, Kali, and Vikrama era dates, converting them to CE for consistent querying.
