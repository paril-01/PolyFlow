package com.ecp.analyticsjava.controller;

import com.ecp.analyticsjava.service.CohortComputeService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/analytics")
public class CohortComputeController {

    private final CohortComputeService service;

    public CohortComputeController(CohortComputeService service) {
        this.service = service;
    }

    @PostMapping("/cohort-compute")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/cohort-compute/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "cohort_compute", "status", "operational"));
    }
}
