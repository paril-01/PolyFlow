package com.ecp.analyticsjava.controller;

import com.ecp.analyticsjava.service.FunnelCompareService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/analytics")
public class FunnelCompareController {

    private final FunnelCompareService service;

    public FunnelCompareController(FunnelCompareService service) {
        this.service = service;
    }

    @PostMapping("/funnel-compare")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/funnel-compare/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "funnel_compare", "status", "operational"));
    }
}
