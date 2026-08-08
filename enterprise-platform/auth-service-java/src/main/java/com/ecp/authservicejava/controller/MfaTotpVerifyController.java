package com.ecp.authservicejava.controller;

import com.ecp.authservicejava.service.MfaTotpVerifyService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/authentication")
public class MfaTotpVerifyController {

    private final MfaTotpVerifyService service;

    public MfaTotpVerifyController(MfaTotpVerifyService service) {
        this.service = service;
    }

    @PostMapping("/mfa-totp-verify")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/mfa-totp-verify/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "mfa_totp_verify", "status", "operational"));
    }
}
