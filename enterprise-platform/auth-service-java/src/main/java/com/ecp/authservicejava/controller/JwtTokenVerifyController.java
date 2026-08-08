package com.ecp.authservicejava.controller;

import com.ecp.authservicejava.service.JwtTokenVerifyService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/authentication")
public class JwtTokenVerifyController {

    private final JwtTokenVerifyService service;

    public JwtTokenVerifyController(JwtTokenVerifyService service) {
        this.service = service;
    }

    @PostMapping("/jwt-token-verify")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/jwt-token-verify/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "jwt_token_verify", "status", "operational"));
    }
}
