package com.ecp.paymentservicejava.controller;

import com.ecp.paymentservicejava.service.EscrowHoldService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/payments")
public class EscrowHoldController {

    private final EscrowHoldService service;

    public EscrowHoldController(EscrowHoldService service) {
        this.service = service;
    }

    @PostMapping("/escrow-hold")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/escrow-hold/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "escrow_hold", "status", "operational"));
    }
}
