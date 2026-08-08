package com.ecp.analyticsjava.controller;

import com.ecp.analyticsjava.service.FunnelComputeService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/analytics")
public class FunnelComputeController {

    private final FunnelComputeService service;

    public FunnelComputeController(FunnelComputeService service) {
        this.service = service;
    }

    @PostMapping("/funnel-compute")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/funnel-compute/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "funnel_compute", "status", "operational"));
    }
}
