# Results & Evaluation Metrics

> **⚠ Important**: All metrics in this document are computed from actual eval scripts (`eval/scripts/`). No numbers are fabricated. Entries marked `not_measured` await real data.

---

## Synthetic Evaluation Results

### Segmentation (Projection Profile)

Run: `python eval/scripts/eval_segmentation.py`

| Script | # Samples | Precision@0.5 | Recall@0.5 | F1@0.5 | Precision@0.7 | Recall@0.7 | F1@0.7 |
|--------|-----------|--------------|-----------|--------|--------------|-----------|--------|
| tam    | n/a       | —            | —         | —      | —            | —         | —      |
| san    | n/a       | —            | —         | —      | —            | —         | —      |
| mal    | n/a       | —            | —         | —      | —            | —         | —      |

**Limitations:**
- Synthetic test data not yet generated (`python -m backend.ml.degradation generate --count 1000`)
- No human-annotated ground truth for real manuscripts available

---

### Recognition (CER/WER)

Run: `python eval/scripts/eval_recognition.py`

| Script | Damage Level | CER | WER | # Samples |
|--------|-------------|-----|-----|-----------|
| tam    | low         | not_measured | not_measured | 0 |
| tam    | medium      | not_measured | not_measured | 0 |
| tam    | high        | not_measured | not_measured | 0 |
| san    | low         | not_measured | not_measured | 0 |
| san    | medium      | not_measured | not_measured | 0 |
| san    | high        | not_measured | not_measured | 0 |
| mal    | low         | not_measured | not_measured | 0 |
| mal    | medium      | not_measured | not_measured | 0 |
| mal    | high        | not_measured | not_measured | 0 |

**Method:** Grapheme-aware CER/WER using `grapheme` library, with NFC/ZWJ normalization. Tesseract `tam`/`mal`/`san` langs.

---

### Retrieval

Run: `python eval/scripts/eval_retrieval.py`

| Mode | Recall@1 | Recall@5 | Recall@10 | MRR | nDCG@10 |
|------|----------|----------|-----------|-----|---------|
| BM25 only | not_measured | not_measured | not_measured | not_measured | not_measured |
| Char n-gram | not_measured | not_measured | not_measured | not_measured | not_measured |
| Phonetic | not_measured | not_measured | not_measured | not_measured | not_measured |
| Dense (FAISS) | not_measured | not_measured | not_measured | not_measured | not_measured |
| **Hybrid (RRF)** | not_measured | not_measured | not_measured | not_measured | not_measured |
| Cross-lingual coverage | not_measured | — | — | — | — |

**Limitations:**
- Requires a real corpus at `eval/corpus/queries.jsonl`
- Query set not yet prepared; all entries are `not_measured`
- Cross-lingual tests depend on Tesseract language packs

---

### Chat / Citation Verification

No automated metrics yet. Manual evaluation needed for:
- Citation resolution rate (should be 100% for valid citations)
- Tier separation compliance (MANUSCRIPT vs ARCHIVE vs BACKGROUND)
- Factual grounding score

---

## How to Get Real Numbers

```bash
# 1. Generate synthetic test data
python -m backend.ml.degradation generate --count 1000 --level medium

# 2. Run segmentation eval
python eval/scripts/eval_segmentation.py

# 3. Run recognition eval
python eval/scripts/eval_recognition.py

# 4. Prepare a real corpus (see docs/DATA_LICENSES.md) and run retrieval eval
python eval/scripts/eval_retrieval.py

# 5. Update this file with actual results
```
