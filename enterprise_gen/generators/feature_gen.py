"""
Feature Code Generator.

Generates realistic feature implementations for each service:
- API endpoints / handlers / routes
- Service layer business logic
- Data models / structs / classes
- Repository / database queries
- Unit tests
"""

import os
import random
import hashlib
from pathlib import Path
from typing import List, Dict
from enterprise_gen.config import (
    FEATURE_DOMAINS, FeatureDomain, SERVICES, ServiceDef, ScaleConfig
)


def _write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _snake_to_camel(s: str) -> str:
    return "".join(w.capitalize() for w in s.split("_"))


def _snake_to_title(s: str) -> str:
    return " ".join(w.capitalize() for w in s.split("_"))


# --- Python Feature Templates ------------------------------------------------

def _python_model(feature_id: str, domain: str) -> str:
    cls = _snake_to_camel(feature_id)
    return f'''"""Data model for {_snake_to_title(feature_id)}."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4


class {cls}Request(BaseModel):
    """Input request model for {_snake_to_title(feature_id)}."""
    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: dict = Field(default_factory=dict)
    metadata: Optional[dict] = None


class {cls}Response(BaseModel):
    """Output response model for {_snake_to_title(feature_id)}."""
    id: UUID
    status: str = "success"
    result: Optional[dict] = None
    processing_time_ms: float = 0.0
    errors: List[str] = Field(default_factory=list)
'''


def _python_service(feature_id: str, domain: str) -> str:
    cls = _snake_to_camel(feature_id)
    fn = feature_id
    return f'''"""{_snake_to_title(feature_id)} — Business Logic Service."""
import time
import logging
from typing import Dict, Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class {cls}Service:
    """Service class implementing {_snake_to_title(feature_id)} business logic."""

    def __init__(self, db_session=None, config: Optional[Dict] = None):
        self.db = db_session
        self.config = config or {{}}
        self._cache = {{}}

    def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the {_snake_to_title(feature_id)} operation."""
        start = time.time()
        trace_id = str(uuid4())[:8]
        logger.info(f"[{{trace_id}}] Executing {fn}")

        try:
            result = self._process(request)
            elapsed = (time.time() - start) * 1000
            logger.info(f"[{{trace_id}}] {fn} completed in {{elapsed:.1f}}ms")
            return {{
                "status": "success",
                "trace_id": trace_id,
                "result": result,
                "processing_time_ms": round(elapsed, 2),
            }}
        except Exception as e:
            logger.error(f"[{{trace_id}}] {fn} failed: {{e}}")
            return {{"status": "error", "trace_id": trace_id, "error": str(e)}}

    def _process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Core processing logic for {_snake_to_title(feature_id)}."""
        # Domain-specific processing
        return {{
            "feature": "{fn}",
            "domain": "{domain}",
            "processed": True,
            "input_keys": list(request.keys()),
        }}
'''


def _python_route(feature_id: str, domain: str) -> str:
    fn = feature_id
    cls = _snake_to_camel(feature_id)
    return f'''"""{_snake_to_title(feature_id)} — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/{domain}", tags=["{domain}"])


@router.post("/{fn.replace('_', '-')}")
async def {fn}_endpoint(request: Dict[str, Any] = {{}}) -> Dict[str, Any]:
    """API endpoint for {_snake_to_title(feature_id)}."""
    from app.services.{fn} import {cls}Service
    svc = {cls}Service()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/{fn.replace('_', '-')}/status")
async def {fn}_status() -> Dict[str, Any]:
    """Health check for {_snake_to_title(feature_id)}."""
    return {{"feature": "{fn}", "status": "operational"}}
'''


def _python_test(feature_id: str, domain: str) -> str:
    cls = _snake_to_camel(feature_id)
    fn = feature_id
    return f'''"""Tests for {_snake_to_title(feature_id)}."""
import pytest
from app.services.{fn} import {cls}Service


class Test{cls}Service:
    """Test suite for {cls}Service."""

    def setup_method(self):
        self.service = {cls}Service()

    def test_execute_success(self):
        result = self.service.execute({{"test_key": "test_value"}})
        assert result["status"] == "success"
        assert "trace_id" in result

    def test_execute_with_empty_request(self):
        result = self.service.execute({{}})
        assert result["status"] == "success"

    def test_process_returns_domain(self):
        result = self.service._process({{"key": "value"}})
        assert result["domain"] == "{domain}"
        assert result["feature"] == "{fn}"
'''


