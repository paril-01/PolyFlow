"""
Repository Tool Interface for AEF Coding Agents.
Provides concrete tools for file inspection, code search, directory listing,
code editing with atomic rollback, command execution, and unified diff inspection.
"""

import os
import re
import sys
import difflib
import subprocess
import shutil
from typing import Optional, Dict, Any, List
from pathlib import Path


class RepoToolEnvironment:
    """
    Sandboxed repository environment providing concrete tools for coding agents.
    Tracks file modifications and maintains original backups for safe rollback.
    """

    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root).resolve()
        if not self.repo_root.exists():
            raise FileNotFoundError(f"Repository root does not exist: {repo_root}")

        self._original_files: Dict[Path, str] = {}
        self._modified_files: List[Path] = []
        self._toolchain_env = self._build_toolchain_env()

    def _build_toolchain_env(self) -> Dict[str, str]:
        """Ensure JDK, PHP, Go, Node, Python are in PATH."""
        env = dict(os.environ)
        extra_paths = [
            r"C:\Program Files\Java\jdk-21\bin",
            r"C:\tools\php83",
            r"C:\Program Files\Go\bin",
            r"C:\Program Files\nodejs",
            r"C:\Python312",
            r"C:\Python312\Scripts",
        ]
        curr_path = env.get("PATH", "")
        paths_to_add = [p for p in extra_paths if os.path.exists(p) and p not in curr_path]
        if paths_to_add:
            env["PATH"] = os.pathsep.join(paths_to_add) + os.pathsep + curr_path
        return env

    def _resolve_safe_path(self, rel_path: str) -> Path:
        """Resolve path relative to repo_root and prevent directory traversal."""
        clean = Path(rel_path).as_posix().lstrip("/")
        full_path = (self.repo_root / clean).resolve()
        try:
            full_path.relative_to(self.repo_root)
        except ValueError:
            raise PermissionError(f"Access denied: Path '{rel_path}' is outside repo root '{self.repo_root}'")
        return full_path

    def inspect_file(self, path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> str:
        """
        Inspect file contents with 1-indexed line numbers.
        Optionally specify start_line and end_line.
        """
        full_path = self._resolve_safe_path(path)
        if not full_path.exists():
            return f"ERROR: File not found: {path}"
        if full_path.is_dir():
            return f"ERROR: Path is a directory, not a file: {path}"

        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except Exception as e:
            return f"ERROR reading file {path}: {str(e)}"

        total_lines = len(lines)
        s = max(1, start_line) if start_line is not None else 1
        e = min(total_lines, end_line) if end_line is not None else total_lines

        if s > total_lines:
            return f"ERROR: start_line {s} exceeds total lines ({total_lines}) in {path}"

        output_lines = [f"{i}: {lines[i - 1]}" for i in range(s, e + 1)]
        return "".join(output_lines)

    def search_code(self, query: str, path: Optional[str] = None, is_regex: bool = False, max_matches: int = 50) -> str:
        """
        Search for query across repository files (or subpath).
        Returns formatted 'file:line: content' matches.
        """
        search_dir = self._resolve_safe_path(path) if path else self.repo_root
        if not search_dir.exists():
            return f"ERROR: Path not found: {path}"

        if not is_regex:
            pattern = re.escape(query)
        else:
            pattern = query

        try:
            regex = re.compile(pattern)
        except re.error as e:
            return f"ERROR invalid regular expression: {e}"

        ignore_dirs = {".git", "node_modules", "vendor", "__pycache__", ".venv", "venv", ".idea", ".vscode"}
        matches = []

        files_to_search = []
        if search_dir.is_file():
            files_to_search = [search_dir]
        else:
            for root, dirs, files in os.walk(search_dir):
                dirs[:] = [d for d in dirs if d not in ignore_dirs]
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in {".png", ".jpg", ".jpeg", ".gif", ".zip", ".tar", ".gz", ".exe", ".dll", ".so", ".class"}:
                        continue
                    files_to_search.append(Path(root) / file)

        for file_path in files_to_search:
            try:
                rel = file_path.relative_to(self.repo_root).as_posix()
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    for line_num, line in enumerate(f, start=1):
                        if regex.search(line):
                            matches.append(f"{rel}:{line_num}: {line.strip()}")
                            if len(matches) >= max_matches:
                                matches.append(f"... reached limit of {max_matches} matches.")
                                return "\n".join(matches)
            except Exception:
                continue

        if not matches:
            return f"No matches found for '{query}' in {path or '.'}"
        return "\n".join(matches)

    def list_dir(self, path: Optional[str] = None) -> str:
        """List files and subdirectories with sizes."""
        target_dir = self._resolve_safe_path(path) if path else self.repo_root
        if not target_dir.exists():
            return f"ERROR: Path not found: {path}"
        if not target_dir.is_dir():
            return f"ERROR: Path is not a directory: {path}"

        items = []
        try:
            for item in sorted(target_dir.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
                if item.name.startswith(".") and item.name != ".poly":
                    continue
                if item.is_dir():
                    items.append(f"[DIR]  {item.name}/")
                else:
                    size = item.stat().st_size
                    items.append(f"[FILE] {item.name:<30} ({size:,} bytes)")
        except Exception as e:
            return f"ERROR reading directory {path}: {e}"

        return "\n".join(items) if items else "(empty directory)"

    def edit_file(self, path: str, old_str: str, new_str: str) -> str:
        """
        Safely replace old_str with new_str in file.
        Backs up original file before applying edit.
        """
        full_path = self._resolve_safe_path(path)
        if not full_path.exists():
            return f"ERROR: File not found: {path}"
        if full_path.is_dir():
            return f"ERROR: Path is a directory: {path}"

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return f"ERROR reading file {path}: {e}"

        if old_str not in content:
            return f"ERROR: Target string to replace was not found in {path}. Make sure whitespace and formatting match exactly."

        count = content.count(old_str)
        if count > 1:
            return f"ERROR: Target string occurs {count} times in {path}. Specify more surrounding context to make replacement unique."

        # Backup original content if not already backed up
        if full_path not in self._original_files:
            self._original_files[full_path] = content

        new_content = content.replace(old_str, new_str, 1)

        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(new_content)
        except Exception as e:
            return f"ERROR writing to file {path}: {e}"

        if full_path not in self._modified_files:
            self._modified_files.append(full_path)

        rel = full_path.relative_to(self.repo_root).as_posix()
        return f"SUCCESS: Modified {rel} (replaced 1 instance)."

    def run_command(self, command: str, timeout_sec: int = 60, cwd: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute command with toolchain PATH resolution.
        Returns dict with exit_code, stdout, stderr, duration_seconds.
        """
        exec_cwd = self._resolve_safe_path(cwd) if cwd else self.repo_root
        import time
        t0 = time.time()
        try:
            proc = subprocess.run(
                command,
                shell=True,
                cwd=str(exec_cwd),
                env=self._toolchain_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout_sec,
            )
            duration = time.time() - t0
            return {
                "exit_code": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "duration_seconds": round(duration, 3),
                "timed_out": False,
            }
        except subprocess.TimeoutExpired as te:
            duration = time.time() - t0
            return {
                "exit_code": -1,
                "stdout": te.stdout or "",
                "stderr": f"Command timed out after {timeout_sec} seconds.",
                "duration_seconds": round(duration, 3),
                "timed_out": True,
            }
        except Exception as e:
            duration = time.time() - t0
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Execution error: {str(e)}",
                "duration_seconds": round(duration, 3),
                "timed_out": False,
            }

    def get_git_diff(self) -> str:
        """
        Generate unified diff of all modifications made in this environment.
        Uses difflib against recorded original backups, guaranteed portable.
        """
        if not self._modified_files:
            return ""

        diff_chunks = []
        for path in self._modified_files:
            orig = self._original_files.get(path, "")
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    curr = f.read()
            except Exception:
                continue

            rel = path.relative_to(self.repo_root).as_posix()
            orig_lines = orig.splitlines(keepends=True)
            curr_lines = curr.splitlines(keepends=True)
            diff = difflib.unified_diff(
                orig_lines,
                curr_lines,
                fromfile=f"a/{rel}",
                tofile=f"b/{rel}",
            )
            chunk = "".join(diff)
            if chunk:
                diff_chunks.append(chunk)

        return "\n".join(diff_chunks)

    def revert_changes(self) -> int:
        """
        Revert all modified files to their original content.
        Returns count of restored files.
        """
        restored = 0
        for path, original_content in self._original_files.items():
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(original_content)
                restored += 1
            except Exception:
                pass
        self._original_files.clear()
        self._modified_files.clear()
        return restored

    def get_modified_files(self) -> List[str]:
        """Return list of relative paths for modified files."""
        return [p.relative_to(self.repo_root).as_posix() for p in self._modified_files]
