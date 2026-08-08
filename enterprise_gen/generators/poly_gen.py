"""
PolyFlow .poly Governance File Generator.

Generates .poly files for every cross-service feature, encoding:
- @contract directives
- @schema definitions
- Multi-language code blocks with @link cross-references
- @merge strategies
- @error-map rules
- @rationale and @decision records
- @audit directives
"""

import random
from pathlib import Path
from typing import List, Dict
from enterprise_gen.config import (
    FEATURE_DOMAINS, CALL_CHAINS, SERVICES, ScaleConfig, DEVELOPERS
)


def _write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _snake_to_camel(s: str) -> str:
    return "".join(w.capitalize() for w in s.split("_"))


def _snake_to_title(s: str) -> str:
    return " ".join(w.capitalize() for w in s.split("_"))


CLASSIFICATIONS = ["public", "internal", "sensitive", "restricted"]
MERGE_STRATEGIES = ["first-success", "fallback", "all-success", "parallel-collect", "vote"]


def _gen_feature_poly(feat_id: str, domain_name: str, language: str, service: str, rng: random.Random) -> str:
    """Generate a .poly governance file for a single feature."""
    cls = domain_name.upper()
    fid = f"ECP-{cls}-{feat_id.upper().replace('_','-')[:20]}"
    classification = rng.choice(CLASSIFICATIONS)
    dev = rng.choice(DEVELOPERS)
    timeout = rng.choice([2000, 3000, 5000, 8000])
    merge = rng.choice(MERGE_STRATEGIES)

    # Build approvers list
    approvers = [dev["email"]]
    if classification in ("sensitive", "restricted"):
        approvers.append(rng.choice(DEVELOPERS)["email"])

    req_fields = _gen_schema_fields(feat_id, "request", rng)
    resp_fields = _gen_schema_fields(feat_id, "response", rng)

    # Build allowed imports based on language
    imports_map = {
        "python": '["json", "time", "uuid", "hashlib", "logging", "typing"]',
        "java": '["java.util", "java.time", "org.springframework", "javax.persistence"]',
        "go": '["fmt", "net/http", "encoding/json", "time", "github.com/google/uuid"]',
        "javascript": '["express", "uuid", "winston", "bull", "nodemailer"]',
        "typescript": '["react", "axios", "@tanstack/react-query"]',
    }
    allowed = imports_map.get(language, '["json"]')

    # Primary language block
    code_block = _gen_code_block(feat_id, domain_name, language)

    # Error map
    error_entries = _gen_error_map(feat_id, language, rng)

    poly = f"""# {_snake_to_title(feat_id)} — PolyFlow Governance Module
# Service: {service} | Language: {language} | Domain: {domain_name}

@contract
feature_id: "{fid}"
owner: "{dev['name']} <{dev['email']}>"
team: "{dev['team']}"
classification: "{classification}"
approvers: [{', '.join(f'"{a}"' for a in approvers)}]
retention_years: 7
timeout_ms: {timeout}
@end

@schema {_snake_to_camel(feat_id)}Request
{req_fields}
@end

@schema {_snake_to_camel(feat_id)}Response
{resp_fields}
@end

@standard language="{language}"
allowed_imports: {allowed}
@end

@{language}[service]
{code_block}
@end

@merge strategy="{merge}" order=["{language}"]
@end

@error-map language="{language}"
{error_entries}
@end

@rationale for="{feat_id}"
reason: "Selected {language} for {_snake_to_title(feat_id)} due to ecosystem maturity and team expertise."
alternatives_considered: ["rust", "elixir"]
rejected_reasons: {{"rust": "Team lacks Rust experience", "elixir": "Insufficient library support"}}
@end

@decision for="{feat_id}"
decision: "Implement as microservice endpoint on {service}"
date: "2024-06-15"
status: "accepted"
stakeholders: ["{dev['name']}"]
@end

@audit
action: "Log {_snake_to_title(feat_id)} execution"
fields: ["status", "trace_id", "processing_time_ms"]
retention: "7_years"
compliance: ["SOC2", "PCI-DSS"]
@end
"""
    return poly


