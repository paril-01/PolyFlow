package com.ecp.analyticsjava.controller;

import com.ecp.analyticsjava.service.AbTestCreateService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/analytics")
public class AbTestCreateController {

    private final AbTestCreateService service;

    public AbTestCreateController(AbTestCreateService service) {
        this.service = service;
    }

    @PostMapping("/ab-test-create")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/ab-test-create/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "ab_test_create", "status", "operational"));
    }
}
