"""RCIR v8 Context Compiler Package."""

from rcir.context.compiler import (
    CompiledContext,
    ContextCompiler,
    ContextEntry,
    ContextGranularity,
)

from rcir.context.models import ContextRetrievalResult

def __getattr__(name):
    # The optional legacy graph provider depends on the source checkout's
    # orchestrator. Token counting and the standalone SDK must not import it.
    if name in {"RCIRContextProvider", "LiveRCIRContextProvider", "RCIRContextError"}:
        from rcir.context import provider
        return getattr(provider, name)
    raise AttributeError(name)

__all__ = [
    "CompiledContext",
    "ContextCompiler",
    "ContextEntry",
    "ContextGranularity",
    "ContextRetrievalResult",
    "RCIRContextProvider",
    "LiveRCIRContextProvider",
    "RCIRContextError",
]
