package com.ecp.analyticsjava.controller;

import com.ecp.analyticsjava.service.CohortRetentionService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/analytics")
public class CohortRetentionController {

    private final CohortRetentionService service;

    public CohortRetentionController(CohortRetentionService service) {
        this.service = service;
    }

    @PostMapping("/cohort-retention")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/cohort-retention/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "cohort_retention", "status", "operational"));
    }
}
