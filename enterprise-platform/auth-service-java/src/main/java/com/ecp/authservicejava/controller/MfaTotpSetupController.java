package com.ecp.authservicejava.controller;

import com.ecp.authservicejava.service.MfaTotpSetupService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/authentication")
public class MfaTotpSetupController {

    private final MfaTotpSetupService service;

    public MfaTotpSetupController(MfaTotpSetupService service) {
        this.service = service;
    }

    @PostMapping("/mfa-totp-setup")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/mfa-totp-setup/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "mfa_totp_setup", "status", "operational"));
    }
}