# --- Go Feature Templates ----------------------------------------------------

def _go_handler(feature_id: str, domain: str) -> str:
    fn_camel = _snake_to_camel(feature_id)
    return f'''package handler

import (
\t"encoding/json"
\t"net/http"
\t"time"
\t"github.com/google/uuid"
\t"github.com/rs/zerolog/log"
)

// {fn_camel}Handler handles {_snake_to_title(feature_id)} requests.
type {fn_camel}Handler struct {{
\t// Dependencies injected here
}}

// New{fn_camel}Handler creates a new handler instance.
func New{fn_camel}Handler() *{fn_camel}Handler {{
\treturn &{fn_camel}Handler{{}}
}}

// Handle processes {_snake_to_title(feature_id)} requests.
func (h *{fn_camel}Handler) Handle(w http.ResponseWriter, r *http.Request) {{
\tstart := time.Now()
\ttraceID := uuid.New().String()[:8]
\tlog.Info().Str("trace_id", traceID).Msg("Processing {feature_id}")

\tvar req map[string]interface{{}}
\tif err := json.NewDecoder(r.Body).Decode(&req); err != nil {{
\t\thttp.Error(w, `{{"error":"invalid request"}}`, http.StatusBadRequest)
\t\treturn
\t}}

\tresult := h.process(req)
\telapsed := time.Since(start).Milliseconds()

\tresp := map[string]interface{{}}{{
\t\t"status":           "success",
\t\t"trace_id":         traceID,
\t\t"result":           result,
\t\t"processing_ms":    elapsed,
\t}}

\tw.Header().Set("Content-Type", "application/json")
\tjson.NewEncoder(w).Encode(resp)
}}

func (h *{fn_camel}Handler) process(req map[string]interface{{}}) map[string]interface{{}} {{
\treturn map[string]interface{{}}{{
\t\t"feature": "{feature_id}",
\t\t"domain":  "{domain}",
\t\t"processed": true,
\t}}
}}
'''


def _go_model(feature_id: str, domain: str) -> str:
    fn_camel = _snake_to_camel(feature_id)
    return f'''package model

import (
\t"time"
\t"github.com/google/uuid"
)

// {fn_camel} represents the data model for {_snake_to_title(feature_id)}.
type {fn_camel} struct {{
\tID        uuid.UUID              `json:"id" db:"id"`
\tStatus    string                 `json:"status" db:"status"`
\tPayload   map[string]interface{{}} `json:"payload"`
\tCreatedAt time.Time              `json:"created_at" db:"created_at"`
\tUpdatedAt time.Time              `json:"updated_at" db:"updated_at"`
}}
'''


def _go_test(feature_id: str, domain: str) -> str:
    fn_camel = _snake_to_camel(feature_id)
    return f'''package handler

import (
\t"bytes"
\t"encoding/json"
\t"net/http"
\t"net/http/httptest"
\t"testing"
\t"github.com/stretchr/testify/assert"
)

func TestNew{fn_camel}Handler(t *testing.T) {{
\th := New{fn_camel}Handler()
\tassert.NotNil(t, h)
}}

func Test{fn_camel}Handle(t *testing.T) {{
\th := New{fn_camel}Handler()
\tbody, _ := json.Marshal(map[string]interface{{}}{{"test": true}})
\treq := httptest.NewRequest(http.MethodPost, "/{feature_id}", bytes.NewBuffer(body))
\trec := httptest.NewRecorder()
\th.Handle(rec, req)
\tassert.Equal(t, http.StatusOK, rec.Code)
}}
'''


# --- Java Feature Templates --------------------------------------------------

