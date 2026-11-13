"""OCR pipeline modules."""
from backend.pipeline.postcorrection import (
    DateNormalizer,
    DomainGlossary,
    EntityExtractor,
    LexiconCorrector,
    Translator,
    Transliterator,
)
from backend.pipeline.recognition import (
    Calibration,
    CRNNRecognizer,
    RecognitionEnsemble,
    TesseractRecognizer,
    VLMRecognizer,
    compute_cer,
    compute_wer,
    split_graphemes,
)
from backend.pipeline.script_id import SCRIPT_REGISTRY, ScriptIdentifier
from backend.pipeline.segmentation import (
    PipelineSegmenter,
    ProjectionProfileSegmenter,
    SegmentedLine,
    compute_iou,
    compute_prf1,
)

__all__ = [
    "ProjectionProfileSegmenter",
    "PipelineSegmenter",
    "SegmentedLine",
    "compute_iou",
    "compute_prf1",
    "ScriptIdentifier",
    "SCRIPT_REGISTRY",
    "RecognitionEnsemble",
    "Calibration",
    "TesseractRecognizer",
    "VLMRecognizer",
    "CRNNRecognizer",
    "split_graphemes",
    "compute_cer",
    "compute_wer",
    "LexiconCorrector",
    "Transliterator",
    "Translator",
    "EntityExtractor",
    "DateNormalizer",
    "DomainGlossary",
]
