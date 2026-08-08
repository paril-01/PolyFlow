package com.ecp.paymentservicejava.controller;

import com.ecp.paymentservicejava.service.RefundFullService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/payments")
public class RefundFullController {

    private final RefundFullService service;

    public RefundFullController(RefundFullService service) {
        this.service = service;
    }

    @PostMapping("/refund-full")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/refund-full/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "refund_full", "status", "operational"));
    }
}
