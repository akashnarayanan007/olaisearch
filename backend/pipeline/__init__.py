"""OCR pipeline modules."""
from backend.pipeline.segmentation import (
    ProjectionProfileSegmenter,
    PipelineSegmenter,
    SegmentedLine,
    compute_iou,
    compute_prf1,
)
from backend.pipeline.script_id import ScriptIdentifier, SCRIPT_REGISTRY
from backend.pipeline.recognition import (
    RecognitionEnsemble,
    Calibration,
    TesseractRecognizer,
    VLMRecognizer,
    CRNNRecognizer,
    split_graphemes,
    compute_cer,
    compute_wer,
)
from backend.pipeline.postcorrection import (
    LexiconCorrector,
    Transliterator,
    Translator,
    EntityExtractor,
    DateNormalizer,
    DomainGlossary,
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