def _gen_schema_fields(feat_id: str, kind: str, rng: random.Random) -> str:
    """Generate realistic schema fields."""
    common_req = [
        '  id: string<format:uuid>',
        '  timestamp: string<format:datetime>',
    ]
    common_resp = [
        '  id: string<format:uuid>',
        '  status: string',
        '  processing_time_ms: number',
    ]
    domain_fields = {
        "order": ['  items: array<OrderItem>', '  total: number<min:0>'],
        "payment": ['  amount: number<min:0>', '  currency: string<len:3>'],
        "inventory": ['  sku: string', '  quantity: integer<min:0>'],
        "price": ['  base_price: number<min:0>', '  discount: number'],
        "auth": ['  username: string<format:email>', '  token: string'],
        "notification": ['  channel: string', '  recipient: string'],
    }

    # Match domain
    extra = []
    for key, fields in domain_fields.items():
        if key in feat_id:
            extra = fields
            break

    if kind == "request":
        return "\n".join(common_req + extra + ['  metadata: object | null'])
    else:
        return "\n".join(common_resp + ['  result: object | null', '  errors: array<string>'])


def _gen_code_block(feat_id: str, domain: str, language: str) -> str:
    """Generate the primary code block for the .poly file."""
    fn = feat_id
    cls = _snake_to_camel(feat_id)

    if language == "python":
        return f'''import time
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)

def process(req):
    """Execute {_snake_to_title(feat_id)}."""
    start = time.time()
    trace_id = str(uuid4())[:8]
    logger.info(f"[{{trace_id}}] Processing {fn}")

    result = {{
        "feature": "{fn}",
        "domain": "{domain}",
        "processed": True,
        "input_keys": list(req.keys()) if isinstance(req, dict) else [],
    }}

    elapsed = (time.time() - start) * 1000
    return {{
        "status": "success",
        "trace_id": trace_id,
        "result": result,
        "processing_time_ms": round(elapsed, 2),
    }}'''

    elif language == "go":
        return f'''package main

import (
    "encoding/json"
    "fmt"
    "time"
)

func process(req map[string]interface{{}}) map[string]interface{{}} {{
    start := time.Now()
    result := map[string]interface{{}}{{
        "feature":   "{fn}",
        "domain":    "{domain}",
        "processed": true,
    }}
    elapsed := time.Since(start).Milliseconds()
    return map[string]interface{{}}{{
        "status":          "success",
        "result":          result,
        "processing_ms":   elapsed,
    }}
}}'''

    elif language == "java":
        return f'''package com.ecp.service;

import java.util.*;

public class {cls}Processor {{
    public Map<String, Object> process(Map<String, Object> req) {{
        long start = System.currentTimeMillis();
        Map<String, Object> result = Map.of(
            "feature", "{fn}",
            "domain", "{domain}",
            "processed", true
        );
        long elapsed = System.currentTimeMillis() - start;
        return Map.of(
            "status", "success",
            "result", result,
            "processing_time_ms", elapsed
        );
    }}
}}'''

    elif language == "javascript":
        return f'''const {{ v4: uuidv4 }} = require('uuid');

async function process(req) {{
  const start = Date.now();
  const traceId = uuidv4().slice(0, 8);

  const result = {{
    feature: '{fn}',
    domain: '{domain}',
    processed: true,
    input_keys: Object.keys(req || {{}}),
  }};

  return {{
    status: 'success',
    trace_id: traceId,
    result,
    processing_time_ms: Date.now() - start,
  }};
}}

module.exports = {{ process }};'''

    elif language == "typescript":
        return f'''import React, {{ useState }} from 'react';

interface {cls}Props {{
  onComplete?: (data: any) => void;
}}

export const {cls}: React.FC<{cls}Props> = ({{ onComplete }}) => {{
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {{
    setLoading(true);
    try {{
      const res = await fetch('/api/v1/{domain}/{fn.replace("_", "-")}', {{ method: 'POST' }});
      const data = await res.json();
      onComplete?.(data);
    }} finally {{
      setLoading(false);
    }}
  }};

  return (
    <button onClick={{handleClick}} disabled={{loading}}>
      {{loading ? 'Processing...' : '{_snake_to_title(feat_id)}'}}
    </button>
  );
}};'''

    return f"// {_snake_to_title(feat_id)} implementation"


