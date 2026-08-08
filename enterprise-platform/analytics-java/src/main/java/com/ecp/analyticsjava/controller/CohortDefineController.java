package com.ecp.analyticsjava.controller;

import com.ecp.analyticsjava.service.CohortDefineService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/analytics")
public class CohortDefineController {

    private final CohortDefineService service;

    public CohortDefineController(CohortDefineService service) {
        this.service = service;
    }

    @PostMapping("/cohort-define")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/cohort-define/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "cohort_define", "status", "operational"));
    }
}
