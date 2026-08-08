package com.ecp.authservicejava.controller;

import com.ecp.authservicejava.service.MfaSmsChallengeService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/authentication")
public class MfaSmsChallengeController {

    private final MfaSmsChallengeService service;

    public MfaSmsChallengeController(MfaSmsChallengeService service) {
        this.service = service;
    }

    @PostMapping("/mfa-sms-challenge")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/mfa-sms-challenge/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "mfa_sms_challenge", "status", "operational"));
    }
}