def _gen_error_map(feat_id: str, language: str, rng: random.Random) -> str:
    maps = {
        "python": f'  "ValueError" -> "Invalid input provided to {feat_id}. Check request parameters."\n  "TimeoutError" -> "Operation {feat_id} timed out. Service may be under heavy load."\n  "ConnectionError" -> "Unable to reach downstream service. Check network connectivity."',
        "java": f'  "NullPointerException" -> "Required field is missing in {feat_id} request."\n  "IllegalArgumentException" -> "Invalid argument passed to {feat_id}."\n  "TimeoutException" -> "Operation {feat_id} timed out."',
        "go": f'  "context.DeadlineExceeded" -> "Request to {feat_id} timed out."\n  "sql.ErrNoRows" -> "Resource not found for {feat_id}."\n  "io.EOF" -> "Unexpected end of input in {feat_id}."',
        "javascript": f'  "TypeError" -> "Type mismatch in {feat_id} payload."\n  "ECONNREFUSED" -> "Downstream service unreachable from {feat_id}."',
        "typescript": f'  "TypeError" -> "Type mismatch in {feat_id} component."\n  "NetworkError" -> "API call failed for {feat_id}."',
    }
    return maps.get(language, f'  "Error" -> "Unknown error in {feat_id}."')


# --- Cross-Service Call Chain .poly Generator --------------------------------

def _gen_call_chain_poly(chain: Dict, rng: random.Random) -> str:
    """Generate a .poly file for a cross-service call chain."""
    name = chain["name"]
    desc = chain["description"]
    steps = chain["steps"]
    dev = rng.choice(DEVELOPERS)

    # Build @link directives
    links = []
    for step in steps:
        links.append(f'@link {step["service"]}::{step["action"]} as {step["action"]}')

    # Build language blocks for each step
    blocks = []
    for i, step in enumerate(steps):
        lang = step["language"]
        if lang == "typescript":
            lang = "typescript"
        blocks.append(f"""@{lang}[step_{i}_{step['action']}]
# Step {i+1}: {step['service']} -> {step['action']}
# Language: {step['language']}
# This is step {i+1} of {len(steps)} in the {_snake_to_title(name)} call chain.
def process(req):
    return {{"step": {i+1}, "service": "{step['service']}", "action": "{step['action']}", "status": "completed"}}
@end""")

    poly = f"""# Cross-Service Call Chain: {_snake_to_title(name)}
# {desc}
# Chain Length: {len(steps)} services, {len(set(s['language'] for s in steps))} languages

@contract
feature_id: "ECP-CHAIN-{name.upper().replace('_','-')}"
owner: "{dev['name']} <{dev['email']}>"
team: "platform"
classification: "internal"
approvers: ["{dev['email']}"]
retention_years: 7
timeout_ms: 15000
@end

{chr(10).join(links)}

{chr(10).join(blocks)}

@merge strategy="all-success" order=[{', '.join(f'"{s["language"]}"' for s in steps)}]
@end

@rationale for="{name}"
reason: "This call chain crosses {len(set(s['language'] for s in steps))} language boundaries. Each step is isolated in its own process cell for fault tolerance."
@end

@decision for="{name}"
decision: "Route through API Gateway for centralized auth and rate limiting"
date: "2024-03-20"
status: "accepted"
@end

@audit
action: "Trace full call chain execution for {_snake_to_title(name)}"
fields: ["chain_id", "total_steps", "total_latency_ms", "failed_steps"]
retention: "7_years"
compliance: ["SOC2"]
@end
"""
    return poly


# --- Main Generator ----------------------------------------------------------

def generate_poly_governance(output_dir: Path, scale: ScaleConfig, rng: random.Random):
    """Generate all .poly governance files."""
    gov_dir = output_dir / "polyflow-governance"
    total = 0

    # Generate feature-level .poly files
    for domain in FEATURE_DOMAINS:
        feature_count = max(1, int(len(domain.features) * scale.feature_multiplier))
        selected = domain.features[:feature_count]

        for feat_id in selected:
            poly_content = _gen_feature_poly(
                feat_id, domain.name, domain.language, domain.service, rng
            )
            _write(gov_dir / domain.poly_prefix / f"{feat_id}.poly", poly_content)
            total += 1

    # Generate cross-service call chain .poly files
    for chain in CALL_CHAINS:
        poly_content = _gen_call_chain_poly(chain, rng)
        _write(gov_dir / "cross-service" / f"{chain['name']}.poly", poly_content)
        total += 1

    print(f"  [OK] Generated {total} .poly governance files")
    return total
