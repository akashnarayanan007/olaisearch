# Real Palm-Leaf Manuscript Test Set - Collection & Labeling Guide

## Purpose

This guide explains how to collect and label 30-50 **real palm-leaf manuscript images** for evaluation. These will be used to measure how well our OCR and retrieval systems work on actual historical manuscripts (not just synthetic data).

**Why this matters**: Synthetic data helps us train models, but real manuscripts have damage patterns, handwriting variations, and script peculiarities we can't fully simulate. Testing on real data shows the true performance gap.

---

## Target: 30-50 Images

### Breakdown by Language
- **Tamil**: 15-20 images
- **Malayalam**: 10-15 images  
- **Sanskrit (Devanagari/Grantha)**: 5-10 images

### Breakdown by Condition
- **Clean/Light damage**: 10-15 images (good lighting, minimal damage)
- **Medium damage**: 15-20 images (some stains, fading, readable)
- **Heavy damage**: 5-10 images (significant damage, holes, very faded)

---

## Where to Find Palm-Leaf Images

### Option 1: Public Datasets (Recommended)
Download from these sources (check availability and licenses):

1. **ICFHR Palm Leaf Dataset** (if available)
   - Historical document competition datasets
   - Usually pre-segmented with some labels

2. **Digital Libraries**
   - Tamil Digital Library: [http://www.tamildigitallibrary.in/](http://www.tamildigitallibrary.in/)
   - Govt. Oriental Manuscripts Library
   - Archive.org (search: "palm leaf manuscript")

3. **Research Papers**
   - Many OCR papers include sample images
   - Check supplementary materials

### Option 2: Photograph Your Own
If you have access to physical manuscripts (museum, library, family collection):
- Use good lighting (diffuse, not direct)
- Take photos perpendicular to the leaf
- Capture full leaf in frame
- Take multiple angles if heavily damaged
- **Note**: Get permission before photographing!

### Option 3: Use Our Collection Script
We'll provide a script that downloads from public sources with proper attribution.

---

## What to Label for Each Image

For each image, create a JSON file with this structure:

```json
{
  "image_path": "real_test_set/tam_001.jpg",
  "language": "Tamil",
  "script": "Tamil",
  "quality": "medium",
  "damage_notes": "Water stains in upper left, slight fading",
  "lines": [
    {
      "line_id": "tam_001_line_0",
      "text": "தமிழ் கையெழுத்து உரை",
      "bbox": {
        "x": 120,
        "y": 80,
        "width": 850,
        "height": 65
      },
      "confidence_notes": "Clear, high confidence expected"
    },
    {
      "line_id": "tam_001_line_1",
      "text": "பழைய இலக்கியம் பற்றி",
      "bbox": {
        "x": 125,
        "y": 160,
        "width": 820,
        "height": 62
      },
      "confidence_notes": "Slightly faded but readable"
    }
  ],
  "metadata": {
    "source": "Tamil Digital Library",
    "date_collected": "2024-09-28",
    "labeler": "your_name",
    "notes": "Historical text about Tamil literature"
  }
}
```

---

## Labeling Process (Step by Step)

### Step 1: Organize Your Images
```
eval/data/real_test_set/
├── images/
│   ├── tam_001.jpg
│   ├── tam_002.jpg
│   ├── mal_001.jpg
│   └── ...
└── labels/
    ├── tam_001.json
    ├── tam_002.json
    ├── mal_001.json
    └── ...
```

### Step 2: Open Image in Viewer
Use any image viewer or our provided labeling tool.

### Step 3: Transcribe the Text
**IMPORTANT**: Transcribe exactly what you see, in the original script.

- **Use Unicode**: Tamil, Malayalam, Devanagari Unicode characters
- **Preserve line breaks**: Each physical line = one entry
- **Mark unreadable**: Use `[?]` for completely illegible characters
- **Note uncertainty**: If unsure about a character, add to `confidence_notes`

**Tools to help**:
- Google Input Tools: [https://www.google.com/inputtools/try/](https://www.google.com/inputtools/try/)
- Tamil Virtual Keyboard
- Malayalam Virtual Keyboard

### Step 4: Draw Bounding Boxes
Use one of these tools:

**Option A: LabelImg (Recommended)**
```bash
pip install labelImg
labelImg eval/data/real_test_set/images
```
- Draw rectangle around each line
- Save coordinates to XML
- We'll convert to our JSON format

**Option B: Our Labeling Script**
```bash
python scripts/label_manuscript.py eval/data/real_test_set/images/tam_001.jpg
```
- Click corners of each line
- Type the text
- Auto-saves JSON

**Option C: Manual** (if small dataset)
- Open image in GIMP/Photoshop
- Use ruler/info tool to get pixel coordinates
- Write JSON manually

### Step 5: Quality Check
For each label, verify:
- [ ] Text is in correct Unicode (not romanized)
- [ ] Bounding boxes don't overlap
- [ ] All readable lines are labeled
- [ ] Unreadable regions marked with `[?]`
- [ ] Quality and damage notes are accurate

---

## Detailed Field Descriptions

### Image-Level Fields

**`language`**: The language of the text
- Options: "Tamil", "Malayalam", "Sanskrit", "Kannada", etc.

**`script`**: The script used (can differ from language)
- Examples: "Tamil", "Grantha" (for Sanskrit in Tamil script), "Devanagari"

**`quality`**: Overall image quality
- "clean": Good lighting, minimal damage, sharp
- "medium": Some damage, readable
- "heavy": Significant damage, many illegible regions

**`damage_notes`**: Free-form description of damage
- Examples: "Water stains upper left", "Insect holes line 3-4", "Severe fading"

### Line-Level Fields

**`text`**: Exact transcription in Unicode
- Preserve original spelling/grammar
- Use `[?]` for unreadable characters
- Use `[...]` for missing regions (holes, tears)

**`bbox`**: Bounding box in pixels
- `x`: Left edge (pixels from image left)
- `y`: Top edge (pixels from image top)
- `width`: Box width
- `height`: Box height
- **Tip**: Box should tightly fit the text, with small margins

**`confidence_notes`**: Your assessment
- "Clear, high confidence" - Easily readable
- "Faded but readable" - Requires careful examination
- "Partially illegible" - Some characters marked [?]
- "Uncertain transcription" - You're not 100% sure

---

## Labeling Script

We provide `scripts/label_manuscript.py` to make this easier:

```python
# Usage
python scripts/label_manuscript.py \
    --image eval/data/real_test_set/images/tam_001.jpg \
    --output eval/data/real_test_set/labels/tam_001.json \
    --language Tamil
```

**Features**:
- Interactive: Click to draw boxes, type text
- Auto-saves progress
- Validates Unicode
- Shows real-time preview

---

## Validation

After labeling, run our validator:

```bash
python scripts/validate_labels.py eval/data/real_test_set/labels/
```

**Checks**:
- All required fields present
- Text is valid Unicode
- Bounding boxes are within image bounds
- No duplicate line IDs
- Image files exist

---

## Example: Complete Labeled Image

**Image**: `tam_001.jpg` (Tamil palm-leaf, medium damage)

**Transcription**:
```
Line 0: தமிழ் கையெழுத்து பிரதி
Line 1: பழைய இலக்கியம் பற்றி
Line 2: [?]வரல[?] நூல்
```

**JSON** (`tam_001.json`):
```json
{
  "image_path": "real_test_set/images/tam_001.jpg",
  "language": "Tamil",
  "script": "Tamil",
  "quality": "medium",
  "damage_notes": "Water stain upper left, line 2 partially faded",
  "lines": [
    {
      "line_id": "tam_001_line_0",
      "text": "தமிழ் கையெழுத்து பிரதி",
      "bbox": {"x": 120, "y": 80, "width": 850, "height": 65},
      "confidence_notes": "Clear, high confidence expected"
    },
    {
      "line_id": "tam_001_line_1",
      "text": "பழைய இலக்கியம் பற்றி",
      "bbox": {"x": 125, "y": 160, "width": 820, "height": 62},
      "confidence_notes": "Clear"
    },
    {
      "line_id": "tam_001_line_2",
      "text": "[?]வரல[?] நூல்",
      "bbox": {"x": 130, "y": 235, "width": 780, "height": 60},
      "confidence_notes": "First and one character illegible due to water damage"
    }
  ],
  "metadata": {
    "source": "Tamil Digital Library",
    "date_collected": "2024-09-28",
    "labeler": "Akash",
    "notes": "Historical Tamil manuscript about literature"
  }
}
```

---

## Timeline

**Target**: 30-50 labeled images

**Estimated effort**:
- 10-15 minutes per image (transcription + boxes + quality check)
- Total: 5-12 hours of labeling work

**Suggested approach**:
1. **Week 1**: Collect/download images (2-3 hours)
2. **Week 1-2**: Label 5-10 images per day (1-2 hours/day)
3. **End of Week 2**: Validation and cleanup

---

## What Happens Next

Once you have labeled the real test set:

1. **I will evaluate** all our models (restoration, segmentation, recognition, retrieval) on it
2. **Compare** synthetic vs real performance
3. **Document gaps** - what works on synthetic but fails on real?
4. **Iterate** - improve models based on real-world failures

**The separate synthetic/real evaluation is critical for your placement interviews** - it shows you understand the sim-to-real gap, a key ML engineering concept.

---

## Questions?

When labeling, if you encounter:
- **Ambiguous characters**: Mark with [?] and note in `confidence_notes`
- **Multiple interpretations**: Choose the most likely, note alternatives
- **Unknown language**: Best guess + note in metadata
- **Torn/missing regions**: Use `[...]` to indicate gap

---

## License & Ethics

- Only use images you have rights to (public domain, CC license, personal photos with permission)
- Document all sources in metadata
- Never label private/sensitive manuscripts without consent
- If downloading from archives, respect their terms of use

---

## Contact

If you need help with:
- Finding sources → Ask me for dataset links
- Unicode input → I'll provide keyboard links
- Labeling tool → I'll build a simple GUI
- Quality checking → Run the validator script

**After you've collected and labeled 30-50 images, notify me and I'll proceed with evaluation on both synthetic and real data.**

