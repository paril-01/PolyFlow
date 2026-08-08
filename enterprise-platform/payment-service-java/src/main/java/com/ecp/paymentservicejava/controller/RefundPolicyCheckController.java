package com.ecp.paymentservicejava.controller;

import com.ecp.paymentservicejava.service.RefundPolicyCheckService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/payments")
public class RefundPolicyCheckController {

    private final RefundPolicyCheckService service;

    public RefundPolicyCheckController(RefundPolicyCheckService service) {
        this.service = service;
    }

    @PostMapping("/refund-policy-check")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/refund-policy-check/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "refund_policy_check", "status", "operational"));
    }
}
