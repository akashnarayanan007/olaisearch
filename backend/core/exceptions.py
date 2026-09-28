"""Custom exceptions."""


class OlaiSearchException(Exception):
    """Base exception for OlaiSearch."""

    pass


class ProviderException(OlaiSearchException):
    """Exception raised by AI providers."""

    pass


class OCRException(OlaiSearchException):
    """Exception raised during OCR."""

    pass


class IndexingException(OlaiSearchException):
    """Exception raised during indexing."""

    pass


class SearchException(OlaiSearchException):
    """Exception raised during search."""

    pass
