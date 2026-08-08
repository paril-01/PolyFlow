package com.ecp.analyticsjava.controller;

import com.ecp.analyticsjava.service.AbTestAssignService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/analytics")
public class AbTestAssignController {

    private final AbTestAssignService service;

    public AbTestAssignController(AbTestAssignService service) {
        this.service = service;
    }

    @PostMapping("/ab-test-assign")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/ab-test-assign/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "ab_test_assign", "status", "operational"));
    }
}
