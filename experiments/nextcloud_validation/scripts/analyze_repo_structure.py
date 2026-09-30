"""
Phase A: Nextcloud Repository Structure Analysis.

Real filesystem inspection of the Nextcloud server repository.
No estimates from memory — every number comes from actual file counting.
"""

import os
import json
import time
from pathlib import Path
from collections import Counter, defaultdict

REPO_PATH = Path(__file__).resolve().parent.parent / "nextcloud-server"

SKIP_DIRS = {
    ".git", "node_modules", "vendor", "build", "dist",
    "__pycache__", ".cache", ".github",
}

# Map file extensions to language names
EXT_TO_LANG = {
    ".php": "PHP",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".jsx": "JSX",
    ".tsx": "TSX",
    ".vue": "Vue",
    ".css": "CSS",
    ".scss": "SCSS",
    ".less": "LESS",
    ".html": "HTML",
    ".twig": "Twig",
    ".xml": "XML",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".md": "Markdown",
    ".txt": "Text",
    ".sh": "Shell",
    ".bash": "Shell",
    ".py": "Python",
    ".sql": "SQL",
    ".go": "Go",
    ".java": "Java",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".c": "C",
    ".h": "C/C++ Header",
    ".cpp": "C++",
    ".cs": "C#",
    ".svg": "SVG",
    ".png": "PNG",
    ".jpg": "JPEG",
    ".gif": "GIF",
    ".ico": "ICO",
    ".lock": "Lock",
    ".map": "SourceMap",
    ".feature": "Gherkin",
    ".ini": "INI",
    ".conf": "Config",
    ".rst": "reStructuredText",
}

CODE_EXTENSIONS = {
    ".php", ".js", ".ts", ".jsx", ".tsx", ".vue",
    ".py", ".java", ".go", ".rb", ".rs", ".c", ".h",
    ".cpp", ".cs", ".sql", ".sh", ".bash",
}

def count_loc(filepath: Path) -> int:
    """Count non-empty, non-comment lines in a file."""
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()
        count = 0
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("//") and not stripped.startswith("#") and not stripped.startswith("*") and stripped != "/*" and stripped != "*/":
                count += 1
        return count
    except Exception:
        return 0


def analyze_directory_structure(repo_path: Path) -> dict:
    """Analyze top-level directory structure."""
    structure = {}
    for item in sorted(repo_path.iterdir()):
        if item.name in SKIP_DIRS or item.name.startswith("."):
            continue
        if item.is_dir():
            # Count files recursively
            file_count = 0
            for _, _, files in os.walk(item):
                file_count += len(files)
            structure[item.name] = {"type": "directory", "file_count": file_count}
        else:
            structure[item.name] = {"type": "file", "size_bytes": item.stat().st_size}
    return structure


def find_framework_patterns(repo_path: Path) -> dict:
    """Detect framework and architecture patterns."""
    patterns = {
        "has_composer_json": (repo_path / "composer.json").exists(),
        "has_package_json": (repo_path / "package.json").exists(),
        "has_webpack_config": any((repo_path / f).exists() for f in ["webpack.config.js", "webpack.common.js"]),
        "has_docker_compose": any((repo_path / f).exists() for f in ["docker-compose.yml", "docker-compose.yaml"]),
        "has_dockerfile": (repo_path / "Dockerfile").exists(),
        "has_makefile": (repo_path / "Makefile").exists(),
        "has_phpunit": (repo_path / "phpunit.xml").exists() or (repo_path / "phpunit.xml.dist").exists(),
        "has_jest_config": any((repo_path / f).exists() for f in ["jest.config.js", "jest.config.ts"]),
        "has_psalm": (repo_path / "psalm.xml").exists() or (repo_path / "psalm.xml.dist").exists(),
        "has_phpstan": (repo_path / "phpstan.neon").exists() or (repo_path / "phpstan.neon.dist").exists(),
    }

    # Check for Nextcloud-specific patterns
    patterns["has_occ"] = (repo_path / "occ").exists()
    patterns["has_lib_private"] = (repo_path / "lib" / "private").exists()
    patterns["has_lib_public"] = (repo_path / "lib" / "public").exists()
    patterns["has_core"] = (repo_path / "core").exists()
    patterns["has_apps"] = (repo_path / "apps").exists()
    patterns["has_config"] = (repo_path / "config").exists()

    return patterns