def _java_controller(feature_id: str, domain: str, svc_name: str) -> str:
    cls = _snake_to_camel(feature_id)
    pkg = svc_name.replace("-", "")
    return f'''package com.ecp.{pkg}.controller;

import com.ecp.{pkg}.service.{cls}Service;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/{domain}")
public class {cls}Controller {{

    private final {cls}Service service;

    public {cls}Controller({cls}Service service) {{
        this.service = service;
    }}

    @PostMapping("/{feature_id.replace("_", "-")}")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {{
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }}

    @GetMapping("/{feature_id.replace("_", "-")}/status")
    public ResponseEntity<Map<String, Object>> status() {{
        return ResponseEntity.ok(Map.of("feature", "{feature_id}", "status", "operational"));
    }}
}}
'''


def _java_service(feature_id: str, domain: str, svc_name: str) -> str:
    cls = _snake_to_camel(feature_id)
    pkg = svc_name.replace("-", "")
    return f'''package com.ecp.{pkg}.service;

import org.springframework.stereotype.Service;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.util.*;

@Service
public class {cls}Service {{

    private static final Logger log = LoggerFactory.getLogger({cls}Service.class);

    public Map<String, Object> execute(Map<String, Object> request) {{
        long start = System.currentTimeMillis();
        String traceId = UUID.randomUUID().toString().substring(0, 8);
        log.info("[{{}}] Executing {feature_id}", traceId);

        try {{
            Map<String, Object> result = process(request);
            long elapsed = System.currentTimeMillis() - start;
            return Map.of(
                "status", "success",
                "trace_id", traceId,
                "result", result,
                "processing_time_ms", elapsed
            );
        }} catch (Exception e) {{
            log.error("[{{}}] {feature_id} failed: {{}}", traceId, e.getMessage());
            return Map.of("status", "error", "trace_id", traceId, "error", e.getMessage());
        }}
    }}

    private Map<String, Object> process(Map<String, Object> request) {{
        return Map.of(
            "feature", "{feature_id}",
            "domain", "{domain}",
            "processed", true
        );
    }}
}}
'''


def _java_model(feature_id: str, domain: str, svc_name: str) -> str:
    cls = _snake_to_camel(feature_id)
    pkg = svc_name.replace("-", "")
    return f'''package com.ecp.{pkg}.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "{feature_id}")
public class {cls} {{

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false)
    private String status = "PENDING";

    @Column(columnDefinition = "jsonb")
    private String payload;

    private LocalDateTime createdAt = LocalDateTime.now();
    private LocalDateTime updatedAt = LocalDateTime.now();

    // Getters and setters
    public UUID getId() {{ return id; }}
    public void setId(UUID id) {{ this.id = id; }}
    public String getStatus() {{ return status; }}
    public void setStatus(String status) {{ this.status = status; }}
    public String getPayload() {{ return payload; }}
    public void setPayload(String payload) {{ this.payload = payload; }}
    public LocalDateTime getCreatedAt() {{ return createdAt; }}
    public LocalDateTime getUpdatedAt() {{ return updatedAt; }}
}}
'''


def _java_test(feature_id: str, domain: str, svc_name: str) -> str:
    cls = _snake_to_camel(feature_id)
    pkg = svc_name.replace("-", "")
    return f'''package com.ecp.{pkg}.service;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import static org.junit.jupiter.api.Assertions.*;
import java.util.Map;

class {cls}ServiceTest {{

    private {cls}Service service;

    @BeforeEach
    void setUp() {{
        service = new {cls}Service();
    }}

    @Test
    void testExecuteSuccess() {{
        Map<String, Object> result = service.execute(Map.of("test", "value"));
        assertEquals("success", result.get("status"));
        assertNotNull(result.get("trace_id"));
    }}

    @Test
    void testExecuteEmptyRequest() {{
        Map<String, Object> result = service.execute(Map.of());
        assertEquals("success", result.get("status"));
    }}
}}
'''


# --- JavaScript/Node Feature Templates ---------------------------------------

