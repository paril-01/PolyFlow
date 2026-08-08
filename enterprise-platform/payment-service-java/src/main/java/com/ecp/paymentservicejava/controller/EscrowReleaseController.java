package com.ecp.paymentservicejava.controller;

import com.ecp.paymentservicejava.service.EscrowReleaseService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/payments")
public class EscrowReleaseController {

    private final EscrowReleaseService service;

    public EscrowReleaseController(EscrowReleaseService service) {
        this.service = service;
    }

    @PostMapping("/escrow-release")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/escrow-release/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "escrow_release", "status", "operational"));
    }
}
