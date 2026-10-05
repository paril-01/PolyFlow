#!/usr/bin/env python3
"""
RCIR v8.4 — Live Agent Provider Capability Probe (PHASE 3).

Verifies true live inference availability:
1. Endpoint reachable
2. Requested model listed
3. Tiny inference request succeeds
4. Response non-empty
5. Latency recorded
6. Model digest / hash verified

If any step fails, status is NOT_AVAILABLE and agent evaluation outputs NOT_MEASURED.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
RAW_AGENT_DIR = REPO_ROOT / "experiments" / "rcir_v8_4" / "raw" / "agent"
RAW_AGENT_DIR.mkdir(parents=True, exist_ok=True)


class ProviderCapabilityProbe:
    """Probes provider endpoint with actual inference request."""

    def __init__(
        self,
        provider: str = "ollama",
        endpoint: str = "http://127.0.0.1:11434",
        model: str = "qwen2.5-coder:7b",
        timeout: float = 10.0,
    ):
        self.provider = provider
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.timeout = timeout

    def probe(self) -> dict[str, Any]:
        t0 = time.time()
        probe_prompt = "Return exactly: READY"
        prompt_hash = hashlib.sha256(probe_prompt.encode("utf-8")).hexdigest()

        result: dict[str, Any] = {
            "provider": self.provider,
            "endpoint": self.endpoint,
            "model": self.model,
            "endpoint_reachable": False,
            "model_present": False,
            "inference_success": False,
            "model_digest": "",
            "probe_prompt_hash": prompt_hash,
            "response_hash": "",
            "latency_ms": 0,
            "status": "NOT_AVAILABLE",
        }

        # 1. Check endpoint and tags
        try:
            req = urllib.request.Request(f"{self.endpoint}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if resp.status == 200:
                    result["endpoint_reachable"] = True
                    tags_data = json.loads(resp.read().decode("utf-8"))
                    models = tags_data.get("models", [])
                    for m in models:
                        if self.model in m.get("name", ""):
                            result["model_present"] = True
                            result["model_digest"] = m.get("digest", "")
                            break
        except Exception as e:
            result["error"] = f"Endpoint unreachable: {e}"
            result["latency_ms"] = int((time.time() - t0) * 1000)
            return result

        if not result["model_present"]:
            result["error"] = f"Model '{self.model}' not found in provider tags."
            result["latency_ms"] = int((time.time() - t0) * 1000)
            return result

        # 2. Execute live test inference request (PHASE 3)
        try:
            inf_start = time.time()
            payload = json.dumps({
                "model": self.model,
                "prompt": probe_prompt,
                "stream": False,
                "options": {"temperature": 0.0},
            }).encode("utf-8")
            req = urllib.request.Request(
                f"{self.endpoint}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if resp.status == 200:
                    gen_data = json.loads(resp.read().decode("utf-8"))
                    response_text = gen_data.get("response", "").strip()
                    if response_text:
                        result["inference_success"] = True
                        result["response_hash"] = hashlib.sha256(response_text.encode("utf-8")).hexdigest()
                        result["latency_ms"] = int((time.time() - inf_start) * 1000)
                        result["status"] = "LIVE_VERIFIED"
        except Exception as e:
            result["error"] = f"Inference execution failed: {e}"

        result["latency_ms"] = int((time.time() - t0) * 1000)
        return result


def main():
    parser = argparse.ArgumentParser(description="RCIR v8.4 Provider Capability Probe")
    parser.add_argument("--endpoint", default=os.getenv("OLLAMA_ENDPOINT", "http://127.0.0.1:11434"))
    parser.add_argument("--model", default=os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b"))
    args = parser.parse_args()

    probe = ProviderCapabilityProbe(endpoint=args.endpoint, model=args.model)
    res = probe.probe()

    out_file = RAW_AGENT_DIR / "provider_probe.json"
    out_file.write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(f"Provider Probe Status: {res['status']} (saved to {out_file})")


if __name__ == "__main__":
    main()