def _node_route(feature_id: str, domain: str) -> str:
    fn = feature_id
    return f'''const express = require('express');
const {{ v4: uuidv4 }} = require('uuid');
const logger = require('../utils/logger');

const router = express.Router();

/**
 * POST /{domain}/{fn.replace('_', '-')}
 * {_snake_to_title(feature_id)}
 */
router.post('/{fn.replace("_", "-")}', async (req, res) => {{
  const start = Date.now();
  const traceId = uuidv4().slice(0, 8);
  logger.info(`[${{traceId}}] Processing {fn}`);

  try {{
    const result = await process{_snake_to_camel(fn)}(req.body);
    const elapsed = Date.now() - start;
    res.json({{
      status: 'success',
      trace_id: traceId,
      result,
      processing_time_ms: elapsed,
    }});
  }} catch (err) {{
    logger.error(`[${{traceId}}] {fn} failed: ${{err.message}}`);
    res.status(500).json({{ status: 'error', error: err.message }});
  }}
}});

async function process{_snake_to_camel(fn)}(payload) {{
  return {{
    feature: '{fn}',
    domain: '{domain}',
    processed: true,
    input_keys: Object.keys(payload || {{}}),
  }};
}}

module.exports = router;
'''


def _node_test(feature_id: str, domain: str) -> str:
    fn = feature_id
    return f'''const request = require('supertest');
const express = require('express');
const router = require('../routes/{fn}');

const app = express();
app.use(express.json());
app.use('/{domain}', router);

describe('{_snake_to_title(feature_id)}', () => {{
  test('POST /{domain}/{fn.replace("_","-")} returns success', async () => {{
    const res = await request(app)
      .post('/{domain}/{fn.replace("_","-")}')
      .send({{ test: true }});
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('success');
  }});
}});
'''


# --- TypeScript (React/Angular) Feature Templates ----------------------------

def _react_component(feature_id: str, domain: str) -> str:
    comp = _snake_to_camel(feature_id)
    return f'''import React, {{ useState, useEffect }} from 'react';
import {{ api }} from '../services/api';

interface {comp}Props {{
  onComplete?: (data: any) => void;
}}

export const {comp}: React.FC<{comp}Props> = ({{ onComplete }}) => {{
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handle{comp} = async () => {{
    setLoading(true);
    setError(null);
    try {{
      const response = await api.post('/{domain}/{feature_id.replace("_", "-")}');
      setData(response.data);
      onComplete?.(response.data);
    }} catch (err: any) {{
      setError(err.message);
    }} finally {{
      setLoading(false);
    }}
  }};

  return (
    <div className="p-4 bg-white rounded-lg shadow-sm border">
      <h3 className="text-lg font-semibold text-gray-800">{_snake_to_title(feature_id)}</h3>
      <button
        onClick={{handle{comp}}}
        disabled={{loading}}
        className="mt-3 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
      >
        {{loading ? 'Processing...' : 'Execute'}}
      </button>
      {{error && <p className="mt-2 text-red-500 text-sm">{{error}}</p>}}
      {{data && <pre className="mt-2 p-2 bg-gray-50 rounded text-xs">{{JSON.stringify(data, null, 2)}}</pre>}}
    </div>
  );
}};

export default {comp};
'''


def _angular_component(feature_id: str, domain: str) -> str:
    comp = _snake_to_camel(feature_id)
    selector = feature_id.replace("_", "-")
    return f'''import {{ Component }} from '@angular/core';
import {{ HttpClient }} from '@angular/common/http';

@Component({{
  selector: 'app-{selector}',
  template: `
    <div class="p-4 bg-white rounded shadow-sm border">
      <h3 class="text-lg font-semibold">{_snake_to_title(feature_id)}</h3>
      <button (click)="execute()" [disabled]="loading"
              class="mt-3 px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700">
        {{{{ loading ? 'Processing...' : 'Execute' }}}}
      </button>
      <div *ngIf="error" class="mt-2 text-red-500">{{{{ error }}}}</div>
      <pre *ngIf="result" class="mt-2 p-2 bg-gray-50 rounded text-xs">{{{{ result | json }}}}</pre>
    </div>
  `
}})
export class {comp}Component {{
  loading = false;
  result: any = null;
  error: string | null = null;

  constructor(private http: HttpClient) {{}}

  execute() {{
    this.loading = true;
    this.error = null;
    this.http.post('/api/v1/{domain}/{selector}', {{}}).subscribe({{
      next: (data) => {{ this.result = data; this.loading = false; }},
      error: (err) => {{ this.error = err.message; this.loading = false; }},
    }});
  }}
}}
'''


