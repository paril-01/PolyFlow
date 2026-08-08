package com.ecp.analyticsjava.controller;

import com.ecp.analyticsjava.service.RealtimeMetricAlertService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/analytics")
public class RealtimeMetricAlertController {

    private final RealtimeMetricAlertService service;

    public RealtimeMetricAlertController(RealtimeMetricAlertService service) {
        this.service = service;
    }

    @PostMapping("/realtime-metric-alert")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/realtime-metric-alert/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "realtime_metric_alert", "status", "operational"));
    }
}
