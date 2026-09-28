# Blog Post Draft — OlaiSearch

> Target: personal tech blog or Medium article. ~1200 words.

---

## Title: OlaiSearch — An Open-Source Pipeline for Palm-Leaf Manuscript Digitization

## Subtitle:
How hybrid retrieval, grapheme-aware OCR, and three-tier evidence make ancient texts searchable.

---

## The Problem

South Asia holds centuries of knowledge in palm-leaf manuscripts — Siddha medicine, temple records, Tamil Sangam literature, Sanskrit commentaries. These documents are deteriorating. Only a fraction have been digitized, and those that have are locked behind institutional portals without search or transcription.

For a researcher, finding a specific herb mentioned across a collection of 10,000 manuscripts means manually browsing each leaf. For a linguist, studying script evolution requires character-level accuracy that generic OCR can't provide.

I built OlaiSearch as a full-stack prototype to bridge this gap — a production-grade pipeline from image upload to conversational query, built entirely on open-source tooling.

## The Pipeline

An uploaded manuscript image flows through eight stages:

1. **Quality check** — blur detection and contrast assessment
2. **Restoration** — classical image processing (CLAHE, background flattening, Sauvola binarization); U-Net restoration is stubbed for future training
3. **Segmentation** — projection profile analysis finds text bands; connected components refine boundaries
4. **Script identification** — a lightweight CNN classifies the script (Tamil, Malayalam, Sanskrit, etc.), falling back to Unicode-range heuristics
5. **Recognition ensemble** — Tesseract runs with script-specific configs; an optional VLM fallback handles severely degraded text; ROVER-style confidence voting combines results
6. **Post-correction** — lexicon-based correction using domain dictionaries (Siddha/Ayurvedic terms)
7. **Transliteration** — ISO 15919-compliant Roman mapping for cross-lingual search
8. **Entity extraction** — LLM-based extraction of people, places, dates, herbs, and deities

Each stage is async, typed with Pydantic v2, and logged with structlog.

## Why Hybrid Retrieval?

A single search algorithm misses too much. Palm-leaf OCR produces errors: a `ங்` (vel + anusvara cluster) might be read as `ங`, a Tamil `ழ` as `ழ்`, diacritics drop off in damaged sections.

Four parallel indexes, each robust to a different failure mode:

- **BM25 (SQLite FTS5)** catches exact word matches
- **Character n-grams (2–5)** tolerate single-character substitutions
- **Phonetic index** maps Roman queries to Indic text (typing "kali" finds "கலி")
- **Dense embeddings (FAISS)** capture semantic similarity

Results from all four are fused by **Reciprocal Rank Fusion** (k=60), a proven method that's parameter-free and works well when you don't have labeled relevance data for training a learning-to-rank model.

## The Three-Tier Evidence System

The hardest problem in AI-assisted research is hallucination. An LLM might confidently state a fact that isn't in the manuscript. OlaiSearch solves this with a strict evidence architecture:

**Tier 1 — MANUSCRIPT**: An exact text span from the manuscript itself, verified by the `CitationVerifier` against the indexed lines. This is the ground truth.

**Tier 2 — ARCHIVE**: Cross-references to other indexed manuscripts or a knowledge base. Corroborated but indirect.

**Tier 3 — BACKGROUND**: General knowledge (historical context, linguistic notes). Always labeled as *unverified* and never mixed with Tier 1 claims.

The citation verifier parses `{manuscript_id, line_id, tier}` JSON citations from the LLM response and strips any that can't be verified. No more "I think this manuscript says..." — every claim is traceable.

## Grapheme-Aware Metrics

Standard CER (character error rate) counts Unicode code points. In Tamil, `கலிங்` is 6 code points but 4 grapheme clusters (the final `ங்` is one visual unit: vel + halant). If the OCR outputs `கலிங்` vs `கலிங்க`, a code-point-based metric reports 2 errors; a grapheme-based metric reports 1.

I use the `grapheme` library to split text into Unicode grapheme clusters before computing edit distance. This gives CER numbers that match how humans actually evaluate Indic OCR quality.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.11, FastAPI, Pydantic v2 |
| Search | SQLite FTS5 + FAISS + custom phonetic index |
| OCR | Tesseract (Tam/Mal/San/Eng packs) |
| Embeddings | sentence-transformers (local fallback) |
| Frontend | React 18, Vite, Tailwind CSS |
| AI API | OmniRoute (OpenAI-compatible, multi-provider) |
| Docker | Multi-stage build, nginx |

All external API calls go through a provider abstraction with retry, caching, and fallback. No hardcoded keys. Everything runs offline once the indexes are built.

## What's Next

The immediate priorities are real data and HITL correction:
- Obtain scanned images from the Oriental Research Institute
- Annotate 50 test manuscripts for segmentation and recognition evaluation
- Build the correction UI where researchers click a low-confidence line and type the right text
- Export to PAGE-XML and IIIF for academic publishing workflows

The platform is production-ready for the pipeline and search components. The remaining work is collecting the data that makes the numbers real.

---

*Repository: github.com/akash/olaisearch*
