"""
PolyFlow Cross-File Linker and Dependency Resolver.

Resolves @link statements across .poly files and loads imported language blocks and schemas.
"""

import os
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
from polyflow.parser import PolyParser, PolyAST, LanguageBlock, SchemaBlock

class LinkResolutionError(Exception):
    pass

class PolyLinker:
    def __init__(self, parser: Optional[PolyParser] = None):
        self.parser = parser or PolyParser()
        self.cache: Dict[str, PolyAST] = {}
        self.visiting: Set[str] = set()

    def resolve_ast(self, ast: PolyAST, base_dir: Path) -> Dict[str, Any]:
        resolved = {
            "linked_blocks": {},  # alias -> list of LanguageBlock
            "linked_schemas": {}, # alias -> SchemaBlock
            "dependency_tree": []
        }

        abs_filepath = str(Path(ast.filepath).resolve()) if ast.filepath else "inline"
        if abs_filepath in self.visiting:
            raise LinkResolutionError(f"Circular link dependency detected involving '{ast.filepath}'.")

        self.visiting.add(abs_filepath)

        for link in ast.links:
            target_path = base_dir / link.target_path
            if not target_path.exists():
                raise LinkResolutionError(f"Link target not found: '{link.target_path}' (resolved to {target_path})")

            target_str = str(target_path.resolve())

            if target_str not in self.cache:
                child_ast = self.parser.parse_file(str(target_path))
                # Recursively resolve child links
                self.resolve_ast(child_ast, target_path.parent)
                self.cache[target_str] = child_ast
            else:
                child_ast = self.cache[target_str]

            alias = link.alias or target_path.stem
            resolved["dependency_tree"].append(target_str)

            # Extract by selector (e.g. python[service], model, typescript)
            if link.selector:
                blocks = self._filter_blocks(child_ast, link.selector)
                resolved["linked_blocks"][alias] = blocks
            else:
                resolved["linked_blocks"][alias] = child_ast.language_blocks
                for schema_name, schema_obj in child_ast.schemas.items():
                    resolved["linked_schemas"][f"{alias}.{schema_name}"] = schema_obj

        self.visiting.remove(abs_filepath)
        return resolved

    def _filter_blocks(self, ast: PolyAST, selector: str) -> List[LanguageBlock]:
        # Selector examples: "python[service]", "python", "model", "[service]"
        results = []
        target_lang = None
        target_tag = None

        if "::" in selector:
            selector = selector.split("::")[-1]

        if "[" in selector and selector.endswith("]"):
            parts = selector[:-1].split("[")
            target_lang = parts[0].strip().lower() if parts[0] else None
            target_tag = parts[1].strip().lower()
        else:
            sel_lower = selector.lower()
            if sel_lower in PolyParser.KNOWN_LANGUAGES:
                target_lang = sel_lower
            else:
                target_tag = sel_lower

        for block in ast.language_blocks:
            lang_match = (target_lang is None) or (block.language.lower() == target_lang)
            tag_match = (target_tag is None) or (block.tag.lower() == target_tag)
            if lang_match and tag_match:
                results.append(block)

        return results
