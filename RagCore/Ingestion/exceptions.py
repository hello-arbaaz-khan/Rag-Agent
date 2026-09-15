
class DocuMindError(Exception):
    """
    The MASTER Base Exception for the entire project.
    Every custom error in DocuMind MUST inherit from this class.
    """
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class IngestionError(DocuMindError):
    """Raisederror_context specifically when file reading or text parsing fails."""
    pass

class IntegrationError(DocuMindError):
    """Raised specifically when third-party cloud APIs (like Google Drive) fail."""
    pass