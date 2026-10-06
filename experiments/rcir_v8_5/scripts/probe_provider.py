#!/usr/bin/env python3
"""
RCIR v8.5 — Live Agent Provider Capability Probe (PHASE 71).

Probes the local or configured LLM provider endpoint:
1. Verifies endpoint connectivity.
2. Enumerates installed models (discovers qwen2.5-coder:1.5b, etc.).
3. Executes a live test inference ("Return exactly: READY").
4. Records exact latency, model digest, and parameter count.
5. Emits raw/agent/provider_probe.json.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

# Add project roots
SCRIPT_DIR = Path(__file__).resolve().parent
RCIR_V8_5_ROOT = SCRIPT_DIR.parent
POLYFLOW_ROOT = RCIR_V8_5_ROOT.parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from environment import get_default_environment


class ProviderCapabilityProbe:
    """Probes provider endpoint with actual live inference request."""

    def __init__(
        self,
        endpoint: str = "http://127.0.0.1:11434",
        preferred_model: str = "qwen2.5-coder:1.5b",
        timeout: float = 15.0,
    ):
        self.endpoint = endpoint.rstrip("/")
        self.preferred_model = os.environ.get("OLLAMA_MODEL", preferred_model)
        self.timeout = timeout

    def probe(self) -> dict[str, Any]:
        t0 = time.time()
        probe_prompt = "Return exactly: READY"
        prompt_hash = hashlib.sha256(probe_prompt.encode("utf-8")).hexdigest()

        result: dict[str, Any] = {
            "provider": "ollama",
            "endpoint": self.endpoint,
            "configured_model": self.preferred_model,
            "endpoint_reachable": False,
            "models_available": [],
            "selected_model": None,
            "model_present": False,
            "inference_success": False,
            "probe_prompt": probe_prompt,
            "prompt_hash": prompt_hash,
            "response_content": None,
            "latency_seconds": None,
            "model_digest": None,
            "parameter_size": None,
            "status": "NOT_AVAILABLE",
        }

        # 1. Check endpoint reachable and enumerate models
        try:
            tags_url = f"{self.endpoint}/api/tags"
            req = urllib.request.Request(tags_url, headers={"User-Agent": "RCIR-Probe/8.5"})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                result["endpoint_reachable"] = True
                models = [m.get("name", "") for m in data.get("models", [])]
                result["models_available"] = models

                # Model selection logic (PHASE 71): probe available models
                if self.preferred_model in models:
                    selected = self.preferred_model
                elif any("qwen2.5-coder" in m for m in models):
                    selected = next(m for m in models if "qwen2.5-coder" in m)
                elif models:
                    selected = models[0]
                else:
                    selected = None

                result["selected_model"] = selected
                result["model_present"] = selected is not None

                # Extract model details
                for m in data.get("models", []):
                    if m.get("name") == selected:
                        result["model_digest"] = m.get("digest")
                        result["parameter_size"] = m.get("details", {}).get("parameter_size")
                        break

        except Exception as e:
            result["error"] = f"Endpoint reachability check failed: {e}"
            result["latency_seconds"] = round(time.time() - t0, 3)
            return result

        if not result["model_present"]:
            result["error"] = f"No compatible model found on {self.endpoint}. Available: {result['models_available']}"
            result["latency_seconds"] = round(time.time() - t0, 3)
            return result

        # 2. Execute live test inference request
        try:
            gen_url = f"{self.endpoint}/api/generate"
            payload = json.dumps({
                "model": result["selected_model"],
                "prompt": probe_prompt,
                "stream": False,
            }).encode("utf-8")

            t_req0 = time.time()
            req = urllib.request.Request(
                gen_url,
                data=payload,
                headers={"Content-Type": "application/json", "User-Agent": "RCIR-Probe/8.5"},
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                gen_data = json.loads(resp.read().decode("utf-8"))
                latency = time.time() - t_req0
                content = gen_data.get("response", "").strip()

                result["response_content"] = content
                result["latency_seconds"] = round(latency, 3)
                result["inference_success"] = len(content) > 0

                if result["inference_success"]:
                    result["status"] = "LIVE_VERIFIED"
                else:
                    result["status"] = "EMPTY_RESPONSE"

        except Exception as e:
            result["error"] = f"Inference execution failed: {e}"
            result["status"] = "INFERENCE_FAILED"
            result["latency_seconds"] = round(time.time() - t0, 3)

        return result


def main():
    print("=" * 80)
    print("RCIR v8.5 — Provider Capability Probe (PHASE 71)")
    print("=" * 80)

    env = get_default_environment()
    raw_agent_dir = env.raw_root / "agent"
    raw_agent_dir.mkdir(parents=True, exist_ok=True)

    probe = ProviderCapabilityProbe()
    probe_result = probe.probe()

    out_file = raw_agent_dir / "provider_probe.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(probe_result, f, indent=2)

    print(f"Status: {probe_result['status']}")
    print(f"Selected Model: {probe_result['selected_model']} ({probe_result['parameter_size']})")
    print(f"Inference Success: {probe_result['inference_success']} (Latency: {probe_result['latency_seconds']}s)")
    print(f"Saved probe report to: {out_file}")


if __name__ == "__main__":
    main()
