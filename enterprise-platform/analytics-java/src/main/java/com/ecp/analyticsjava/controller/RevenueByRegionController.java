package com.ecp.analyticsjava.controller;

import com.ecp.analyticsjava.service.RevenueByRegionService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/analytics")
public class RevenueByRegionController {

    private final RevenueByRegionService service;

    public RevenueByRegionController(RevenueByRegionService service) {
        this.service = service;
    }

    @PostMapping("/revenue-by-region")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/revenue-by-region/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "revenue_by_region", "status", "operational"));
    }
}
