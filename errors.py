class OrchestratorError(Exception):
    """Base exception for all errors in the orchestrator."""
    pass

class NodeConnectionError(OrchestratorError):
    """Raised when node connections are invalid or workflow has issues."""
    pass

class NodeValidationError(OrchestratorError):
    """Raised when input or output validation for a node fails."""
    pass

class NodeExecutionError(OrchestratorError):
    """Raised when execution of a node fails."""
    pass