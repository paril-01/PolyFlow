package com.ecp.analyticsjava.controller;

import com.ecp.analyticsjava.service.EventTrackService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/analytics")
public class EventTrackController {

    private final EventTrackService service;

    public EventTrackController(EventTrackService service) {
        this.service = service;
    }

    @PostMapping("/event-track")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/event-track/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "event_track", "status", "operational"));
    }
}
