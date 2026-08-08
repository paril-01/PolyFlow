package com.ecp.authservicejava.controller;

import com.ecp.authservicejava.service.PasswordResetConfirmService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/authentication")
public class PasswordResetConfirmController {

    private final PasswordResetConfirmService service;

    public PasswordResetConfirmController(PasswordResetConfirmService service) {
        this.service = service;
    }

    @PostMapping("/password-reset-confirm")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/password-reset-confirm/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "password_reset_confirm", "status", "operational"));
    }
}
