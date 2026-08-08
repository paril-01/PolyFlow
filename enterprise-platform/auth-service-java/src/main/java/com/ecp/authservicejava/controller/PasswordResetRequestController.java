package com.ecp.authservicejava.controller;

import com.ecp.authservicejava.service.PasswordResetRequestService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/authentication")
public class PasswordResetRequestController {

    private final PasswordResetRequestService service;

    public PasswordResetRequestController(PasswordResetRequestService service) {
        this.service = service;
    }

    @PostMapping("/password-reset-request")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/password-reset-request/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "password_reset_request", "status", "operational"));
    }
}
