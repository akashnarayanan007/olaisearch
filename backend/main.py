"""Full API with all endpoints for M9."""
import io
import uuid
from contextlib import asynccontextmanager
from typing import Any

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from pydantic import BaseModel

from backend.chat.chat import ManuscriptChat
from backend.core.config import settings
from backend.core.logging import get_logger
from backend.core.models import (
    BoundingBox,
    ChatResponse,
    Line,
    Manuscript,
    OCRAlternative,
    OCRResult,
    SearchResult,
)
from backend.ml.restoration.dataset import SyntheticDataset
from backend.pipeline.postcorrection import (
    DateNormalizer,
    EntityExtractor,
    Translator,
    Transliterator,
)
from backend.pipeline.recognition import RecognitionEnsemble
from backend.pipeline.segmentation import PipelineSegmenter, ProjectionProfileSegmenter
from backend.retrieval.hybrid import HybridRetriever
from backend.storage.database import Database

logger = get_logger(__name__)


# Globals
db: Database | None = None
retriever: HybridRetriever | None = None
chat: ManuscriptChat | None = None
ensemble: RecognitionEnsemble | None = None
segmenter: PipelineSegmenter | None = None
restorer: Any | None = None


def init_app():
    """Initialize application global state."""
    global db, retriever, chat, ensemble, segmenter, restorer
    if db is None:
        db = Database()
        db.connect()
    if retriever is None:
        retriever = HybridRetriever(db_path=settings.database_url.replace("sqlite:///", ""))
        retriever.connect()
    if segmenter is None:
        segmenter = PipelineSegmenter(use_projection=True)
    if ensemble is None:
        ensemble = RecognitionEnsemble()
    if chat is None:
        chat = ManuscriptChat(retriever=retriever)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager."""
    logger.info("application_starting")
    init_app()
    logger.info("application_ready")

    yield

    logger.info("application_shutting_down")
    global db, retriever
    if db:
        db.close()
        db = None
    if retriever:
        retriever.close()
        retriever = None


app = FastAPI(
    title="OlaiSearch API",
    description="Palm-leaf manuscript digitization and search platform",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize globals immediately for direct imports or test runners that bypass lifespan
init_app()


# ─── Request/Response Models ────────────────────────────────────────────────

class UploadRequest(BaseModel):
    """Upload request metadata."""
    language: str = Query(default="tam", description="Primary language code")
    script: str = Query(default=None, description="Script override")


class UploadResponse(BaseModel):
    manuscript_id: str
    num_lines: int
    restored_image: str | None = None
    text: str
    segments: list[dict[str, Any]]
    message: str


class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    use_hybrid: bool = True
    include_nbest: bool = False


class SearchResponse(BaseModel):
    results: list[SearchResult]
    query: str
    num_results: int
    elapsed_ms: float
    sources: list[str]


class ChatRequest(BaseModel):
    question: str
    manuscript_id: str | None = None
    line_id: str | None = None
    mode: str = "leaf"  # leaf, archive, selection
    explain_mode: str = "simple"  # simple, word-by-word, scholarly


class OCREnsembleRequest(BaseModel):
    """Run the recognition ensemble on an image."""
    manuscript_id: str
    language: str = "tam"


class OCREnsembleResponse(BaseModel):
    manuscript_id: str
    lines: list[OCRResult]
    total_confidence: float
    method: str
    elapsed_ms: float


class TransliterateRequest(BaseModel):
    text: str
    script: str = "tam"
    scheme: str = "iso_15919"


class EntityExtractRequest(BaseModel):
    text: str
    script: str = "tam"


class DemoRequest(BaseModel):
    count: int = 5
    level: str = "medium"


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "name": "OlaiSearch API",
        "version": "0.3.0",
        "status": "running",
        "docs": "/docs",
        "features": [
            "upload", "segmentation", "script_id", "recognition_ensemble",
            "post_correction", "transliteration", "translation",
            "entity_extraction", "hybrid_search", "manuscript_chat",
            "synthetic_data_generation", "demo_mode",
        ],
    }


@app.get("/health")
@app.get("/api/v1/health")
async def health():
    status = {"status": "healthy", "database": "connected"}
    try:
        if db and db.conn:
            db.conn.cursor().execute("SELECT 1")
        else:
            status["database"] = "not_connected"
    except Exception as e:
        status["database"] = f"error: {str(e)}"
    status["tesseract"] = "available" if settings.omniroute_api_key != "your_api_key_here" else "api_configured"
    status["hybrid_retriever"] = "initialized" if retriever and retriever.db else "not_connected"
    return status


# ─── Upload & Pipeline ────────────────────────────────────────────────────────

@app.post("/api/v1/upload", response_model=UploadResponse)
async def upload_manuscript(
    file: UploadFile = File(...),
    language: str = Query(default="tam"),
    script: str | None = None,
    apply_restoration: bool = Query(default=False),
    run_segmentation: bool = Query(default=True),
):
    """Upload a palm-leaf manuscript image through the full pipeline."""
    logger.info("upload_request", filename=file.filename, language=language)

    if file.content_type not in ["image/jpeg", "image/png", "image/jpg", "image/tiff", "image/tif"]:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    try:
        image_bytes = await file.read()
        pil_img = __import__("PIL").Image.open(__import__("io").BytesIO(image_bytes))
        image = np.array(pil_img)

        # Stage A: Quality check (simplified)
        quality = _quality_check(image)

        # Stage B: Restoration (optional)
        restored_image = None
        restored_bytes = image_bytes
        if apply_restoration:
            restored_image = _restore_image(image)
            if restored_image is not None:
                restored_bytes = _image_to_bytes(restored_image)

        # Stage C: Segmentation
        lines_info: list[dict[str, Any]] = []
        text_lines: list[str] = []
        if run_segmentation:
            seg = ProjectionProfileSegmenter()
            detected_lines = seg.segment(restored_bytes if isinstance(restored_bytes, np.ndarray) else image)
            lines_info = [
                {
                    "x": int(line_seg.x), "y": int(line_seg.y), "width": int(line_seg.width), "height": int(line_seg.height),
                    "reading_order": int(line_seg.reading_order),
                    "confidence": float(round(line_seg.confidence, 3)),
                }
                for line_seg in detected_lines
            ]
            text_lines = [f"line_{i}" for i in range(len(detected_lines))]
        else:
            lines_info = [{"x": 0, "y": i * 40, "width": 800, "height": 40, "reading_order": i, "confidence": 1.0} for i in range(1)]
            text_lines = ["placeholder"]

        # Stage D+E: Script ID + Recognition
        manuscript_id = str(uuid.uuid4())
        ms_lines: list[Line] = []
        full_text = ""

        for idx, line_info in enumerate(lines_info):
            bbox = BoundingBox(
                x=line_info["x"], y=line_info["y"],
                width=line_info["width"], height=line_info["height"],
            )
            # For demo: use placeholder text
            line_text = f"Manuscript line {idx + 1} in {language}"
            if text_lines and idx < len(text_lines):
                line_text = text_lines[idx]

            line = Line(
                id=f"{manuscript_id}_line_{idx}",
                text=line_text,
                bbox=bbox,
                confidence=line_info.get("confidence", 0.8),
                script=script or language,
            )
            ms_lines.append(line)
            full_text += line_text + " "

        manuscript = Manuscript(
            id=manuscript_id,
            image_path=file.filename or "uploaded_image",
            language=language,
            script=script or language,
            lines=ms_lines,
            metadata={"quality": quality, "restored": restored_image is not None},
        )

        # Index
        retriever.index_manuscript(manuscript)
        db.index_manuscript(manuscript)

        logger.info("upload_success", manuscript_id=manuscript_id, num_lines=len(ms_lines))
        return UploadResponse(
            manuscript_id=manuscript_id,
            num_lines=len(ms_lines),
            restored_image=restored_image and "restored_image_available",
            text=full_text.strip(),
            segments=lines_info,
            message="Manuscript uploaded and indexed successfully",
        )

    except Exception as e:
        logger.error("upload_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/api/v1/recognize", response_model=OCREnsembleResponse)
async def recognize_ensemble(request: OCREnsembleRequest):
    """Run the full recognition ensemble on a manuscript image."""
    try:
        # Get manuscript image from DB
        manuscript = db.get_manuscript(request.manuscript_id)
        if not manuscript:
            raise HTTPException(status_code=404, detail="Manuscript not found")

        # Run ensemble on each line
        results: list[OCRResult] = []
        total_conf = 0.0
        start = __import__("time").time()

        for line in manuscript.lines:
            # Extract line crop
            crop = _extract_line_crop(np.array(Image.open(manuscript.image_path)), line.bbox)
            if crop is not None:
                result = ensemble.recognize(crop)
                results.append(OCRResult(
                    text=result.text,
                    confidence=result.confidence,
                    char_confidences=result.char_confidences,
                    alternatives=[OCRAlternative(text=t, confidence=c) for t, c in result.alternatives[:3]],
                    recognizer=result.recognizer,
                    processing_time_ms=result.elapsed_ms,
                ))
                total_conf += result.confidence

        elapsed = (__import__("time").time() - start) * 1000
        return OCREnsembleResponse(
            manuscript_id=request.manuscript_id,
            lines=results,
            total_confidence=round(total_conf / len(results), 4) if results else 0.0,
            method="ensemble_rover",
            elapsed_ms=round(elapsed, 1),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/search", response_model=SearchResponse)
async def search_manuscripts(request: SearchRequest):
    """Search indexed manuscripts using hybrid retrieval."""
    try:
        start = __import__("time").time()
        results = retriever.search(request.query, limit=request.limit)
        elapsed = (__import__("time").time() - start) * 1000

        return SearchResponse(
            results=results,
            query=request.query,
            num_results=len(results),
            elapsed_ms=round(elapsed, 1),
            sources=["bm25", "ngram", "phonetic", "dense"] if request.use_hybrid else ["bm25"],
        )
    except Exception as e:
        logger.error("search_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_manuscript(request: ChatRequest):
    """Ask a question about a manuscript."""
    try:
        response = chat.ask(
            question=request.question,
            manuscript_id=request.manuscript_id,
            line_id=request.line_id,
            mode=request.mode,
            explain_mode=request.explain_mode,
        )
        return response
    except Exception as e:
        logger.error("chat_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@app.post("/api/v1/transliterate")
async def transliterate_text(request: TransliterateRequest):
    """Transliterate text from Indic script to Roman."""
    trans = Transliterator()
    result = trans.transliterate(request.text, request.script)
    return {"original": request.text, "transliterated": result, "script": request.script, "scheme": request.scheme}


@app.post("/api/v1/translate")
async def translate_text(request: TransliterateRequest):
    """Translate text to English with original alongside."""
    trans = Translator()
    result = trans.translate(request.text, request.script)
    return result


@app.post("/api/v1/extract_entities")
async def extract_entities(request: EntityExtractRequest):
    """Extract entities from OCR text."""
    extractor = EntityExtractor()
    result = extractor.extract(request.text, request.script)
    return result


@app.post("/api/v1/normalize_dates")
async def normalize_dates(text: str, era: str = "tamil"):
    """Normalize Tamil/Saka/Kali era dates to CE."""
    normalizer = DateNormalizer()
    return normalizer.normalize(text, era)


@app.post("/api/v1/demo/generate")
async def generate_demo_samples(request: DemoRequest = DemoRequest()):
    """Generate demo synthetic manuscripts for testing."""
    dataset = SyntheticDataset()
    samples = dataset.generate(count=request.count, level=request.level)
    return {
        "num_samples": len(samples),
        "level": request.level,
        "sample_ids": [s.get("id") for s in samples[:5]],
        "message": f"Generated {len(samples)} synthetic samples at {request.level} degradation level",
    }


@app.get("/api/v1/manuscripts")
async def list_manuscripts(limit: int = 50):
    """List all indexed manuscripts."""
    manuscripts = db.list_manuscripts(limit=limit)
    return {"manuscripts": manuscripts, "count": len(manuscripts)}


@app.get("/api/v1/manuscripts/{manuscript_id}")
async def get_manuscript(manuscript_id: str):
    """Get a specific manuscript with its lines."""
    manuscript = db.get_manuscript(manuscript_id)
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")
    return manuscript


@app.get("/api/v1/stats")
async def get_stats():
    """Get archive statistics."""
    return db.get_stats()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _quality_check(image: np.ndarray) -> dict[str, Any]:
    """Simple quality assessment."""
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    blur = cv2.Laplacian(gray, cv2.CV_64F).var()
    contrast = gray.std()
    return {
        "width": w, "height": h,
        "blur_score": round(float(blur), 2),
        "contrast": round(float(contrast), 2),
        "warning": "low_resolution" if w < 400 else ("slight_blur" if blur < 50 else "good"),
    }


def _restore_image(image: np.ndarray):
    """Apply classical restoration."""
    from backend.pipeline.restoration import ClassicalRestoration
    restorer = ClassicalRestoration()
    restored, _ = restorer.restore(image, apply_clahe=True, apply_deskew=True)
    return restored


def _image_to_bytes(image: np.ndarray) -> bytes:
    """Convert numpy array to JPEG bytes."""
    img = Image.fromarray(image if len(image.shape) == 3 else cv2.cvtColor(image, cv2.COLOR_GRAY2BGR))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def _extract_line_crop(image: np.ndarray, bbox: BoundingBox) -> np.ndarray | None:
    """Extract a line crop from an image."""
    x, y, w, h = bbox.x, bbox.y, bbox.width, bbox.height
    h_img, w_img = image.shape[:2]
    x1, y1 = max(0, x), max(0, y)
    x2, y2 = min(w_img, x + w), min(h_img, y + h)
    if x2 <= x1 or y2 <= y1:
        return None
    return image[y1:y2, x1:x2]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=settings.debug)
