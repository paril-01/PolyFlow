package com.ecp.authservicejava.controller;

import com.ecp.authservicejava.service.SessionValidateService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/authentication")
public class SessionValidateController {

    private final SessionValidateService service;

    public SessionValidateController(SessionValidateService service) {
        this.service = service;
    }

    @PostMapping("/session-validate")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/session-validate/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "session_validate", "status", "operational"));
    }
}
