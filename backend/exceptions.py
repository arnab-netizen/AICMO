class QualityGateFailedError(Exception):
    def __init__(self, reasons: list[str]) -> None:
        self.reasons = reasons
        super().__init__("Quality gate failed: " + "; ".join(reasons))


class BlankPdfError(Exception):
    """Raised when PDF rendering produces empty or invalid output."""

    pass


class PdfRenderError(Exception):
    """Raised when PDF rendering fails due to technical errors."""

    pass
