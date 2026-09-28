# Interview Q&A — OlaiSearch

> Prepare these answers. The project demonstrates expertise across NLP, IR, and full-stack engineering.

---

## Architecture Questions

**Q: Walk me through the system.**
A: "OlaiSearch digitizes palm-leaf manuscripts through an 8-stage pipeline: quality check, restoration, segmentation, script identification, OCR ensemble, post-correction, transliteration, and entity extraction. Results are indexed into a hybrid retrieval engine (BM25 + char n-gram + phonetic + dense FAISS) and made searchable through a React frontend with a three-tier evidence chat system."

**Q: Why hybrid retrieval instead of pure BM25 or pure embeddings?**
A: "Palm-leaf OCR produces noise: character substitutions, missing diacritics, and variant spellings. Pure BM25 fails on misspelled queries; pure dense retrieval lacks exact match guarantees. Four indexes cover different failure modes — BM25 for exact words, char n-gram for typo tolerance, phonetic for cross-script queries, and dense for semantic similarity — fused by RRF which is robust to individual index noise."

**Q: Why RRF instead of learning-to-rank?**
A: "RRF is parameter-free and theoretically optimal for small result sets. With <100k documents, learning-to-rank would require expensive feature engineering and labeled relevance data we don't have. RRF's k=60 constant is the proven sweet spot. A learned reranker is on the roadmap but not the right tradeoff today."

---

## NLP / OCR Questions

**Q: How do you handle Indic script variability in OCR?**
A: "Three strategies: (1) Language-specific Tesseract configs (`tam`, `mal`, `san`), (2) a VLM fallback for degraded text where Tesseract fails, and (3) ROVER-style confidence-weighted voting across recognizers. The VLM confidence is treated as a weak signal — it's calibrated against actual error rates before being weighted heavily in the ensemble."

**Q: What is grapheme-aware CER and why does it matter for Indic scripts?**
A: "Naive character error rate counts Unicode code points. In Indic scripts, a single visual character (e.g. `கலிங்`) may be 3–4 code points due to combining marks. Using the `grapheme` library we split text into Unicode grapheme clusters first, so substituting `ங்` (one cluster) with `ங` (one cluster) costs 1 error, not 3. This matches how humans actually judge OCR quality."

**Q: How do you handle ZWJ sequences like emoji family? What about NFC/NFD?**
A: "All input text is NFC-normalized before grapheme splitting. ZWJ sequences (e.g. 👨‍👩‍👦) are preserved as single clusters — we don't split on ZWJ. For Indic scripts this matters less but it ensures the pipeline is robust to any Unicode input."

---

## Retrieval / IR Questions

**Q: How does cross-lingual search work in this system?**
A: "The `PhoneticNormalizer` maps Tamil/Malayalam/Devanagari characters to their Roman phonetic equivalents (e.g. `கலிங்` → `kaliṅk`). A query typed in Roman is normalized and searched against the phonetic FTS5 index. This means a user typing 'kali' can find the Tamil manuscript line 'கலிங்' without needing a translation model."

**Q: What is the citation verifier and why is it important?**
A: "LLMs are prone to hallucination. Every factual claim in a chat response must map to a verifiable citation in the format `{manuscript_id, line_id, tier}`. The `CitationVerifier` parses these JSON citations from the response, checks each against the database, and strips any unverifiable ones. This makes the system auditable — a user can click a citation and see exactly where the text came from."

---

## Engineering Questions

**Q: How do you handle missing API keys for the VLM fallback?**
A: "All external API calls go through the `OmniRouteProvider` which has a tenacity retry with exponential backoff. If the API key is missing, VLM and LLM-dependent features fall back to template responses. Tesseract runs locally with no key needed. The system never crashes on a missing key — it degrades gracefully."

**Q: How would you scale this to millions of documents?**
A: "The current SQLite + FAISS architecture handles ~100k documents well. At scale: (1) SQLite FTS5 migrates to Elasticsearch/OpenSearch, (2) FAISS index gets sharded by script/language, (3) the recognition pipeline becomes a batch job with Celery/RQ workers, (4) Redis replaces SQLite for caching hot results. The hybrid query interface stays the same — only the backends change."

---

## Business / Product Questions

**Q: Who is the target user?**
A: "Researchers and archivists at institutions like the Grantha Library in Madurai or the Oriental Research Institute in Thiruvananthapuram. They need digitized, searchable copies of palm-leaf manuscripts for scholarly work. The three-tier evidence system directly addresses their need for auditability — they can't publish claims they can't trace to the original leaf."

**Q: What's your differentiator vs. a generic search engine?**
A: "Three things: (1) Domain-specific preprocessing — degradation simulation for synthetic training, projection-profile segmentation tuned for curved palm leaves, (2) Indic script handling — grapheme-aware metrics, phonetic cross-lingual search, (3) Evidence-tier architecture — every claim is tied to a specific manuscript line, not just returned as raw text."
