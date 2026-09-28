"""FastAPI application - main entry point."""
import uuid
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.core.logging import setup_logging, get_logger
from backend.core.config import settings
from backend.core.models import Manuscript, Line, BoundingBox, SearchResult
from backend.storage.database import Database
from backend.pipeline.recognition import TesseractRecognizer

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Global instances
db: Database
recognizer: TesseractRecognizer


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup/shutdown."""
    global db, recognizer

    # Startup
    logger.info("application_starting")
    db = Database()
    db.connect()
    recognizer = TesseractRecognizer()
    logger.info("application_ready")

    yield

    # Shutdown
    logger.info("application_shutting_down")
    db.close()


# Create FastAPI app
app = FastAPI(
    title="OlaiSearch API",
    description="Palm-leaf manuscript digitization and search platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class UploadResponse(BaseModel):
    """Response from upload endpoint."""
    manuscript_id: str
    text: str
    num_lines: int
    message: str


class SearchRequest(BaseModel):
    """Search request."""
    query: str
    limit: int = 10


class SearchResponse(BaseModel):
    """Search response."""
    results: List[SearchResult]
    query: str
    num_results: int


# Endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "OlaiSearch API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected",
        "tesseract": "available",
    }


@app.post("/api/v1/upload", response_model=UploadResponse)
async def upload_manuscript(
    file: UploadFile = File(...),
    language: str = Query(default="tam", description="Language code (tam/mal/san)"),
):
    """Upload and OCR a palm-leaf manuscript image.

    This is the vertical slice endpoint: upload → Tesseract → index.

    Args:
        file: Uploaded image file (JPG/PNG)
        language: Language code for OCR

    Returns:
        UploadResponse with manuscript ID and recognized text
    """
    logger.info(
        "upload_request",
        filename=file.filename,
        content_type=file.content_type,
        language=language,
    )

    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Only JPG/PNG allowed."
        )

    try:
        # Read image bytes
        image_bytes = await file.read()

        # Run Tesseract OCR
        text = recognizer.recognize_page(image_bytes)

        if not text:
            raise HTTPException(
                status_code=400,
                detail="No text could be recognized from the image"
            )

        # Create manuscript object
        manuscript_id = str(uuid.uuid4())

        # For vertical slice: treat whole page as one line
        # (Later milestones will add proper line segmentation)
        line_id = f"{manuscript_id}_line_0"
        line = Line(
            id=line_id,
            text=text,
            bbox=BoundingBox(x=0, y=0, width=100, height=100),  # Placeholder
            confidence=0.8,  # Placeholder
            script=language,
        )

        manuscript = Manuscript(
            id=manuscript_id,
            image_path=file.filename or "uploaded_image",
            language=language,
            script=language,
            lines=[line],
        )

        # Index in database
        db.index_manuscript(manuscript)

        logger.info(
            "upload_success",
            manuscript_id=manuscript_id,
            text_length=len(text),
        )

        return UploadResponse(
            manuscript_id=manuscript_id,
            text=text,
            num_lines=1,
            message="Manuscript uploaded and indexed successfully",
        )

    except Exception as e:
        logger.error("upload_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/api/v1/search", response_model=SearchResponse)
async def search_manuscripts(request: SearchRequest):
    """Search for text in indexed manuscripts using BM25.

    Args:
        request: Search request with query and limit

    Returns:
        SearchResponse with ranked results
    """
    logger.info("search_request", query=request.query, limit=request.limit)

    try:
        results = db.search(request.query, limit=request.limit)

        logger.info(
            "search_success",
            query=request.query,
            num_results=len(results),
        )

        return SearchResponse(
            results=results,
            query=request.query,
            num_results=len(results),
        )

    except Exception as e:
        logger.error("search_error", query=request.query, error=str(e))
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/api/v1/manuscripts")
async def list_manuscripts():
    """List all indexed manuscripts."""
    # TODO: Implement manuscript listing
    return {"message": "Manuscript listing not yet implemented"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
