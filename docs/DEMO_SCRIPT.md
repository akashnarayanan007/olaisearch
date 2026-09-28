# Demo Script — OlaiSearch

> 3-minute demo for portfolio presentations.

---

## Opening (10 seconds)

*"Palm-leaf manuscripts are among the oldest written records in South Asia — but they're fragile, handwritten, and mostly undigitized. OlaiSearch is an end-to-end platform that ingests a manuscript image, digitizes the text, and makes it searchable and conversational."*

---

## Demo Flow

### 1. Upload & Pipeline (45 seconds)

**Action:** Drag-and-drop a manuscript image (or hit "Generate Demo Samples").

> "I'm uploading a palm-leaf manuscript image. The backend runs it through an 8-stage pipeline: quality check, optional restoration, projection-profile segmentation to detect text lines, script identification, Tesseract OCR with a VLM fallback, lexicon post-correction, and transliteration."

**Show:** The upload result card with line count and confidence scores.

> "Five lines detected with an average confidence of 0.87. The bounding boxes appear on the viewer."

### 2. Zoomable Viewer (20 seconds)

**Action:** Click and drag to pan, scroll to zoom. Click a line to see its bounding box highlighted.

> "The viewer is zoomable and draggable. Each detected line has a bounding box with confidence — low-confidence lines get a red indicator."

### 3. Hybrid Search (45 seconds)

**Action:** Type "kaliṅka" or a Tamil phrase in the search bar.

> "I'm searching with a Roman transliteration — 'kaliṅka'. Even though the manuscript is in Tamil script, the phonetic index finds it. The hybrid engine ranks results using Reciprocal Rank Fusion across four indexes: BM25, character n-grams, phonetic, and dense embeddings."

**Show:** Result cards with confidence scores and source IDs.

### 4. Manuscript Chat (45 seconds)

**Action:** Ask "What herbs are mentioned in this manuscript?"

> "The chat system answers with three tiers of evidence. The manuscript evidence shows the exact OCR text. Archive evidence shows related entries. Background knowledge is labeled separately as unverified. A citation verifier strips any claims that can't be traced to a real line."

### 5. Analytics Dashboard (20 seconds)

**Action:** Switch to the Analytics tab.

> "The analytics dashboard shows archive statistics, provider cost tracking, and system health — all real-time from the API."

---

## Closing (10 seconds)

*"Built with FastAPI, SQLite FTS5, FAISS, and a React frontend. Fully offline-capable with local Tesseract. Dockerized for easy deployment. Key innovation: the three-tier evidence system makes every claim auditable — critical for scholarly work."*

---

## Backup Answers

**Interviewer: "What was the hardest part?"**
> "Handling Indic script variability in OCR. Tesseract's Indic models are good but degrade fast on damaged manuscripts. The solution is the ensemble — Tesseract + VLM fallback + confidence calibration — and grapheme-aware metrics so our CER numbers actually reflect human judgment."

**Interviewer: "Would you add anything?"**
> "Active learning for the segmentation model — when a researcher corrects a line in the HITL UI, that correction gets added to a training set. And IIIF export so the digitized manuscripts can be published in academic digital libraries."
