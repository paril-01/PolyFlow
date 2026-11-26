"""Resolved Git/overlay identities and contained, immutable source bytes."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import subprocess


class ServiceError(ValueError):
    def __init__(self, status, message):
        self.status = status
        super().__init__(message)


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


DENIED = {".git", ".ssh", ".venv", "venv", "node_modules", "vendor", "3rdparty", "__pycache__", "dist", "build", ".rcir", "private", "hidden_tests"}
EXTENSIONS = {".py", ".php", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs", ".c", ".h", ".cpp", ".cs", ".json", ".yaml", ".yml", ".toml", ".md"}


def safe_path(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\x00" in relative or ":" in relative:
        raise ServiceError("INVALID_SCOPE", "Invalid relative source path")
    normalized = relative.replace("\\", "/")
    if PureWindowsPath(relative).anchor or normalized.startswith("/") or any(p in {"", ".", ".."} for p in normalized.split("/")):
        raise ServiceError("INVALID_SCOPE", "Path traversal rejected")
    candidate = root / normalized
    try:
        candidate.resolve().relative_to(root)
        for part in (candidate, *candidate.parents):
            if part == root:
                break
            if part.is_symlink():
                raise ServiceError("INVALID_SCOPE", "Symlink source paths are unsupported")
    except (ValueError, OSError, RuntimeError) as exc:
        raise ServiceError("INVALID_SCOPE", "Source escapes repository") from exc
    return candidate


def read_stable(root: Path, relative: str) -> bytes:
    path = safe_path(root, relative)
    try:
        before = path.stat()
        with path.open("rb") as stream:
            opened = os.fstat(stream.fileno())
            data = stream.read()
            closed = os.fstat(stream.fileno())
        after = safe_path(root, relative).stat()
    except OSError as exc:
        raise ServiceError("STALE", "Source disappeared or is unavailable") from exc
    identities = {(s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns) for s in (before, opened, closed, after)}
    if len(identities) != 1:
        raise ServiceError("STALE", "Source changed during capture")
    return data


@dataclass(frozen=True)
class SourceFile:
    path: str
    raw: bytes
    sha256: str


class Snapshot:
    policy_version = "tracked-source-uniform-v1"

    def __init__(self, root: Path, ref="HEAD", allow_overlay=False, allow_unversioned=False):
        self.root = Path(root).resolve()
        if not self.root.is_dir():
            raise ServiceError("INVALID_SCOPE", "Repository does not exist")
        self.allow_overlay = allow_overlay
        self.allow_unversioned = allow_unversioned
        self.git = self._git("rev-parse", "--show-toplevel", required=False)
        if self.git:
            if Path(self.git.decode().strip()).resolve() != self.root:
                raise ServiceError("INVALID_SCOPE", "Use the repository root, not a nested directory")
            self.commit = self._git("rev-parse", f"{ref}^{{commit}}").decode().strip()
            if self.commit != self._git("rev-parse", "HEAD").decode().strip():
                raise ServiceError("STALE", "Working source is not checked out at requested ref")
            self.tree = self._git("rev-parse", "HEAD^{tree}").decode().strip()
            self.dirty = bool(self._git("status", "--porcelain", "--untracked-files=normal"))
            if self.dirty and not allow_overlay:
                raise ServiceError("INVALID_SCOPE", "Dirty source requires explicit overlay capture")
        elif allow_unversioned:
            self.commit, self.tree, self.dirty = None, None, True
        else:
            raise ServiceError("INVALID_SCOPE", "Git repository required")
        self.files = {}
        self.omitted_files = []
        self.paths = self._paths()
        for path in self.paths:
            try:
                absolute = safe_path(self.root, path)
                if absolute.stat().st_size > 2_000_000:
                    self.omitted_files.append({"path": path, "reason": "FILE_SIZE_LIMIT"})
                    continue
                raw = read_stable(self.root, path)
                raw.decode("utf-8", errors="strict")
                if b"\x00" in raw:
                    raise UnicodeError("Binary source")
                self.files[path] = SourceFile(path, raw, digest(raw))
            except (OSError, UnicodeError, ServiceError) as exc:
                if isinstance(exc, ServiceError) and exc.status == "STALE":
                    raise
                self.omitted_files.append({"path": path, "reason": "UNSUPPORTED_OR_UNSAFE_SOURCE"})
        identity = {"commit": self.commit, "tree": self.tree, "policy": self.policy_version,
                    "overlay": allow_overlay, "files": {p: f.sha256 for p, f in self.files.items()}, "omissions": self.omitted_files}
        self.id = digest(canonical(identity))
        self.verify()

    def _git(self, *arguments, required=True):
        result = subprocess.run(["git", "-C", str(self.root), *arguments], capture_output=True, timeout=60)
        if result.returncode:
            if required:
                raise ServiceError("INVALID_SCOPE", "Git revision or source census failed")
            return b""
        return result.stdout

    def _paths(self):
        if self.git:
            names = self._git("ls-files", "-z", "--cached").split(b"\x00")
            if self.allow_overlay:
                names += self._git("ls-files", "-z", "--others", "--exclude-standard").split(b"\x00")
            paths = [os.fsdecode(p).replace("\\", "/") for p in names if p]
        else:
            paths = []
            for base, directories, files in os.walk(self.root, followlinks=False):
                directories[:] = sorted(d for d in directories if d not in DENIED and not (Path(base) / d).is_symlink())
                paths += [(Path(base) / name).relative_to(self.root).as_posix() for name in sorted(files)]
        return sorted(set(p for p in paths if not (set(Path(p).parts) & DENIED)
                          and Path(p).suffix.lower() in EXTENSIONS
                          and not Path(p).name.startswith(".env")
                          and Path(p).name not in {"oracle.json", "credentials.json"}))

    def verify(self):
        if self.git and self._git("rev-parse", "HEAD").decode().strip() != self.commit:
            raise ServiceError("STALE", "Repository revision changed")
        if self._paths() != self.paths:
            raise ServiceError("STALE", "Source inventory changed")
        for path, source in self.files.items():
            if digest(read_stable(self.root, path)) != source.sha256:
                raise ServiceError("STALE", "Source bytes changed; refresh the index")

    def manifest(self):
        return {"snapshot_id": self.id, "commit": self.commit, "tree": self.tree,
                "dirty": self.dirty, "overlay_captured": self.allow_overlay,
                "policy": self.policy_version, "files": {p: f.sha256 for p, f in self.files.items()},
                "omitted_files": self.omitted_files}