def detect_test_structure(repo_path: Path) -> dict:
    """Find test directories and count test files."""
    test_dirs = []
    test_file_count = 0

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        rel = Path(root).relative_to(repo_path).as_posix()

        # Common test directory names
        if any(part in ("tests", "test", "Tests", "Test", "__tests__", "spec") for part in Path(rel).parts):
            test_files = [f for f in files if f.endswith((".php", ".js", ".ts"))]
            if test_files:
                test_dirs.append({"path": rel, "test_files": len(test_files)})
                test_file_count += len(test_files)

    return {
        "test_directories": test_dirs[:20],  # Top 20
        "total_test_files": test_file_count,
    }


def detect_migrations(repo_path: Path) -> dict:
    """Find database migration files."""
    migration_files = []
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        rel = Path(root).relative_to(repo_path).as_posix()
        if "migration" in rel.lower():
            for f in files:
                if f.endswith(".php"):
                    migration_files.append(f"{rel}/{f}")

    return {
        "migration_files_found": len(migration_files),
        "sample_paths": migration_files[:10],
    }


def detect_apps(repo_path: Path) -> dict:
    """Detect Nextcloud apps (plugin architecture)."""
    apps_dir = repo_path / "apps"
    apps = []
    if apps_dir.exists():
        for item in sorted(apps_dir.iterdir()):
            if item.is_dir() and not item.name.startswith("."):
                info_xml = item / "appinfo" / "info.xml"
                routes_php = item / "appinfo" / "routes.php"
                apps.append({
                    "name": item.name,
                    "has_info_xml": info_xml.exists(),
                    "has_routes": routes_php.exists(),
                })
    return {
        "app_count": len(apps),
        "apps": apps,
    }


def main():
    start = time.time()
    print(f"Analyzing: {REPO_PATH}")
    print(f"Repo exists: {REPO_PATH.exists()}")

    if not REPO_PATH.exists():
        print("ERROR: Nextcloud repo not found!")
        return

    # Count all files and LOC
    total_files = 0
    total_loc = 0
    ext_counter = Counter()
    lang_counter = Counter()
    lang_loc = Counter()
    code_files = 0

    for root, dirs, files in os.walk(REPO_PATH):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            fp = Path(root) / f
            ext = fp.suffix.lower()
            total_files += 1
            ext_counter[ext] += 1

            lang = EXT_TO_LANG.get(ext, f"Other ({ext})" if ext else "No extension")
            lang_counter[lang] += 1

            if ext in CODE_EXTENSIONS:
                code_files += 1
                loc = count_loc(fp)
                total_loc += loc
                lang_loc[lang] += loc

    elapsed = time.time() - start

    # Language distribution
    lang_dist = []
    for lang, count in lang_counter.most_common():
        lang_dist.append({
            "language": lang,
            "file_count": count,
            "percentage": round(count / total_files * 100, 1),
            "loc": lang_loc.get(lang, 0),
        })

    # Directory structure
    dir_structure = analyze_directory_structure(REPO_PATH)

    # Framework detection
    framework = find_framework_patterns(REPO_PATH)

    # Test structure
    test_structure = detect_test_structure(REPO_PATH)

    # Migrations
    migrations = detect_migrations(REPO_PATH)

    # Apps
    apps = detect_apps(REPO_PATH)

    result = {
        "repo_path": str(REPO_PATH),
        "analysis_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "analysis_duration_seconds": round(elapsed, 2),
        "summary": {
            "total_files": total_files,
            "code_files": code_files,
            "total_code_loc": total_loc,
        },
        "language_distribution": lang_dist,
        "top_level_structure": dir_structure,
        "framework_patterns": framework,
        "test_structure": test_structure,
        "database_migrations": migrations,
        "app_architecture": apps,
    }

    output_path = Path(__file__).resolve().parent.parent / "rcir" / "repo_analysis.json"
    output_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(f"\nResults saved to: {output_path}")

    # Print summary
    print(f"\n{'='*60}")
    print(f"NEXTCLOUD REPOSITORY ANALYSIS")
    print(f"{'='*60}")
    print(f"Total files:     {total_files}")
    print(f"Code files:      {code_files}")
    print(f"Total code LOC:  {total_loc}")
    print(f"Analysis time:   {elapsed:.1f}s")
    print(f"\nLanguage Distribution (top 10):")
    for item in lang_dist[:10]:
        print(f"  {item['language']:20s}  {item['file_count']:6d} files  ({item['percentage']:5.1f}%)  {item['loc']:8d} LOC")
    print(f"\nApps found: {apps['app_count']}")
    print(f"Test files: {test_structure['total_test_files']}")
    print(f"Migration files: {migrations['migration_files_found']}")


if __name__ == "__main__":
    main()
