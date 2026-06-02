"""Project-level exceptions used for fail-fast pipeline behavior."""


class PipelineError(Exception):
    """Base error for pipeline failures."""


class ValidationError(PipelineError):
    """Raised when schema or field validation fails."""


class HarnessError(PipelineError):
    """Raised when a harness constraint blocks unsafe pipeline output."""


class SourceIntegrityError(HarnessError):
    """Raised when raw source metadata is missing or suspicious."""


class LoopGuardError(HarnessError):
    """Raised when processing exceeds the configured step budget."""
