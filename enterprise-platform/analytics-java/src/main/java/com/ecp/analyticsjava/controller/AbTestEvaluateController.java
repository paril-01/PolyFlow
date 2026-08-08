package com.ecp.analyticsjava.controller;

import com.ecp.analyticsjava.service.AbTestEvaluateService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/analytics")
public class AbTestEvaluateController {

    private final AbTestEvaluateService service;

    public AbTestEvaluateController(AbTestEvaluateService service) {
        this.service = service;
    }

    @PostMapping("/ab-test-evaluate")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/ab-test-evaluate/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "ab_test_evaluate", "status", "operational"));
    }
}
