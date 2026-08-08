package com.ecp.analyticsjava.controller;

import com.ecp.analyticsjava.service.EventSchemaValidateService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/analytics")
public class EventSchemaValidateController {

    private final EventSchemaValidateService service;

    public EventSchemaValidateController(EventSchemaValidateService service) {
        this.service = service;
    }

    @PostMapping("/event-schema-validate")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/event-schema-validate/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "event_schema_validate", "status", "operational"));
    }
}
