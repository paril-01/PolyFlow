"""
'polyflow run' Command.

Executes a .poly file with optional input payloads and environment contexts.
"""

import sys
import json
from pathlib import Path
from typing import Optional

from polyflow_sdk.core.interpreter import PolyInterpreter


def execute_run(file_path: str, payload_str: Optional[str] = None) -> int:
    path = Path(file_path)
    if not path.is_file():
        print(f"Error: File '{file_path}' does not exist.")
        return 1

    payload = {}
    if payload_str:
        try:
            payload = json.loads(payload_str)
        except Exception as e:
            print(f"Error parsing JSON payload: {e}")
            return 1

    print(f"\n[PolyFlow] Interpreting: {path.name}")
    interpreter = PolyInterpreter()

    try:
        res = interpreter.execute_file(path, payload=payload)
    except Exception as e:
        print(f"\n[FATAL] Interpreter error: {e}")
        return 1

    print(f"Contracts: {res['contracts_count']} | Schemas: {res['schemas_count']} | Cells: {res['cells_executed']}")
    print("-" * 60)

    for cell in res["results"]:
        status_sym = "✓" if cell["status"] == "success" else "✗"
        print(f"[{status_sym}] @{cell['language']}[{cell['tag']}] ({cell['execution_time_ms']:.1f}ms)")
        if cell["status"] == "success":
            print(f"    Output: {json.dumps(cell['output'], default=str)}")
        else:
            print(f"    Error:  {cell['error']}")

    print("-" * 60)
    print(f"Status: {res['status'].upper()}\n")
    return 0 if res["status"] == "success" else 1
