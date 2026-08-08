package com.ecp.analyticsjava.controller;

import com.ecp.analyticsjava.service.RevenueDashboardComputeService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/analytics")
public class RevenueDashboardComputeController {

    private final RevenueDashboardComputeService service;

    public RevenueDashboardComputeController(RevenueDashboardComputeService service) {
        this.service = service;
    }

    @PostMapping("/revenue-dashboard-compute")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/revenue-dashboard-compute/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "revenue_dashboard_compute", "status", "operational"));
    }
}
