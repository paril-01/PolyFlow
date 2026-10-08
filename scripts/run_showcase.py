#!/usr/bin/env python3
"""
scripts/run_showcase.py — Launcher for PolyFlow Evidence & Showcase Server.
"""

import sys
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

def main():
    print("=" * 80)
    print("STARTING POLYFLOW EVIDENCE & SHOWCASE SERVER")
    print("=" * 80)
    print("Host: 127.0.0.1 | Port: 8000")
    print("Open your browser at: http://127.0.0.1:8000")
    print("Press Ctrl+C to terminate server.")
    print("=" * 80)

    try:
        import uvicorn
        uvicorn.run("showcase_app.backend.app:app", host="127.0.0.1", port=8000, reload=True, app_dir=str(REPO_ROOT))
    except KeyboardInterrupt:
        print("\nServer terminated cleanly.")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
