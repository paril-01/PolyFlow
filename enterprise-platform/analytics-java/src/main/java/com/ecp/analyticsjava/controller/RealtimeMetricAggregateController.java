package com.ecp.analyticsjava.controller;

import com.ecp.analyticsjava.service.RealtimeMetricAggregateService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/analytics")
public class RealtimeMetricAggregateController {

    private final RealtimeMetricAggregateService service;

    public RealtimeMetricAggregateController(RealtimeMetricAggregateService service) {
        this.service = service;
    }

    @PostMapping("/realtime-metric-aggregate")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/realtime-metric-aggregate/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "realtime_metric_aggregate", "status", "operational"));
    }
}
