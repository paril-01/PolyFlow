"""
'polyflow doctor' Command — Modeled after Flutter Doctor.

Inspects host development environment, verifies all multi-language compilers,
runtimes, package managers, and RCIR engine readiness.
"""

import sys
import shutil
import subprocess
from typing import Dict, Any, List, Tuple


def _run_cmd(args: List[str]) -> Tuple[int, str]:
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=5)
        out = (proc.stdout.strip() or proc.stderr.strip()).splitlines()
        first_line = out[0] if out else "OK"
        return proc.returncode, first_line
    except Exception as e:
        return -1, str(e)


def check_toolchains() -> List[Dict[str, Any]]:
    checks = []

    # 1. Python
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    checks.append({
        "name": "Python Environment",
        "status": sys.version_info >= (3, 10),
        "version": f"Python {py_ver} ({sys.executable})",
        "details": "Required >= 3.10 for PolyFlow AST and pattern matching",
    })

    # 2. Node.js
    node_path = shutil.which("node")
    if node_path:
        code, out = _run_cmd([node_path, "-v"])
        checks.append({
            "name": "Node.js Runtime",
            "status": code == 0,
            "version": f"{out} ({node_path})",
            "details": "Executes JavaScript, TypeScript, and Vue frontend blocks",
        })
    else:
        checks.append({
            "name": "Node.js Runtime",
            "status": False,
            "version": "Not installed",
            "details": "Install Node.js from https://nodejs.org or via winget install OpenJS.NodeJS",
        })

    # 3. Java JDK
    javac_path = shutil.which("javac")
    java_path = shutil.which("java")
    if javac_path and java_path:
        code, out = _run_cmd([javac_path, "-version"])
        checks.append({
            "name": "Java Development Kit (JDK)",
            "status": code == 0,
            "version": f"{out} ({javac_path})",
            "details": "Compiles and executes JVM enterprise backend cells",
        })
    else:
        checks.append({
            "name": "Java Development Kit (JDK)",
            "status": False,
            "version": "Not installed",
            "details": "Install OpenJDK (e.g. Eclipse Adoptium Temurin 21)",
        })

    # 4. Go Compiler
    go_path = shutil.which("go")
    if go_path:
        code, out = _run_cmd([go_path, "version"])
        checks.append({
            "name": "Go Programming Language",
            "status": code == 0,
            "version": f"{out} ({go_path})",
            "details": "Compiles high-throughput microservices and gateway cells",
        })
    else:
        checks.append({
            "name": "Go Programming Language",
            "status": False,
            "version": "Not installed",
            "details": "Install Go from https://go.dev/dl/ or winget install GoLang.Go",
        })

    # 5. PHP Runtime
    php_path = shutil.which("php")
    if php_path:
        code, out = _run_cmd([php_path, "-v"])
        checks.append({
            "name": "PHP Host Engine",
            "status": code == 0,
            "version": f"{out} ({php_path})",
            "details": "Executes PHP backend cells and Nextcloud application services",
        })
    else:
        checks.append({
            "name": "PHP Host Engine",
            "status": False,
            "version": "Not installed",
            "details": "Install PHP 8.2+ via winget install PHP.PHP.8.3",
        })

    # 6. Git VCS
    git_path = shutil.which("git")
    if git_path:
        code, out = _run_cmd([git_path, "--version"])
        checks.append({
            "name": "Git Version Control",
            "status": code == 0,
            "version": f"{out} ({git_path})",
            "details": "Repository change impact and historical commit benchmarks",
        })
    else:
        checks.append({
            "name": "Git Version Control",
            "status": False,
            "version": "Not installed",
            "details": "Install Git from https://git-scm.com",
        })

    # 7. RCIR Dependency Engine
    from polyflow_sdk.core.rcir_bridge import RcirBridge
    if RcirBridge.is_available():
        rcir_ok = True
        rcir_msg = "v7 §10 Hardened Polyglot Engine Ready"
        rcir_desc = "Cross-language AST parsing, route extraction, and impact analysis"
    else:
        rcir_ok = True
        rcir_msg = "Standalone Mode (Built-in Static Extraction Active)"
        rcir_desc = "Standard static AST and symbol extraction without external rcir"

    checks.append({
        "name": "RCIR Dependency Engine",
        "status": rcir_ok,
        "version": rcir_msg,
        "details": rcir_desc,
    })

    return checks


def execute_doctor() -> int:
    """Print Flutter-style doctor report to terminal."""
    print("\n" + "=" * 65)
    print(" PolyFlow Doctor — Toolchain & Environment Diagnostics")
    print("=" * 65)

    checks = check_toolchains()
    python_ok = True

    for c in checks:
        icon = "[OK]" if c["status"] else "[! ]"
        status_word = "PASSED" if c["status"] else "OPTIONAL / NOT CONFIGURED"
        print(f"\n{icon} {c['name']} - {status_word}")
        print(f"    Version: {c['version']}")
        print(f"    Info:    {c['details']}")
        if c["name"].startswith("Python") and not c["status"]:
            python_ok = False

    print("\n" + "-" * 65)
    if python_ok:
        print(" [OK] Core PolyFlow runtime ready.\n")
        return 0
    else:
        print(" [!] Python runtime environment issues detected.\n")
        return 1
