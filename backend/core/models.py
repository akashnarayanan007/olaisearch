"""Core data models."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Bounding box coordinates."""

    x: int
    y: int
    width: int
    height: int


class OCRAlternative(BaseModel):
    """Alternative OCR reading."""

    text: str
    confidence: float = Field(ge=0.0, le=1.0)


class Line(BaseModel):
    """Text line in a manuscript."""

    id: str
    text: str
    bbox: BoundingBox
    confidence: float = Field(ge=0.0, le=1.0)
    script: Optional[str] = None
    alternatives: List[OCRAlternative] = Field(default_factory=list)
    char_confidences: List[float] = Field(default_factory=list)
    ocr: Optional[OCRResult] = None


class Manuscript(BaseModel):
    """Palm-leaf manuscript."""

    id: str
    image_path: str
    restored_image_path: Optional[str] = None
    language: str
    script: str
    lines: List[Line] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class OCRResult(BaseModel):
    """OCR recognition result."""

    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    char_confidences: List[float] = Field(default_factory=list)
    alternatives: List[OCRAlternative] = Field(default_factory=list)
    recognizer: str = "unknown"
    processing_time_ms: float = 0.0


class SearchResult(BaseModel):
    """Search result."""

    manuscript_id: str
    line_id: str
    text: str
    score: float
    bbox: BoundingBox
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Citation(BaseModel):
    """Citation in chat response."""

    tier: str  # "manuscript", "archive", "background"
    manuscript_id: Optional[str] = None
    line_id: Optional[str] = None
    text: str
    bbox: Optional[BoundingBox] = None
    confidence: Optional[float] = None


class ChatResponse(BaseModel):
    """ManuscriptChat response."""

    answer: str
    citations: List[Citation] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_tiers_used: List[str] = Field(default_factory=list)
    uncertainty_notes: List[str] = Field(default_factory=list)
    follow_up_suggestions: List[str] = Field(default_factory=list)

    @property
    def response(self) -> str:
        """Alias for ``answer`` to support attribute-style access."""
        return self.answer
