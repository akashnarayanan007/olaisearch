# TODO / User Tasks

> This file tracks tasks that require user action (data, approvals, external setup). Completed items are checked off.

---

## Data & Datasets

- [ ] **Obtain real palm-leaf manuscript images** — sources:
  - [ ] Oriental Research Institute, Thiruvananthapuram (public domain images available on request)
  - [ ] Grantha Library, Madurai (contact via ORIF)
  - [ ] Sarada Sangamaya Library, Mysore (open-access collections)
  - [ ] Internet Archive Tamil manuscripts (search `palm leaf` in collections)
- [ ] **Create eval corpus** — `eval/corpus/queries.jsonl` with human-written queries and relevance judgments
- [ ] **Annotate a small test set** — 20–50 images with ground-truth bounding boxes for segmentation eval
- [ ] **License verification** — ensure all images used in eval comply with their source license (see `docs/DATA_LICENSES.md`)

---

## Infrastructure Setup

- [ ] **Install Tesseract with Indic packs** on Windows:
  ```powershell
  # Download Tesseract OCR with Tam/Mal/San langs from UB Mannheim releases
  # Set TESSDATA_PREFIX environment variable
  $env:TESSDATA_PREFIX = "C:\Program Files\Tesseract-OCR\tessdata"
  ```
- [ ] **Set up Redis** for caching (or remove the Redis dependency and use SQLite only)
- [ ] **Configure MLFlow** for experiment tracking (optional)
- [ ] **Set up GitHub Actions CI** — add `workflow/olaisearch.yml` with lint/test/run-eval jobs
- [ ] **Add SSL / HTTPS** for production deployment (nginx reverse proxy with certbot)

---

## Evaluation Completion

- [ ] **Generate synthetic data** and run all eval scripts:
  ```bash
  python -m backend.ml.degradation generate --count 1000
  python eval/scripts/eval_segmentation.py
  python eval/scripts/eval_recognition.py
  python eval/scripts/eval_retrieval.py
  ```
- [ ] **Update `docs/RESULTS.md`** with actual numbers from the above
- [ ] **Add real-metrics comparison table** to README (synthetic vs expected baseline)
- [ ] **Document the gap** between synthetic and real performance explicitly

---

## Stretch Features (M10)

- [ ] **HITL correction UI** — allow users to click a line and edit OCR output
- [ ] **Uncertainty heatmap** — visualize low-confidence characters on the viewer
- [ ] **PAGE-XML / ALTO-XML export** — standard academic manuscript representation
- [ ] **TEI-XML export** — for scholarly publication workflows
- [ ] **IIIF manifest generation** — for interoperability with IIIF viewers
- [ ] **Batch upload mode** — drag-and-drop multiple files, queued processing

---

## Deployment

- [ ] **Deploy to a cloud VM** (AWS EC2 / Google Cloud / Railway)
- [ ] **Set up a demo video script** (see `docs/DEMO_SCRIPT.md` — TODO)
- [ ] **Write the blog post** — see `docs/BLOG_POST.md` draft
- [ ] **Prepare the interview Q&A sheet** — see `docs/INTERVIEW_QA.md`
