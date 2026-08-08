package com.ecp.analyticsjava.controller;

import com.ecp.analyticsjava.service.EventBatchIngestService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/analytics")
public class EventBatchIngestController {

    private final EventBatchIngestService service;

    public EventBatchIngestController(EventBatchIngestService service) {
        this.service = service;
    }

    @PostMapping("/event-batch-ingest")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/event-batch-ingest/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "event_batch_ingest", "status", "operational"));
    }
}
