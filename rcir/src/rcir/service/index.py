"""Source-bound lexical/BM25 candidates; Python AST semantics are explicit."""
from __future__ import annotations

import ast
from collections import Counter, defaultdict
import math
import re

from .snapshot import Snapshot, canonical, digest


def terms(text):
    split = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    return re.findall(r"[a-z0-9]+", split.lower()) + re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text.lower())


class SourceIndex:
    def __init__(self, snapshot: Snapshot):
        self.snapshot = snapshot
        self.documents = {}
        self.frequency = Counter()
        self.symbols = defaultdict(list)
        self.reverse = defaultdict(set)
        self.relations = []
        self.unsupported = []
        for path, source in snapshot.files.items():
            text = source.raw.decode("utf-8")
            counts = Counter(terms(text))
            self.documents[path] = counts
            self.frequency.update(counts.keys())
            if path.endswith(".py"):
                self._python(path, source.raw, text)
            else:
                for number, line in enumerate(text.splitlines(), 1):
                    for match in re.finditer(r"\b(?:class|interface|function|func|fn)\s+([A-Za-z_]\w*)", line):
                        self.symbols[path].append(self._span(path, max(1, number - 2), min(len(text.splitlines()), number + 20), match.group(1), "INFERRED", "lexical_declaration_candidate"))
        self.average_length = sum(sum(c.values()) for c in self.documents.values()) / max(1, len(self.documents))
        self._link_imports()

    def _span(self, path, start, end, symbol, certainty, reason, begin_byte=None, end_byte=None):
        raw = self.snapshot.files[path].raw
        lines = raw.splitlines(keepends=True)
        begin = sum(map(len, lines[:start - 1])) if begin_byte is None else begin_byte
        finish = sum(map(len, lines[:end])) if end_byte is None else end_byte
        content = raw[begin:finish]
        return {"file_path": path, "file_sha256": self.snapshot.files[path].sha256,
                "start_line": start, "end_line": end, "start_byte": begin, "end_byte": finish,
                "snippet": content.decode("utf-8"), "span_sha256": digest(content),
                "symbol_name": symbol, "symbol_identity": f"{path}::{symbol}" if symbol else None,
                "resolution_class": certainty, "reason_code": reason,
                "freshness": "VERIFIED_AT_SNAPSHOT", "required": False}

    def _python(self, path, raw, text):
        try:
            tree = ast.parse(text)
        except (SyntaxError, ValueError):
            self.unsupported.append({"path": path, "reason": "PYTHON_PARSE_FAILED_LEXICAL_ONLY"})
            return
        lines = raw.splitlines(keepends=True)
        def walk(node, scope=""):
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    name = f"{scope}.{child.name}" if scope else child.name
                    start = min([child.lineno] + [d.lineno for d in child.decorator_list])
                    end = child.end_lineno
                    begin = sum(map(len, lines[:start - 1]))
                    finish = sum(map(len, lines[:end - 1])) + child.end_col_offset
                    self.symbols[path].append(self._span(path, start, end, name, "STATIC_EXACT", "python_ast_definition", begin, finish))
                    walk(child, name)
                else:
                    walk(child, scope)
        walk(tree)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
                for module in names:
                    self.relations.append({"source_file": path, "target_module": module, "line": node.lineno,
                                           "kind": "imports", "certainty": "SYNTACTIC_MODULE_REFERENCE"})

    def _link_imports(self):
        modules = {}
        for path in self.documents:
            if path.endswith(".py"):
                module = path[:-3].replace("/", ".")
                modules[module] = path
                if module.endswith(".__init__"):
                    modules[module[:-9]] = path
        for edge in self.relations:
            target = modules.get(edge["target_module"])
            if target:
                edge["target_file"] = target
                self.reverse[target].add(edge["source_file"])

    def candidates(self, query):
        query_terms = Counter(terms(query))
        if not query_terms:
            return []
        scores = {}
        count = len(self.documents)
        for path, frequencies in self.documents.items():
            length = sum(frequencies.values())
            score = 0.0
            for word in query_terms:
                tf = frequencies.get(word, 0)
                if tf:
                    idf = math.log(1 + (count - self.frequency[word] + .5) / (self.frequency[word] + .5))
                    score += idf * tf * 2.2 / (tf + 1.2 * (.25 + .75 * length / max(1, self.average_length)))
            if score > 0:
                scores[path] = score
        candidates = []
        for path, score in sorted(scores.items(), key=lambda pair: (-pair[1], pair[0])):
            symbols = self.symbols.get(path, [])
            direct = [s for s in symbols if set(terms(s["symbol_name"])) & query_terms.keys()]
            if direct:
                for span in direct:
                    candidates.append({**span, "score": score + 5, "required": False})
            else:
                text_lines = self.snapshot.files[path].raw.decode("utf-8").splitlines()
                if not text_lines:
                    continue
                line = max(range(len(text_lines)), key=lambda i: len(set(terms(text_lines[i])) & query_terms.keys()))
                candidates.append({**self._span(path, max(1, line - 5), min(len(text_lines), line + 16), "", "INFERRED", "bm25_source_window"), "score": score})
        return sorted(candidates, key=lambda s: (-s["score"], s["file_path"], s["start_byte"], s["symbol_name"]))

    def impact(self, path):
        visited, pending = set(), [path]
        while pending:
            current = pending.pop()
            if current in visited:
                continue
            visited.add(current)
            pending.extend(self.reverse.get(current, set()) - visited)
        return sorted(visited - {path})
