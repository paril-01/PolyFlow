"""
PolyFlow (.poly) File Parser and AST Generator.

Re-exports the canonical parser and AST from polyflow_sdk.core.parser
for complete backward compatibility within the monorepo.
"""

from polyflow_sdk.core.parser import (
    LanguageBlock,
    SchemaBlock,
    LinkDirective,
    SourceDirective,
    ErrorMapping,
    GovernanceBlock,
    PolyAST,
    PolyParser,
)

__all__ = [
    "LanguageBlock",
    "SchemaBlock",
    "LinkDirective",
    "SourceDirective",
    "ErrorMapping",
    "GovernanceBlock",
    "PolyAST",
    "PolyParser",
]
