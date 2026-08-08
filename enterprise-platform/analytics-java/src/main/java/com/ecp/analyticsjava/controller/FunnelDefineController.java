package com.ecp.analyticsjava.controller;

import com.ecp.analyticsjava.service.FunnelDefineService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/analytics")
public class FunnelDefineController {

    private final FunnelDefineService service;

    public FunnelDefineController(FunnelDefineService service) {
        this.service = service;
    }

    @PostMapping("/funnel-define")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/funnel-define/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "funnel_define", "status", "operational"));
    }
}
