package com.ecp.authservicejava.controller;

import com.ecp.authservicejava.service.PasswordHashService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/authentication")
public class PasswordHashController {

    private final PasswordHashService service;

    public PasswordHashController(PasswordHashService service) {
        this.service = service;
    }

    @PostMapping("/password-hash")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/password-hash/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "password_hash", "status", "operational"));
    }
}