# --- Main Feature Generator --------------------------------------------------

def generate_features(output_dir: Path, scale: ScaleConfig, rng: random.Random):
    """Generate feature implementations across all services."""
    total_features = 0
    total_files = 0
    total_tests = 0

    for domain in FEATURE_DOMAINS:
        # Scale features
        feature_count = max(1, int(len(domain.features) * scale.feature_multiplier))
        selected = domain.features[:feature_count]

        svc = _find_service(domain.service)

        for feat_id in selected:
            files, tests = _generate_single_feature(output_dir, domain, feat_id, svc, rng)
            total_features += 1
            total_files += files
            total_tests += tests

    print(f"  [OK] Generated {total_features} features, {total_files} files, {total_tests} test files")
    return total_features


def _find_service(name: str):
    for s in SERVICES:
        if s.name == name:
            return s
    return None


def _generate_single_feature(output_dir: Path, domain: FeatureDomain, feat_id: str, svc, rng) -> tuple:
    files = 0
    tests = 0

    if svc is None:
        # Infrastructure/shared features
        return 0, 0

    svc_dir = output_dir / svc.name

    if domain.language == "python":
        _write(svc_dir / "app" / "models" / f"{feat_id}.py", _python_model(feat_id, domain.name))
        _write(svc_dir / "app" / "services" / f"{feat_id}.py", _python_service(feat_id, domain.name))
        _write(svc_dir / "app" / "routes" / f"{feat_id}.py", _python_route(feat_id, domain.name))
        _write(svc_dir / "tests" / f"test_{feat_id}.py", _python_test(feat_id, domain.name))
        files += 3
        tests += 1

    elif domain.language == "go":
        _write(svc_dir / "internal" / "handler" / f"{feat_id}.go", _go_handler(feat_id, domain.name))
        _write(svc_dir / "internal" / "model" / f"{feat_id}.go", _go_model(feat_id, domain.name))
        _write(svc_dir / "internal" / "handler" / f"{feat_id}_test.go", _go_test(feat_id, domain.name))
        files += 2
        tests += 1

    elif domain.language == "java":
        pkg_path = svc_dir / "src" / "main" / "java" / "com" / "ecp" / svc.name.replace("-", "")
        test_path = svc_dir / "src" / "test" / "java" / "com" / "ecp" / svc.name.replace("-", "")
        _write(pkg_path / "controller" / f"{_snake_to_camel(feat_id)}Controller.java", _java_controller(feat_id, domain.name, svc.name))
        _write(pkg_path / "service" / f"{_snake_to_camel(feat_id)}Service.java", _java_service(feat_id, domain.name, svc.name))
        _write(pkg_path / "model" / f"{_snake_to_camel(feat_id)}.java", _java_model(feat_id, domain.name, svc.name))
        _write(test_path / "service" / f"{_snake_to_camel(feat_id)}ServiceTest.java", _java_test(feat_id, domain.name, svc.name))
        files += 3
        tests += 1

    elif domain.language == "javascript":
        _write(svc_dir / "src" / "routes" / f"{feat_id}.js", _node_route(feat_id, domain.name))
        _write(svc_dir / "src" / "services" / f"{feat_id}.js", f"// {_snake_to_title(feat_id)} service logic\n")
        _write(svc_dir / "tests" / f"{feat_id}.test.js", _node_test(feat_id, domain.name))
        # Utils logger
        _write(svc_dir / "src" / "utils" / "logger.js", "const winston = require('winston');\nmodule.exports = winston.createLogger({level:'info',transports:[new winston.transports.Console()]});\n")
        files += 2
        tests += 1

    elif domain.language == "typescript":
        if "react" in svc.name or "frontend_customer" in domain.name:
            target = output_dir / "frontend-react"
            _write(target / "src" / "components" / f"{_snake_to_camel(feat_id)}.tsx", _react_component(feat_id, domain.name))
            files += 1
        elif "angular" in svc.name or "admin" in domain.name:
            target = output_dir / "frontend-angular"
            _write(target / "src" / "app" / "pages" / f"{feat_id.replace('_','-')}.component.ts", _angular_component(feat_id, domain.name))
            files += 1

    return files, tests
