package com.ecp.paymentservicejava.controller;

import com.ecp.paymentservicejava.service.RefundPartialService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/payments")
public class RefundPartialController {

    private final RefundPartialService service;

    public RefundPartialController(RefundPartialService service) {
        this.service = service;
    }

    @PostMapping("/refund-partial")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/refund-partial/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "refund_partial", "status", "operational"));
    }
}
